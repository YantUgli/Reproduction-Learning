#!/usr/bin/env python3
"""Snapshot sumber otoritatif (L3 · grounding).

Menulis `data/sources/<id>.md` dari `url_or_locator` di `data/sources.yaml`. Snapshot
inilah bahan pembanding gerbang kutipan verbatim (`backend/app/services/grounding.py`)
yang dipakai gate R3 (M7) dan peta Library (L3).

ATURAN PALING PENTING: isi snapshot TIDAK PERNAH diketik manusia/AI dari ingatan. Ia
hasil unduhan script ini (`provenance: fetch`) atau salinan berkas yang Bryant sediakan
(`provenance: manual`). Kalau AI boleh mengarang snapshot, gerbang "kutipan ⊆ snapshot"
jadi melingkar: karang sumbernya, karang kutipannya, lolos.

Pemakaian:
    python scripts/fetch_source.py --id fastapi_docs_first_steps
    python scripts/fetch_source.py --all
    python scripts/fetch_source.py --id buku_bab3 --from-file bab3.txt
    python scripts/fetch_source.py --id … --force

Exit 0 sukses/skip · 1 gagal unduh atau hasil tak layak · 2 argumen/registry tidak valid.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import re
import sys
import urllib.error
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

import yaml
from _console import force_utf8_stdio

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SOURCES_YAML = _REPO_ROOT / "data" / "sources.yaml"
_SNAPSHOT_DIR = _REPO_ROOT / "data" / "sources"

_UA = "Mozilla/5.0 (compatible; ReproductionLearningEngine/1.0)"
_TIMEOUT_SECONDS = 20

#: Snapshot sependek ini hampir pasti bukan halamannya (dinding JS, halaman error,
#: layar consent). Menyimpannya justru berbahaya: ia menjadi "sumber" yang tak memuat
#: apa pun, sehingga SETIAP kutipan atasnya gagal — dan gagalnya membingungkan.
_MIN_SNAPSHOT_CHARS = 500

_SKIP_TAGS = {"script", "style", "noscript", "svg", "head", "template"}
_BLOCK_TAGS = {"p", "div", "section", "article", "br", "li", "ul", "ol", "tr", "table",
               "h1", "h2", "h3", "h4", "h5", "h6", "pre", "blockquote", "header",
               "footer", "nav", "aside", "main"}


class _HtmlToText(HTMLParser):
    """Pengupas tag seadanya — cukup untuk pencocokan substring, bukan renderer.

    Yang dikejar bukan tampilan cantik melainkan teks yang STABIL untuk dicocokkan.
    `convert_charrefs=True` sudah menerjemahkan entity; JANGAN `html.unescape()` lagi
    sesudahnya — halaman dokumentasi penuh contoh kode, dan unescape ganda mengubahnya.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._chunks: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag in _SKIP_TAGS:
            self._skip_depth += 1
        elif tag in _BLOCK_TAGS:
            self._chunks.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in _SKIP_TAGS:
            self._skip_depth = max(0, self._skip_depth - 1)
        elif tag in _BLOCK_TAGS:
            self._chunks.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth == 0:
            self._chunks.append(data)

    def text(self) -> str:
        return "".join(self._chunks)


def html_to_text(raw: str) -> str:
    parser = _HtmlToText()
    parser.feed(raw)
    parser.close()
    text = re.sub(r"[ \t\u00a0]+", " ", parser.text())  # spasi, tab, nbsp
    text = "\n".join(line.strip() for line in text.splitlines())
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def fetch_url(url: str) -> str:
    """Teks polos satu URL. Melempar urllib.error.* / OSError bila gagal."""
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    with urllib.request.urlopen(req, timeout=_TIMEOUT_SECONDS) as resp:
        ctype = (resp.headers.get_content_type() or "").lower()
        charset = resp.headers.get_content_charset() or "utf-8"
        raw = resp.read().decode(charset, errors="replace")
    return html_to_text(raw) if "html" in ctype else raw.strip()


def load_registry() -> dict[str, dict]:
    data = yaml.safe_load(_SOURCES_YAML.read_text("utf-8")) or {}
    return {s["id"]: s for s in data.get("sources", [])
            if isinstance(s, dict) and "id" in s}


def snapshot_text(entry: dict, body: str, provenance: str, fetched_at: str) -> str:
    fm = {"source_ref_id": entry["id"],
          "url_or_locator": entry.get("url_or_locator", ""),
          "provenance": provenance,
          "fetched_at": fetched_at,
          "char_count": len(body)}
    dumped = yaml.safe_dump(fm, sort_keys=False, allow_unicode=True).strip()
    return f"---\n{dumped}\n---\n\n{body}\n"


def snapshot_one(sid: str, entry: dict, args: argparse.Namespace,
                 fetched_at: str) -> tuple[str, str]:
    """(status, pesan) dengan status ∈ {created, skipped, failed}. Tak melempar."""
    path = _SNAPSHOT_DIR / f"{sid}.md"
    if path.exists() and not args.force:
        return "skipped", "sudah ada (pakai --force untuk memperbarui)"

    if args.from_file:
        try:
            body = args.from_file.read_text("utf-8").strip()
        except OSError as exc:
            return "failed", f"gagal membaca --from-file: {exc}"
        provenance = "manual"
    else:
        locator = str(entry.get("url_or_locator", ""))
        if not locator.startswith(("http://", "https://")):
            return "failed", (f"locator bukan URL ({locator!r}) — sumber seperti ini "
                              "harus disalin MANUSIA lewat --from-file")
        try:
            body = fetch_url(locator)
        except (urllib.error.URLError, OSError, ValueError) as exc:
            return "failed", f"gagal mengunduh {locator}: {exc}"
        provenance = "fetch"

    if len(body) < _MIN_SNAPSHOT_CHARS:
        return "failed", (f"hasil cuma {len(body)} karakter (< {_MIN_SNAPSHOT_CHARS}) — "
                          "halaman mungkin butuh JavaScript; salin manual via --from-file")

    if not args.dry_run:
        _SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
        path.write_text(snapshot_text(entry, body, provenance, fetched_at),
                        encoding="utf-8")
    return "created", f"{len(body)} karakter · provenance={provenance}"


def resolve_targets(args: argparse.Namespace, registry: dict[str, dict]) -> list[str]:
    if not args.all:
        return [args.id]
    return [sid for sid, e in registry.items()
            if str(e.get("url_or_locator", "")).startswith(("http://", "https://"))]


def main(argv: list[str]) -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="Snapshot sumber otoritatif (L3).")
    grp = ap.add_mutually_exclusive_group(required=True)
    grp.add_argument("--id", help="id SourceRef di data/sources.yaml")
    grp.add_argument("--all", action="store_true",
                     help="semua sumber ber-URL di registry")
    ap.add_argument("--from-file", type=Path,
                    help="ambil teks dari berkas (untuk sumber non-URL)")
    ap.add_argument("--force", action="store_true", help="timpa snapshot yang ada")
    ap.add_argument("--dry-run", action="store_true", help="laporkan tanpa menulis")
    args = ap.parse_args(argv)

    if args.from_file and args.all:
        print("--from-file hanya untuk satu --id", file=sys.stderr)
        return 2
    try:
        registry = load_registry()
    except (OSError, yaml.YAMLError) as exc:
        print(f"REGISTRY TIDAK TERBACA: {exc}", file=sys.stderr)
        return 2
    if args.id and args.id not in registry:
        print(f"id {args.id!r} tak ada di data/sources.yaml — daftarkan dulu di sana",
              file=sys.stderr)
        return 2

    fetched_at = _dt.datetime.now(tz=_dt.UTC).isoformat(timespec="seconds")
    targets = resolve_targets(args, registry)
    failed = 0
    tag = "(dry-run) " if args.dry_run else ""
    print(f"{tag}snapshot: {len(targets)} sumber")
    for sid in targets:
        status, msg = snapshot_one(sid, registry[sid], args, fetched_at)
        marker = {"created": "+", "skipped": "=", "failed": "x"}[status]
        print(f"  {marker} {sid}: {msg}")
        if status == "failed":
            failed += 1
    if failed:
        print(f"\n{failed} sumber gagal di-snapshot.", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
