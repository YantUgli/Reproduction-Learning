"""Placement probe (M4 langkah 4) — MENEMUKAN lantai, bukan mengasumsikannya.

Premis PRD §1/§6: self-report Bryant tidak reliabel (illusion of competence). Karena
itu placement **tidak pernah bertanya "kamu sudah bisa apa"**. Ia menyodorkan rangkaian
tantangan reproduksi yang **menurun** — dari unit framework paling jauh di hilir turun
ke primitif — dan **berhenti di batas fail→pass pertama**. Node yang pertama berhasil
diproduksi itulah lantai awal.

Urutan menurun dipakai dari kedalaman DAG prasyarat keras (`hard_depth`): makin dalam
sebuah node, makin banyak yang harus sudah dikuasai lebih dulu. Ini pengurutan daftar,
BUKAN graf visual (§8).

**Open question PRD Q4 diputuskan di sini: maksimum `PLACEMENT_MAX_NODES` (7) node per
sesi.** Placement hampir selalu berhenti jauh lebih cepat (di pass pertama); batas ini
melindungi kasus terburuk — gagal terus sampai dasar — supaya satu sesi tak berubah
jadi tujuh tantangan reproduksi beruntun yang melelahkan dan malah merusak sinyalnya.
Kalau batas tercapai tanpa satu pun pass, hasilnya `exhausted`: lantai belum ketemu,
dan itu sendiri informasi (mulai dari node paling primitif, atau kurikulum butuh node
yang lebih dasar).

Yang TIDAK dilakukan placement:
- Tidak ada probe. Placement adalah reproduksi dingin tanpa scaffold apa pun; probe
  adalah gerbang untuk jalur akuisisi (di mana worked example sudah dilihat).
- Tidak menandai node mana pun `acquired` selain yang benar-benar dieksekusi dan lolos.
  Prasyarat di bawah lantai hanya DIBUKA kuncinya (`available`) — membuka ≠ mengklaim
  mastery (PRD §2).
"""

from dataclasses import dataclass, field

from sqlmodel import Session, select

from app.config import PLACEMENT_MAX_NODES
from app.models import Attempt, Node
from app.models import Session as SessionRow
from app.services.mastery import Outcome, apply_outcome, unlock
from app.services.progress import hard_ancestors, hard_depth
from app.services.scaffold import verification_instance

PLACEMENT_MODE = "placement"


@dataclass
class PlacementChallenge:
    node_id: str
    concept: str
    instance_id: str
    prompt: str
    signature_contract: str
    timebox_seconds: int
    position: int  # urutan ke-berapa dalam sesi (1-based)


@dataclass
class PlacementState:
    session_id: int
    order: list[str]
    max_nodes: int
    tested: list[dict] = field(default_factory=list)
    finished: bool = False
    exhausted: bool = False
    floor_node_id: str | None = None
    current: PlacementChallenge | None = None


def descending_order(session: Session) -> list[str]:
    """Node terurut dari yang PALING JAUH DI HILIR ke primitif (kandidat placement)."""
    depth = hard_depth(session)
    nodes = session.exec(select(Node)).all()
    # Kedalaman menurun; id menurun sebagai tie-break stabil (id belakangan biasanya
    # materi belakangan).
    return [n.id for n in sorted(nodes, key=lambda n: (depth.get(n.id, 0), n.id), reverse=True)]


def start_placement(session: Session) -> PlacementState:
    """Buka sesi placement baru. `ai_available=False` — placement itu reproduksi murni."""
    row = SessionRow(mode=PLACEMENT_MODE, ai_available=False)
    session.add(row)
    session.commit()
    session.refresh(row)
    return compute_state(session, row.id)


def _placement_attempts(session: Session, session_id: int) -> list[Attempt]:
    return list(
        session.exec(
            select(Attempt)
            .where(Attempt.session_id == session_id, Attempt.mode == PLACEMENT_MODE)
            .order_by(Attempt.id)
        ).all()
    )


def _challenge_for(session: Session, node_id: str, position: int) -> PlacementChallenge:
    node = session.get(Node, node_id)
    # Pakai varian VERIFIKASI, bukan varian pengajaran: kalau nanti Bryant masuk jalur
    # akuisisi untuk node ini, worked example-nya masih segar (belum pernah dilihat).
    instance = verification_instance(session, node_id)
    return PlacementChallenge(
        node_id=node_id,
        concept=node.concept,
        instance_id=instance.id,
        prompt=instance.prompt,
        signature_contract=instance.signature_contract,
        timebox_seconds=node.timebox_seconds,
        position=position,
    )


def compute_state(session: Session, session_id: int) -> PlacementState:
    """Rekonstruksi state sesi placement dari Attempt-nya (tak ada state di memori)."""
    row = session.get(SessionRow, session_id)
    if row is None or row.mode != PLACEMENT_MODE:
        raise ValueError(f"sesi placement tak ditemukan: {session_id}")

    order = descending_order(session)
    attempts = _placement_attempts(session, session_id)
    max_nodes = min(PLACEMENT_MAX_NODES, len(order))

    state = PlacementState(session_id=session_id, order=order, max_nodes=max_nodes)
    state.tested = [
        {"node_id": a.node_id, "result": a.result, "attempt_id": a.id} for a in attempts
    ]

    for attempt in attempts:
        if attempt.result == "pass":
            # BATAS fail→pass pertama — lantai ditemukan, berhenti di sini.
            state.finished = True
            state.floor_node_id = attempt.node_id
            return state

    if len(attempts) >= max_nodes:
        state.finished = True
        state.exhausted = True
        return state

    state.current = _challenge_for(session, order[len(attempts)], len(attempts) + 1)
    return state


@dataclass
class PlacementSubmitResult:
    state: PlacementState
    passed: bool
    test_output: str
    attempt_id: int
    floor_outcome: Outcome | None = None
    unlocked: list[str] = field(default_factory=list)


def submit_placement(
    session: Session,
    *,
    session_id: int,
    submitted_code: str,
    duration_seconds: int = 0,
    timebox_exceeded: bool = False,
) -> PlacementSubmitResult:
    """Kerjakan tantangan placement saat ini, lalu majukan sesi."""
    # Impor lokal: attempt_service mengimpor mastery yang mengimpor scaffold —
    # jaga arah dependensi tetap satu arah.
    from app.services.attempt_service import submit_attempt

    state = compute_state(session, session_id)
    if state.finished or state.current is None:
        raise ValueError("sesi placement sudah selesai")

    challenge = state.current
    res = submit_attempt(
        session,
        node_id=challenge.node_id,
        instance_id=challenge.instance_id,
        # Placement tak punya scaffold sama sekali — bukan L0 dari tangga L3→L0.
        scaffold_level="",
        submitted_code=submitted_code,
        duration_seconds=duration_seconds,
        timebox_exceeded=timebox_exceeded,
        mode=PLACEMENT_MODE,
        session_id=session_id,
    )

    new_state = compute_state(session, session_id)
    result = PlacementSubmitResult(
        state=new_state,
        passed=res.grade.passed,
        test_output=res.attempt.test_output,
        attempt_id=res.attempt.id,
    )

    if new_state.finished and new_state.floor_node_id:
        result.floor_outcome, result.unlocked = apply_floor(session, new_state.floor_node_id)
    if new_state.finished:
        _close_session(session, session_id)
    return result


def apply_floor(session: Session, floor_node_id: str) -> tuple[Outcome, list[str]]:
    """Terapkan lantai: node lantai jadi `acquired` + masuk jadwal; prasyaratnya DIBUKA.

    Node lantai memang lolos eksekusi tanpa scaffold apa pun — bukti reproduksi yang
    lebih dingin daripada L0 di jalur akuisisi, jadi `acquired` sah (§2 terpenuhi:
    yang memutuskan tetap eksekusi kode). Prasyarat transitifnya TIDAK dieksekusi,
    jadi maksimal dibuka jadi `available` — bukan diklaim dikuasai.
    """
    outcome = apply_outcome(
        session,
        node_id=floor_node_id,
        test_passed=True,
        probe_correct=None,  # placement memang tak memakai probe
    )
    unlocked: list[str] = []
    for ancestor in sorted(hard_ancestors(session, floor_node_id)):
        item = unlock(session, ancestor)
        if item is not None and item.status == "available":
            unlocked.append(ancestor)
    session.commit()
    return outcome, unlocked


def _close_session(session: Session, session_id: int) -> None:
    from app.services.scheduler import utcnow

    row = session.get(SessionRow, session_id)
    if row is not None and row.ended_at is None:
        row.ended_at = utcnow()
        session.add(row)
        session.commit()


def latest_floor(session: Session) -> str | None:
    """Lantai dari sesi placement terakhir yang selesai (untuk dashboard)."""
    rows = session.exec(
        select(SessionRow).where(SessionRow.mode == PLACEMENT_MODE).order_by(SessionRow.id.desc())
    ).all()
    for row in rows:
        for attempt in _placement_attempts(session, row.id):
            if attempt.result == "pass":
                return attempt.node_id
    return None
