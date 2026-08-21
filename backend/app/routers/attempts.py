"""Router attempt: POST /attempts adalah JANTUNG loop (submit kode → verdict).

Response memuat `test_output` supaya UI menampilkan kegagalan test ke Bryant —
itu sinyal belajar (cermin §7.6), bukan hukuman yang disembunyikan.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session

from app.db import get_session
from app.services.attempt_service import node_attempts, submit_attempt

router = APIRouter(tags=["attempts"])


class SubmitIn(BaseModel):
    node_id: str
    instance_id: str
    scaffold_level: str
    submitted_code: str
    duration_seconds: int = 0
    timebox_exceeded: bool = False


class SubmitOut(BaseModel):
    attempt_id: int
    passed: bool
    result: str
    test_output: str
    timed_out: bool
    duration_seconds: float
    mode: str
    scaffold_level: str


class AttemptOut(BaseModel):
    id: int
    node_id: str
    instance_id: str | None
    mode: str
    scaffold_level: str
    result: str | None
    probe_result: str | None
    duration_seconds: int


@router.post("/attempts", response_model=SubmitOut)
def create_attempt(body: SubmitIn, session: Session = Depends(get_session)) -> SubmitOut:
    try:
        res = submit_attempt(
            session,
            node_id=body.node_id,
            instance_id=body.instance_id,
            scaffold_level=body.scaffold_level,
            submitted_code=body.submitted_code,
            duration_seconds=body.duration_seconds,
            timebox_exceeded=body.timebox_exceeded,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    return SubmitOut(
        attempt_id=res.attempt.id,
        passed=res.grade.passed,
        result=res.attempt.result,
        test_output=res.grade.test_output,
        timed_out=res.grade.timed_out,
        duration_seconds=res.grade.duration_seconds,
        mode=res.attempt.mode,
        scaffold_level=res.attempt.scaffold_level,
    )


@router.get("/nodes/{node_id}/attempts", response_model=list[AttemptOut])
def list_attempts(node_id: str, session: Session = Depends(get_session)) -> list[AttemptOut]:
    return [
        AttemptOut(
            id=a.id,
            node_id=a.node_id,
            instance_id=a.instance_id,
            mode=a.mode,
            scaffold_level=a.scaffold_level,
            result=a.result,
            probe_result=a.probe_result,
            duration_seconds=a.duration_seconds,
        )
        for a in node_attempts(session, node_id)
    ]
