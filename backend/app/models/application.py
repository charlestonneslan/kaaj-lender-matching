from datetime import datetime
from enum import StrEnum
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel


class ApplicationStatus(StrEnum):
    draft = "draft"
    submitted = "submitted"
    evaluated = "evaluated"


class Application(SQLModel, table=True):
    __tablename__ = "applications"

    id: int | None = Field(default=None, primary_key=True)
    status: ApplicationStatus = Field(default=ApplicationStatus.draft)
    submitted_at: datetime | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    borrower: Optional["Borrower"] = Relationship(
        back_populates="application",
        sa_relationship_kwargs={"uselist": False, "cascade": "all, delete-orphan"},
    )
    guarantor: Optional["Guarantor"] = Relationship(
        back_populates="application",
        sa_relationship_kwargs={"uselist": False, "cascade": "all, delete-orphan"},
    )
    business_credit: Optional["BusinessCredit"] = Relationship(
        back_populates="application",
        sa_relationship_kwargs={"uselist": False, "cascade": "all, delete-orphan"},
    )
    loan_request: Optional["LoanRequest"] = Relationship(
        back_populates="application",
        sa_relationship_kwargs={"uselist": False, "cascade": "all, delete-orphan"},
    )


class Borrower(SQLModel, table=True):
    __tablename__ = "borrowers"

    id: int | None = Field(default=None, primary_key=True)
    application_id: int = Field(foreign_key="applications.id", unique=True)

    legal_name: str
    industry: str
    state: str = Field(max_length=2)
    years_in_business: float
    annual_revenue: float
    is_us_citizen: bool = True
    has_physical_location: bool = True
    is_startup: bool = False

    application: Optional[Application] = Relationship(back_populates="borrower")


class Guarantor(SQLModel, table=True):
    __tablename__ = "guarantors"

    id: int | None = Field(default=None, primary_key=True)
    application_id: int = Field(foreign_key="applications.id", unique=True)

    name: str
    fico: int
    revolving_balance: float = 0
    unsecured_debt: float = 0
    homeowner: bool = False
    has_bankruptcy: bool = False
    bk_discharge_years: float | None = None
    has_judgments: bool = False
    has_foreclosure: bool = False
    has_repossession: bool = False
    has_tax_lien: bool = False
    has_recent_collections: bool = False

    application: Optional[Application] = Relationship(back_populates="guarantor")


class BusinessCredit(SQLModel, table=True):
    __tablename__ = "business_credit"

    id: int | None = Field(default=None, primary_key=True)
    application_id: int = Field(foreign_key="applications.id", unique=True)

    paynet_score: int | None = None
    comparable_credit_pct: float = 0
    trade_lines_count: int = 0
    clean_payment_history_months: int = 0

    application: Optional[Application] = Relationship(back_populates="business_credit")


class LoanRequest(SQLModel, table=True):
    __tablename__ = "loan_requests"

    id: int | None = Field(default=None, primary_key=True)
    application_id: int = Field(foreign_key="applications.id", unique=True)

    amount: float
    term_months: int
    equipment_type: str
    equipment_year: int | None = None
    equipment_age_years: float | None = None
    down_payment_pct: float = 0
    is_private_party: bool = False

    application: Optional[Application] = Relationship(back_populates="loan_request")
