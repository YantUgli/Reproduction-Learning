"""Router statistik dashboard (M4 langkah 6) — KPI inti PRD §9.

Router tipis di atas `services/kpi.py`; definisi KPI-nya ada di sana.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import Session

from app.db import get_session
from app.services.kpi import compute_stats
from app.services.placement import latest_floor

router = APIRouter(tags=["stats"])


class NodeStatOut(BaseModel):
    node_id: str
    concept: str
    status: str
    attempts: int
    passed: int
    pass_rate: float | None
    review_count: int
    consecutive_success: int
    due_at: str | None
    is_due: bool


class StatsOut(BaseModel):
    total_nodes: int
    by_status: dict[str, int]
    mastered_count: int
    due_count: int
    reproduce_attempts: int
    reproduce_passed: int
    reproduce_pass_rate: float | None
    successes_needed: int
    placement_floor_node_id: str | None
    nodes: list[NodeStatOut]


@router.get("/stats", response_model=StatsOut)
def get_stats(session: Session = Depends(get_session)) -> StatsOut:
    stats = compute_stats(session)
    return StatsOut(
        total_nodes=stats.total_nodes,
        by_status=stats.by_status,
        mastered_count=stats.mastered_count,
        due_count=stats.due_count,
        reproduce_attempts=stats.reproduce_attempts,
        reproduce_passed=stats.reproduce_passed,
        reproduce_pass_rate=stats.reproduce_pass_rate,
        successes_needed=stats.successes_needed,
        placement_floor_node_id=latest_floor(session),
        nodes=[
            NodeStatOut(
                node_id=n.node_id,
                concept=n.concept,
                status=n.status,
                attempts=n.attempts,
                passed=n.passed,
                pass_rate=n.pass_rate,
                review_count=n.review_count,
                consecutive_success=n.consecutive_success,
                due_at=n.due_at.isoformat() if n.due_at else None,
                is_due=n.is_due,
            )
            for n in stats.nodes
        ],
    )
