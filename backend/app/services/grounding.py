"""Grounding materi R3 — kutipan VERBATIM, bukan sekadar ID sumber (M7 langkah 3).

Sampai M6, satu-satunya pemeriksaan atas sitasi adalah `source_ref_id` ADA di
`sources.yaml` (`contracts.check_citations_known`). Itu membuktikan sumbernya
terdaftar — **bukan** bahwa klaimnya ditopang sumber itu. Keputusan M5 (2026-08-22)
menyebut ini apa adanya dan menjadikan approve Isyah wajib justru karena celah ini:
"yang bisa diverifikasi mesin hanyalah bahwa `source_ref_id` ADA, bukan bahwa
klaimnya benar-benar ditopang sumber itu."

M7 mencabut approve itu, jadi celahnya harus ditutup lebih dulu — bukan diwariskan.
Caranya: teks sumber di-*snapshot* ke `data/sources/<id>.md` (di-commit, bisa
di-diff seperti kode), dan tiap klaim wajib membawa `quote` yang dicek sebagai
SUBSTRING dari snapshot itu.

Batas yang jujur harus disebut: ini membuktikan kutipannya nyata ada di sumber, dan
bahwa klaimnya berdampingan dengan kutipan itu. Ia TIDAK membuktikan kutipan itu
benar-benar menopang klaimnya — itu penalaran, dan tak ada mesin di sini yang
melakukannya. Yang kita naikkan adalah lantainya: mengarang sitasi jadi mustahil,
mengarang klaim jadi jauh lebih sulit.

Normalisasi hanya menyentuh SPASI (baris terlipat, indentasi, CRLF). Huruf besar-kecil
sengaja TIDAK dinormalisasi: sumber di sini banyak berisi kode, dan `Query` vs `query`
adalah dua hal berbeda.
"""

import re
from dataclasses import dataclass
from pathlib import Path

from app.config import DATA_DIR

#: Snapshot teks sumber otoritatif. Satu berkas per `SourceRef.id`.
SNAPSHOT_DIR = DATA_DIR / "sources"

#: Kutipan terlalu pendek cocok dengan apa saja — "the" ada di setiap dokumen.
#: Ambang ini yang membedakan kutipan dari kebetulan.
MIN_QUOTE_CHARS = 25

_WS = re.compile(r"\s+")


#: Jenis masalah. Bedanya menentukan nasib artifact, jadi ia bukan sekadar label:
#: `NO_SNAPSHOT` berarti "TAK BISA diverifikasi" (kita yang belum menyalin sumbernya),
#: sisanya berarti "SUDAH diverifikasi dan cacat". Yang pertama tak boleh dihukum sama
#: dengan yang kedua — tapi juga tak boleh lolos otomatis ke Bryant.
NO_SNAPSHOT = "no_snapshot"
NOT_FOUND = "not_found"
MISSING_QUOTE = "missing_quote"
TOO_SHORT = "too_short"


@dataclass
class QuoteProblem:
    source_ref_id: str
    reason: str
    kind: str = NOT_FOUND

    def __str__(self) -> str:
        return f"{self.source_ref_id}: {self.reason}"


def only_missing_snapshots(problems: list["QuoteProblem"]) -> bool:
    """Semua masalahnya cuma "sumbernya belum di-snapshot"?

    Kalau ya, artifact-nya belum tentu cacat — kita yang belum punya bahan
    pembanding. Pemanggil memakai ini untuk membedakan MENOLAK dari MENAHAN.
    """
    return bool(problems) and all(p.kind == NO_SNAPSHOT for p in problems)


def normalize(text: str) -> str:
    """Rapikan spasi saja — lipatan baris & indentasi tak boleh jadi alasan gagal."""
    return _WS.sub(" ", text).strip()


def snapshot_path(source_ref_id: str, *, snapshot_dir: Path | None = None) -> Path:
    return (snapshot_dir or SNAPSHOT_DIR) / f"{source_ref_id}.md"


def has_snapshot(source_ref_id: str, *, snapshot_dir: Path | None = None) -> bool:
    return snapshot_path(source_ref_id, snapshot_dir=snapshot_dir).exists()


def check_quotes(citations, *, snapshot_dir: Path | None = None) -> list[QuoteProblem]:
    """Tiap sitasi wajib membawa kutipan verbatim yang ADA di snapshot sumbernya.

    `citations` adalah objek apa pun dengan `.source_ref_id` dan `.quote` (di praktik:
    `contracts.Citation`). Mengembalikan daftar masalah — kosong berarti lolos.
    """
    problems: list[QuoteProblem] = []
    cache: dict[str, str | None] = {}

    for citation in citations:
        sid = citation.source_ref_id
        quote = (getattr(citation, "quote", "") or "").strip()

        if not quote:
            problems.append(
                QuoteProblem(
                    sid, "klaim tanpa `quote` — sitasinya tak bisa diverifikasi", MISSING_QUOTE
                )
            )
            continue
        if len(normalize(quote)) < MIN_QUOTE_CHARS:
            problems.append(
                QuoteProblem(
                    sid,
                    f"kutipan terlalu pendek ({len(normalize(quote))} < {MIN_QUOTE_CHARS} "
                    "karakter) — potongan sependek itu cocok secara kebetulan",
                    TOO_SHORT,
                )
            )
            continue

        if sid not in cache:
            path = snapshot_path(sid, snapshot_dir=snapshot_dir)
            cache[sid] = path.read_text(encoding="utf-8") if path.exists() else None

        snapshot = cache[sid]
        if snapshot is None:
            problems.append(
                QuoteProblem(
                    sid,
                    "belum ada snapshot teks sumbernya di "
                    f"`{snapshot_path(sid, snapshot_dir=snapshot_dir)}` — tanpa itu "
                    "kutipannya tak bisa dicocokkan dengan apa pun",
                    NO_SNAPSHOT,
                )
            )
            continue

        if normalize(quote) not in normalize(snapshot):
            problems.append(
                QuoteProblem(
                    sid,
                    f"kutipan TIDAK ditemukan di snapshot sumber: {quote[:80]!r}",
                    NOT_FOUND,
                )
            )

    return problems
