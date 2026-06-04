from typing import Any

from pydantic import BaseModel


class RuleIn(BaseModel):
    kind: str
    field: str
    op: str
    value: Any
    weight: int = 1
    hard: bool = True
    message: str | None = None


class RuleRead(RuleIn):
    id: int
    program_id: int


class ProgramRead(BaseModel):
    id: int
    name: str
    priority: int
    base_rate: float | None
    notes: str | None
    rules: list[RuleRead]


class LenderRead(BaseModel):
    id: int
    slug: str
    name: str
    contact: str | None
    notes: str | None
    active: bool
    programs: list[ProgramRead]
