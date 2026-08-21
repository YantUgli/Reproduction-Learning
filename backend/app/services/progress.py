"""Status node efektif untuk dashboard (M3).

Locking dinamis: node `locked` bila ada `hard` edge prasyarat yang belum `acquired`.
Hanya `hard` yang mengikat urutan (§9 PRD); `soft` tidak mengunci.

Status efektif:
  acquired  → sudah lolos bersih (test PASS + probe benar) minimal sekali
  available → semua hard-prereq acquired (atau tak punya prereq)
  locked    → ada hard-prereq yang belum acquired
"""

from sqlmodel import Session, select

from app.models import Edge, Node, ScheduleItem, ScheduleStatus


def _acquired_ids(session: Session) -> set[str]:
    items = session.exec(
        select(ScheduleItem).where(ScheduleItem.status == ScheduleStatus.acquired.value)
    ).all()
    return {i.node_id for i in items}


def _hard_prereqs(session: Session) -> dict[str, list[str]]:
    """node_id → daftar node_id prasyarat keras (from) yang mengunci `to`."""
    prereqs: dict[str, list[str]] = {}
    for e in session.exec(select(Edge).where(Edge.type == "hard")).all():
        prereqs.setdefault(e.to_node_id, []).append(e.from_node_id)
    return prereqs


def effective_status(session: Session, node_id: str) -> str:
    acquired = _acquired_ids(session)
    if node_id in acquired:
        return ScheduleStatus.acquired.value
    prereqs = _hard_prereqs(session).get(node_id, [])
    if all(p in acquired for p in prereqs):
        return ScheduleStatus.available.value
    return ScheduleStatus.locked.value


def all_statuses(session: Session) -> dict[str, str]:
    acquired = _acquired_ids(session)
    prereqs = _hard_prereqs(session)
    statuses: dict[str, str] = {}
    for node in session.exec(select(Node)).all():
        if node.id in acquired:
            statuses[node.id] = ScheduleStatus.acquired.value
        elif all(p in acquired for p in prereqs.get(node.id, [])):
            statuses[node.id] = ScheduleStatus.available.value
        else:
            statuses[node.id] = ScheduleStatus.locked.value
    return statuses
