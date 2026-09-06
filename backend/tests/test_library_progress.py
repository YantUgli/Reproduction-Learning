"""Test penjaga metrik lajur Library (L5).

Yang dibuktikan di sini semuanya adalah aturan yang membuat angkanya JUJUR:

- Mengisi seluruh catatan (`status: captured`) TIDAK menggerakkan satu angka pun.
  Ini test terpenting di berkas ini: begitu ia merah, lajur Library sudah berubah
  jadi metrik "% dibaca" dan penjaganya bocor.
- Attempt BERSCAFFOLD (`acquisition`) bukan bukti reproduksi.
- Materi tanpa `node_ids` tetap masuk penyebut (course tampil berlubang).
- Materi dengan banyak node butuh SEMUANYA terbukti.
- `node_ids` menggantung dilaporkan, dan dihitung BELUM terbukti.
- Berkas struktural (`_index`) tak ikut dihitung.
- Modul ini tak pernah menulis ke `library/`.
"""

from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

from app.main import app
from app.models import Attempt, AttemptMode, AttemptResult, ScheduleItem, ScheduleStatus
from app.services import library_progress as lp

NODE_A = "n002_get_json_route"
NODE_B = "n003_path_param_404"


def _write(lib: Path, rel: str, **over) -> Path:
    parts = rel.split("/")
    fm = {
        "title": parts[-1].removesuffix(".md"),
        "course": parts[0],
        "module": parts[1] if len(parts) > 2 else "",
        "type": "note",
        "source_refs": [],
        "node_ids": [],
        "status": "outline",
        "created": "2026-09-06",
    }
    fm.update(over)
    path = lib / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    dumped = yaml.safe_dump(fm, sort_keys=False, allow_unicode=True).strip()
    path.write_text(f"---\n{dumped}\n---\n\n# {fm['title']}\n", encoding="utf-8")
    return path


@pytest.fixture
def lib(tmp_path):
    """Course kecil: 2 _index struktural + 3 materi (satu ditautkan ke NODE_A)."""
    root = tmp_path / "library"
    _write(root, "kursus/_index.md", type="outline", status="captured", title="Kursus")
    _write(root, "kursus/01-modul/_index.md", type="outline", status="captured", title="Modul 1")
    _write(root, "kursus/01-modul/a.md", node_ids=[NODE_A])
    _write(root, "kursus/01-modul/b.md")
    _write(root, "kursus/01-modul/c.md")
    return root


def _attempt(session, node_id, *, mode=AttemptMode.verification.value, result="pass"):
    session.add(Attempt(node_id=node_id, mode=mode, result=result))
    session.commit()


def _schedule(session, node_id, status):
    """UPDATE, bukan INSERT — `load_domain_into_db` (conftest) sudah membuat satu
    `ScheduleItem` per node, dan `node_id` adalah primary key. Menambah baris baru
    akan gagal `UNIQUE constraint failed: scheduleitem.node_id`."""
    item = session.get(ScheduleItem, node_id) or ScheduleItem(node_id=node_id)
    item.status = status
    session.add(item)
    session.commit()


def _by_name(data: lp.LibraryProgress, nama: str) -> lp.MaterialProgress:
    for course in data.courses:
        for module in course.modules:
            for materi in module.materials:
                if materi.rel_path.endswith(nama):
                    return materi
    raise AssertionError(f"materi {nama} tak ada di hasil")


# --------------------------------------------------------------------------- #
# Penyebut & keadaan
# --------------------------------------------------------------------------- #
def test_materi_tanpa_node_ids_tetap_masuk_penyebut(session, lib):
    data = lp.compute(session, library_dir=lib)
    course = data.courses[0]
    assert course.total == 3  # _index TIDAK dihitung
    assert course.unmapped == 2
    assert course.reproduced == 0
    assert course.reproduced_pct == 0.0


def test_index_struktural_tak_masuk_penyebut(session, lib):
    data = lp.compute(session, library_dir=lib)
    paths = [m.rel_path for c in data.courses for mo in c.modules for m in mo.materials]
    assert not any(p.endswith("_index.md") for p in paths)


def test_judul_course_dan_modul_dari_index(session, lib):
    data = lp.compute(session, library_dir=lib)
    assert data.courses[0].title == "Kursus"
    assert data.courses[0].modules[0].title == "Modul 1"


def test_attempt_dingin_membuktikan_materi(session, lib):
    _attempt(session, NODE_A)
    data = lp.compute(session, library_dir=lib)
    materi = _by_name(data, "a.md")
    assert materi.state == lp.REPRODUCED
    assert data.courses[0].reproduced == 1


def test_attempt_berscaffold_tidak_dihitung(session, lib):
    """Latihan dengan scaffold di layar bukan bukti reproduksi (kpi.REPRODUCE_MODES)."""
    _attempt(session, NODE_A, mode=AttemptMode.acquisition.value)
    data = lp.compute(session, library_dir=lib)
    assert _by_name(data, "a.md").state == lp.MAPPED_UNPROVEN


def test_attempt_gagal_tidak_dihitung(session, lib):
    _attempt(session, NODE_A, result=AttemptResult.failed.value)
    data = lp.compute(session, library_dir=lib)
    assert _by_name(data, "a.md").state == lp.MAPPED_UNPROVEN


def test_materi_dengan_dua_node_butuh_keduanya(session, lib):
    _write(lib, "kursus/01-modul/a.md", node_ids=[NODE_A, NODE_B])
    _attempt(session, NODE_A)
    assert _by_name(lp.compute(session, library_dir=lib), "a.md").state == lp.MAPPED_UNPROVEN
    _attempt(session, NODE_B)
    assert _by_name(lp.compute(session, library_dir=lib), "a.md").state == lp.REPRODUCED


def test_node_menggantung_dilaporkan_dan_belum_terbukti(session, lib):
    _write(lib, "kursus/01-modul/a.md", node_ids=["n999_tak_ada"])
    materi = _by_name(lp.compute(session, library_dir=lib), "a.md")
    assert materi.missing_node_ids == ["n999_tak_ada"]
    assert materi.state == lp.MAPPED_UNPROVEN


def test_transcription_ikut_dihitung_roadmap_tidak(session, lib):
    _write(lib, "kursus/01-modul/d.md", type="transcription")
    _write(lib, "kursus/01-modul/peta.md", type="roadmap")
    assert lp.compute(session, library_dir=lib).courses[0].total == 4


# --------------------------------------------------------------------------- #
# Penanda
# --------------------------------------------------------------------------- #
def test_lapsed_tetap_terbukti_tapi_ditandai_meluruh(session, lib):
    """Yang meluruh memorinya, BUKAN buktinya (§7 2026-08-21 Q3)."""
    _attempt(session, NODE_A)
    _schedule(session, NODE_A, ScheduleStatus.lapsed.value)
    materi = _by_name(lp.compute(session, library_dir=lib), "a.md")
    assert materi.state == lp.REPRODUCED and materi.decayed is True


def test_mastered_ditandai(session, lib):
    _attempt(session, NODE_A)
    _schedule(session, NODE_A, ScheduleStatus.mastered.value)
    assert _by_name(lp.compute(session, library_dir=lib), "a.md").mastered is True


# --------------------------------------------------------------------------- #
# ANTI-GAMING — test terpenting di berkas ini
# --------------------------------------------------------------------------- #
def test_status_captured_tidak_menggerakkan_angka(session, lib):
    _attempt(session, NODE_A)
    sebelum = lp.compute(session, library_dir=lib)

    for path in lib.glob("**/*.md"):
        teks = path.read_text(encoding="utf-8")
        path.write_text(teks.replace("status: outline", "status: captured"), encoding="utf-8")

    sesudah = lp.compute(session, library_dir=lib)
    assert (sesudah.total, sesudah.reproduced, sesudah.reproduced_pct) == (
        sebelum.total,
        sebelum.reproduced,
        sebelum.reproduced_pct,
    )
    # Labelnya BOLEH berubah — yang tak boleh adalah angkanya.
    assert _by_name(sesudah, "b.md").note_status == "captured"
    assert _by_name(sesudah, "b.md").state == lp.UNMAPPED


def test_membaca_tidak_pernah_menulis(session, lib):
    jejak = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in sorted(lib.glob("**/*.md"))}
    lp.compute(session, library_dir=lib)
    assert {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in sorted(lib.glob("**/*.md"))} == jejak


def test_berkas_cacat_dilewati_bukan_meledak(session, lib):
    (lib / "kursus/01-modul/rusak.md").write_text("bukan frontmatter", encoding="utf-8")
    data = lp.compute(session, library_dir=lib)
    assert data.courses[0].total == 3  # tetap 3, tanpa exception


def test_library_kosong_tidak_error(session, tmp_path):
    data = lp.compute(session, library_dir=tmp_path / "tak-ada")
    assert data.courses == [] and data.total == 0 and data.reproduced_pct is None


# --------------------------------------------------------------------------- #
# Endpoint (membaca library/ & DB SUNGGUHAN — tegakkan BENTUK, bukan angka)
# --------------------------------------------------------------------------- #
def test_endpoint_progress_membalas_bentuk_yang_benar():
    with TestClient(app) as client:
        resp = client.get("/library/progress")
    assert resp.status_code == 200
    body = resp.json()
    assert {"total", "reproduced", "reproduced_pct", "courses"} <= set(body)
    assert body["reproduced"] <= body["total"]
