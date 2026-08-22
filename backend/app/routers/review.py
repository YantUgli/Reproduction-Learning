"""Router review harian (M4 langkah 5).

Alur satu review:

    GET  /review/due                  → node yang due_at <= sekarang
    GET  /review/{node_id}/challenge  → instance BERBEDA dari yang terakhir dipakai
    POST /review/submit               → jalankan hidden test; GAGAL → langsung lapsed
    POST /review/probe                → probe deterministik; lalu jadwal ulang via FSRS

Dua fase disengaja: probe baru masuk akal setelah Bryant melihat verdict test-nya.
Kalau test gagal, hasilnya diterapkan seketika (tak ada gunanya bertanya probe untuk
node yang produksinya sudah gagal — verdict-nya sudah pasti `lapsed`).
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from app.db import get_session
from app.models import ComprehensionProbe, Node, ScheduleItem
from app.services.attempt_service import submit_attempt
from app.services.mastery import IN_SCHEDULE, Outcome, apply_outcome
from app.services.scaffold import review_instance
from app.services.scheduler import as_utc, utcnow

router = APIRouter(prefix="/review", tags=["review"])


class DueItem(BaseModel):
    node_id: str
    concept: str
    status: str
    due_at: str | None
    overdue_days: float
    review_count: int
    consecutive_success: int
    successes_needed: int


class ReviewChallenge(BaseModel):
    node_id: str
    concept: str
    instance_id: str
    variant_label: str
    prompt: str
    signature_contract: str
    timebox_seconds: int
    previous_instance_id: str | None
    needs_more_variants: bool


class OutcomeOut(BaseModel):
    node_id: str
    previous_status: str
    status: str
    rating: str
    clean: bool
    spaced: bool
    consecutive_success: int
    successes_needed: int
    due_at: str | None
    interval_days: float | None
    became_acquired: bool
    became_mastered: bool
    became_lapsed: bool

    @classmethod
    def of(cls, o: Outcome) -> "OutcomeOut":
        return cls(
            node_id=o.node_id,
            previous_status=o.previous_status,
            status=o.status,
            rating=o.rating,
            clean=o.clean,
            spaced=o.spaced,
            consecutive_success=o.consecutive_success,
            successes_needed=o.successes_needed,
            due_at=o.due_at.isoformat() if o.due_at else None,
            interval_days=o.interval_days,
            became_acquired=o.became_acquired,
            became_mastered=o.became_mastered,
            became_lapsed=o.became_lapsed,
        )


class ReviewSubmitIn(BaseModel):
    node_id: str
    instance_id: str
    submitted_code: str
    duration_seconds: int = 0
    timebox_exceeded: bool = False


class ProbeOut(BaseModel):
    # Tanpa correct_answer — jawaban benar tak pernah dikirim ke klien.
    id: str
    node_id: str
    type: str
    question: str
    options: list[str]


class ReviewSubmitOut(BaseModel):
    attempt_id: int
    passed: bool
    test_output: str
    timed_out: bool
    probe: ProbeOut | None  # None bila test gagal (hasil sudah final)
    outcome: OutcomeOut | None  # terisi seketika bila test gagal


class ReviewProbeIn(BaseModel):
    attempt_id: int
    probe_id: str
    answer: str


class ReviewProbeOut(BaseModel):
    probe_correct: bool
    outcome: OutcomeOut


def _due_rows(session: Session) -> list[tuple[ScheduleItem, Node]]:
    now = utcnow()
    items = session.exec(
        select(ScheduleItem).where(
            ScheduleItem.due_at.is_not(None),
            ScheduleItem.status.in_(tuple(IN_SCHEDULE)),
        )
    ).all()
    rows = []
    for item in items:
        if as_utc(item.due_at) > now:
            continue
        node = session.get(Node, item.node_id)
        if node is not None:
            rows.append((item, node))
    rows.sort(key=lambda r: as_utc(r[0].due_at))
    return rows


def due_items(session: Session) -> list[DueItem]:
    from app.config import MASTERY_SUCCESSES_DEFAULT

    now = utcnow()
    return [
        DueItem(
            node_id=item.node_id,
            concept=node.concept,
            status=item.status,
            due_at=item.due_at.isoformat() if item.due_at else None,
            overdue_days=(now - as_utc(item.due_at)).total_seconds() / 86400,
            review_count=item.review_count,
            consecutive_success=item.consecutive_success,
            successes_needed=MASTERY_SUCCESSES_DEFAULT,
        )
        for item, node in _due_rows(session)
    ]


@router.get("/due", response_model=list[DueItem])
def list_due(session: Session = Depends(get_session)) -> list[DueItem]:
    return due_items(session)


@router.get("/{node_id}/challenge", response_model=ReviewChallenge)
def get_challenge(node_id: str, session: Session = Depends(get_session)) -> ReviewChallenge:
    node = session.get(Node, node_id)
    if node is None:
        raise HTTPException(status_code=404, detail="node not found")
    item = session.get(ScheduleItem, node_id)
    if item is None or item.status not in IN_SCHEDULE:
        raise HTTPException(
            status_code=400,
            detail="node belum pernah acquired — kerjakan lewat sesi node, bukan review",
        )
    try:
        picked = review_instance(session, node_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    return ReviewChallenge(
        node_id=node_id,
        concept=node.concept,
        instance_id=picked.instance.id,
        variant_label=picked.instance.variant_label,
        prompt=picked.instance.prompt,
        signature_contract=picked.instance.signature_contract,
        timebox_seconds=node.timebox_seconds,
        previous_instance_id=picked.previous_instance_id,
        needs_more_variants=picked.needs_more_variants,
    )


@router.post("/submit", response_model=ReviewSubmitOut)
def submit_review(body: ReviewSubmitIn, session: Session = Depends(get_session)) -> ReviewSubmitOut:
    try:
        res = submit_attempt(
            session,
            node_id=body.node_id,
            instance_id=body.instance_id,
            scaffold_level="L0",  # review selalu tanpa scaffold
            submitted_code=body.submitted_code,
            duration_seconds=body.duration_seconds,
            timebox_exceeded=body.timebox_exceeded,
            mode="review",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    if not res.grade.passed:
        # Produksi gagal → verdict sudah final; jangan tunda dengan probe.
        outcome = apply_outcome(
            session, node_id=body.node_id, test_passed=False, probe_correct=None
        )
        return ReviewSubmitOut(
            attempt_id=res.attempt.id,
            passed=False,
            test_output=res.attempt.test_output,
            timed_out=res.grade.timed_out,
            probe=None,
            outcome=OutcomeOut.of(outcome),
        )

    probe = session.exec(
        select(ComprehensionProbe).where(ComprehensionProbe.node_id == body.node_id)
    ).first()
    if probe is None:
        # Node tanpa probe (seharusnya ditolak M2) — terapkan hasil apa adanya.
        outcome = apply_outcome(session, node_id=body.node_id, test_passed=True, probe_correct=None)
        return ReviewSubmitOut(
            attempt_id=res.attempt.id,
            passed=True,
            test_output=res.attempt.test_output,
            timed_out=res.grade.timed_out,
            probe=None,
            outcome=OutcomeOut.of(outcome),
        )

    return ReviewSubmitOut(
        attempt_id=res.attempt.id,
        passed=True,
        test_output=res.attempt.test_output,
        timed_out=res.grade.timed_out,
        probe=ProbeOut(
            id=probe.id,
            node_id=probe.node_id,
            type=probe.type,
            question=probe.question,
            options=probe.options,
        ),
        outcome=None,
    )


@router.post("/probe", response_model=ReviewProbeOut)
def submit_review_probe(
    body: ReviewProbeIn, session: Session = Depends(get_session)
) -> ReviewProbeOut:
    from app.services.attempt_service import answer_probe

    try:
        res = answer_probe(
            session, attempt_id=body.attempt_id, probe_id=body.probe_id, answer=body.answer
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    if res.outcome is None:
        raise HTTPException(status_code=400, detail="attempt ini bukan attempt review")
    return ReviewProbeOut(probe_correct=res.probe_correct, outcome=OutcomeOut.of(res.outcome))
