"""Test UnitTestGrader — verdict pass/fail berasal dari eksekusi hidden test asli."""

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from app.config import DATA_DIR
from app.graders import get_grader
from app.models import ChallengeInstance, Node
from app.services.node_loader import load_domain_into_db

FASTAPI_DOMAIN = DATA_DIR / "domains" / "fastapi"

CORRECT_PAGINATE = (
    "def paginate(items, page, per_page):\n"
    "    if page < 1 or per_page < 1:\n"
    "        raise ValueError('bad')\n"
    "    start = (page - 1) * per_page\n"
    "    return list(items)[start:start + per_page]\n"
)

# Salah: mengabaikan `page` → gagal test halaman ke-2.
WRONG_PAGINATE = (
    "def paginate(items, page, per_page):\n"
    "    return list(items)[:per_page]\n"
)


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


def _n001_instance(session: Session) -> ChallengeInstance:
    return session.exec(
        select(ChallengeInstance).where(ChallengeInstance.node_id == "n001_paginate")
    ).first()


def test_correct_solution_passes(session: Session):
    node = session.get(Node, "n001_paginate")
    grader = get_grader(node.grader_type)
    result = grader.grade(_n001_instance(session), CORRECT_PAGINATE)
    assert result.passed is True
    assert result.timed_out is False


def test_wrong_solution_fails(session: Session):
    node = session.get(Node, "n001_paginate")
    grader = get_grader(node.grader_type)
    result = grader.grade(_n001_instance(session), WRONG_PAGINATE)
    assert result.passed is False
    assert result.test_output  # kegagalan test ditampilkan (cermin)


def test_fastapi_node_grades_via_testclient(session: Session):
    # n002: GET route sederhana — grader menjalankan TestClient di subprocess.
    inst = session.exec(
        select(ChallengeInstance).where(
            ChallengeInstance.node_id == "n002_get_json_route",
            ChallengeInstance.variant_label == "variant_a",
        )
    ).first()
    node = session.get(Node, "n002_get_json_route")
    grader = get_grader(node.grader_type)

    correct = (
        "from fastapi import FastAPI\n"
        "app = FastAPI()\n"
        "@app.get('/status')\n"
        "def s():\n"
        "    return {'service': 'orders', 'ok': True}\n"
    )
    assert grader.grade(inst, correct).passed is True

    wrong = (
        "from fastapi import FastAPI\n"
        "app = FastAPI()\n"
        "@app.get('/status')\n"
        "def s():\n"
        "    return {'service': 'WRONG', 'ok': True}\n"
    )
    assert grader.grade(inst, wrong).passed is False
