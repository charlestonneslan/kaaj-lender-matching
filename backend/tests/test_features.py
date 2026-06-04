from datetime import datetime

from app.matching.features import derive


def test_derives_equipment_age_from_year():
    out = derive(
        {"loan_request": {"equipment_year": 2020}},
        today=datetime(2026, 6, 1),
    )
    assert out["loan_request"]["equipment_age_years"] == 6


def test_preserves_explicit_equipment_age():
    out = derive(
        {"loan_request": {"equipment_year": 2020, "equipment_age_years": 3}},
        today=datetime(2026, 6, 1),
    )
    assert out["loan_request"]["equipment_age_years"] == 3


def test_derives_business_type_from_industry():
    out = derive({"borrower": {"industry": "trucking"}})
    assert out["borrower"]["business_type"] == "transportation"


def test_unknown_industry_falls_back_to_other():
    out = derive({"borrower": {"industry": "underwater_basket_weaving"}})
    assert out["borrower"]["business_type"] == "other"


def test_missing_sections_dont_crash():
    out = derive({})
    assert out["borrower"] == {}
    assert out["loan_request"] == {}
