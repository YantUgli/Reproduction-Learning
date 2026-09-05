#!/usr/bin/env python3
"""Scaffolder lajur Library (L1 · course-intake; `kind: roadmap` L3 · learn-intake).

Baca spec course (YAML) → pancarkan pohon `library/<slug>/` kosong-terstruktur
mengikuti format beku `library/README.md` (L0). CREATE-ONLY: tak pernah menimpa
file yang sudah ada, jadi catatan Bryant aman saat re-run.

Spec `kind: roadmap` (L3) menghasilkan PETA bersitasi, bukan kerangka kosong: tiap
materi wajib membawa `source_ref` + `quote` verbatim + `reproduce`. Kutipannya dicek
terhadap snapshot `data/sources/<id>.md` oleh `check_grounding()` SEBELUM satu berkas
pun ditulis — gerbang TULIS; kembarannya gerbang BACA di `verify_library.py`.

Pemakaian:
    python scripts/library_scaffold.py --spec <spec.yaml> [--dry-run]
Exit 0 = sukses (termasuk semua di-skip); 2 = spec tidak valid / grounding gagal.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from _console import force_utf8_stdio

_REPO_ROOT = Path(__file__).resolve().parents[1]
_LIBRARY_ROOT = _REPO_ROOT / "library"
_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_REQUIRED_FM = {"title", "course", "module", "type", "source_refs",
                "node_ids", "status", "created"}

# --- L3: gerbang grounding DIPINJAM dari backend, bukan ditulis ulang ------------
# Aturan kutipan verbatim sudah hidup di `app/services/grounding.py` (gate R3/M7).
# Dua implementasi atas gerbang yang SAMA akan menyimpang diam-diam — dan yang
# menyimpang adalah gerbang inti L3. Karena itu di-import, bukan disalin.
sys.path.insert(0, str(_REPO_ROOT / "backend"))
from app.services.grounding import MIN_QUOTE_CHARS, normalize  # noqa: E402

_SOURCES_YAML = _REPO_ROOT / "data" / "sources.yaml"
_SNAPSHOT_DIR = _REPO_ROOT / "data" / "sources"
_VALID_KIND = {"course", "roadmap"}
#: Satu kalimat "apa yang harus bisa kamu tulis ulang". Lebih panjang dari ini berarti
#: ia sudah menjelaskan, dan peta tidak menjelaskan (KUNCI 8).
_MAX_REPRODUCE_CHARS = 200


class SpecError(ValueError):
    """Spec course tidak valid — tak ada file yang ditulis."""


@dataclass
class Material:
    slug: str
    title: str
    source_ref: str = ""      # (L3) id di data/sources.yaml
    quote: str = ""           # (L3) kutipan verbatim dari snapshot sumber
    reproduce: str = ""       # (L3) satu kalimat tujuan reproduksi
    #: (L3) usulan node Forge — LABEL kebab-case, bukan node id (`n002_get_json_route`).
    #: Bentuk yang berbeda mencegahnya salah dibaca sebagai node yang sudah ada.
    candidate_node: str = ""


@dataclass
class Module:
    slug: str
    title: str
    materials: list[Material] = field(default_factory=list)


@dataclass
class Course:
    slug: str
    title: str
    source: str
    modules: list[Module]
    kind: str = "course"                               # (L3)
    goal: str = ""                                     # (L3)
    baseline: str = ""                                 # (L3)
    cut_list: list[str] = field(default_factory=list)  # (L3)


# ---------- parsing & validasi ----------

def _require(cond: bool, msg: str) -> None:
    if not cond:
        raise SpecError(msg)


def _valid_slug(s: object) -> bool:
    return isinstance(s, str) and bool(_SLUG_RE.match(s))


def _no_fence(text: str, where: str) -> None:
    _require("```" not in text, f"{where}: dilarang blok kode di peta (peta menunjuk "
                                "sumber, tidak mengajarkan)")


def parse_spec(raw: object) -> Course:
    _require(isinstance(raw, dict), "spec harus mapping YAML di level atas")
    c = raw.get("course")
    _require(isinstance(c, dict), "field `course` (mapping) wajib")
    slug, title = c.get("slug"), c.get("title")
    source = (c.get("source") or "")
    _require(_valid_slug(slug), f"course.slug harus kebab-case a-z0-9-: {slug!r}")
    _require(isinstance(title, str) and title.strip(), "course.title wajib non-kosong")
    _require(isinstance(source, str), "course.source harus teks")

    kind = c.get("kind", "course")
    _require(kind in _VALID_KIND, f"course.kind harus course|roadmap: {kind!r}")
    goal = str(c.get("goal") or "").strip()
    baseline = str(c.get("baseline") or "").strip()
    raw_cut = c.get("cut_list") or []
    _require(isinstance(raw_cut, list), "course.cut_list harus list")
    cut_list = [str(x).strip() for x in raw_cut if str(x).strip()]
    if kind == "roadmap":
        _require(bool(goal), "course.goal wajib diisi untuk kind: roadmap")
    for text, where in ((title, "course.title"), (source, "course.source"),
                        (goal, "course.goal"), (baseline, "course.baseline")):
        _no_fence(text, where)

    raw_mods = raw.get("modules")
    _require(isinstance(raw_mods, list) and raw_mods,
             "field `modules` (list non-kosong) wajib")
    modules: list[Module] = []
    seen_m: set[str] = set()
    for i, m in enumerate(raw_mods):
        _require(isinstance(m, dict), f"modules[{i}] harus mapping")
        ms, mt = m.get("slug"), m.get("title")
        _require(_valid_slug(ms), f"modules[{i}].slug tidak valid: {ms!r}")
        _require(ms not in seen_m, f"slug modul duplikat: {ms!r}")
        seen_m.add(ms)
        _require(isinstance(mt, str) and mt.strip(), f"modules[{i}].title wajib")
        mats: list[Material] = []
        seen_a: set[str] = set()
        for j, a in enumerate(m.get("materials") or []):
            _require(isinstance(a, dict), f"modules[{i}].materials[{j}] harus mapping")
            asg, att = a.get("slug"), a.get("title")
            _require(_valid_slug(asg), f"materi slug tidak valid: {asg!r}")
            _require(asg not in seen_a, f"slug materi duplikat di {ms}: {asg!r}")
            seen_a.add(asg)
            _require(isinstance(att, str) and att.strip(), "material.title wajib")
            src_ref = str(a.get("source_ref") or "").strip()
            quote = str(a.get("quote") or "").strip()
            reproduce = str(a.get("reproduce") or "").strip()
            cand = str(a.get("candidate_node") or "").strip()
            if kind == "roadmap":
                _require(bool(src_ref), f"{asg}: source_ref wajib untuk kind: roadmap")
                _require("\n" not in quote, f"{asg}: quote harus SATU baris")
                _require(len(normalize(quote)) >= MIN_QUOTE_CHARS,
                         f"{asg}: quote minimal {MIN_QUOTE_CHARS} karakter — potongan "
                         "sependek itu cocok secara kebetulan")
                _require(bool(reproduce), f"{asg}: reproduce wajib (satu kalimat)")
                _require(len(reproduce) <= _MAX_REPRODUCE_CHARS,
                         f"{asg}: reproduce > {_MAX_REPRODUCE_CHARS} karakter — itu "
                         "penjelasan, bukan tujuan reproduksi")
            _require(not cand or _valid_slug(cand),
                     f"{asg}: candidate_node harus kebab-case: {cand!r}")
            _no_fence(quote, f"{asg}.quote")
            _no_fence(reproduce, f"{asg}.reproduce")
            mats.append(Material(asg, att.strip(), src_ref, quote, reproduce, cand))
        modules.append(Module(ms, mt.strip(), mats))
    return Course(slug, title.strip(), source.strip(), modules,
                  kind, goal, baseline, cut_list)


# ---------- gerbang TULIS (L3) ----------

def load_source_ids() -> set[str]:
    data = yaml.safe_load(_SOURCES_YAML.read_text("utf-8")) or {}
    return {s["id"] for s in data.get("sources", [])
            if isinstance(s, dict) and "id" in s}


def check_grounding(course: Course, *, snapshot_dir: Path | None = None) -> list[str]:
    """Gerbang TULIS L3: tiap kutipan wajib benar-benar ADA di snapshot sumbernya.

    Dijalankan SEBELUM satu berkas pun ditulis, jadi peta cacat tak pernah lahir.
    Yang dibuktikan: kutipannya nyata. Yang TIDAK dibuktikan: bahwa kutipan itu
    menopang entri petanya — itu penalaran, dan tak ada mesin di sini yang melakukannya.
    """
    if course.kind != "roadmap":
        return []
    snap_dir = snapshot_dir or _SNAPSHOT_DIR
    known = load_source_ids()
    cache: dict[str, str | None] = {}
    problems: list[str] = []
    for mod in course.modules:
        for mat in mod.materials:
            sid = mat.source_ref
            where = f"{mod.slug}/{mat.slug}"
            if sid not in known:
                problems.append(f"{where}: source_ref {sid!r} tak ada di sources.yaml")
                continue
            if sid not in cache:
                p = snap_dir / f"{sid}.md"
                cache[sid] = p.read_text("utf-8") if p.is_file() else None
            snap = cache[sid]
            if snap is None:
                problems.append(f"{where}: {sid} belum di-snapshot — jalankan "
                                f"scripts/fetch_source.py --id {sid}")
            elif normalize(mat.quote) not in normalize(snap):
                problems.append(f"{where}: kutipan TIDAK ada di snapshot {sid}: "
                                f"{mat.quote[:60]!r}")
    return problems


# ---------- penomoran modul ----------

def resolve_module_numbers(course_dir: Path, modules: list[Module]) -> dict[str, str]:
    existing: dict[str, int] = {}
    max_nn = 0
    if course_dir.exists():
        for child in course_dir.iterdir():
            mobj = re.match(r"^(\d{2})-(.+)$", child.name) if child.is_dir() else None
            if mobj:
                nn = int(mobj.group(1))
                existing[mobj.group(2)] = nn
                max_nn = max(max_nn, nn)
    out: dict[str, str] = {}
    for mod in modules:
        if mod.slug in existing:
            nn = existing[mod.slug]
        else:
            max_nn += 1
            nn = max_nn
        out[mod.slug] = f"{nn:02d}"
    return out


# ---------- template konten ----------

def _frontmatter(**fields: object) -> str:
    assert _REQUIRED_FM <= set(fields), "frontmatter kehilangan field wajib"
    body = yaml.safe_dump(fields, sort_keys=False, allow_unicode=True).strip()
    return f"---\n{body}\n---\n"


def course_index_md(course: Course, nn: dict[str, str], created: str) -> str:
    fm = _frontmatter(title=course.title, course=course.slug, module="",
                      type="outline", source_refs=[], node_ids=[],
                      status="captured", created=created)
    src = course.source or "(isi provenance sumber course)"
    lines = [f"- [[{nn[m.slug]}-{m.slug}/_index|{nn[m.slug]} · {m.title}]]"
             for m in course.modules]
    return (f"{fm}\n# {course.title}\n\n"
            f"Sumber: {src}\n\n"
            f"## Modul\n" + "\n".join(lines) + "\n")


def module_index_md(course: Course, mod: Module, nn: dict[str, str],
                    prev: Module | None, nxt: Module | None, created: str) -> str:
    my = nn[mod.slug]
    fm = _frontmatter(title=mod.title, course=course.slug, module=f"{my}-{mod.slug}",
                      type="outline", source_refs=[], node_ids=[],
                      status="captured", created=created)
    if mod.materials:
        mats = "\n".join(f"- [[{a.slug}|{a.title}]] · *stub, isi via note-refine*"
                         for a in mod.materials)
    else:
        mats = "- *(materi belum didaftarkan — tambah via note-refine / re-run intake)*"
    nav = []
    if prev:
        nav.append(f"Balik: [[../{nn[prev.slug]}-{prev.slug}/_index|"
                   f"{nn[prev.slug]} · {prev.title}]]")
    if nxt:
        nav.append(f"Lanjut: [[../{nn[nxt.slug]}-{nxt.slug}/_index|"
                   f"{nn[nxt.slug]} · {nxt.title}]]")
    nav_line = ("\n" + " · ".join(nav) + "\n") if nav else ""
    return f"{fm}\n# {my} · {mod.title}\n\n## Materi\n{mats}\n{nav_line}"


def course_index_roadmap_md(course: Course, nn: dict[str, str], created: str) -> str:
    refs = sorted({m.source_ref for mod in course.modules
                   for m in mod.materials if m.source_ref})
    fm = _frontmatter(title=course.title, course=course.slug, module="",
                      type="roadmap", source_refs=refs, node_ids=[],
                      status="captured", created=created)
    mods = "\n".join(f"- [[{nn[m.slug]}-{m.slug}/_index|{nn[m.slug]} · {m.title}]]"
                     for m in course.modules)
    head = [f"{fm}\n# {course.title}\n", f"**Tujuan:** {course.goal}\n"]
    if course.baseline:
        head.append(f"**Baseline (lantai awal, BUKAN mastery):** {course.baseline} — "
                    "lantai sungguhan ditentukan `/placement`, bukan berkas ini.\n")
    if course.cut_list:
        head.append("**Sengaja TIDAK dipelajari dulu:** "
                    + " · ".join(course.cut_list) + "\n")
    tail = ("\n> Peta ini menunjuk sumber asli; penjelasan tidak ditulis di sini.\n"
            "> Materi just-in-time muncul di Forge sesudah attempt gagal (gerbang 403).\n")
    return "\n".join(head) + f"\n## Modul\n{mods}\n" + tail


def module_index_roadmap_md(course: Course, mod: Module, nn: dict[str, str],
                            prev: Module | None, nxt: Module | None,
                            created: str) -> str:
    my = nn[mod.slug]
    refs = sorted({m.source_ref for m in mod.materials if m.source_ref})
    fm = _frontmatter(title=mod.title, course=course.slug,
                      module=f"{my}-{mod.slug}", type="roadmap", source_refs=refs,
                      node_ids=[], status="captured", created=created)
    entries = []
    for mat in mod.materials:
        # Bentuk baris kutipan `> "…"` itu KONTRAK, bukan gaya: verify_library.py
        # mengenali kutipan justru dari bentuk ini. Mengubahnya = kutipan lolos
        # tanpa diperiksa.
        block = [f"### [[{mat.slug}|{mat.title}]]",
                 f"**Reproduksi:** {mat.reproduce}",
                 f"**Sumber:** `{mat.source_ref}`",
                 f'> "{mat.quote}"']
        if mat.candidate_node:
            block.append(f"**Kandidat node:** `{mat.candidate_node}` — "
                         "belum ditempa (L4).")
        entries.append("\n".join(block))
    body = ("\n\n".join(entries) if entries
            else "*(peta modul kosong — tambahkan materi di spec)*")
    nav = []
    if prev:
        nav.append(f"Balik: [[../{nn[prev.slug]}-{prev.slug}/_index|"
                   f"{nn[prev.slug]} · {prev.title}]]")
    if nxt:
        nav.append(f"Lanjut: [[../{nn[nxt.slug]}-{nxt.slug}/_index|"
                   f"{nn[nxt.slug]} · {nxt.title}]]")
    nav_line = ("\n" + " · ".join(nav) + "\n") if nav else ""
    return f"{fm}\n# {my} · {mod.title}\n\n## Peta materi\n\n{body}\n{nav_line}"


def material_md(course: Course, mod: Module, nn: dict[str, str],
                mat: Material, created: str) -> str:
    """Stub materi. Untuk kind: roadmap ia membawa POINTER (tujuan reproduksi + id
    sumber) tapi TAK PERNAH kutipan: kutipan hidup di file peta yang diverifikasi.
    Sentinel stub dipertahankan supaya `--capture` (L2) tetap menolak flip status
    sampai Bryant benar-benar menulis catatannya.
    """
    fm = _frontmatter(title=mat.title, course=course.slug,
                      module=f"{nn[mod.slug]}-{mod.slug}", type="note",
                      source_refs=[mat.source_ref] if mat.source_ref else [],
                      node_ids=[], status="outline", created=created)
    extra = ""
    if mat.reproduce:
        extra += f"**Yang harus bisa kamu reproduksi:** {mat.reproduce}\n"
    if mat.source_ref:
        extra += f"**Baca sumber aslinya:** `{mat.source_ref}`\n"
    if extra:
        extra += "\n"
    return (f"{fm}\n# {mat.title}\n\n"
            "> `status: outline` — kerangka. Isi lewat note-refine (L2).\n\n"
            f"{extra}Balik: [[_index|{mod.title}]]\n")


# ---------- tulis (create-only) ----------

def write_if_absent(path: Path, content: str, dry_run: bool) -> bool:
    """True = dibuat; False = di-skip karena sudah ada. Tak pernah menimpa."""
    if path.exists():
        return False
    if not dry_run:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return True


def scaffold(course: Course, created: str,
             dry_run: bool = False) -> tuple[list[str], list[str]]:
    made: list[str] = []
    skipped: list[str] = []
    course_dir = _LIBRARY_ROOT / course.slug
    nn = resolve_module_numbers(course_dir, course.modules)

    # Pilih templat SEKALI di sini — bukan `if` per berkas.
    course_tpl = (course_index_roadmap_md if course.kind == "roadmap"
                  else course_index_md)
    module_tpl = (module_index_roadmap_md if course.kind == "roadmap"
                  else module_index_md)

    def emit(path: Path, content: str) -> None:
        rel = path.relative_to(_REPO_ROOT).as_posix()
        (made if write_if_absent(path, content, dry_run) else skipped).append(rel)

    emit(course_dir / "_index.md", course_tpl(course, nn, created))
    for idx, mod in enumerate(course.modules):
        mod_dir = course_dir / f"{nn[mod.slug]}-{mod.slug}"
        prev = course.modules[idx - 1] if idx > 0 else None
        nxt = course.modules[idx + 1] if idx < len(course.modules) - 1 else None
        emit(mod_dir / "_index.md", module_tpl(course, mod, nn, prev, nxt, created))
        for mat in mod.materials:
            emit(mod_dir / f"{mat.slug}.md", material_md(course, mod, nn, mat, created))
    return made, skipped


# ---------- CLI ----------

def main(argv: list[str]) -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="Scaffolder lajur Library (L1).")
    ap.add_argument("--spec", required=True, type=Path, help="path spec.yaml")
    ap.add_argument("--dry-run", action="store_true", help="laporkan tanpa menulis")
    args = ap.parse_args(argv)

    try:
        raw = yaml.safe_load(args.spec.read_text(encoding="utf-8"))
        course = parse_spec(raw)
    except (SpecError, yaml.YAMLError, OSError) as exc:
        print(f"SPEC TIDAK VALID: {exc}", file=sys.stderr)
        return 2

    problems = check_grounding(course)
    if problems:
        print("GROUNDING GAGAL — tak ada berkas yang ditulis:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 2

    created = _dt.datetime.now(tz=_dt.timezone.utc).date().isoformat()
    made, skipped = scaffold(course, created, dry_run=args.dry_run)

    tag = "(dry-run) " if args.dry_run else ""
    print(f"{tag}dibuat: {len(made)} · skip: {len(skipped)} (sudah ada)")
    for p in made:
        print(f"  + {p}")
    for p in skipped:
        print(f"  = {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
