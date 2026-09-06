"""Join lajur Library -> Forge: "% direproduksi", bukan "% dibaca" (L5).

Ini PENJAGA, bukan fitur pelaporan. Brainstorm lajur Library menyebut bahayanya apa
adanya: bukan satu invariant jebol, melainkan Bryant menghabiskan waktunya di Library
yang nyaman sementara Forge yang tak nyaman terbengkalai. Begitu progres Library bisa
naik karena MEMBACA, seluruh lajur ini berubah jadi consumption comfort yang §8 tolak.

Tiga aturan yang membuat angkanya jujur — ketiganya diuji di
`backend/tests/test_library_progress.py`:

1. Yang menggerakkan angka HANYA eksekusi kode: attempt mode dingin
   (`kpi.REPRODUCE_MODES`), di-IMPORT bukan disalin. Dua definisi
   "reproduce-without-AI" akan menyimpang, dan yang longgar yang akan dipakai.
2. `status` frontmatter (`outline`/`captured` = status CATATAN, L0) tak pernah masuk
   cabang perhitungan mana pun. Mengisi seluruh catatan = angka identik.
3. Materi tanpa `node_ids` tetap masuk PENYEBUT — course tampil berlubang sampai
   node-nya tertempa DAN terbukti. Itu tampilan yang benar, bukan bug.

Modul ini READ-ONLY terhadap `library/`. Penulisnya `scripts/` (L1-L3) dan
`verify_library.py --link` (L4).
"""

from dataclasses import dataclass
from pathlib import Path

import yaml
from sqlmodel import Session, select

from app.config import LIBRARY_DIR
from app.models import Attempt, AttemptResult, Node, ScheduleStatus
from app.services.kpi import REPRODUCE_MODES
from app.services.progress import all_statuses

#: Materi yang bisa "direproduksi". `outline`/`roadmap` adalah berkas STRUKTURAL
#: (indeks & peta): memasukkannya ke penyebut menghukum course hanya karena ia punya
#: banyak modul, dan peta memang bukan unit yang direproduksi.
LEARNABLE_TYPES = ("note", "transcription")

#: Keadaan materi. Tiga, bukan satu angka — "belum ditempa" dan "sudah ditempa tapi
#: belum kamu buktikan" adalah dua utang yang berbeda dan butuh tindakan berbeda.
UNMAPPED = "unmapped"
MAPPED_UNPROVEN = "mapped_unproven"
REPRODUCED = "reproduced"


@dataclass
class MaterialProgress:
    rel_path: str  # relatif terhadap library/ (POSIX)
    title: str
    type: str
    note_status: str  # LABEL saja — tak pernah masuk hitungan (aturan 2)
    node_ids: list[str]
    missing_node_ids: list[str]
    state: str
    mastered: bool
    decayed: bool


@dataclass
class ModuleProgress:
    module: str
    title: str
    materials: list[MaterialProgress]


@dataclass
class CourseProgress:
    course: str
    title: str
    modules: list[ModuleProgress]
    total: int
    unmapped: int
    mapped_unproven: int
    reproduced: int
    mastered: int
    decayed: int
    reproduced_pct: float | None


@dataclass
class LibraryProgress:
    courses: list[CourseProgress]
    total: int
    reproduced: int
    reproduced_pct: float | None


@dataclass
class RawMaterial:
    rel_path: str
    course: str
    module: str
    fm: dict


# --------------------------------------------------------------------------- #
# Baca berkas (tanpa DB)
# --------------------------------------------------------------------------- #
def _frontmatter(text: str) -> dict | None:
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    try:
        fm = yaml.safe_load(parts[1])
    except yaml.YAMLError:
        return None
    return fm if isinstance(fm, dict) else None


def read_materials(library_dir: Path | None = None) -> list[RawMaterial]:
    """Frontmatter seluruh berkas `library/`. MURNI BACA — tak ada Session di sini.

    Berkas cacat DILEWATI: yang bertugas meneriakkannya `scripts/verify_library.py`
    (gerbang commit). Dashboard mati total gara-gara satu berkas setengah tersunting
    adalah kegagalan yang tak sepadan.
    """
    root = library_dir or LIBRARY_DIR
    out: list[RawMaterial] = []
    if not root.is_dir():
        return out
    for path in sorted(root.glob("**/*.md")):
        rel = path.relative_to(root)
        if len(rel.parts) < 2:  # README.md & apa pun di akar library/
            continue
        try:
            fm = _frontmatter(path.read_text(encoding="utf-8"))
        except OSError:
            continue
        if fm is None:
            continue
        out.append(
            RawMaterial(
                # POSIX, bukan str(rel): di Windows path berisi "\" dan pointer di
                # respons akan berubah bentuk tergantung OS penulisnya (kebocoran
                # yang sama sudah diperbaiki di `node_loader` pada M4).
                rel_path=rel.as_posix(),
                course=rel.parts[0],
                module=rel.parts[1] if len(rel.parts) > 2 else "",
                fm=fm,
            )
        )
    return out


# --------------------------------------------------------------------------- #
# Sisi Forge (DB)
# --------------------------------------------------------------------------- #
def _forge_state(session: Session) -> tuple[set[str], set[str], set[str], set[str]]:
    """(terbukti dingin, mastered, lapsed, node yang dikenal DB).

    "Terbukti" dihitung dari ATTEMPT, bukan dari status: status bisa berubah karena
    peluruhan jadwal, sedangkan bukti bahwa Bryant pernah memproduksinya tidak hilang
    (§7 2026-08-21 Q3).
    """
    known = {n.id for n in session.exec(select(Node)).all()}
    proven = {
        a.node_id
        for a in session.exec(
            select(Attempt).where(
                Attempt.mode.in_(REPRODUCE_MODES),  # type: ignore[attr-defined]
                Attempt.result == AttemptResult.passed.value,
            )
        ).all()
    }
    statuses = all_statuses(session)
    mastered = {nid for nid, s in statuses.items() if s == ScheduleStatus.mastered.value}
    lapsed = {nid for nid, s in statuses.items() if s == ScheduleStatus.lapsed.value}
    return proven, mastered, lapsed, known


# --------------------------------------------------------------------------- #
# Join
# --------------------------------------------------------------------------- #
def compute(session: Session, *, library_dir: Path | None = None) -> LibraryProgress:
    proven, mastered_ids, lapsed_ids, known = _forge_state(session)
    materials = read_materials(library_dir)

    # Judul course & modul diambil dari `_index.md`-nya (berkas struktural itu tak
    # ikut dihitung, tapi ia yang menyimpan namanya).
    titles: dict[tuple[str, str], str] = {}
    for raw in materials:
        if Path(raw.rel_path).name == "_index.md":
            titles[(raw.course, raw.module)] = str(raw.fm.get("title") or "")

    grouped: dict[str, dict[str, list[MaterialProgress]]] = {}
    for raw in materials:
        if str(raw.fm.get("type") or "") not in LEARNABLE_TYPES:
            continue  # _index (outline/roadmap) = struktural, bukan unit belajar
        node_ids = [str(x) for x in (raw.fm.get("node_ids") or [])]
        missing = [n for n in node_ids if n not in known]
        # Node menggantung tak ada di `proven`, jadi materinya otomatis BELUM terbukti —
        # tautan salah tak boleh tampak seperti kemajuan (KUNCI 9).
        reproduced = bool(node_ids) and all(n in proven for n in node_ids)
        state = REPRODUCED if reproduced else (UNMAPPED if not node_ids else MAPPED_UNPROVEN)
        grouped.setdefault(raw.course, {}).setdefault(raw.module, []).append(
            MaterialProgress(
                rel_path=raw.rel_path,
                title=str(raw.fm.get("title") or Path(raw.rel_path).stem),
                type=str(raw.fm.get("type") or ""),
                note_status=str(raw.fm.get("status") or ""),
                node_ids=node_ids,
                missing_node_ids=missing,
                state=state,
                mastered=bool(node_ids) and all(n in mastered_ids for n in node_ids),
                decayed=any(n in lapsed_ids for n in node_ids),
            )
        )

    courses: list[CourseProgress] = []
    for course in sorted(grouped):
        modules = [
            ModuleProgress(
                module=module,
                title=titles.get((course, module)) or module,
                materials=sorted(mats, key=lambda m: m.rel_path),
            )
            for module, mats in sorted(grouped[course].items())
        ]
        semua = [m for mod in modules for m in mod.materials]
        n = len(semua)
        rep = sum(1 for m in semua if m.state == REPRODUCED)
        courses.append(
            CourseProgress(
                course=course,
                title=titles.get((course, "")) or course,
                modules=modules,
                total=n,
                unmapped=sum(1 for m in semua if m.state == UNMAPPED),
                mapped_unproven=sum(1 for m in semua if m.state == MAPPED_UNPROVEN),
                reproduced=rep,
                mastered=sum(1 for m in semua if m.mastered),
                decayed=sum(1 for m in semua if m.decayed),
                reproduced_pct=(rep / n) if n else None,
            )
        )

    total = sum(c.total for c in courses)
    reproduced = sum(c.reproduced for c in courses)
    return LibraryProgress(
        courses=courses,
        total=total,
        reproduced=reproduced,
        reproduced_pct=(reproduced / total) if total else None,
    )
