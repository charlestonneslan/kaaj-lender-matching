from datetime import datetime
from typing import Any, Optional

from sqlalchemy import JSON, Column
from sqlmodel import Field, Relationship, SQLModel


class MatchResult(SQLModel, table=True):
    __tablename__ = "match_results"

    id: int | None = Field(default=None, primary_key=True)
    application_id: int = Field(foreign_key="applications.id", index=True)
    lender_id: int = Field(foreign_key="lenders.id", index=True)
    program_id: int | None = Field(default=None, foreign_key="programs.id")
    eligible: bool = False
    fit_score: float = 0.0
    rank: int | None = None
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)

    evaluations: list["RuleEvaluation"] = Relationship(
        back_populates="match_result",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class RuleEvaluation(SQLModel, table=True):
    __tablename__ = "rule_evaluations"

    id: int | None = Field(default=None, primary_key=True)
    match_result_id: int = Field(foreign_key="match_results.id", index=True)
    rule_id: int = Field(foreign_key="rules.id")
    passed: bool
    hard: bool
    weight: int
    field: str
    op: str
    required: Any = Field(sa_column=Column(JSON))
    actual: Any = Field(sa_column=Column(JSON))
    message: str

    match_result: Optional[MatchResult] = Relationship(back_populates="evaluations")
