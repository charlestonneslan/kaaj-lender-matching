from typing import Any

from pydantic import BaseModel, Field


class RuleIn(BaseModel):
    kind: str
    field: str
    op: str
    value: Any
    weight: int = 1
    hard: bool = True
    message: str | None = None


class ProgramIn(BaseModel):
    name: str
    priority: int = 0
    base_rate: float | None = None
    notes: str | None = None
    rules: list[RuleIn] = Field(default_factory=list)


class LenderIn(BaseModel):
    slug: str
    name: str
    contact: str | None = None
    notes: str | None = None
    active: bool = True
    programs: list[ProgramIn] = Field(default_factory=list)


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
