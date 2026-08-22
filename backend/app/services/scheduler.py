"""Scheduler spaced repetition — pembungkus tipis `py-fsrs` (M4 langkah 2).

INVARIANT (CLAUDE.md §2, PRD §7.5): **algoritma SR tidak ditulis sendiri.** Modul ini
hanya menerjemahkan dua arah:

    verdict eksekusi (+ probe)  ->  Rating FSRS
    ScheduleItem (baris DB)     <-> Card (objek py-fsrs)

Semua keputusan interval milik py-fsrs. Kalau suatu saat modul ini mulai menghitung
interval sendiri, itu tanda invariant sedang dilanggar.

Pemetaan verdict -> Rating (PRD open question Q5, diputuskan di M4):

    eksekusi hidden test | comprehension probe | Rating  | arti
    ---------------------+---------------------+---------+---------------------------
    FAIL                 | apa pun / tak ada   | Again   | produksi gagal → lupa
    PASS                 | SALAH               | Hard    | bisa memproduksi, paham rapuh
    PASS                 | BENAR               | Good    | lolos bersih
    PASS                 | tidak ada (placement)| Good   | reproduksi dingin, tanpa scaffold

Catatan penting soal pemetaan ini:
- Probe **ikut memberi rating** (Hard vs Good), tapi ia **tak pernah sendirian
  menurunkan status**. Yang bisa membuat sebuah node `lapsed` hanya kegagalan
  eksekusi kode — itu penegakan langsung invariant §2 ("hanya eksekusi kode yang
  boleh memutuskan mastery") di level scheduler.
- `Easy` sengaja TIDAK dipakai di v1. Tak ada sinyal deterministik ketiga yang jujur
  membedakan "benar" dari "benar & gampang"; memakai durasi sebagai proksi berarti
  jadwal ditentukan angka berisik. Kalau kelak ada sinyal yang layak, tambahkan di
  sini — satu tempat.
"""

from dataclasses import dataclass
from datetime import UTC, datetime

from fsrs import Card, Rating, Scheduler, State

from app.config import (
    FSRS_DESIRED_RETENTION,
    FSRS_ENABLE_FUZZING,
    FSRS_LEARNING_STEPS,
    FSRS_RELEARNING_STEPS,
)
from app.models import ScheduleItem

_scheduler = Scheduler(
    desired_retention=FSRS_DESIRED_RETENTION,
    learning_steps=FSRS_LEARNING_STEPS,
    relearning_steps=FSRS_RELEARNING_STEPS,
    enable_fuzzing=FSRS_ENABLE_FUZZING,
)


def utcnow() -> datetime:
    return datetime.now(UTC)


def as_utc(dt: datetime | None) -> datetime | None:
    """SQLite membuang tzinfo saat menyimpan datetime; py-fsrs menolak yang naive.
    Anggap yang naive sebagai UTC (semua penulisan di kode ini memang UTC)."""
    if dt is None:
        return None
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=UTC)


def rating_for(*, test_passed: bool, probe_correct: bool | None) -> Rating:
    """Terjemahkan verdict menjadi Rating FSRS (tabel di docstring modul)."""
    if not test_passed:
        return Rating.Again
    if probe_correct is False:
        return Rating.Hard
    return Rating.Good


@dataclass
class ScheduleUpdate:
    rating: str
    due_at: datetime
    interval_days: float
    stability: float | None
    difficulty: float | None
    review_count: int


def to_card(item: ScheduleItem) -> Card:
    """Pulihkan Card py-fsrs dari baris ScheduleItem (kartu baru bila belum pernah)."""
    if item.fsrs_stability is None:
        return Card()
    state = State[item.fsrs_state] if item.fsrs_state else State.Review
    return Card(
        state=state,
        step=item.fsrs_step,
        stability=item.fsrs_stability,
        difficulty=item.fsrs_difficulty,
        due=as_utc(item.due_at),
        last_review=as_utc(item.last_review_at),
    )


def apply_rating(item: ScheduleItem, rating: Rating, now: datetime | None = None) -> ScheduleUpdate:
    """Jalankan satu review FSRS pada `item` (dimutasi di tempat) dan kembalikan ringkasan.

    Pemanggil bertanggung jawab menambahkan `item` ke session & commit.
    """
    now = as_utc(now) or utcnow()
    card, _log = _scheduler.review_card(to_card(item), rating, review_datetime=now)

    item.fsrs_stability = card.stability
    item.fsrs_difficulty = card.difficulty
    item.due_at = card.due
    item.fsrs_state = card.state.name
    item.fsrs_step = card.step
    item.last_review_at = now
    item.review_count = (item.review_count or 0) + 1

    return ScheduleUpdate(
        rating=rating.name,
        due_at=card.due,
        interval_days=(card.due - now).total_seconds() / 86400,
        stability=card.stability,
        difficulty=card.difficulty,
        review_count=item.review_count,
    )


def is_due(item: ScheduleItem, now: datetime | None = None) -> bool:
    """Sudah jatuh tempo? Node yang belum pernah masuk jadwal (due_at None) TIDAK due —
    ia belum pernah dibuktikan, jadi tempatnya di jalur akuisisi, bukan di review."""
    if item.due_at is None:
        return False
    return (as_utc(now) or utcnow()) >= as_utc(item.due_at)
