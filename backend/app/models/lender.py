from datetime import datetime
from typing import Any, Optional

from sqlalchemy import JSON, Column
from sqlmodel import Field, Relationship, SQLModel


class Lender(SQLModel, table=True):
    __tablename__ = "lenders"

    id: int | None = Field(default=None, primary_key=True)
    slug: str = Field(index=True, unique=True)
    name: str
    contact: str | None = None
    notes: str | None = None
    active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    programs: list["Program"] = Relationship(
        back_populates="lender",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class Program(SQLModel, table=True):
    __tablename__ = "programs"

    id: int | None = Field(default=None, primary_key=True)
    lender_id: int = Field(foreign_key="lenders.id", index=True)
    name: str
    priority: int = 0
    base_rate: float | None = None
    notes: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    lender: Optional[Lender] = Relationship(back_populates="programs")
    rules: list["Rule"] = Relationship(
        back_populates="program",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class Rule(SQLModel, table=True):
    __tablename__ = "rules"

    id: int | None = Field(default=None, primary_key=True)
    program_id: int = Field(foreign_key="programs.id", index=True)
    kind: str
    field: str
    op: str
    value: Any = Field(sa_column=Column(JSON))
    weight: int = 1
    hard: bool = True
    message: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    program: Optional[Program] = Relationship(back_populates="rules")
