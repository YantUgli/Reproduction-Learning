"""Fixture bersama untuk test M4.

DB in-memory (StaticPool supaya satu koneksi dipakai ulang) + seluruh node A1 dimuat
dari `data/` — test M4 menguji perilaku loop di atas node NYATA, bukan node palsu.
"""

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.config import DATA_DIR
from app.services.node_loader import load_domain_into_db

FASTAPI_DOMAIN = DATA_DIR / "domains" / "fastapi"


@pytest.fixture()
def session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        load_domain_into_db(s, FASTAPI_DOMAIN)
        yield s
