"""Test grounding verbatim (M7 langkah 3).

Yang dibuktikan: sitasi tak lagi cukup menunjuk sumber yang ADA — kutipannya harus
benar-benar ditemukan di snapshot sumber. Ini menutup celah yang disebut sendiri
oleh keputusan M5 2026-08-22 sebagai alasan approve Isyah diwajibkan.
"""

import pytest

from app.claude.contracts import Citation
from app.services import grounding

SNAPSHOT = """# FastAPI - Query Parameters

When you declare other function parameters that are not part of the path
parameters, they are automatically interpreted as "query" parameters.
"""
KUTIPAN_ASLI = 'they are automatically interpreted as "query" parameters'


@pytest.fixture()
def snapshots(tmp_path):
    (tmp_path / "fastapi_docs_query_params.md").write_text(SNAPSHOT, encoding="utf-8")
    return tmp_path


def _cite(quote: str, source: str = "fastapi_docs_query_params") -> Citation:
    return Citation(source_ref_id=source, claim="query param dibaca dari URL", quote=quote)


def test_kutipan_asli_lolos(snapshots):
    assert grounding.check_quotes([_cite(KUTIPAN_ASLI)], snapshot_dir=snapshots) == []


def test_kutipan_karangan_ditolak(snapshots):
    problems = grounding.check_quotes(
        [_cite("query parameters must always be declared with the Query class")],
        snapshot_dir=snapshots,
    )
    assert len(problems) == 1
    assert "TIDAK ditemukan" in problems[0].reason


def test_lipatan_baris_bukan_alasan_gagal(snapshots):
    """Kutipan yang benar sering terpotong baris berbeda dari sumbernya. Normalisasi
    menyentuh SPASI saja — kalau tidak, gerbang ini akan menolak sitasi yang sah."""
    terlipat = 'they are\n   automatically     interpreted\nas "query" parameters'
    assert grounding.check_quotes([_cite(terlipat)], snapshot_dir=snapshots) == []


def test_beda_huruf_besar_kecil_ditolak(snapshots):
    """Huruf sengaja TIDAK dinormalisasi: sumber di sini penuh kode, dan `Query`
    bukan `query`."""
    problems = grounding.check_quotes([_cite(KUTIPAN_ASLI.upper())], snapshot_dir=snapshots)
    assert len(problems) == 1


def test_kutipan_terlalu_pendek_ditolak(snapshots):
    """Potongan sependek 'the' ada di setiap dokumen — itu kebetulan, bukan sitasi."""
    problems = grounding.check_quotes([_cite("query")], snapshot_dir=snapshots)
    assert "terlalu pendek" in problems[0].reason


def test_tanpa_kutipan_ditolak(snapshots):
    problems = grounding.check_quotes([_cite("")], snapshot_dir=snapshots)
    assert "tanpa `quote`" in problems[0].reason


def test_sumber_tanpa_snapshot_ditolak_dengan_path_yang_bisa_ditindak(snapshots):
    """Tanpa snapshot, kutipan tak bisa dicocokkan dengan apa pun. Pesannya menyebut
    berkas persis yang harus dibuat — ini satu-satunya pekerjaan manusia yang
    tersisa di jalur R3."""
    problems = grounding.check_quotes(
        [_cite(KUTIPAN_ASLI, source="fastapi_docs_path_params")], snapshot_dir=snapshots
    )
    assert len(problems) == 1
    assert "fastapi_docs_path_params.md" in problems[0].reason


# --------------------------------------------------------------------------- #
# Beda MENOLAK dan MENAHAN
# --------------------------------------------------------------------------- #
def test_snapshot_hilang_dibedakan_dari_kutipan_karangan(snapshots):
    """Kekurangan di pihak kita (belum menyalin sumber) tak boleh dihukum sama
    dengan cacat di artifact (mengarang kutipan). Yang pertama menahan promosi;
    yang kedua menolak artifact."""
    tanpa_snapshot = grounding.check_quotes(
        [_cite(KUTIPAN_ASLI, source="fastapi_docs_path_params")], snapshot_dir=snapshots
    )
    karangan = grounding.check_quotes(
        [_cite("kalimat yang tak ada di sumber mana pun")], snapshot_dir=snapshots
    )

    assert grounding.only_missing_snapshots(tanpa_snapshot)
    assert not grounding.only_missing_snapshots(karangan)


def test_campuran_dihitung_sebagai_cacat(snapshots):
    """Satu kutipan karangan cukup membuat artifact ditolak, walau sisanya cuma
    kekurangan snapshot — kalau tidak, cacat bisa bersembunyi di balik ketiadaan."""
    problems = grounding.check_quotes(
        [
            _cite(KUTIPAN_ASLI, source="fastapi_docs_path_params"),
            _cite("kalimat yang tak ada di sumber mana pun"),
        ],
        snapshot_dir=snapshots,
    )
    assert not grounding.only_missing_snapshots(problems)
