from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db import get_session
from app.matching.engine import evaluate_application
from app.models import (
    Application,
    ApplicationStatus,
    Borrower,
    BusinessCredit,
    Guarantor,
    Lender,
    LoanRequest,
    MatchResult,
    Program,
)
from app.schemas import (
    ApplicationCreate,
    ApplicationRead,
    ApplicationSummary,
    BorrowerIn,
    BusinessCreditIn,
    GuarantorIn,
    LoanRequestIn,
    MatchResultRead,
    RuleEvaluationRead,
)

router = APIRouter(prefix="/applications", tags=["applications"])


def _to_read(app: Application) -> ApplicationRead:
    def maybe(model, schema):
        if model is None:
            return None
        return schema.model_validate(model.model_dump())

    return ApplicationRead(
        id=app.id,
        status=app.status,
        created_at=app.created_at,
        updated_at=app.updated_at,
        submitted_at=app.submitted_at,
        borrower=maybe(app.borrower, BorrowerIn),
        guarantor=maybe(app.guarantor, GuarantorIn),
        business_credit=maybe(app.business_credit, BusinessCreditIn),
        loan_request=maybe(app.loan_request, LoanRequestIn),
    )


@router.get("", response_model=list[ApplicationSummary])
def list_applications(session: Session = Depends(get_session)):
    rows = session.exec(select(Application).order_by(Application.created_at.desc())).all()
    out: list[ApplicationSummary] = []
    for a in rows:
        out.append(
            ApplicationSummary(
                id=a.id,
                status=a.status,
                legal_name=a.borrower.legal_name if a.borrower else None,
                amount=a.loan_request.amount if a.loan_request else None,
                state=a.borrower.state if a.borrower else None,
                industry=a.borrower.industry if a.borrower else None,
                created_at=a.created_at,
            )
        )
    return out


@router.post("", response_model=ApplicationRead, status_code=201)
def create_application(payload: ApplicationCreate, session: Session = Depends(get_session)):
    app = Application(status=ApplicationStatus.submitted, submitted_at=datetime.utcnow())
    session.add(app)
    session.flush()

    session.add(Borrower(application_id=app.id, **payload.borrower.model_dump()))
    session.add(Guarantor(application_id=app.id, **payload.guarantor.model_dump()))
    session.add(BusinessCredit(application_id=app.id, **payload.business_credit.model_dump()))
    session.add(LoanRequest(application_id=app.id, **payload.loan_request.model_dump()))

    session.commit()
    session.refresh(app)
    return _to_read(app)


@router.get("/{app_id}", response_model=ApplicationRead)
def get_application(app_id: int, session: Session = Depends(get_session)):
    app = session.get(Application, app_id)
    if app is None:
        raise HTTPException(404, "application not found")
    return _to_read(app)


@router.delete("/{app_id}", status_code=204)
def delete_application(app_id: int, session: Session = Depends(get_session)):
    app = session.get(Application, app_id)
    if app is None:
        raise HTTPException(404, "application not found")
    session.delete(app)
    session.commit()


@router.post("/{app_id}/evaluate", response_model=list[MatchResultRead])
def run_evaluation(app_id: int, session: Session = Depends(get_session)):
    app = session.get(Application, app_id)
    if app is None:
        raise HTTPException(404, "application not found")
    if app.borrower is None or app.loan_request is None:
        raise HTTPException(400, "application missing required sections")

    results = evaluate_application(session, app)
    app.status = ApplicationStatus.evaluated
    session.add(app)
    session.commit()
    return _results_to_read(session, results)


@router.get("/{app_id}/results", response_model=list[MatchResultRead])
def get_results(app_id: int, session: Session = Depends(get_session)):
    app = session.get(Application, app_id)
    if app is None:
        raise HTTPException(404, "application not found")
    results = session.exec(
        select(MatchResult).where(MatchResult.application_id == app_id).order_by(MatchResult.rank)
    ).all()
    return _results_to_read(session, results)


def _results_to_read(session: Session, results: list[MatchResult]) -> list[MatchResultRead]:
    lender_names = {l.id: l.name for l in session.exec(select(Lender)).all()}
    program_names = {p.id: p.name for p in session.exec(select(Program)).all()}
    out: list[MatchResultRead] = []
    for r in results:
        evals = [
            RuleEvaluationRead(
                id=e.id,
                rule_id=e.rule_id,
                field=e.field,
                op=e.op,
                required=e.required,
                actual=e.actual,
                passed=e.passed,
                hard=e.hard,
                weight=e.weight,
                message=e.message,
            )
            for e in r.evaluations
        ]
        out.append(
            MatchResultRead(
                id=r.id,
                lender_id=r.lender_id,
                lender_name=lender_names.get(r.lender_id, "?"),
                program_id=r.program_id,
                program_name=program_names.get(r.program_id) if r.program_id else None,
                eligible=r.eligible,
                fit_score=r.fit_score,
                rank=r.rank,
                evaluations=evals,
            )
        )
    return out
