from dataclasses import dataclass, field

from sqlmodel import Session, select

from app.matching.features import derive
from app.matching.rules import EvalOutcome, RuleSpec, evaluate_rule
from app.models import (
    Application,
    Lender,
    MatchResult,
    Program,
    Rule,
    RuleEvaluation,
)


@dataclass
class ProgramOutcome:
    program: Program
    eligible: bool
    fit_score: float
    outcomes: list[tuple[Rule, EvalOutcome]] = field(default_factory=list)


@dataclass
class LenderOutcome:
    lender: Lender
    best: ProgramOutcome | None
    all_programs: list[ProgramOutcome]


def application_to_dict(app: Application) -> dict:
    def asdict(model) -> dict:
        if model is None:
            return {}
        return {k: v for k, v in model.model_dump().items() if k != "application_id"}

    return {
        "borrower": asdict(app.borrower),
        "guarantor": asdict(app.guarantor),
        "business_credit": asdict(app.business_credit),
        "loan_request": asdict(app.loan_request),
    }


def evaluate_program(program: Program, app_data: dict) -> ProgramOutcome:
    outcomes: list[tuple[Rule, EvalOutcome]] = []
    any_hard_failed = False
    weight_total = 0
    weight_passed = 0

    for rule in program.rules:
        spec = RuleSpec(
            kind=rule.kind,
            field=rule.field,
            op=rule.op,
            value=rule.value,
            weight=rule.weight,
            hard=rule.hard,
            message=rule.message,
        )
        outcome = evaluate_rule(spec, app_data)
        outcomes.append((rule, outcome))

        weight_total += rule.weight
        if outcome.passed:
            weight_passed += rule.weight
        elif rule.hard:
            any_hard_failed = True

    fit_score = (weight_passed / weight_total * 100.0) if weight_total else 0.0
    eligible = not any_hard_failed

    return ProgramOutcome(
        program=program,
        eligible=eligible,
        fit_score=round(fit_score, 2),
        outcomes=outcomes,
    )


def evaluate_application(session: Session, application: Application) -> list[MatchResult]:
    app_data = derive(application_to_dict(application))
    lenders = session.exec(select(Lender).where(Lender.active == True)).all()  # noqa: E712

    existing = session.exec(
        select(MatchResult).where(MatchResult.application_id == application.id)
    ).all()
    for old in existing:
        session.delete(old)
    session.flush()

    lender_outcomes: list[tuple[Lender, ProgramOutcome | None]] = []
    for lender in lenders:
        program_outs = [evaluate_program(p, app_data) for p in lender.programs]
        if not program_outs:
            lender_outcomes.append((lender, None))
            continue

        eligible_outs = [p for p in program_outs if p.eligible]
        best = max(eligible_outs, key=lambda p: p.fit_score) if eligible_outs else max(
            program_outs, key=lambda p: p.fit_score
        )
        lender_outcomes.append((lender, best))

    lender_outcomes.sort(
        key=lambda lo: (
            lo[1].eligible if lo[1] else False,
            lo[1].fit_score if lo[1] else 0.0,
        ),
        reverse=True,
    )

    results: list[MatchResult] = []
    for rank, (lender, best) in enumerate(lender_outcomes, start=1):
        if best is None:
            mr = MatchResult(
                application_id=application.id,
                lender_id=lender.id,
                program_id=None,
                eligible=False,
                fit_score=0.0,
                rank=rank,
            )
            session.add(mr)
            results.append(mr)
            continue

        mr = MatchResult(
            application_id=application.id,
            lender_id=lender.id,
            program_id=best.program.id,
            eligible=best.eligible,
            fit_score=best.fit_score,
            rank=rank,
        )
        session.add(mr)
        session.flush()

        for rule, outcome in best.outcomes:
            ev = RuleEvaluation(
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
            session.add(ev)
        results.append(mr)

    session.commit()
    return results
