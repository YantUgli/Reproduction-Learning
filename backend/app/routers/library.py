"""Router lajur Library (L5) — "% direproduksi", bukan "% dibaca".

Router tipis di atas `services/library_progress.py`; definisi metriknya ada di sana
(pola yang sama dengan `stats.py` di atas `kpi.py`).

READ-ONLY: tak ada satu pun endpoint di sini yang menulis ke `library/`. Penulisnya
`scripts/` (L1-L3) dan `verify_library.py --link` (L4) — dan batas itu yang menjaga
lajur Library tetap bisa dipakai (Obsidian, git) tanpa backend menyala.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import Session

from app.db import get_session
from app.services import library_progress

router = APIRouter(prefix="/library", tags=["library"])


class MaterialOut(BaseModel):
    path: str  # relatif repo, mis. "library/fastapi-dasar/01-routing/get.md"
    title: str
    type: str
    #: Status CATATAN (outline/captured). Sengaja TIDAK bernama `status` supaya tak ada
    #: yang memperlakukannya sebagai status kemajuan — status reproduksi hanya datang
    #: dari eksekusi kode (§1.2), dan yang ini cuma label (§7 2026-09-04).
    note_status: str
    node_ids: list[str]
    missing_node_ids: list[str]
    state: str  # unmapped | mapped_unproven | reproduced
    mastered: bool
    decayed: bool


class ModuleOut(BaseModel):
    module: str
    title: str
    materials: list[MaterialOut]


class CourseOut(BaseModel):
    course: str
    title: str
    total: int
    unmapped: int
    mapped_unproven: int
    reproduced: int
    mastered: int
    decayed: int
    reproduced_pct: float | None
    modules: list[ModuleOut]


class LibraryProgressOut(BaseModel):
    total: int
    reproduced: int
    reproduced_pct: float | None
    courses: list[CourseOut]


@router.get("/progress", response_model=LibraryProgressOut)
def get_library_progress(session: Session = Depends(get_session)) -> LibraryProgressOut:
    data = library_progress.compute(session)
    return LibraryProgressOut(
        total=data.total,
        reproduced=data.reproduced,
        reproduced_pct=data.reproduced_pct,
        courses=[
            CourseOut(
                course=c.course,
                title=c.title,
                total=c.total,
                unmapped=c.unmapped,
                mapped_unproven=c.mapped_unproven,
                reproduced=c.reproduced,
                mastered=c.mastered,
                decayed=c.decayed,
                reproduced_pct=c.reproduced_pct,
                modules=[
                    ModuleOut(
                        module=m.module,
                        title=m.title,
                        materials=[
                            MaterialOut(
                                path=f"library/{mat.rel_path}",
                                title=mat.title,
                                type=mat.type,
                                note_status=mat.note_status,
                                node_ids=mat.node_ids,
                                missing_node_ids=mat.missing_node_ids,
                                state=mat.state,
                                mastered=mat.mastered,
                                decayed=mat.decayed,
                            )
                            for mat in m.materials
                        ],
                    )
                    for m in c.modules
                ],
            )
            for c in data.courses
        ],
    )
