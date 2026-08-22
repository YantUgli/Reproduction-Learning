"""Router probe: cek jawaban comprehension probe secara DETERMINISTIK.

Pengecekan = kecocokan string dengan `correct_answer` (di server; tak pernah dikirim
ke klien). Tak ada AI/penilaian makna di sini (§1/§3 invariant).
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session

from app.db import get_session
from app.services.attempt_service import answer_probe

router = APIRouter(prefix="/probes", tags=["probes"])


class ProbeAnswerIn(BaseModel):
    attempt_id: int
    probe_id: str
    answer: str


class ProbeAnswerOut(BaseModel):
    probe_correct: bool
    acquired: bool
    # M4: setelah lolos bersih, node masuk jadwal FSRS — UI menampilkan kapan
    # jatuh temponya & berapa sukses berjarak lagi menuju `mastered`.
    status: str | None = None
    due_at: str | None = None
    interval_days: float | None = None
    consecutive_success: int | None = None
    successes_needed: int | None = None
    became_mastered: bool = False


@router.post("/answer", response_model=ProbeAnswerOut)
def submit_probe_answer(
    body: ProbeAnswerIn, session: Session = Depends(get_session)
) -> ProbeAnswerOut:
    try:
        outcome = answer_probe(
            session,
            attempt_id=body.attempt_id,
            probe_id=body.probe_id,
            answer=body.answer,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    o = outcome.outcome
    return ProbeAnswerOut(
        probe_correct=outcome.probe_correct,
        acquired=outcome.acquired,
        status=o.status if o else None,
        due_at=o.due_at.isoformat() if o and o.due_at else None,
        interval_days=o.interval_days if o else None,
        consecutive_success=o.consecutive_success if o else None,
        successes_needed=o.successes_needed if o else None,
        became_mastered=bool(o and o.became_mastered),
    )
