from datetime import datetime

from pydantic import BaseModel, Field

from app.models.application import ApplicationStatus


class BorrowerIn(BaseModel):
    legal_name: str
    industry: str
    state: str = Field(min_length=2, max_length=2)
    years_in_business: float
    annual_revenue: float
    is_us_citizen: bool = True
    has_physical_location: bool = True
    is_startup: bool = False


class GuarantorIn(BaseModel):
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


class BusinessCreditIn(BaseModel):
    paynet_score: int | None = None
    comparable_credit_pct: float = 0
    trade_lines_count: int = 0
    clean_payment_history_months: int = 0


class LoanRequestIn(BaseModel):
    amount: float
    term_months: int
    equipment_type: str
    equipment_year: int | None = None
    equipment_age_years: float | None = None
    down_payment_pct: float = 0
    is_private_party: bool = False


class ApplicationCreate(BaseModel):
    borrower: BorrowerIn
    guarantor: GuarantorIn
    business_credit: BusinessCreditIn
    loan_request: LoanRequestIn


class ApplicationSummary(BaseModel):
    id: int
    status: ApplicationStatus
    legal_name: str | None
    amount: float | None
    state: str | None
    industry: str | None
    created_at: datetime


class ApplicationRead(BaseModel):
    id: int
    status: ApplicationStatus
    created_at: datetime
    updated_at: datetime
    submitted_at: datetime | None
    borrower: BorrowerIn | None
    guarantor: GuarantorIn | None
    business_credit: BusinessCreditIn | None
    loan_request: LoanRequestIn | None
