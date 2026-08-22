"""Test sesi review harian (M4 langkah 5).

Membuktikan:
- review hanya menampilkan node yang benar-benar jatuh tempo,
- tiap review memakai **instance BERBEDA** dari yang barusan dipakai (transfer, bukan
  hafalan jawaban) — dan varian yang menipis ditandai, bukan didiamkan,
- hasil review disalurkan ke FSRS + mastery (jadwal ulang, status bergerak),
- review gagal langsung final tanpa menunggu probe.

Router dipanggil sebagai fungsi biasa (session disuntik langsung) — tak perlu server.
"""

from sqlmodel import Session

from app.models import ScheduleItem, ScheduleStatus
from app.routers import review as review_router
from app.services.mastery import apply_outcome
from app.services.scaffold import review_instance
from app.services.scheduler import as_utc

NODE = "n001_paginate"

CORRECT_PAGINATE = (
    "def paginate(items, page, per_page):\n"
    "    if page < 1 or per_page < 1:\n"
    "        raise ValueError('bad')\n"
    "    start = (page - 1) * per_page\n"
    "    return list(items)[start:start + per_page]\n"
)
WRONG_PAGINATE = "def paginate(items, page, per_page):\n    return list(items)[:per_page]\n"
PROBE_ID = "n001_probe_01"
PROBE_BENAR = "[30, 40]"
PROBE_SALAH = "[10, 20]"


def _acquire(session: Session) -> None:
    apply_outcome(session, node_id=NODE, test_passed=True, probe_correct=True)


def _make_due(session: Session) -> None:
    """Percepat waktu: mundurkan due_at supaya node jatuh tempo sekarang."""
    item = session.get(ScheduleItem, NODE)
    item.due_at = as_utc(item.due_at).replace(year=2000)
    session.add(item)
    session.commit()


def test_due_kosong_sebelum_ada_yang_acquired(session: Session):
    assert review_router.due_items(session) == []


def test_node_belum_jatuh_tempo_tidak_muncul_di_due(session: Session):
    _acquire(session)
    assert [d.node_id for d in review_router.due_items(session)] == []

    _make_due(session)
    due = review_router.due_items(session)
    assert [d.node_id for d in due] == [NODE]
    assert due[0].status == ScheduleStatus.acquired.value
    assert due[0].overdue_days > 0


def test_review_memakai_instance_berbeda_dari_yang_terakhir(session: Session):
    _acquire(session)
    _make_due(session)

    pertama = review_instance(session, NODE)
    # Kerjakan pakai instance itu → attempt tercatat.
    review_router.submit_review(
        review_router.ReviewSubmitIn(
            node_id=NODE,
            instance_id=pertama.instance.id,
            submitted_code=CORRECT_PAGINATE,
        ),
        session,
    )

    kedua = review_instance(session, NODE)
    assert kedua.instance.id != pertama.instance.id
    assert kedua.previous_instance_id == pertama.instance.id
    # A1 baru punya 2 varian per node → sinyal untuk authoring, bukan blokir.
    assert kedua.needs_more_variants is True


def test_review_lolos_bersih_menjadwal_ulang_lewat_fsrs(session: Session):
    _acquire(session)
    _make_due(session)
    picked = review_instance(session, NODE)

    hasil = review_router.submit_review(
        review_router.ReviewSubmitIn(
            node_id=NODE, instance_id=picked.instance.id, submitted_code=CORRECT_PAGINATE
        ),
        session,
    )
    # Test lolos → probe disodorkan, hasil BELUM final.
    assert hasil.passed is True
    assert hasil.probe is not None
    assert hasil.outcome is None
    assert "correct_answer" not in hasil.probe.model_dump()

    final = review_router.submit_review_probe(
        review_router.ReviewProbeIn(
            attempt_id=hasil.attempt_id, probe_id=PROBE_ID, answer=PROBE_BENAR
        ),
        session,
    )
    assert final.probe_correct is True
    assert final.outcome.rating == "Good"
    assert final.outcome.spaced is True
    assert final.outcome.consecutive_success == 2
    assert final.outcome.interval_days > 0
    assert as_utc(session.get(ScheduleItem, NODE).due_at).year > 2000  # dijadwal ulang


def test_review_gagal_langsung_lapsed_tanpa_probe(session: Session):
    _acquire(session)
    _make_due(session)
    picked = review_instance(session, NODE)

    hasil = review_router.submit_review(
        review_router.ReviewSubmitIn(
            node_id=NODE, instance_id=picked.instance.id, submitted_code=WRONG_PAGINATE
        ),
        session,
    )

    assert hasil.passed is False
    assert hasil.probe is None  # tak ada gunanya bertanya — verdict sudah pasti
    assert hasil.outcome.status == ScheduleStatus.lapsed.value
    assert hasil.outcome.rating == "Again"
    assert hasil.outcome.consecutive_success == 0
    assert hasil.test_output  # kegagalan DITAMPILKAN (cermin §7.6)


def test_review_lolos_tapi_probe_salah_tak_menurunkan_status(session: Session):
    _acquire(session)
    _make_due(session)
    picked = review_instance(session, NODE)

    hasil = review_router.submit_review(
        review_router.ReviewSubmitIn(
            node_id=NODE, instance_id=picked.instance.id, submitted_code=CORRECT_PAGINATE
        ),
        session,
    )
    final = review_router.submit_review_probe(
        review_router.ReviewProbeIn(
            attempt_id=hasil.attempt_id, probe_id=PROBE_ID, answer=PROBE_SALAH
        ),
        session,
    )

    assert final.probe_correct is False
    assert final.outcome.rating == "Hard"
    assert final.outcome.status == ScheduleStatus.acquired.value  # BUKAN lapsed
    assert final.outcome.consecutive_success == 1  # tak maju menuju mastered
