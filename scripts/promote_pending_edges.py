#!/usr/bin/env python3
"""Veto & promosi manual antrian `edges.pending.yaml` (Amandemen C / Langkah 2).

Rancangan lengkap: `docs/design-async-review-mechanism.md` §4-§5 +
`docs/execution-plan-async-review.md` Langkah 2. Ringkasnya: usulan edge `hard` dari L4
menunggu di `data/domains/<domain>/edges.pending.yaml` selama 7 hari kalender
(`PENDING_REVIEW_DAYS`). Isyah bisa memveto kapan saja; bila tak diveto sampai matang,
script ini (dan HANYA script ini — bukan cron/scheduler) yang boleh mempromosikannya
jadi `hard` sungguhan di `edges.yaml`.

Dua mode:
  (default)             promosikan semua usulan `matang` (7 hari, tak diveto) di SEMUA
                         domain → `edges.yaml` sebagai `type: hard`, hapus dari pending.
  --dry-run              laporkan apa yang AKAN dipromosikan, tanpa menulis apa pun.
  --veto <edge_id>       tandai satu usulan sebagai diveto (`vetoed_at`+`veto_reason`).
                         TAK menghapus entri — jejak keputusan sengaja tinggal. Veto ulang
                         MENIMPA vetoed_at/veto_reason lama (selalu berhasil, idempoten).
  --reason "..."         alasan veto (dipakai dengan --veto).

`edge_id` = `<from>__<to>` (lihat `app.services.pending_edges.edge_id`).

Penulisan `edges.yaml` memakai `app.services.edge_writer.append_edge`; penulisan
`edges.pending.yaml` memakai `edge_writer.write_pending` — keduanya modul BERSAMA dengan
backend supaya tak ada dua penulis/serializer yang menyimpang diam-diam. `edges.yaml`
di-append-teks (komentar kurasi Isyah selamat); `edges.pending.yaml` ditulis ulang penuh
(murni state mesin, tak ada komentar untuk dijaga).

Kedua berkas di-backup sebelum ditulis; kegagalan apa pun (reparse `edges.yaml` gagal,
dll.) mengembalikan KEDUANYA byte-identik dengan semula (pola rollback yang sama dengan
`review_queue._promote_node_genesis`).
"""
from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path

from _console import force_utf8_stdio

_REPO_ROOT = Path(__file__).resolve().parents[1]
_DOMAINS_DIR = _REPO_ROOT / "data" / "domains"

# Aturan pending (edge_id, state, PendingEdge) DIPINJAM dari backend — satu sumber
# kebenaran, sama seperti verify_library.py meminjam grounding.py dari backend.
sys.path.insert(0, str(_REPO_ROOT / "backend"))
from app.services.edge_writer import append_edge, write_pending
from app.services.pending_edges import (
    STATE_MATANG,
    edge_id,
    load_pending,
    state,
)


def _domain_dirs() -> list[Path]:
    if not _DOMAINS_DIR.is_dir():
        return []
    return sorted(p for p in _DOMAINS_DIR.iterdir() if p.is_dir())


def _pending_path(domain_dir: Path) -> Path:
    return domain_dir / "edges.pending.yaml"


def _edges_path(domain_dir: Path) -> Path:
    return domain_dir / "edges.yaml"


# --------------------------------------------------------------------------- #
# Veto
# --------------------------------------------------------------------------- #
def veto(edge_id_target: str, reason: str) -> str | None:
    """Tandai satu usulan sebagai diveto di domain mana pun ia berada.

    Kembalikan nama domain bila ditemukan, `None` bila tidak. Veto ulang MENIMPA
    `vetoed_at`/`veto_reason` — selalu berhasil, tak pernah menolak dengan pesan.
    """
    now = datetime.now(UTC)
    for domain_dir in _domain_dirs():
        path = _pending_path(domain_dir)
        entries = load_pending(path)
        matched = [e for e in entries if edge_id(e) == edge_id_target]
        if not matched:
            continue
        backup = path.read_text(encoding="utf-8")
        try:
            for e in matched:
                e.vetoed_at = now
                e.veto_reason = reason
            write_pending(path, entries)
        except Exception:
            path.write_text(backup, encoding="utf-8")
            raise
        return domain_dir.name
    return None


# --------------------------------------------------------------------------- #
# Promosi
# --------------------------------------------------------------------------- #
def promote_matured(*, dry_run: bool = False) -> list[dict]:
    """Promosikan semua usulan `matang` (di semua domain) jadi `hard` di `edges.yaml`.

    `dry_run=True`: hanya melaporkan, nol berkas tersentuh. Idempoten by construction:
    entri yang sudah dipromosikan hilang dari pending, jadi run berikutnya tak
    menemukannya lagi.
    """
    now = datetime.now(UTC)
    report: list[dict] = []
    for domain_dir in _domain_dirs():
        pending_path = _pending_path(domain_dir)
        entries = load_pending(pending_path)
        if not entries:
            continue

        matured = [e for e in entries if state(e, now=now) == STATE_MATANG]
        if not matured:
            continue
        matured_ids = {id(e) for e in matured}
        remaining = [e for e in entries if id(e) not in matured_ids]

        for e in matured:
            report.append(
                {
                    "domain": domain_dir.name,
                    "edge_id": edge_id(e),
                    "from": e.from_,
                    "to": e.to,
                    "job_id": e.job_id,
                    "library_file": e.library_file,
                }
            )
        if dry_run:
            continue

        edges_path = _edges_path(domain_dir)
        edges_backup = edges_path.read_text(encoding="utf-8") if edges_path.exists() else None
        pending_backup = pending_path.read_text(encoding="utf-8")
        try:
            for e in matured:
                append_edge(
                    edges_path,
                    from_id=e.from_,
                    to_id=e.to,
                    edge_type="hard",
                    source_ref_id=e.source_ref_id,
                    comment=(
                        f"Dipromosikan otomatis (7 hari tanpa veto) — job {e.job_id}, "
                        f"peta: {e.library_file}"
                    ),
                    note=e.note or "Dipromosikan dari antrian pending — matang tanpa veto.",
                )
            write_pending(pending_path, remaining)
        except Exception:
            if edges_backup is None:
                edges_path.unlink(missing_ok=True)
            else:
                edges_path.write_text(edges_backup, encoding="utf-8")
            pending_path.write_text(pending_backup, encoding="utf-8")
            raise
    return report


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def main(argv: list[str]) -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(
        description="Veto & promosi manual antrian edges.pending.yaml (Amandemen C)."
    )
    ap.add_argument("--veto", metavar="EDGE_ID", help="tandai satu usulan sebagai diveto")
    ap.add_argument("--reason", default="", help="alasan veto (dipakai dengan --veto)")
    ap.add_argument(
        "--dry-run", action="store_true", help="laporkan yang akan dipromosikan, tanpa menulis"
    )
    args = ap.parse_args(argv)

    if args.veto:
        domain = veto(args.veto, args.reason.strip())
        if domain is None:
            print(f"tak ditemukan usulan pending dengan edge_id {args.veto!r}", file=sys.stderr)
            return 1
        alasan = f" — alasan: {args.reason.strip()}" if args.reason.strip() else ""
        print(f"diveto: {args.veto} (domain {domain}){alasan}")
        return 0

    report = promote_matured(dry_run=args.dry_run)
    if not report:
        print("tak ada usulan matang untuk dipromosikan.")
        return 0

    verb = "AKAN dipromosikan" if args.dry_run else "dipromosikan"
    for r in report:
        print(f"{verb}: {r['from']} -> {r['to']} (domain {r['domain']}, job {r['job_id']})")
    print(f"\n{len(report)} edge {verb.lower()} jadi hard.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
