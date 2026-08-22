"""Transisi status mastery (M4 langkah 3) — satu-satunya tempat status berubah.

    locked ─(prasyarat hard terpenuhi)→ available
    available ─(lolos bersih pertama)→ acquired
    acquired ─(N sukses BERJARAK)→ mastered
    acquired|mastered ─(eksekusi GAGAL)→ lapsed
    lapsed ─(lolos bersih lagi)→ acquired

INVARIANT yang ditegakkan di sini:

1. **Hanya eksekusi kode yang boleh menurunkan status** (PRD §2). Probe yang salah
   memperberat jadwal (Rating.Hard) dan membatalkan hitungan sukses, tapi ia TIDAK
   PERNAH sendirian membuat node `lapsed`. Yang menjatuhkan hanya hidden test gagal.

2. **`mastered` butuh N sukses BERJARAK, bukan N sukses.** Empat kali lolos dalam satu
   sesi sore ≠ mastered. Jarak ditegakkan lewat `due_at`: satu sukses hanya dihitung
   kalau attempt-nya terjadi saat node memang sudah jatuh tempo (`now >= due_at`).
   Karena FSRS di sini tak punya learning step menit-an (config), jatuh tempo paling
   cepat berskala hari — jadi "berjarak" benar-benar berarti berjarak.

3. **Jadwal tak disentuh sebelum node terbukti.** Gagal di L2 saat masih berlatih tidak
   membuat node "jatuh tempo"; ia belum pernah masuk jadwal. Attempt tetap dicatat
   (itu data KPI), tapi FSRS baru mulai berjalan pada lolos bersih pertama.

Open question PRD Q3 diputuskan di sini: `lapsed` kembali ke **`acquired`**, bukan
`available` penuh. Alasan: `available` berarti "belum pernah dibuktikan" — padahal
Bryant PERNAH memproduksinya; yang terjadi adalah memori meluruh, bukan bukti hilang.
Konsekuensinya `lapsed` juga tidak mengunci ulang node hilirnya (lihat progress.py):
satu review buruk tak boleh merobohkan separuh peta.
"""

from dataclasses import dataclass
from datetime import datetime

from sqlmodel import Session

from app.config import MASTERY_SUCCESSES_DEFAULT
from app.models import Node, ScheduleItem, ScheduleStatus
from app.services.scheduler import ScheduleUpdate, apply_rating, as_utc, rating_for, utcnow

# Status yang berarti "node sudah pernah dibuktikan lewat eksekusi" → sudah masuk jadwal.
IN_SCHEDULE = {
    ScheduleStatus.acquired.value,
    ScheduleStatus.mastered.value,
    ScheduleStatus.lapsed.value,
}


@dataclass
class Outcome:
    node_id: str
    previous_status: str
    status: str
    rating: str
    clean: bool  # test PASS dan probe tidak salah
    spaced: bool  # attempt ini jatuh pada/ setelah due_at → dihitung sebagai sukses berjarak
    consecutive_success: int
    successes_needed: int
    due_at: datetime | None
    interval_days: float | None
    became_acquired: bool
    became_mastered: bool
    became_lapsed: bool


def ensure_schedule_item(session: Session, node: Node) -> ScheduleItem:
    item = session.get(ScheduleItem, node.id)
    if item is None:
        item = ScheduleItem(node_id=node.id, status=node.status_default)
        session.add(item)
    return item


def apply_outcome(
    session: Session,
    *,
    node_id: str,
    test_passed: bool,
    probe_correct: bool | None,
    now: datetime | None = None,
    successes_needed: int = MASTERY_SUCCESSES_DEFAULT,
) -> Outcome:
    """Terapkan hasil satu attempt terverifikasi ke status + jadwal sebuah node.

    `probe_correct=None` berarti attempt ini memang tak memakai probe (placement:
    reproduksi dingin tanpa scaffold sama sekali) — bukan "probe dilewati".
    """
    node = session.get(Node, node_id)
    if node is None:
        raise ValueError(f"node tak ditemukan: {node_id!r}")

    item = ensure_schedule_item(session, node)
    now = as_utc(now) or utcnow()
    previous = item.status

    clean = test_passed and probe_correct is not False
    was_in_schedule = previous in IN_SCHEDULE
    # Berjarak = node memang sudah jatuh tempo saat dikerjakan. Akuisisi pertama
    # (belum punya due_at) dihitung sebagai sukses pertama.
    spaced = item.due_at is None or now >= as_utc(item.due_at)

    became_acquired = became_mastered = became_lapsed = False

    if not test_passed:
        item.consecutive_success = 0
        if was_in_schedule and previous != ScheduleStatus.lapsed.value:
            item.status = ScheduleStatus.lapsed.value
            became_lapsed = True
        elif previous == ScheduleStatus.lapsed.value:
            item.status = ScheduleStatus.lapsed.value
    elif not clean:
        # Test lolos tapi probe salah: produksi terbukti, pemahaman rapuh.
        # Status DIAM (tak naik, tak turun); hanya jadwal yang diperberat (Hard).
        pass
    else:
        if spaced:
            item.consecutive_success = (item.consecutive_success or 0) + 1
        if previous != ScheduleStatus.mastered.value:
            item.status = ScheduleStatus.acquired.value
            became_acquired = previous not in IN_SCHEDULE
        if item.consecutive_success >= successes_needed:
            item.status = ScheduleStatus.mastered.value
            became_mastered = previous != ScheduleStatus.mastered.value

    # FSRS hanya berjalan untuk node yang sudah/baru saja masuk jadwal (invariant 3).
    update: ScheduleUpdate | None = None
    if was_in_schedule or item.status in IN_SCHEDULE:
        rating = rating_for(test_passed=test_passed, probe_correct=probe_correct)
        update = apply_rating(item, rating, now)

    session.add(item)
    session.commit()
    session.refresh(item)

    return Outcome(
        node_id=node_id,
        previous_status=previous,
        status=item.status,
        rating=update.rating if update else "(belum masuk jadwal)",
        clean=clean,
        spaced=spaced,
        consecutive_success=item.consecutive_success,
        successes_needed=successes_needed,
        due_at=item.due_at,
        interval_days=update.interval_days if update else None,
        became_acquired=became_acquired,
        became_mastered=became_mastered,
        became_lapsed=became_lapsed,
    )


def unlock(session: Session, node_id: str) -> ScheduleItem | None:
    """Naikkan node `locked` menjadi `available` — MEMBUKA, bukan mengklaim mastery.

    Dipakai placement: saat batas fail→pass ditemukan, prasyarat di bawah lantai jelas
    sudah dikuasai secara implisit, jadi tak masuk akal membiarkannya terkunci. Tapi
    ia TIDAK di-set `acquired`: tak ada eksekusi yang membuktikannya (PRD §2).
    """
    node = session.get(Node, node_id)
    if node is None:
        return None
    item = ensure_schedule_item(session, node)
    if item.status == ScheduleStatus.locked.value:
        item.status = ScheduleStatus.available.value
        session.add(item)
    return item
