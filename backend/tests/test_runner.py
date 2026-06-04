import asyncio

import pytest

from app.matching.runner import run_async, with_retry
from app.models import RunStatus, UnderwritingRun
from tests.test_engine import make_app


def test_async_runner_parallelizes_and_completes(seeded_session):
    app = make_app(seeded_session)
    run = UnderwritingRun(application_id=app.id)
    seeded_session.add(run)
    seeded_session.commit()
    seeded_session.refresh(run)

    results = asyncio.run(run_async(seeded_session, app, run))

    assert run.status == RunStatus.completed
    assert run.lenders_total == run.lenders_done == 5
    eligible = [r for r in results if r.eligible]
    assert len(eligible) >= 3


def test_retry_succeeds_after_transient_failures():
    calls = {"n": 0}

    async def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise RuntimeError("transient")
        return "ok"

    out = asyncio.run(with_retry(flaky, attempts=3, base_delay=0.001, label="t"))
    assert out == "ok"
    assert calls["n"] == 3


def test_retry_raises_after_exhausting_attempts():
    async def always_fails():
        raise RuntimeError("nope")

    with pytest.raises(RuntimeError):
        asyncio.run(with_retry(always_fails, attempts=2, base_delay=0.001, label="t"))
