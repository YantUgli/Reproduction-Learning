"""Penulis BERSAMA untuk satu entri baru di `edges.yaml` (APPEND TEKS + reparse-sebagai-
bukti).

Dua pemanggil harus memakai fungsi yang SAMA, bukan dua salinan yang bisa diam-diam
menyimpang (preseden: `grounding.py` di-import oleh R3/L3/L4, bukan disalin):

  - `app.claude.review_queue._append_soft_edge` — edge `soft` langsung saat node lahir
    (L4 node genesis).
  - `scripts/promote_pending_edges.py` — edge `hard` yang sudah matang 7 hari tanpa veto
    (Amandemen C / Langkah 2).

Kenapa APPEND TEKS, bukan `yaml.dump` ulang: `edges.yaml` penuh komentar kurasi manusia
("difinalkan Isyah 2026-08-22 …") dan dumper akan menghapusnya diam-diam. `load_edges`
dipanggil sesudah menulis sebagai BUKTI berkasnya masih parse — bukan formalitas; pemanggil
bertanggung jawab rollback bila ia melempar.
"""

from pathlib import Path

import yaml

from app.services.node_loader import load_edges
from app.services.pending_edges import PendingEdge, load_pending


def append_edge(
    edges_path: Path,
    *,
    from_id: str,
    to_id: str,
    edge_type: str,
    source_ref_id: str,
    comment: str,
    note: str,
) -> None:
    """Tambah satu blok edge di akhir `edges_path`, lalu buktikan berkasnya masih parse.

    `comment` jadi baris `# ...` di atas entri (jejak asal-usul, dibaca manusia saat
    `git diff`/`git blame`). `load_edges` dipanggil di sini, bukan di pemanggil: gagal
    parse harus SELALU melempar sebelum pemanggil menganggap tulisan ini sukses.
    """
    blok = (
        f"\n  # {comment}\n"
        f"  - from: {from_id}\n"
        f"    to: {to_id}\n"
        f"    type: {edge_type}\n"
        f"    source_ref_id: {source_ref_id}\n"
        f'    note: "{note}"\n'
    )
    if edges_path.exists():
        edges_path.write_text(
            edges_path.read_text(encoding="utf-8").rstrip("\n") + "\n" + blok, encoding="utf-8"
        )
    else:
        edges_path.write_text("edges:\n" + blok, encoding="utf-8")
    load_edges(edges_path)  # gagal parse → exception → rollback di pemanggil


# --------------------------------------------------------------------------- #
# Penulisan `edges.pending.yaml` (Amandemen C)
#
# Berbeda dari `edges.yaml`: berkas pending murni STATE MESIN — tak ada komentar kurasi
# manusia untuk dijaga — jadi ia ditulis ulang penuh (`yaml.dump`), bukan append-teks.
# Serializer-nya tinggal di sini (BUKAN di `pending_edges.py`, yang sengaja READ-only
# supaya jalur baca audit tak bisa menyentuh disk) dan dipakai bersama oleh dua penulis:
#   - `append_pending_edge` (backend, saat node lahir dengan usulan `hard`).
#   - `scripts/promote_pending_edges.py` (veto & promosi manual).
# Satu serializer = dua penulis tak bisa menyimpang diam-diam.
# --------------------------------------------------------------------------- #
class _IndentedPendingDumper(yaml.SafeDumper):
    """List di-indent di bawah key-nya — sama gaya dengan `edges.yaml`/`node.yaml`
    tulisan tangan (preseden: `review_queue._IndentedDumper`)."""

    def increase_indent(self, flow=False, indentless=False):
        return super().increase_indent(flow, False)


def pending_entry_to_dict(entry: PendingEdge) -> dict:
    """Satu entri pending → dict siap-`yaml.dump`. `from_` dipetakan balik ke key `from`;
    field opsional (note/veto) hanya ditulis bila terisi supaya berkasnya tetap ringkas."""
    out = {
        "from": entry.from_,
        "to": entry.to,
        "type": entry.type.value if hasattr(entry.type, "value") else str(entry.type),
        "source_ref_id": entry.source_ref_id,
        "library_file": entry.library_file,
        "job_id": entry.job_id,
        "queued_at": entry.queued_at.isoformat(),
    }
    if entry.note:
        out["note"] = entry.note
    if entry.vetoed_at is not None:
        out["vetoed_at"] = entry.vetoed_at.isoformat()
    if entry.veto_reason:
        out["veto_reason"] = entry.veto_reason
    return out


def write_pending(path: Path, entries: list[PendingEdge]) -> None:
    """Tulis ulang seluruh berkas pending satu domain, lalu reparse sebagai bukti.

    Daftar kosong → `edges: []` (bukan hapus berkas): absennya berkas berarti "belum
    pernah ada usulan", `edges: []` berarti "pernah ada, sudah tuntas semua" — dua
    peristiwa berbeda. Pemanggil bertanggung jawab rollback bila ini melempar.
    """
    data = {"edges": [pending_entry_to_dict(e) for e in entries]}
    path.write_text(
        yaml.dump(
            data, Dumper=_IndentedPendingDumper, allow_unicode=True, sort_keys=False, width=200
        ),
        encoding="utf-8",
    )
    load_pending(path)  # gagal parse → exception → rollback di pemanggil


def append_pending_edge(pending_path: Path, entry: PendingEdge) -> None:
    """Tambah SATU usulan ke `edges.pending.yaml` (baca entri lama → append → tulis ulang).

    Read-modify-write, bukan append-teks: berkas pending tak punya komentar untuk dijaga,
    dan menulis ulang penuh menjamin bentuknya selalu sah (tak ada risiko append cacat).
    """
    entries = load_pending(pending_path)
    entries.append(entry)
    write_pending(pending_path, entries)
