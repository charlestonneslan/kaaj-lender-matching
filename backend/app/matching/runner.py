"""Async runner that evaluates an application against every lender in parallel.

The synchronous `engine.evaluate_application` is still the primitive — this
module just spreads per-lender evaluation across asyncio.gather so the whole
underwriting run finishes in roughly max(lender_time) instead of sum(lender_time),
and wraps each per-lender call in a retry so a transient failure in one
lender's evaluation doesn't sink the run.

In production this is the shape a Hatchet workflow would orchestrate
across workers: one fan-out task per lender, a join step that writes the
ranked results, with the same retry semantics enforced by Hatchet's
retry policy instead of the inline decorator.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Awaitable, Callable, TypeVar

from sqlmodel import Session, select

from app.matching.engine import (
    LenderOutcome,
    ProgramOutcome,
    application_to_dict,
    evaluate_program,
)
from app.matching.features import derive
from app.models import (
    Application,
    Lender,
    MatchResult,
    RuleEvaluation,
    RunStatus,
    UnderwritingRun,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")


async def with_retry(
    fn: Callable[[], Awaitable[T]],
    *,
    attempts: int = 3,
    base_delay: float = 0.05,
    label: str = "task",
) -> T:
    last: Exception | None = None
    for i in range(attempts):
        try:
            return await fn()
        except Exception as e:
            last = e
            wait = base_delay * (2**i)
            logger.warning("%s failed (attempt %d/%d): %s", label, i + 1, attempts, e)
            await asyncio.sleep(wait)
    assert last is not None
    raise last


async def _eval_one_lender(lender: Lender, app_data: dict) -> tuple[Lender, ProgramOutcome | None]:
    async def task():
        program_outs = [evaluate_program(p, app_data) for p in lender.programs]
        if not program_outs:
            return None
        eligible = [p for p in program_outs if p.eligible]
        return max(eligible, key=lambda p: p.fit_score) if eligible else max(
            program_outs, key=lambda p: p.fit_score
        )

    best = await with_retry(task, label=f"evaluate:{lender.slug}")
    return lender, best


async def run_async(
    session: Session, application: Application, run: UnderwritingRun
) -> list[MatchResult]:
    run.status = RunStatus.running
    run.started_at = datetime.utcnow()
    session.add(run)
    session.commit()

    try:
        app_data = derive(application_to_dict(application))
        lenders = session.exec(select(Lender).where(Lender.active == True)).all()  # noqa: E712
        run.lenders_total = len(lenders)
        session.add(run)
        session.commit()

        for old in session.exec(
            select(MatchResult).where(MatchResult.application_id == application.id)
        ).all():
            session.delete(old)
        session.flush()

        outcomes = await asyncio.gather(
            *(_eval_one_lender(l, app_data) for l in lenders)
        )
        outcomes.sort(
            key=lambda lo: (
                lo[1].eligible if lo[1] else False,
                lo[1].fit_score if lo[1] else 0.0,
            ),
            reverse=True,
        )

        results: list[MatchResult] = []
        for rank, (lender, best) in enumerate(outcomes, start=1):
            mr = MatchResult(
                application_id=application.id,
                lender_id=lender.id,
                program_id=best.program.id if best else None,
                eligible=best.eligible if best else False,
                fit_score=best.fit_score if best else 0.0,
                rank=rank,
            )
            session.add(mr)
            session.flush()
            if best is None:
                continue
            for rule, outcome in best.outcomes:
                session.add(
                    RuleEvaluation(
                        match_result_id=mr.id,
                        rule_id=rule.id,
                        passed=outcome.passed,
                        hard=rule.hard,
                        weight=rule.weight,
                        field=rule.field,
                        op=rule.op,
                        required=outcome.required,
                        actual=outcome.actual,
                        message=outcome.message,
                    )
                )
            results.append(mr)
            run.lenders_done = rank
            session.add(run)
            session.commit()

        run.status = RunStatus.completed
        run.finished_at = datetime.utcnow()
        session.add(run)
        session.commit()
        return results
    except Exception as e:
        run.status = RunStatus.failed
        run.error = str(e)
        run.finished_at = datetime.utcnow()
        session.add(run)
        session.commit()
        raise


__all__ = ["run_async", "with_retry", "LenderOutcome"]
