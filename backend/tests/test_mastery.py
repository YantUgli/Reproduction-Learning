"""Test transisi mastery (M4).

Membuktikan aturan yang menentukan arti "menguasai" di produk ini:
- lolos bersih pertama → `acquired` (bukan `mastered`),
- `mastered` butuh N=4 sukses **BERJARAK** — empat kali dalam satu sesi TIDAK cukup,
- gagal di jatuh tempo → `lapsed` + interval reset,
- `lapsed` naik lagi ke `acquired` (keputusan Q3), dan tak mengunci ulang node hilir,
- probe salah memperberat jadwal tapi TAK PERNAH sendirian menurunkan status (§2).
"""

from datetime import timedelta

from sqlmodel import Session

from app.config import MASTERY_SUCCESSES_DEFAULT
from app.models import ScheduleItem, ScheduleStatus
from app.services.mastery import apply_outcome
from app.services.progress import all_statuses, effective_status
from app.services.scheduler import as_utc, utcnow

NODE = "n001_paginate"
DOWNSTREAM = "n003_path_param_404"  # hard-prereq: n002_get_json_route
UPSTREAM = "n002_get_json_route"


def _clean_pass(session: Session, node_id: str, now=None):
    return apply_outcome(session, node_id=node_id, test_passed=True, probe_correct=True, now=now)


def _due(session: Session, node_id: str):
    """Waktu tepat saat node jatuh tempo — dipakai untuk 'mempercepat' waktu di test."""
    return as_utc(session.get(ScheduleItem, node_id).due_at)


def test_lolos_pertama_jadi_acquired_bukan_mastered(session: Session):
    outcome = _clean_pass(session, NODE)

    assert outcome.status == ScheduleStatus.acquired.value
    assert outcome.became_acquired is True
    assert outcome.became_mastered is False
    assert outcome.consecutive_success == 1
    # Masuk jadwal: due_at terisi, interval berskala hari.
    assert outcome.due_at is not None
    assert outcome.interval_days >= 1


def test_mastered_setelah_empat_sukses_berjarak(session: Session):
    outcome = _clean_pass(session, NODE)
    for _ in range(MASTERY_SUCCESSES_DEFAULT - 1):
        assert outcome.status != ScheduleStatus.mastered.value
        outcome = _clean_pass(session, NODE, now=_due(session, NODE))

    assert outcome.consecutive_success == MASTERY_SUCCESSES_DEFAULT
    assert outcome.status == ScheduleStatus.mastered.value
    assert outcome.became_mastered is True
    assert session.get(ScheduleItem, NODE).status == ScheduleStatus.mastered.value


def test_empat_sukses_dalam_satu_sesi_bukan_mastered(session: Session):
    """Inti definisi: JARAK adalah bagian dari mastery, bukan hiasan."""
    now = utcnow()
    outcome = _clean_pass(session, NODE, now=now)
    for i in range(MASTERY_SUCCESSES_DEFAULT + 2):
        # Waktu tidak dimajukan — semua di sesi yang sama, jauh sebelum jatuh tempo.
        outcome = _clean_pass(session, NODE, now=now + timedelta(minutes=i + 1))

    assert outcome.spaced is False
    assert outcome.consecutive_success == 1
    assert outcome.status == ScheduleStatus.acquired.value
    assert outcome.status != ScheduleStatus.mastered.value


def test_gagal_di_jatuh_tempo_jadi_lapsed_dan_interval_reset(session: Session):
    outcome = _clean_pass(session, NODE)
    for _ in range(2):
        outcome = _clean_pass(session, NODE, now=_due(session, NODE))
    interval_sebelum = outcome.interval_days
    assert outcome.consecutive_success == 3

    lapse = apply_outcome(
        session,
        node_id=NODE,
        test_passed=False,
        probe_correct=None,
        now=_due(session, NODE),
    )

    assert lapse.status == ScheduleStatus.lapsed.value
    assert lapse.became_lapsed is True
    assert lapse.consecutive_success == 0
    assert lapse.interval_days < interval_sebelum  # interval RESET


def test_lapsed_kembali_ke_acquired_bukan_available(session: Session):
    """Keputusan PRD Q3: bukti pernah ada; yang meluruh cuma memorinya."""
    _clean_pass(session, NODE)
    apply_outcome(
        session, node_id=NODE, test_passed=False, probe_correct=None, now=_due(session, NODE)
    )
    assert session.get(ScheduleItem, NODE).status == ScheduleStatus.lapsed.value

    pulih = _clean_pass(session, NODE, now=_due(session, NODE))
    assert pulih.status == ScheduleStatus.acquired.value
    assert pulih.consecutive_success == 1  # hitungan mastery mulai dari nol lagi


def test_lapsed_tidak_mengunci_ulang_node_hilir(session: Session):
    assert effective_status(session, DOWNSTREAM) == ScheduleStatus.locked.value

    _clean_pass(session, UPSTREAM)
    assert effective_status(session, DOWNSTREAM) == ScheduleStatus.available.value

    apply_outcome(
        session,
        node_id=UPSTREAM,
        test_passed=False,
        probe_correct=None,
        now=_due(session, UPSTREAM),
    )
    statuses = all_statuses(session)
    assert statuses[UPSTREAM] == ScheduleStatus.lapsed.value
    # Satu review buruk tak boleh merobohkan separuh peta.
    assert statuses[DOWNSTREAM] == ScheduleStatus.available.value


def test_probe_salah_tak_menurunkan_status_tapi_memperberat_jadwal(session: Session):
    """INVARIANT §2: hanya eksekusi kode yang boleh menurunkan status."""
    _clean_pass(session, NODE)
    _clean_pass(session, NODE, now=_due(session, NODE))
    sebelum = session.get(ScheduleItem, NODE)
    sukses_sebelum = sebelum.consecutive_success

    hasil = apply_outcome(
        session,
        node_id=NODE,
        test_passed=True,
        probe_correct=False,
        now=_due(session, NODE),
    )

    assert hasil.rating == "Hard"
    assert hasil.clean is False
    assert hasil.status == ScheduleStatus.acquired.value  # TIDAK lapsed
    assert hasil.became_lapsed is False
    assert hasil.consecutive_success == sukses_sebelum  # tak maju menuju mastered


def test_gagal_sebelum_pernah_acquired_tak_membuat_jadwal(session: Session):
    """Latihan yang gagal bukan 'review yang gagal' — node belum masuk jadwal."""
    hasil = apply_outcome(session, node_id=NODE, test_passed=False, probe_correct=None)

    assert hasil.status == ScheduleStatus.locked.value or hasil.status == (
        ScheduleStatus.available.value
    )
    assert hasil.due_at is None
    assert hasil.became_lapsed is False
    assert session.get(ScheduleItem, NODE).due_at is None


def test_mastered_yang_gagal_turun_ke_lapsed(session: Session):
    outcome = _clean_pass(session, NODE)
    for _ in range(MASTERY_SUCCESSES_DEFAULT - 1):
        outcome = _clean_pass(session, NODE, now=_due(session, NODE))
    assert outcome.status == ScheduleStatus.mastered.value

    lapse = apply_outcome(
        session,
        node_id=NODE,
        test_passed=False,
        probe_correct=True,
        now=_due(session, NODE),
    )
    assert lapse.status == ScheduleStatus.lapsed.value
    assert lapse.consecutive_success == 0
