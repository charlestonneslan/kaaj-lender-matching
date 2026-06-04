import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app import models  # noqa: F401
from app.seed import upsert_lender, load_yaml, LENDERS_DIR


@pytest.fixture()
def session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


@pytest.fixture()
def seeded_session(session):
    for path in sorted(LENDERS_DIR.glob("*.yaml")):
        upsert_lender(session, load_yaml(path))
    session.commit()
    return session
