#!/usr/bin/env python3
"""Scaffolder lajur Library (L1 · course-intake).

Baca spec course (YAML) → pancarkan pohon `library/<slug>/` kosong-terstruktur
mengikuti format beku `library/README.md` (L0). CREATE-ONLY: tak pernah menimpa
file yang sudah ada, jadi catatan Bryant aman saat re-run.

Pemakaian:
    python scripts/library_scaffold.py --spec <spec.yaml> [--dry-run]
Exit 0 = sukses (termasuk semua di-skip); 2 = spec tidak valid.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[1]
_LIBRARY_ROOT = _REPO_ROOT / "library"
_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_REQUIRED_FM = {"title", "course", "module", "type", "source_refs",
                "node_ids", "status", "created"}


class SpecError(ValueError):
    """Spec course tidak valid — tak ada file yang ditulis."""


@dataclass
class Material:
    slug: str
    title: str


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


# ---------- parsing & validasi ----------

def _require(cond: bool, msg: str) -> None:
    if not cond:
        raise SpecError(msg)


def _valid_slug(s: object) -> bool:
    return isinstance(s, str) and bool(_SLUG_RE.match(s))


def parse_spec(raw: object) -> Course:
    _require(isinstance(raw, dict), "spec harus mapping YAML di level atas")
    c = raw.get("course")
    _require(isinstance(c, dict), "field `course` (mapping) wajib")
    slug, title = c.get("slug"), c.get("title")
    source = (c.get("source") or "")
    _require(_valid_slug(slug), f"course.slug harus kebab-case a-z0-9-: {slug!r}")
    _require(isinstance(title, str) and title.strip(), "course.title wajib non-kosong")
    _require(isinstance(source, str), "course.source harus teks")

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
            mats.append(Material(asg, att.strip()))
        modules.append(Module(ms, mt.strip(), mats))
    return Course(slug, title.strip(), source.strip(), modules)


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


def material_md(course: Course, mod: Module, nn: dict[str, str],
                mat: Material, created: str) -> str:
    fm = _frontmatter(title=mat.title, course=course.slug,
                      module=f"{nn[mod.slug]}-{mod.slug}", type="note",
                      source_refs=[], node_ids=[], status="outline", created=created)
    return (f"{fm}\n# {mat.title}\n\n"
            "> `status: outline` — kerangka. Isi lewat note-refine (L2).\n\n"
            f"Balik: [[_index|{mod.title}]]\n")


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

    def emit(path: Path, content: str) -> None:
        rel = path.relative_to(_REPO_ROOT).as_posix()
        (made if write_if_absent(path, content, dry_run) else skipped).append(rel)

    emit(course_dir / "_index.md", course_index_md(course, nn, created))
    for idx, mod in enumerate(course.modules):
        mod_dir = course_dir / f"{nn[mod.slug]}-{mod.slug}"
        prev = course.modules[idx - 1] if idx > 0 else None
        nxt = course.modules[idx + 1] if idx < len(course.modules) - 1 else None
        emit(mod_dir / "_index.md", module_index_md(course, mod, nn, prev, nxt, created))
        for mat in mod.materials:
            emit(mod_dir / f"{mat.slug}.md", material_md(course, mod, nn, mat, created))
    return made, skipped


# ---------- CLI ----------

def main(argv: list[str]) -> int:
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
