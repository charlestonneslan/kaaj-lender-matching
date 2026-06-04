from app.matching.rules import RuleSpec, evaluate_rule, get_field


def test_get_field_dotted():
    app = {"guarantor": {"fico": 720}, "borrower": {"state": "TX"}}
    assert get_field(app, "guarantor.fico") == 720
    assert get_field(app, "borrower.state") == "TX"
    assert get_field(app, "loan_request.amount") is None


def test_numeric_gte_pass():
    spec = RuleSpec(kind="numeric", field="guarantor.fico", op="gte", value=700)
    out = evaluate_rule(spec, {"guarantor": {"fico": 720}})
    assert out.passed
    assert out.actual == 720


def test_numeric_gte_fail():
    spec = RuleSpec(
        kind="numeric",
        field="guarantor.fico",
        op="gte",
        value=700,
        message="FICO {actual} below required {required}",
    )
    out = evaluate_rule(spec, {"guarantor": {"fico": 650}})
    assert not out.passed
    assert "650" in out.message
    assert "700" in out.message


def test_numeric_between():
    spec = RuleSpec(kind="numeric", field="loan_request.amount", op="between", value=[10000, 75000])
    assert evaluate_rule(spec, {"loan_request": {"amount": 50000}}).passed
    assert not evaluate_rule(spec, {"loan_request": {"amount": 80000}}).passed
    assert not evaluate_rule(spec, {"loan_request": {"amount": 5000}}).passed


def test_set_not_in():
    spec = RuleSpec(
        kind="set",
        field="borrower.industry",
        op="not_in",
        value=["cannabis", "gambling"],
    )
    assert evaluate_rule(spec, {"borrower": {"industry": "construction"}}).passed
    assert not evaluate_rule(spec, {"borrower": {"industry": "cannabis"}}).passed


def test_set_case_insensitive():
    spec = RuleSpec(kind="set", field="borrower.state", op="not_in", value=["CA", "NV"])
    assert not evaluate_rule(spec, {"borrower": {"state": "ca"}}).passed


def test_boolean():
    spec = RuleSpec(kind="boolean", field="guarantor.has_bankruptcy", op="eq", value=False)
    assert evaluate_rule(spec, {"guarantor": {"has_bankruptcy": False}}).passed
    assert not evaluate_rule(spec, {"guarantor": {"has_bankruptcy": True}}).passed


def test_composite_revolver():
    spec = RuleSpec(kind="composite", field="revolver_limit", op="call", value=None)
    safe = {"guarantor": {"revolving_balance": 10000, "unsecured_debt": 5000}}
    over = {"guarantor": {"revolving_balance": 35000, "unsecured_debt": 0}}
    combined = {"guarantor": {"revolving_balance": 20000, "unsecured_debt": 40000}}
    assert evaluate_rule(spec, safe).passed
    assert not evaluate_rule(spec, over).passed
    assert not evaluate_rule(spec, combined).passed


def test_composite_comp_credit():
    spec = RuleSpec(kind="composite", field="comp_credit_pct", op="call", value=70)
    assert evaluate_rule(spec, {"business_credit": {"comparable_credit_pct": 80}}).passed
    assert not evaluate_rule(spec, {"business_credit": {"comparable_credit_pct": 50}}).passed


def test_missing_field_fails_numeric():
    spec = RuleSpec(kind="numeric", field="guarantor.fico", op="gte", value=700)
    assert not evaluate_rule(spec, {"guarantor": {}}).passed
