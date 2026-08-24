"""Test placement probe (M4).

Membuktikan bahwa lantai **ditemukan lewat eksekusi**, bukan diasumsikan:
- urutan tantangan MENURUN (hilir → primitif),
- sesi BERHENTI di batas fail→pass pertama,
- node lantai jadi `acquired`; prasyaratnya cuma DIBUKA (`available`), tak diklaim,
- batas `PLACEMENT_MAX_NODES` (keputusan Q4) menghentikan sesi yang gagal terus,
- tak ada satu pun endpoint/langkah yang menanyakan "kamu sudah bisa apa".

Test ini menjalankan hidden test SUNGGUHAN lewat Executor, jadi lebih lambat dari
test lain — itu memang harganya: yang diuji adalah sinyal pass/fail asli.
"""

import pytest
from sqlmodel import Session, select

from app.graders.files import reference_solution_path
from app.models import (
    Attempt,
    ChallengeInstance,
    Edge,
    EdgeType,
    ScheduleItem,
    ScheduleStatus,
)
from app.services.placement import (
    compute_state,
    descending_order,
    latest_floor,
    start_placement,
    submit_placement,
)

GARBAGE = "def wrong():\n    return None\n"


def _reference_code(session: Session, instance_id: str) -> str:
    """Solusi referensi untuk instance — dijamin hijau (gerbang mutu M2)."""
    instance = session.get(ChallengeInstance, instance_id)
    return reference_solution_path(instance).read_text(encoding="utf-8")


def test_urutan_menurun_hilir_ke_primitif(session: Session):
    order = descending_order(session)

    # INVARIAN, bukan id hardcoded: kurikulum tumbuh tiap batch authoring, jadi node
    # "paling hilir" berubah. Yang tak boleh berubah adalah PROPERTI urutan menurun —
    # setiap node dependen muncul SEBELUM prasyarat kerasnya (makin hilir makin dulu).
    hard_edges = session.exec(select(Edge).where(Edge.type == EdgeType.hard.value)).all()
    assert hard_edges  # ada prasyarat keras yang membentuk urutan
    for e in hard_edges:
        assert order.index(e.to_node_id) < order.index(e.from_node_id), (
            f"{e.to_node_id} (dependen) harus sebelum prasyarat {e.from_node_id} "
            "dalam urutan menurun"
        )

    # n001 (fungsi murni, tanpa prasyarat keras, id terkecil) tetap paling primitif.
    assert order[-1] == "n001_paginate"


def test_sesi_dimulai_dari_node_paling_hilir(session: Session):
    state = start_placement(session)

    assert state.finished is False
    assert state.current is not None
    assert state.current.node_id == descending_order(session)[0]
    assert state.current.position == 1


def test_berhenti_di_batas_fail_lalu_pass(session: Session):
    state = start_placement(session)
    sid = state.session_id

    # Node paling hilir: gagal.
    gagal = submit_placement(session, session_id=sid, submitted_code=GARBAGE)
    assert gagal.passed is False
    assert gagal.state.finished is False
    # Sesi turun satu tingkat, bukan berhenti.
    assert gagal.state.current.node_id == descending_order(session)[1]
    assert gagal.state.floor_node_id is None

    # Node berikutnya: lolos → di sinilah lantainya.
    lantai_node = gagal.state.current.node_id
    kode = _reference_code(session, gagal.state.current.instance_id)
    lolos = submit_placement(session, session_id=sid, submitted_code=kode)

    assert lolos.passed is True
    assert lolos.state.finished is True
    assert lolos.state.exhausted is False
    assert lolos.state.floor_node_id == lantai_node
    # Berhenti berarti berhenti: tak ada tantangan berikutnya.
    assert lolos.state.current is None
    assert len(lolos.state.tested) == 2


def test_lantai_jadi_acquired_dan_prasyaratnya_hanya_dibuka(session: Session):
    state = start_placement(session)
    sid = state.session_id
    submit_placement(session, session_id=sid, submitted_code=GARBAGE)

    state = compute_state(session, sid)
    lantai = state.current.node_id
    hasil = submit_placement(
        session, session_id=sid, submitted_code=_reference_code(session, state.current.instance_id)
    )

    # Lantai: lolos eksekusi tanpa scaffold apa pun → acquired sah (§2 terpenuhi).
    item = session.get(ScheduleItem, lantai)
    assert item.status == ScheduleStatus.acquired.value
    assert item.due_at is not None  # langsung masuk jadwal FSRS
    assert hasil.floor_outcome.became_acquired is True

    # Prasyarat keras di bawah lantai: DIBUKA, bukan diklaim dikuasai.
    assert "n002_get_json_route" in hasil.unlocked
    prasyarat = session.get(ScheduleItem, "n002_get_json_route")
    assert prasyarat.status == ScheduleStatus.available.value
    assert prasyarat.status != ScheduleStatus.acquired.value
    assert prasyarat.due_at is None  # tak pernah dibuktikan → tak masuk jadwal


def test_batas_maksimum_node_menghentikan_sesi(session: Session, monkeypatch):
    """Keputusan Q4: sesi tak boleh berubah jadi maraton tantangan reproduksi."""
    monkeypatch.setattr("app.services.placement.PLACEMENT_MAX_NODES", 2)

    state = start_placement(session)
    sid = state.session_id
    assert state.max_nodes == 2

    submit_placement(session, session_id=sid, submitted_code=GARBAGE)
    hasil = submit_placement(session, session_id=sid, submitted_code=GARBAGE)

    assert hasil.state.finished is True
    assert hasil.state.exhausted is True
    assert hasil.state.floor_node_id is None
    assert hasil.state.current is None
    # Gagal terus TIDAK memberi status apa pun ke node mana pun.
    assert all(
        i.status != ScheduleStatus.acquired.value for i in session.exec(select(ScheduleItem)).all()
    )

    with pytest.raises(ValueError):
        submit_placement(session, session_id=sid, submitted_code=GARBAGE)


def test_attempt_placement_tercatat_dengan_mode_dan_sesi(session: Session):
    state = start_placement(session)
    sid = state.session_id
    submit_placement(session, session_id=sid, submitted_code=GARBAGE)

    attempts = session.exec(select(Attempt).where(Attempt.session_id == sid)).all()
    assert len(attempts) == 1
    assert attempts[0].mode == "placement"
    assert attempts[0].result == "fail"
    # Placement tak memakai probe — reproduksi dingin, tanpa gerbang pemahaman.
    assert attempts[0].probe_result is None


def test_latest_floor_terbaca_untuk_dashboard(session: Session):
    assert latest_floor(session) is None

    state = start_placement(session)
    sid = state.session_id
    submit_placement(session, session_id=sid, submitted_code=GARBAGE)
    state = compute_state(session, sid)
    submit_placement(
        session, session_id=sid, submitted_code=_reference_code(session, state.current.instance_id)
    )

    assert latest_floor(session) == state.current.node_id
