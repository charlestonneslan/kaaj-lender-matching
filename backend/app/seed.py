import sys
from pathlib import Path

import yaml
from sqlmodel import Session, select

from app.db import engine, init_db
from app.models import Lender, MatchResult, Program, Rule

LENDERS_DIR = Path(__file__).resolve().parent.parent / "lenders"


def load_yaml(path: Path) -> dict:
    with path.open() as f:
        return yaml.safe_load(f)


def upsert_lender(session: Session, data: dict) -> Lender:
    existing = session.exec(select(Lender).where(Lender.slug == data["slug"])).first()
    if existing is None:
        lender = Lender(
            slug=data["slug"],
            name=data["name"],
            contact=data.get("contact"),
            notes=data.get("notes"),
        )
        session.add(lender)
        session.flush()
    else:
        existing.name = data["name"]
        existing.contact = data.get("contact")
        existing.notes = data.get("notes")
        # Replacing this lender's programs invalidates any prior results that
        # reference its rules, so clear them first (cascades to the per-rule
        # evaluations). Otherwise the program/rule delete trips their FKs.
        for mr in session.exec(select(MatchResult).where(MatchResult.lender_id == existing.id)):
            session.delete(mr)
        session.flush()
        for program in existing.programs:
            session.delete(program)
        session.flush()
        lender = existing

    for idx, prog_data in enumerate(data.get("programs", [])):
        program = Program(
            lender_id=lender.id,
            name=prog_data["name"],
            priority=prog_data.get("priority", idx),
            base_rate=prog_data.get("base_rate"),
            notes=prog_data.get("notes"),
        )
        session.add(program)
        session.flush()
        for rule_data in prog_data.get("rules", []):
            rule = Rule(
                program_id=program.id,
                kind=rule_data["kind"],
                field=rule_data["field"],
                op=rule_data["op"],
                value=rule_data.get("value"),
                weight=rule_data.get("weight", 1),
                hard=rule_data.get("hard", True),
                message=rule_data.get("message"),
            )
            session.add(rule)
    return lender


def seed_all(verbose: bool = True) -> list[str]:
    loaded: list[str] = []
    with Session(engine) as session:
        for path in sorted(LENDERS_DIR.glob("*.yaml")):
            data = load_yaml(path)
            lender = upsert_lender(session, data)
            loaded.append(lender.slug)
            if verbose:
                print(f"seeded {lender.slug} with {len(data.get('programs', []))} programs")
        session.commit()
    return loaded


def main() -> int:
    init_db()
    seed_all()
    return 0


if __name__ == "__main__":
    sys.exit(main())
