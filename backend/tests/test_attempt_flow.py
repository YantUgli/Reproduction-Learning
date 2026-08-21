"""Test alur Attempt end-to-end (M3): submit → grade → probe → acquired.

Membuktikan:
- L0 solusi benar + probe benar → status `acquired` (BUKAN mastered).
- L0 solusi salah → fail, Attempt tetap tercatat, TIDAK acquired.
- Verifikasi L0 memakai instance VARIAN BERBEDA dari worked example (transfer).
- Setiap Attempt tersimpan (sinyal reproduce-without-AI).
"""

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from app.config import DATA_DIR
from app.models import Attempt, ScheduleItem
from app.services.attempt_service import answer_probe, submit_attempt
from app.services.node_loader import load_domain_into_db
from app.services.scaffold import teaching_instance, verification_instance

FASTAPI_DOMAIN = DATA_DIR / "domains" / "fastapi"

CORRECT_PAGINATE = (
    "def paginate(items, page, per_page):\n"
    "    if page < 1 or per_page < 1:\n"
    "        raise ValueError('bad')\n"
    "    start = (page - 1) * per_page\n"
    "    return list(items)[start:start + per_page]\n"
)
WRONG_PAGINATE = "def paginate(items, page, per_page):\n    return list(items)[:per_page]\n"


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


def test_l0_verification_uses_different_variant(session: Session):
    teaching = teaching_instance(session, "n001_paginate")
    verify = verification_instance(session, "n001_paginate")
    assert verify.variant_label != teaching.variant_label


def test_clean_pass_sets_acquired_not_mastered(session: Session):
    verify = verification_instance(session, "n001_paginate")
    res = submit_attempt(
        session,
        node_id="n001_paginate",
        instance_id=verify.id,
        scaffold_level="L0",
        submitted_code=CORRECT_PAGINATE,
        duration_seconds=42,
    )
    assert res.grade.passed is True
    assert res.attempt.mode == "verification"
    assert res.attempt.result == "pass"

    outcome = answer_probe(
        session,
        attempt_id=res.attempt.id,
        probe_id="n001_probe_01",
        answer="[30, 40]",  # jawaban benar
    )
    assert outcome.probe_correct is True
    assert outcome.acquired is True

    item = session.get(ScheduleItem, "n001_paginate")
    assert item.status == "acquired"
    assert item.status != "mastered"  # mastery TIDAK diklaim di M3


def test_wrong_solution_fails_and_is_recorded(session: Session):
    verify = verification_instance(session, "n001_paginate")
    res = submit_attempt(
        session,
        node_id="n001_paginate",
        instance_id=verify.id,
        scaffold_level="L0",
        submitted_code=WRONG_PAGINATE,
        duration_seconds=10,
    )
    assert res.grade.passed is False
    assert res.attempt.result == "fail"

    # Attempt gagal TETAP tersimpan (data sinyal inti).
    stored = session.exec(select(Attempt).where(Attempt.node_id == "n001_paginate")).all()
    assert len(stored) == 1

    item = session.get(ScheduleItem, "n001_paginate")
    assert item.status != "acquired"


def test_pass_but_wrong_probe_not_acquired(session: Session):
    verify = verification_instance(session, "n001_paginate")
    res = submit_attempt(
        session,
        node_id="n001_paginate",
        instance_id=verify.id,
        scaffold_level="L0",
        submitted_code=CORRECT_PAGINATE,
        duration_seconds=30,
    )
    outcome = answer_probe(
        session,
        attempt_id=res.attempt.id,
        probe_id="n001_probe_01",
        answer="[10, 20]",  # salah
    )
    assert outcome.probe_correct is False
    assert outcome.acquired is False
    item = session.get(ScheduleItem, "n001_paginate")
    assert item.status != "acquired"


def test_timebox_exceeded_flag_recorded(session: Session):
    verify = verification_instance(session, "n001_paginate")
    res = submit_attempt(
        session,
        node_id="n001_paginate",
        instance_id=verify.id,
        scaffold_level="L0",
        submitted_code=CORRECT_PAGINATE,
        duration_seconds=999,
        timebox_exceeded=True,
    )
    assert "timebox habis" in res.attempt.test_output
