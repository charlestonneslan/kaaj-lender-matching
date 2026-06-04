"""Derived features computed from raw application input.

The application form takes what an underwriter actually has on the form
(equipment year, industry slug, etc.). The matching engine needs
secondary features (equipment age, broad business type) derived from
those. Keep derivation here so rules can reference the derived fields
the same way they reference input fields.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

INDUSTRY_TO_BUSINESS_TYPE: dict[str, str] = {
    "construction": "trades",
    "manufacturing": "manufacturing",
    "machine_tools": "manufacturing",
    "woodworking": "manufacturing",
    "trucking": "transportation",
    "logging": "transportation",
    "medical": "professional",
    "restaurant": "hospitality",
    "cannabis": "regulated",
    "oil_gas": "regulated",
    "gaming": "regulated",
}


def derive(app_data: dict, today: datetime | None = None) -> dict:
    today = today or datetime.utcnow()
    loan = dict(app_data.get("loan_request") or {})
    borrower = dict(app_data.get("borrower") or {})

    year = loan.get("equipment_year")
    if year and not loan.get("equipment_age_years"):
        loan["equipment_age_years"] = float(today.year - int(year))

    industry = borrower.get("industry")
    if industry:
        borrower["business_type"] = INDUSTRY_TO_BUSINESS_TYPE.get(
            industry.lower(), "other"
        )

    return {
        **app_data,
        "loan_request": loan,
        "borrower": borrower,
    }


def maybe_derive(value: Any, fallback: Any = None) -> Any:
    return value if value is not None else fallback
