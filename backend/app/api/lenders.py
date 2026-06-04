from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db import get_session
from app.models import Lender, Program, Rule
from app.schemas import LenderRead, ProgramRead, RuleIn, RuleRead

router = APIRouter(prefix="/lenders", tags=["lenders"])


def _to_lender_read(lender: Lender) -> LenderRead:
    programs = sorted(lender.programs, key=lambda p: p.priority)
    return LenderRead(
        id=lender.id,
        slug=lender.slug,
        name=lender.name,
        contact=lender.contact,
        notes=lender.notes,
        active=lender.active,
        programs=[
            ProgramRead(
                id=p.id,
                name=p.name,
                priority=p.priority,
                base_rate=p.base_rate,
                notes=p.notes,
                rules=[
                    RuleRead(
                        id=r.id,
                        program_id=r.program_id,
                        kind=r.kind,
                        field=r.field,
                        op=r.op,
                        value=r.value,
                        weight=r.weight,
                        hard=r.hard,
                        message=r.message,
                    )
                    for r in p.rules
                ],
            )
            for p in programs
        ],
    )


@router.get("", response_model=list[LenderRead])
def list_lenders(session: Session = Depends(get_session)):
    lenders = session.exec(select(Lender).order_by(Lender.name)).all()
    return [_to_lender_read(l) for l in lenders]


@router.get("/{lender_id}", response_model=LenderRead)
def get_lender(lender_id: int, session: Session = Depends(get_session)):
    lender = session.get(Lender, lender_id)
    if lender is None:
        raise HTTPException(404, "lender not found")
    return _to_lender_read(lender)


@router.patch("/rules/{rule_id}", response_model=RuleRead)
def update_rule(rule_id: int, payload: RuleIn, session: Session = Depends(get_session)):
    rule = session.get(Rule, rule_id)
    if rule is None:
        raise HTTPException(404, "rule not found")
    for field, value in payload.model_dump().items():
        setattr(rule, field, value)
    session.add(rule)
    session.commit()
    session.refresh(rule)
    return RuleRead(
        id=rule.id,
        program_id=rule.program_id,
        kind=rule.kind,
        field=rule.field,
        op=rule.op,
        value=rule.value,
        weight=rule.weight,
        hard=rule.hard,
        message=rule.message,
    )


@router.post("/programs/{program_id}/rules", response_model=RuleRead, status_code=201)
def add_rule(program_id: int, payload: RuleIn, session: Session = Depends(get_session)):
    program = session.get(Program, program_id)
    if program is None:
        raise HTTPException(404, "program not found")
    rule = Rule(program_id=program_id, **payload.model_dump())
    session.add(rule)
    session.commit()
    session.refresh(rule)
    return RuleRead(
        id=rule.id,
        program_id=rule.program_id,
        kind=rule.kind,
        field=rule.field,
        op=rule.op,
        value=rule.value,
        weight=rule.weight,
        hard=rule.hard,
        message=rule.message,
    )


@router.delete("/rules/{rule_id}", status_code=204)
def delete_rule(rule_id: int, session: Session = Depends(get_session)):
    rule = session.get(Rule, rule_id)
    if rule is None:
        raise HTTPException(404, "rule not found")
    session.delete(rule)
    session.commit()
