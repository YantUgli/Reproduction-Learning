"""Status node efektif untuk dashboard (M3, diperluas M4).

Sumber kebenaran status adalah `ScheduleItem.status` — kecuali untuk node yang belum
pernah masuk jadwal, yang statusnya dihitung dari locking prasyarat:

  mastered  → sudah lolos N kali BERJARAK (M4)
  acquired  → sudah lolos bersih minimal sekali
  lapsed    → pernah acquired lalu gagal di jatuh tempo (M4)
  available → semua hard-prereq sudah pernah dibuktikan (atau tak punya prereq)
  locked    → ada hard-prereq yang belum pernah dibuktikan

Locking dinamis hanya mengikuti edge `hard` (§9 PRD); `soft` tidak mengunci.

Keputusan M4 (turunan dari PRD Q3): yang MEMBUKA kunci hilir adalah "pernah
dibuktikan" — yaitu `acquired`, `mastered`, **dan `lapsed`**. Node lapsed tidak
mengunci ulang hilirnya: buktinya pernah ada, yang meluruh cuma memorinya, dan satu
review buruk tak boleh merobohkan separuh peta di dashboard.
"""

from sqlmodel import Session, select

from app.models import Edge, Node, ScheduleItem, ScheduleStatus
from app.services.mastery import IN_SCHEDULE


def _items(session: Session) -> dict[str, ScheduleItem]:
    return {i.node_id: i for i in session.exec(select(ScheduleItem)).all()}


def _proven_ids(items: dict[str, ScheduleItem]) -> set[str]:
    """Node yang pernah dibuktikan lewat eksekusi → tidak lagi mengunci hilirnya."""
    return {nid for nid, item in items.items() if item.status in IN_SCHEDULE}


def _hard_prereqs(session: Session) -> dict[str, list[str]]:
    """node_id → daftar node_id prasyarat keras (from) yang mengunci `to`."""
    prereqs: dict[str, list[str]] = {}
    for e in session.exec(select(Edge).where(Edge.type == "hard")).all():
        prereqs.setdefault(e.to_node_id, []).append(e.from_node_id)
    return prereqs


def _status_for(
    node_id: str, items: dict[str, ScheduleItem], proven: set[str], prereqs: dict[str, list[str]]
) -> str:
    item = items.get(node_id)
    if item is not None and item.status in IN_SCHEDULE:
        return item.status
    if all(p in proven for p in prereqs.get(node_id, [])):
        return ScheduleStatus.available.value
    return ScheduleStatus.locked.value


def effective_status(session: Session, node_id: str) -> str:
    items = _items(session)
    return _status_for(node_id, items, _proven_ids(items), _hard_prereqs(session))


def all_statuses(session: Session) -> dict[str, str]:
    items = _items(session)
    proven = _proven_ids(items)
    prereqs = _hard_prereqs(session)
    return {
        node.id: _status_for(node.id, items, proven, prereqs)
        for node in session.exec(select(Node)).all()
    }


def hard_ancestors(session: Session, node_id: str) -> set[str]:
    """Seluruh prasyarat keras (transitif) sebuah node."""
    prereqs = _hard_prereqs(session)
    seen: set[str] = set()
    stack = list(prereqs.get(node_id, []))
    while stack:
        current = stack.pop()
        if current in seen:
            continue
        seen.add(current)
        stack.extend(prereqs.get(current, []))
    return seen


def hard_depth(session: Session) -> dict[str, int]:
    """Kedalaman node di DAG prasyarat keras (0 = tak punya prasyarat).

    Dipakai placement sebagai proksi kesulitan: makin dalam, makin banyak yang harus
    sudah dikuasai lebih dulu. Ini BUKAN graf visual — cuma pengurutan daftar (§8).
    """
    prereqs = _hard_prereqs(session)
    depth: dict[str, int] = {}

    def resolve(node_id: str, visiting: frozenset[str]) -> int:
        if node_id in depth:
            return depth[node_id]
        if node_id in visiting:  # siklus di data — jangan menggantung
            return 0
        parents = prereqs.get(node_id, [])
        value = 0 if not parents else 1 + max(resolve(p, visiting | {node_id}) for p in parents)
        depth[node_id] = value
        return value

    for node in session.exec(select(Node)).all():
        resolve(node.id, frozenset())
    return depth
