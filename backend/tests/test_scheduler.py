"""Test wrapper FSRS (M4).

Yang diuji BUKAN kebenaran algoritma FSRS (itu tanggung jawab py-fsrs) melainkan
kontrak wrapper-nya:
- verdict eksekusi + probe dipetakan ke Rating yang benar & konsisten,
- `due_at` maju saat sukses, dan RESET saat gagal,
- kartu bisa dipulihkan utuh dari baris DB (state/step/last_review ikut tersimpan),
- interval berskala HARI, bukan menit ala flashcard.
"""

from datetime import timedelta

from fsrs import Rating

from app.models import ScheduleItem
from app.services.scheduler import (
    apply_rating,
    as_utc,
    is_due,
    rating_for,
    to_card,
    utcnow,
)


def test_rating_mapping_verdict_ke_fsrs():
    # Eksekusi gagal → Again, apa pun kabar probe-nya.
    assert rating_for(test_passed=False, probe_correct=True) is Rating.Again
    assert rating_for(test_passed=False, probe_correct=False) is Rating.Again
    assert rating_for(test_passed=False, probe_correct=None) is Rating.Again
    # Lolos tapi probe salah → Hard (produksi bisa, pemahaman rapuh).
    assert rating_for(test_passed=True, probe_correct=False) is Rating.Hard
    # Lolos bersih → Good.
    assert rating_for(test_passed=True, probe_correct=True) is Rating.Good
    # Tanpa probe (placement) → Good, bukan dihukum.
    assert rating_for(test_passed=True, probe_correct=None) is Rating.Good


def test_due_at_maju_saat_sukses_berulang():
    item = ScheduleItem(node_id="x")
    now = utcnow()

    first = apply_rating(item, Rating.Good, now)
    assert first.interval_days >= 1  # skala HARI, bukan menit (bukan flashcard)

    now = as_utc(item.due_at)
    second = apply_rating(item, Rating.Good, now)
    assert second.interval_days > first.interval_days
    assert as_utc(item.due_at) > now
    assert item.review_count == 2


def test_gagal_mereset_interval():
    item = ScheduleItem(node_id="x")
    now = utcnow()
    for _ in range(3):
        update = apply_rating(item, Rating.Good, now)
        now = as_utc(item.due_at)
    long_interval = update.interval_days
    assert long_interval > 10

    reset = apply_rating(item, Rating.Again, now)
    assert reset.interval_days < long_interval
    assert reset.stability < update.stability


def test_kartu_pulih_utuh_dari_schedule_item():
    item = ScheduleItem(node_id="x")
    apply_rating(item, Rating.Good, utcnow())

    # Semua state kartu tersimpan di baris DB — bukan cuma stability/difficulty.
    assert item.fsrs_state is not None
    assert item.last_review_at is not None

    card = to_card(item)
    assert card.stability == item.fsrs_stability
    assert card.difficulty == item.fsrs_difficulty
    assert card.state.name == item.fsrs_state
    assert as_utc(card.due) == as_utc(item.due_at)


def test_kartu_pulih_walau_datetime_naive_dari_sqlite():
    """SQLite mengembalikan datetime TANPA tzinfo; wrapper harus tetap jalan."""
    item = ScheduleItem(node_id="x")
    apply_rating(item, Rating.Good, utcnow())
    item.due_at = item.due_at.replace(tzinfo=None)
    item.last_review_at = item.last_review_at.replace(tzinfo=None)

    update = apply_rating(item, Rating.Good, as_utc(item.due_at))
    assert update.interval_days > 0


def test_is_due_hanya_untuk_node_yang_sudah_masuk_jadwal():
    item = ScheduleItem(node_id="x")
    # Belum pernah dibuktikan → bukan urusan review.
    assert is_due(item) is False

    now = utcnow()
    apply_rating(item, Rating.Good, now)
    assert is_due(item, now) is False
    assert is_due(item, as_utc(item.due_at) + timedelta(seconds=1)) is True
