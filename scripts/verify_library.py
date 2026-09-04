#!/usr/bin/env python3
"""Validator + capture lajur Library (L2 · note-refine).

Dua mode:
  (default)         validasi SEMUA library/**/*.md → gerbang commit.
                    exit 0 bersih / 1 ada pelanggaran.
  --capture <file>  validasi SATU file lalu flip status outline→captured BILA body
                    sudah berisi (bukan stub). exit 0 sukses / 1 ditolak.

Registry (sumber kebenaran untuk ⊆):
  - source ids ← data/sources.yaml  (source_refs ⊆ ini)
  - node ids   ← data/domains/*/nodes/*/node.yaml `id` (node_ids ⊆ ini)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[1]
_LIBRARY_ROOT = _REPO_ROOT / "library"
_SOURCES_YAML = _REPO_ROOT / "data" / "sources.yaml"

_REQUIRED_FM = {"title", "course", "module", "type", "source_refs",
                "node_ids", "status", "created"}
_VALID_TYPE = {"note", "transcription", "outline", "roadmap"}
_VALID_STATUS = {"outline", "captured"}
# Sentinel stub dari library_scaffold.material_md (L1). Kehadirannya = belum diisi.
_STUB_SENTINEL = "`status: outline` — kerangka"


# ---------- registry ----------

def load_source_ids() -> set[str]:
    data = yaml.safe_load(_SOURCES_YAML.read_text("utf-8"))
    return {s["id"] for s in (data or {}).get("sources", [])
            if isinstance(s, dict) and "id" in s}


def load_node_ids() -> set[str]:
    ids: set[str] = set()
    for p in _REPO_ROOT.glob("data/domains/*/nodes/*/node.yaml"):
        if p.parent.name == "_example":
            continue
        try:
            data = yaml.safe_load(p.read_text("utf-8"))
            nid = data.get("id") if isinstance(data, dict) else None
        except (yaml.YAMLError, OSError):
            nid = None
        ids.add(nid or p.parent.name)
    return ids


# ---------- parsing ----------

def split_frontmatter(text: str) -> tuple[dict | None, str]:
    """(mapping_frontmatter, body). Kembalikan (None, text) bila bentuk salah."""
    if not text.startswith("---"):
        return None, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None, text
    try:
        fm = yaml.safe_load(parts[1])
    except yaml.YAMLError:
        return None, text
    if not isinstance(fm, dict):
        return None, text
    return fm, parts[2]


def is_stub_body(body: str) -> bool:
    """True bila body belum berisi catatan (masih kerangka L1)."""
    if _STUB_SENTINEL in body:
        return True
    for raw in body.splitlines():
        line = raw.strip()
        if not line or len(line) < 3:
            continue
        if line.startswith(("#", ">", "Balik:", "Lanjut:", "Sumber:",
                            "- [[", "- *")):
            continue  # heading/blockquote/nav/bullet wikilink — bukan prosa
        return False   # ada baris prosa nyata → bukan stub
    return True


# ---------- validasi ----------

def _field_errors(fm: dict, path: Path, source_ids: set[str],
                  node_ids: set[str]) -> list[str]:
    errs: list[str] = []
    keys = set(fm)
    for miss in sorted(_REQUIRED_FM - keys):
        errs.append(f"field wajib hilang: {miss}")
    for extra in sorted(keys - _REQUIRED_FM):
        errs.append(f"field asing (format L0 beku): {extra}")

    if fm.get("type") not in _VALID_TYPE:
        errs.append(f"type tak sah: {fm.get('type')!r}")
    if fm.get("status") not in _VALID_STATUS:
        errs.append(f"status tak sah: {fm.get('status')!r}")
    for key in ("title", "course"):
        val = fm.get(key)
        if not (isinstance(val, str) and val.strip()):
            errs.append(f"{key} wajib string non-kosong")
    if not str(fm.get("created") or "").strip():
        errs.append("created wajib non-kosong")

    # course cocok folder course: library/<course>/...
    try:
        top = path.relative_to(_LIBRARY_ROOT).parts[0]
        if fm.get("course") != top:
            errs.append(f"course={fm.get('course')!r} != folder {top!r}")
    except ValueError:
        errs.append("file di luar library/")

    for key, registry, label in (("source_refs", source_ids, "sources.yaml"),
                                 ("node_ids", node_ids, "data/ nodes")):
        val = fm.get(key)
        if not isinstance(val, list):
            errs.append(f"{key} harus list")
            continue
        for item in val:
            if item not in registry:
                errs.append(f"{key}: {item!r} tak ada di {label}")
    return errs


def validate_file(path: Path, source_ids: set[str],
                  node_ids: set[str]) -> list[str]:
    text = path.read_text("utf-8")
    fm, body = split_frontmatter(text)
    if fm is None:
        return ["frontmatter tak terbaca (harus diawali blok --- … ---)"]
    errs = _field_errors(fm, path, source_ids, node_ids)
    if (fm.get("status") == "captured"
            and fm.get("type") in {"note", "transcription"}
            and is_stub_body(body)):
        errs.append("status=captured tapi body masih stub (belum ada catatan)")
    return errs


# ---------- capture (flip outline→captured) ----------

def capture(path: Path, source_ids: set[str], node_ids: set[str]) -> list[str]:
    """Flip status→captured bila valid & berisi. Kembalikan daftar alasan tolak
    ([] = sukses & file ditulis ulang)."""
    if not path.is_file():
        return ["file tak ditemukan"]
    text = path.read_text("utf-8")
    fm, body = split_frontmatter(text)
    if fm is None:
        return ["frontmatter tak terbaca"]
    errs = _field_errors(fm, path, source_ids, node_ids)
    if errs:
        return errs
    if fm.get("type") in {"note", "transcription"} and is_stub_body(body):
        return ["body masih stub — isi catatan dulu sebelum capture"]
    if fm.get("status") == "captured":
        return []  # sudah captured; idempoten, tak menulis ulang
    fm["status"] = "captured"
    dumped = yaml.safe_dump(fm, sort_keys=False, allow_unicode=True).strip()
    path.write_text(f"---\n{dumped}\n---{body}", encoding="utf-8")
    return []


# ---------- CLI ----------

def _iter_library_files() -> list[Path]:
    # hanya file di DALAM folder course (rel parts >= 2); lewati README & top-level.
    out = []
    for p in sorted(_LIBRARY_ROOT.glob("**/*.md")):
        rel = p.relative_to(_LIBRARY_ROOT)
        if len(rel.parts) >= 2:
            out.append(p)
    return out


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Validator + capture lajur Library (L2).")
    ap.add_argument("--capture", type=Path, metavar="FILE",
                    help="flip satu file outline→captured bila body berisi")
    args = ap.parse_args(argv)

    source_ids = load_source_ids()
    node_ids = load_node_ids()

    if args.capture is not None:
        path = args.capture.resolve()
        reasons = capture(path, source_ids, node_ids)
        try:
            rel = path.relative_to(_REPO_ROOT).as_posix()
        except ValueError:
            rel = str(path)
        if reasons:
            print(f"CAPTURE DITOLAK: {rel}", file=sys.stderr)
            for r in reasons:
                print(f"  - {r}", file=sys.stderr)
            return 1
        print(f"captured: {rel}")
        return 0

    problems = 0
    for path in _iter_library_files():
        errs = validate_file(path, source_ids, node_ids)
        if errs:
            problems += 1
            rel = path.relative_to(_REPO_ROOT).as_posix()
            print(f"✗ {rel}")
            for e in errs:
                print(f"    - {e}")
    if problems:
        print(f"\n{problems} file bermasalah.", file=sys.stderr)
        return 1
    print("library/ bersih — semua frontmatter valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
