"""Router node: daftar node + detail + tampilan per scaffold level.

Dashboard adalah DAFTAR LINEAR node + status — bukan graf visual/DAG (§8 Guardrails).
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from app.config import DATA_DIR
from app.db import get_session
from app.models import Attempt, Node
from app.services.progress import all_statuses, effective_status
from app.services.scaffold import LEVELS, build_level_view, pick_probe

router = APIRouter(prefix="/nodes", tags=["nodes"])


class NodeSummary(BaseModel):
    id: str
    concept: str
    description: str
    grader_type: str
    estimated_minutes: int
    timebox_seconds: int
    status: str


class NodeDetail(NodeSummary):
    levels: list[str]


class LevelViewOut(BaseModel):
    level: str
    kind: str
    title: str
    prompt: str
    code: str
    signature_contract: str
    instance_id: str
    editable: bool
    show_timebox: bool
    timebox_seconds: int


class ExplanationOut(BaseModel):
    node_id: str
    markdown: str
    worked_example: str


class ProbeOut(BaseModel):
    # SENGAJA tanpa correct_answer — jangan bocorkan jawaban ke klien.
    id: str
    node_id: str
    type: str
    question: str
    options: list[str]


@router.get("", response_model=list[NodeSummary])
def list_nodes(session: Session = Depends(get_session)) -> list[NodeSummary]:
    statuses = all_statuses(session)
    nodes = session.exec(select(Node)).all()
    nodes = sorted(nodes, key=lambda n: n.id)
    return [
        NodeSummary(
            id=n.id,
            concept=n.concept,
            description=n.description,
            grader_type=n.grader_type,
            estimated_minutes=n.estimated_minutes,
            timebox_seconds=n.timebox_seconds,
            status=statuses.get(n.id, "locked"),
        )
        for n in nodes
    ]


@router.get("/{node_id}", response_model=NodeDetail)
def get_node(node_id: str, session: Session = Depends(get_session)) -> NodeDetail:
    node = session.get(Node, node_id)
    if node is None:
        raise HTTPException(status_code=404, detail="node not found")
    return NodeDetail(
        id=node.id,
        concept=node.concept,
        description=node.description,
        grader_type=node.grader_type,
        estimated_minutes=node.estimated_minutes,
        timebox_seconds=node.timebox_seconds,
        status=effective_status(session, node.id),
        levels=LEVELS,
    )


@router.get("/{node_id}/level/{level}", response_model=LevelViewOut)
def get_level(
    node_id: str, level: str, session: Session = Depends(get_session)
) -> LevelViewOut:
    node = session.get(Node, node_id)
    if node is None:
        raise HTTPException(status_code=404, detail="node not found")
    try:
        view = build_level_view(session, node, level)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return LevelViewOut(**view.__dict__)


@router.get("/{node_id}/explanation", response_model=ExplanationOut)
def get_explanation(node_id: str, session: Session = Depends(get_session)) -> ExplanationOut:
    """Materi just-in-time (R3, M5) — HANYA setelah kegagalan nyata.

    Gerbang "harus ada attempt gagal" ada di server, bukan cuma di UI: tanpa itu
    `explanation.md` berubah jadi bab bacaan yang bisa dilahap sebelum mencoba —
    persis content library yang ditolak §8.
    """
    node = session.get(Node, node_id)
    if node is None:
        raise HTTPException(status_code=404, detail="node not found")

    failed = session.exec(
        select(Attempt).where(Attempt.node_id == node_id, Attempt.result == "fail")
    ).first()
    if failed is None:
        raise HTTPException(
            status_code=403,
            detail="materi just-in-time baru terbuka setelah attempt yang gagal",
        )

    node_dir = DATA_DIR / "domains" / node.domain_id / "nodes" / node_id
    explanation = node_dir / "explanation.md"
    worked = node_dir / "worked_example.py"
    if not explanation.exists():
        raise HTTPException(status_code=404, detail="node ini belum punya materi just-in-time")
    return ExplanationOut(
        node_id=node_id,
        markdown=explanation.read_text(encoding="utf-8"),
        worked_example=worked.read_text(encoding="utf-8") if worked.exists() else "",
    )


@router.get("/{node_id}/probe", response_model=ProbeOut)
def get_probe(node_id: str, session: Session = Depends(get_session)) -> ProbeOut:
    probe = pick_probe(session, node_id)
    if probe is None:
        raise HTTPException(status_code=404, detail="probe not found for node")
    return ProbeOut(
        id=probe.id,
        node_id=probe.node_id,
        type=probe.type,
        question=probe.question,
        options=probe.options,
    )
