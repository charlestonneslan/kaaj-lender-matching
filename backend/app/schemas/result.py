from typing import Any

from pydantic import BaseModel


class RuleEvaluationRead(BaseModel):
    id: int
    rule_id: int
    field: str
    op: str
    required: Any
    actual: Any
    passed: bool
    hard: bool
    weight: int
    message: str


class MatchResultRead(BaseModel):
    id: int
    lender_id: int
    lender_name: str
    program_id: int | None
    program_name: str | None
    eligible: bool
    fit_score: float
    rank: int | None
    evaluations: list[RuleEvaluationRead]
