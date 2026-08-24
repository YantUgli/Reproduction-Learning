"""Test M6: node React & ML lewat loop yang SAMA PERSIS dengan FastAPI.

Ini acceptance criterion inti M6 — dan satu-satunya cara membuktikannya adalah
menjalankan loop itu sendiri (submit → grade → probe → mastery → FSRS) di atas node
domain lain, memakai fungsi yang sama, tanpa satu pun argumen "ini domain apa".

Dua lapis bukti:
1. **Perilaku**: `submit_attempt` + `answer_probe` + `apply_outcome` menggerakkan
   node React/ML persis seperti node FastAPI.
2. **Struktur**: kode loop tak pernah menyebut nama domain / grader tertentu. Kalau
   suatu saat ada yang menulis `if domain == "react"` di scheduler, test ini merah.
"""

import re
from pathlib import Path

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from app.config import DATA_DIR, REACT_RUNTIME_DIR
from app.graders.files import reference_solution_path
from app.models import ChallengeInstance, ScheduleItem, ScheduleStatus
from app.services.attempt_service import answer_probe, submit_attempt
from app.services.mastery import apply_outcome
from app.services.node_loader import load_domain_into_db
from app.services.scaffold import build_level_view, pick_probe, verification_instance

REACT_RUNTIME_READY = (REACT_RUNTIME_DIR / "node_modules" / "vitest" / "vitest.mjs").exists()

WRONG_COUNTER = """
export default function Counter() {
  return <p>Jumlah: 0</p>;
}
"""

# Softmax naif: benar untuk input kecil, MELEDAK untuk input besar — persis
# kesalahan yang node ini ada untuk menangkapnya.
NAIVE_SOFTMAX = """
import numpy as np


def softmax(x):
    x = np.asarray(x, dtype=float)
    exps = np.exp(x)
    return exps / np.sum(exps)
"""


@pytest.fixture()
def session():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        for domain in ("fastapi", "react", "ml"):
            load_domain_into_db(s, DATA_DIR / "domains" / domain)
        yield s


def _verify_instance(session: Session, node_id: str) -> ChallengeInstance:
    return verification_instance(session, node_id)


def _reference_code(instance: ChallengeInstance) -> str:
    """Solusi referensi milik instance ITU.

    Bukan konstanta di file test: L0 sengaja memakai varian BERBEDA dari worked
    example, jadi menempelkan jawaban varian A di sini akan gagal karena alasan yang
    salah (soalnya beda), bukan karena loop-nya bermasalah.
    """
    return reference_solution_path(instance).read_text(encoding="utf-8")


# --------------------------------------------------------------------------- #
# 1. Perilaku — loop yang sama menggerakkan domain baru
# --------------------------------------------------------------------------- #
@pytest.mark.skipif(not REACT_RUNTIME_READY, reason="runtime React belum di-`npm install`")
def test_react_node_moves_through_the_same_loop(session: Session):
    node_id = "r001_state_counter"
    instance = _verify_instance(session, node_id)

    res = submit_attempt(
        session,
        node_id=node_id,
        instance_id=instance.id,
        scaffold_level="L0",
        submitted_code=_reference_code(instance),
        duration_seconds=300,
    )
    assert res.attempt.result == "pass"
    assert res.attempt.mode == "verification"  # ditentukan scaffold, bukan domain

    probe = pick_probe(session, node_id)
    outcome = answer_probe(
        session, attempt_id=res.attempt.id, probe_id=probe.id, answer=probe.correct_answer
    )
    assert outcome.probe_correct is True
    assert outcome.outcome.status == ScheduleStatus.acquired.value
    # Masuk jadwal FSRS seperti node domain mana pun.
    assert session.get(ScheduleItem, node_id).due_at is not None


@pytest.mark.skipif(not REACT_RUNTIME_READY, reason="runtime React belum di-`npm install`")
def test_react_failure_is_a_normal_failure(session: Session):
    node_id = "r001_state_counter"
    instance = _verify_instance(session, node_id)

    res = submit_attempt(
        session,
        node_id=node_id,
        instance_id=instance.id,
        scaffold_level="L0",
        submitted_code=WRONG_COUNTER,  # tak punya tombol → interaksi gagal
        duration_seconds=120,
    )

    assert res.attempt.result == "fail"
    assert session.get(ScheduleItem, node_id).status != ScheduleStatus.acquired.value


def test_ml_node_moves_through_the_same_loop(session: Session):
    node_id = "m001_softmax_stable"
    instance = _verify_instance(session, node_id)

    res = submit_attempt(
        session,
        node_id=node_id,
        instance_id=instance.id,
        scaffold_level="L0",
        submitted_code=_reference_code(instance),
        duration_seconds=200,
    )
    assert res.attempt.result == "pass"

    probe = pick_probe(session, node_id)
    outcome = answer_probe(
        session, attempt_id=res.attempt.id, probe_id=probe.id, answer=probe.correct_answer
    )
    assert outcome.outcome.status == ScheduleStatus.acquired.value


def test_ml_tolerance_catches_the_unstable_implementation(session: Session):
    """`value_assert` bukan sekadar 'pytest dengan nama lain': toleransinya menangkap
    softmax naif yang benar di kasus mudah tapi `nan` di input besar."""
    node_id = "m001_softmax_stable"
    instance = _verify_instance(session, node_id)

    res = submit_attempt(
        session,
        node_id=node_id,
        instance_id=instance.id,
        scaffold_level="L0",
        submitted_code=NAIVE_SOFTMAX,
        duration_seconds=200,
    )

    assert res.attempt.result == "fail"


def test_mastery_rules_are_identical_across_domains(session: Session):
    """4 sukses berjarak → mastered, untuk node ML sama seperti node FastAPI."""
    for node_id in ("m002_sigmoid_bce", "n001_paginate"):
        for _ in range(4):
            item = session.get(ScheduleItem, node_id)
            if item is not None and item.due_at is not None:
                # Majukan waktu: sukses dihitung hanya bila BERJARAK (M4).
                item.due_at = item.due_at.replace(year=item.due_at.year - 1)
                session.add(item)
                session.commit()
            apply_outcome(session, node_id=node_id, test_passed=True, probe_correct=True)

        assert session.get(ScheduleItem, node_id).status == ScheduleStatus.mastered.value


def test_scaffold_levels_work_for_every_domain(session: Session):
    """L3 worked example membaca `reference_solution.*` — `.jsx` maupun `.py`."""
    for node_id in ("r002_controlled_input", "m003_mse_gradient", "n002_get_json_route"):
        node = session.exec(
            select(ChallengeInstance).where(ChallengeInstance.node_id == node_id)
        ).first()
        assert node is not None

        from app.models import Node

        view = build_level_view(session, session.get(Node, node_id), "L3")
        assert view.code.strip(), f"{node_id}: worked example L3 kosong"

        verify = build_level_view(session, session.get(Node, node_id), "L0")
        assert verify.instance_id != view.instance_id  # transfer, bukan hafalan


# --------------------------------------------------------------------------- #
# 2. Struktur — tak ada cabang per-domain di kode loop
# --------------------------------------------------------------------------- #
_LOOP_MODULES = (
    "services/attempt_service.py",
    "services/mastery.py",
    "services/scheduler.py",
    "services/scaffold.py",
    "services/progress.py",
    "services/placement.py",
    "services/kpi.py",
    "routers/attempts.py",
    "routers/review.py",
    "routers/placement.py",
)

#: Nama domain & grader sebagai NILAI (string literal) atau atribut yang dibandingkan.
#: Yang dicari bukan sekadar katanya, melainkan kode yang MEMPERLAKUKAN domain sebagai
#: percabangan: `"react"`, `'value_assert'`, `domain_id ==`, `grader_type ==`.
#: `from fastapi import APIRouter` bukan pelanggaran — itu web framework aplikasinya,
#: bukan domain kurikulum.
_DOMAIN_LITERAL = re.compile(
    r"""["'](react|ml|jsx|dom_behavior|value_assert|unit_test|metric_threshold|structural)["']""",
    re.I,
)
_DOMAIN_BRANCH = re.compile(r"\b(domain_id|grader_type)\s*(==|!=|\bin\b)")


@pytest.mark.parametrize("module", _LOOP_MODULES)
def test_loop_modules_never_branch_on_domain(module: str):
    path = Path(__file__).resolve().parents[1] / "app" / module
    source = path.read_text(encoding="utf-8")

    offenders = [
        (i, line)
        for i, line in enumerate(source.splitlines(), start=1)
        if not _is_comment(line) and (_DOMAIN_LITERAL.search(line) or _DOMAIN_BRANCH.search(line))
    ]

    assert not offenders, (
        f"{module} bercabang atas domain/grader di baris "
        f"{[i for i, _ in offenders]} — pindahkan ke grader, jangan bercabang di loop"
    )


def _is_comment(line: str) -> bool:
    """Komentar & docstring BOLEH menyebut domain (mis. menjelaskan asal keputusan);
    yang dilarang adalah KODE yang bercabang karenanya."""
    stripped = line.strip()
    return stripped.startswith("#") or stripped.startswith('"') or stripped.startswith("'")
