"""KPI inti produk (PRD §9) — dihitung dari Attempt, bukan dari perasaan.

Dua angka yang dipakai dashboard:
- **`reproduce-without-AI pass rate`** (keseluruhan & per node)
- **jumlah node `mastered`**

Definisi pass rate di sini sengaja SEMPIT: hanya attempt yang benar-benar menguji
reproduksi tanpa bantuan di layar — mode `verification` (L0), `review`, dan `placement`.
Attempt mode `acquisition` (L3–L1, scaffold masih terpampang) TIDAK dihitung.
Memasukkannya akan menggelembungkan angkanya dengan latihan bersontekan, dan KPI yang
menggelembung persis adalah illusion of competence yang produk ini seharusnya lawan.
"""

from dataclasses import dataclass
from datetime import datetime

from sqlmodel import Session, select

from app.config import MASTERY_SUCCESSES_DEFAULT
from app.models import Attempt, Node, ScheduleItem, ScheduleStatus
from app.services.progress import all_statuses
from app.services.scheduler import as_utc, utcnow

# Mode attempt yang dihitung sebagai bukti reproduce-without-AI.
REPRODUCE_MODES = ("verification", "review", "placement")


@dataclass
class NodeStat:
    node_id: str
    concept: str
    status: str
    attempts: int
    passed: int
    pass_rate: float | None  # None = belum pernah diuji tanpa bantuan
    review_count: int
    consecutive_success: int
    due_at: datetime | None
    is_due: bool


@dataclass
class Stats:
    total_nodes: int
    by_status: dict[str, int]
    mastered_count: int
    due_count: int
    reproduce_attempts: int
    reproduce_passed: int
    reproduce_pass_rate: float | None
    successes_needed: int
    nodes: list[NodeStat]


def compute_stats(session: Session) -> Stats:
    now = utcnow()
    statuses = all_statuses(session)
    items = {i.node_id: i for i in session.exec(select(ScheduleItem)).all()}
    nodes = sorted(session.exec(select(Node)).all(), key=lambda n: n.id)

    attempts = session.exec(select(Attempt).where(Attempt.mode.in_(REPRODUCE_MODES))).all()

    tally: dict[str, list[int]] = {}
    for a in attempts:
        row = tally.setdefault(a.node_id, [0, 0])
        row[0] += 1
        if a.result == "pass":
            row[1] += 1

    node_stats: list[NodeStat] = []
    due_count = 0
    for node in nodes:
        item = items.get(node.id)
        total, passed = tally.get(node.id, (0, 0))
        due_at = as_utc(item.due_at) if item and item.due_at else None
        status = statuses.get(node.id, ScheduleStatus.locked.value)
        is_due = bool(due_at and due_at <= now and status != ScheduleStatus.locked.value)
        if is_due:
            due_count += 1
        node_stats.append(
            NodeStat(
                node_id=node.id,
                concept=node.concept,
                status=status,
                attempts=total,
                passed=passed,
                pass_rate=(passed / total) if total else None,
                review_count=item.review_count if item else 0,
                consecutive_success=item.consecutive_success if item else 0,
                due_at=due_at,
                is_due=is_due,
            )
        )

    by_status: dict[str, int] = {s.value: 0 for s in ScheduleStatus}
    for status in statuses.values():
        by_status[status] = by_status.get(status, 0) + 1

    total_attempts = sum(t[0] for t in tally.values())
    total_passed = sum(t[1] for t in tally.values())

    return Stats(
        total_nodes=len(nodes),
        by_status=by_status,
        mastered_count=by_status.get(ScheduleStatus.mastered.value, 0),
        due_count=due_count,
        reproduce_attempts=total_attempts,
        reproduce_passed=total_passed,
        reproduce_pass_rate=(total_passed / total_attempts) if total_attempts else None,
        successes_needed=MASTERY_SUCCESSES_DEFAULT,
        nodes=node_stats,
    )
