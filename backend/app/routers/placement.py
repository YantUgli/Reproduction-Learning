"""Router placement (M4 langkah 4).

    POST /placement/start            → buka sesi, dapat tantangan pertama (paling hilir)
    GET  /placement/{session_id}     → state sesi (tantangan berjalan / lantai)
    POST /placement/{session_id}/submit → kerjakan tantangan, sesi maju satu langkah

Tak ada endpoint "tanya Bryant sudah bisa apa" — dan memang tak boleh ada (§1 PRD:
lantai DITEMUKAN, tidak diasumsikan).
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session

from app.db import get_session
from app.routers.review import OutcomeOut
from app.services.placement import (
    PlacementState,
    compute_state,
    start_placement,
    submit_placement,
)

router = APIRouter(prefix="/placement", tags=["placement"])


class ChallengeOut(BaseModel):
    node_id: str
    concept: str
    instance_id: str
    prompt: str
    signature_contract: str
    timebox_seconds: int
    position: int


class TestedOut(BaseModel):
    node_id: str
    result: str | None
    attempt_id: int | None


class StateOut(BaseModel):
    session_id: int
    max_nodes: int
    tested: list[TestedOut]
    finished: bool
    exhausted: bool
    floor_node_id: str | None
    current: ChallengeOut | None

    @classmethod
    def of(cls, s: PlacementState) -> "StateOut":
        return cls(
            session_id=s.session_id,
            max_nodes=s.max_nodes,
            tested=[TestedOut(**t) for t in s.tested],
            finished=s.finished,
            exhausted=s.exhausted,
            floor_node_id=s.floor_node_id,
            current=ChallengeOut(**s.current.__dict__) if s.current else None,
        )


class SubmitIn(BaseModel):
    submitted_code: str
    duration_seconds: int = 0
    timebox_exceeded: bool = False


class SubmitOut(BaseModel):
    passed: bool
    test_output: str
    attempt_id: int
    state: StateOut
    floor_outcome: OutcomeOut | None
    unlocked: list[str]


@router.post("/start", response_model=StateOut)
def post_start(session: Session = Depends(get_session)) -> StateOut:
    return StateOut.of(start_placement(session))


@router.get("/{session_id}", response_model=StateOut)
def get_state(session_id: int, session: Session = Depends(get_session)) -> StateOut:
    try:
        return StateOut.of(compute_state(session, session_id))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.post("/{session_id}/submit", response_model=SubmitOut)
def post_submit(
    session_id: int, body: SubmitIn, session: Session = Depends(get_session)
) -> SubmitOut:
    try:
        res = submit_placement(
            session,
            session_id=session_id,
            submitted_code=body.submitted_code,
            duration_seconds=body.duration_seconds,
            timebox_exceeded=body.timebox_exceeded,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    return SubmitOut(
        passed=res.passed,
        test_output=res.test_output,
        attempt_id=res.attempt_id,
        state=StateOut.of(res.state),
        floor_outcome=OutcomeOut.of(res.floor_outcome) if res.floor_outcome else None,
        unlocked=res.unlocked,
    )
