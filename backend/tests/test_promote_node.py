"""Test promosi node baru ke `data/` + DB (L4).

Ini test promosi PERTAMA di repo — M5/M7 tak punya, dan itu justru yang membuatnya
perlu: promosi adalah satu-satunya jalur tulis ke kurikulum, dan jalur tulis tanpa
test adalah jalur yang kesalahannya baru terlihat di `git status`.

SEMUA test di sini mem-`monkeypatch` `review_queue.DATA_DIR` ke `tmp_path`. Lupa satu
kali = test menulis node palsu ke kurikulum sungguhan.
"""

import shutil

import pytest
import yaml

from app.claude import review_queue
from app.claude.artifacts import Job, Role
from app.config import DATA_DIR as REAL_DATA_DIR
from app.services.node_loader import NodeValidationError

from .test_node_genesis import PROBE, REQUEST, _genesis_files, _write

PREREQ = "n002_get_json_route"


@pytest.fixture
def data_tmp(tmp_path, monkeypatch):
    """Salinan `data/` nyata di tmp — lalu DATA_DIR diarahkan ke sana.

    Disalin, bukan dikarang: promosi memanggil `assemble_node` + `load_domain_into_db`
    atas SELURUH domain, jadi domain palsu setengah jadi akan gagal karena alasan yang
    tak ada hubungannya dengan yang sedang diuji.
    """
    data = tmp_path / "data"
    (data / "domains").mkdir(parents=True)
    shutil.copy(REAL_DATA_DIR / "sources.yaml", data / "sources.yaml")
    shutil.copytree(REAL_DATA_DIR / "domains" / "fastapi", data / "domains" / "fastapi")
    monkeypatch.setattr(review_queue, "DATA_DIR", data)
    return data


@pytest.fixture
def job_at(tmp_path, monkeypatch):
    """Job palsu mode `node` yang `dir`-nya menunjuk direktori artifact di tmp."""
    job_dir = tmp_path / "job"
    job_dir.mkdir()
    monkeypatch.setattr(Job, "dir", property(lambda self: job_dir))
    return Job(
        id="r4-fake",
        role=Role.r4_challenge.value,
        status="ready",
        created_at="",
        updated_at="",
        request={
            **REQUEST,
            "library_file": "library/fastapi-produksi/01-routing-dasar/get-route.md",
            "prereq_node_id": PREREQ,
        },
    )


def _node_dir(data, node_id="n014_get_route"):
    return data / "domains" / "fastapi" / "nodes" / node_id


def test_promosi_menulis_node_dan_edge_soft(data_tmp, session, job_at):
    _write(job_at.dir, _genesis_files())
    promotion = review_queue._promote_node_genesis(session, job_at)

    target = _node_dir(data_tmp)
    assert (target / "node.yaml").is_file()
    for label in ("variant_a", "variant_b"):
        vdir = target / "instances" / label
        assert {p.name for p in vdir.iterdir()} == {
            "prompt.md",
            "starter_code.py",
            "reference_solution.py",
            "hidden_test.py",
        }
    assert (target / "probes" / "n014_probe_01.yaml").is_file()

    # node.yaml hasil AI ter-diff sama bentuknya dengan tulisan tangan (string, bukan enum).
    fm = yaml.safe_load((target / "node.yaml").read_text("utf-8"))
    assert fm["grader_type"] == "unit_test" and fm["status_default"] == "locked"

    assert promotion.node_id == "n014_get_route"
    assert promotion.db_effect["variants"] == ["variant_a", "variant_b"]
    assert promotion.db_effect["soft_edge_from"] == PREREQ


def test_node_baru_terdaftar_di_db(data_tmp, session, job_at):
    from app.models import ChallengeInstance, Node

    _write(job_at.dir, _genesis_files())
    review_queue._promote_node_genesis(session, job_at)

    node = session.get(Node, "n014_get_route")
    assert node is not None and node.domain_id == "fastapi"
    assert session.get(ChallengeInstance, "n014_get_route__variant_a") is not None
    assert session.get(ChallengeInstance, "n014_get_route__variant_b") is not None


def test_edge_yang_ditulis_selalu_soft(data_tmp, session, job_at):
    """Usul AI tak pernah mengunci urutan (§7 2026-09-01)."""
    _write(job_at.dir, _genesis_files())
    review_queue._promote_node_genesis(session, job_at)

    raw = (data_tmp / "domains" / "fastapi" / "edges.yaml").read_text("utf-8")
    blok = raw[raw.index("n014_get_route") - 200 :]
    assert "type: soft" in blok
    assert "type: hard" not in blok.split("n014_get_route")[1]


def test_append_edge_mempertahankan_komentar(tmp_path):
    """Komentar kurasi di edges.yaml masih ada setelah append (KUNCI 9).

    Ini alasan edge ditulis sebagai TEKS, bukan `yaml.dump` ulang: dumper akan
    menghapus komentar kurasi Isyah diam-diam.
    """
    path = tmp_path / "edges.yaml"
    path.write_text(
        "# Edge prasyarat — difinalkan Isyah 2026-08-22.\nedges:\n"
        "  - from: a\n    to: b\n    type: hard\n",
        encoding="utf-8",
    )
    review_queue._append_soft_edge(
        path, from_id="b", to_id="c", source_ref_id="cs2023_ku", library_file="library/x.md"
    )
    raw = path.read_text("utf-8")
    assert "difinalkan Isyah 2026-08-22" in raw
    assert "type: soft" in raw and "type: hard" in raw


def test_append_edge_menolak_hasil_yang_tak_parse(tmp_path):
    """`load_edges` dipanggil sebagai BUKTI berkasnya masih sah — bukan formalitas."""
    path = tmp_path / "edges.yaml"
    path.write_text("edges:\n  - from: a\n    to: b\n    type: hard\n", encoding="utf-8")
    with pytest.raises(Exception):  # noqa: B017 — self-loop ditolak EdgeYaml
        review_queue._append_soft_edge(
            path, from_id="c", to_id="c", source_ref_id="", library_file="library/x.md"
        )


def test_promosi_menolak_node_yang_sudah_ada(data_tmp, session, job_at):
    _write(job_at.dir, _genesis_files())
    review_queue._promote_node_genesis(session, job_at)
    with pytest.raises(review_queue.PromotionError, match="sudah ada"):
        review_queue._promote_node_genesis(session, job_at)


def test_promosi_rollback_saat_node_tak_sah(data_tmp, session, job_at, monkeypatch):
    """Node setengah jadi mematikan SELURUH domain, bukan cuma dirinya.

    Yang diuji kontrak rollback-nya, bukan penyebab gagalnya: apa pun yang meledak di
    dalam blok promosi harus meninggalkan `data/` persis seperti sebelumnya.
    """
    edges_path = data_tmp / "domains" / "fastapi" / "edges.yaml"
    sebelum = edges_path.read_text("utf-8")
    _write(job_at.dir, _genesis_files())

    def _meledak(_):
        raise NodeValidationError("butuh >= 2 varian instance")

    monkeypatch.setattr(review_queue, "assemble_node", _meledak)
    with pytest.raises(review_queue.PromotionError, match="promosi dibatalkan"):
        review_queue._promote_node_genesis(session, job_at)

    assert not _node_dir(data_tmp).exists()  # folder node HILANG lagi
    assert edges_path.read_text("utf-8") == sebelum  # edges.yaml persis seperti semula


def test_promosi_tanpa_prereq_tak_menyentuh_edges(data_tmp, session, job_at):
    """Edge itu OPSIONAL — node hasil L4 selalu `available` (KUNCI 8)."""
    edges_path = data_tmp / "domains" / "fastapi" / "edges.yaml"
    sebelum = edges_path.read_text("utf-8")
    job_at.request["prereq_node_id"] = ""
    _write(job_at.dir, _genesis_files())
    review_queue._promote_node_genesis(session, job_at)
    assert edges_path.read_text("utf-8") == sebelum


def test_probe_ditulis_sebagai_string_bukan_enum(data_tmp, session, job_at):
    _write(job_at.dir, _genesis_files())
    review_queue._promote_node_genesis(session, job_at)
    raw = (_node_dir(data_tmp) / "probes" / "n014_probe_01.yaml").read_text("utf-8")
    probe = yaml.safe_load(raw)
    assert probe["type"] == PROBE["type"]
    assert "!!python" not in raw
