from app.matching.engine import application_to_dict, evaluate_application
from app.time import utcnow
from app.models import (
    Application,
    ApplicationStatus,
    Borrower,
    BusinessCredit,
    Guarantor,
    LoanRequest,
)


def make_app(
    session,
    *,
    fico: int = 720,
    paynet: int | None = 700,
    tib: float = 5,
    state: str = "TX",
    industry: str = "construction",
    amount: float = 80000,
    term: int = 60,
    equipment_type: str = "skid_steer",
    equipment_age: float = 2,
    is_us_citizen: bool = True,
    homeowner: bool = True,
    bankruptcy: bool = False,
    bk_discharge: float | None = None,
    revolving: float = 5000,
    unsecured: float = 5000,
    comp_credit: float = 90,
    is_startup: bool = False,
    is_private_party: bool = False,
    down_payment_pct: float = 15,
) -> Application:
    app = Application(status=ApplicationStatus.submitted, submitted_at=utcnow())
    session.add(app)
    session.flush()
    session.add(
        Borrower(
            application_id=app.id,
            legal_name="Acme LLC",
            industry=industry,
            state=state,
            years_in_business=tib,
            annual_revenue=500000,
            is_us_citizen=is_us_citizen,
            is_startup=is_startup,
        )
    )
    session.add(
        Guarantor(
            application_id=app.id,
            name="Pat Owner",
            fico=fico,
            homeowner=homeowner,
            has_bankruptcy=bankruptcy,
            bk_discharge_years=bk_discharge,
            revolving_balance=revolving,
            unsecured_debt=unsecured,
        )
    )
    session.add(
        BusinessCredit(
            application_id=app.id,
            paynet_score=paynet,
            comparable_credit_pct=comp_credit,
            trade_lines_count=5,
        )
    )
    session.add(
        LoanRequest(
            application_id=app.id,
            amount=amount,
            term_months=term,
            equipment_type=equipment_type,
            equipment_age_years=equipment_age,
            is_private_party=is_private_party,
            down_payment_pct=down_payment_pct,
        )
    )
    session.commit()
    session.refresh(app)
    return app


def test_strong_app_matches_multiple_lenders(seeded_session):
    app = make_app(seeded_session)
    results = evaluate_application(seeded_session, app)
    eligible = [r for r in results if r.eligible]
    assert len(eligible) >= 3, f"expected 3+ matches, got {len(eligible)}: {[(r.lender_id, r.eligible) for r in results]}"


def test_low_fico_breaks_top_tier(seeded_session):
    app = make_app(seeded_session, fico=640, paynet=640, tib=2, amount=40000)
    results = evaluate_application(seeded_session, app)
    eligible_count = sum(1 for r in results if r.eligible)
    assert eligible_count < len(results)


def test_california_excludes_apex_and_citizens(seeded_session):
    app = make_app(seeded_session, state="CA", amount=40000)
    results = evaluate_application(seeded_session, app)
    # find apex + citizens results - they should be ineligible due to state
    fail_reasons = []
    for r in results:
        if not r.eligible:
            for ev in r.evaluations:
                if not ev.passed and "state" in ev.field.lower():
                    fail_reasons.append(ev.message)
    assert any("CA" in m for m in fail_reasons), f"expected CA exclusion; got: {fail_reasons}"


def test_cannabis_excluded_everywhere_relevant(seeded_session):
    app = make_app(seeded_session, industry="cannabis", amount=40000)
    results = evaluate_application(seeded_session, app)
    industry_fails = [
        ev for r in results for ev in r.evaluations if not ev.passed and "industry" in ev.field
    ]
    assert any("cannabis" in (ev.message or "").lower() for ev in industry_fails)


def test_oversized_amount_falls_through_to_higher_program(seeded_session):
    app = make_app(seeded_session, amount=300000)
    results = evaluate_application(seeded_session, app)
    eligible = [r for r in results if r.eligible]
    assert len(eligible) >= 1


def test_ineligible_returns_detailed_reasons(seeded_session):
    app = make_app(seeded_session, fico=580, paynet=580, tib=1, bankruptcy=True)
    results = evaluate_application(seeded_session, app)
    assert all(not r.eligible for r in results)
    for r in results:
        if r.evaluations:
            failed = [ev for ev in r.evaluations if not ev.passed]
            assert len(failed) > 0


def test_application_to_dict_shape():
    class M:
        def model_dump(self):
            return {"fico": 720, "application_id": 1}

    class App:
        borrower = M()
        guarantor = M()
        business_credit = None
        loan_request = None

    d = application_to_dict(App())
    assert "fico" in d["guarantor"]
    assert "application_id" not in d["guarantor"]
    assert d["business_credit"] == {}
