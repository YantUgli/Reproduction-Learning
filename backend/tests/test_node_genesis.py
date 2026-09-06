"""Test kelahiran node dari peta Library (L4).

Tiga lapis yang diuji terpisah, karena tiga-tiganya bisa gagal sendiri-sendiri:
  1. trigger  — menolak permintaan yang tak layak SEBELUM model dipanggil (hemat menit).
  2. kontrak  — menolak artifact yang identitas/bentuknya menyimpang.
  3. gerbang  — menolak soal yang tak lolos triad DUA varian / probe.
Promosi diuji di `test_promote_node.py` karena ia menulis ke disk.
"""

import json
import shutil

import pytest
import yaml

from app.claude import contracts, jobs
from app.claude.artifacts import Job, Role
from app.config import DATA_DIR as REAL_DATA_DIR
from app.graders.base import GradeResult
from app.models import ChallengeInstance
from app.services import node_loader

MATERIAL = """---
title: "GET route JSON"
course: fastapi-produksi
module: 01-routing-dasar
type: note
source_refs: [fastapi_docs_first_steps]
node_ids: []
status: outline
created: 2026-09-06
---

# GET route JSON
"""

VALID_TEST = (
    "from fastapi.testclient import TestClient\n"
    "from solution import app\n\n"
    "client = TestClient(app)\n\n\n"
    "def test_status_ok():\n"
    "    assert client.get('/x').status_code == 200\n"
)
VALID_REFERENCE = (
    "from fastapi import FastAPI\n\napp = FastAPI()\n\n\n"
    "@app.get('/x')\ndef read_x():\n    return {'ok': True}\n"
)


@pytest.fixture
def materi(tmp_path, monkeypatch):
    """Berkas materi Library palsu, di bawah `library/` versi tmp."""
    monkeypatch.setattr(jobs, "REPO_ROOT", tmp_path)
    path = tmp_path / "library" / "fastapi-produksi" / "01-routing-dasar" / "get-route.md"
    path.parent.mkdir(parents=True)
    path.write_text(MATERIAL, encoding="utf-8")
    return "library/fastapi-produksi/01-routing-dasar/get-route.md"


@pytest.fixture
def contoh_terjangkau(tmp_path):
    """Salin kurikulum FastAPI nyata ke bawah REPO_ROOT versi tmp.

    `trigger_r4_node` membaca berkas node CONTOH lewat `REPO_ROOT / hidden_test_path`
    (pointer relatif-repo dari DB). Fixture `materi` mengarahkan REPO_ROOT ke tmp_path,
    jadi tanpa salinan ini jalur sukses tak bisa diuji sama sekali — dan yang diuji
    justru bagian yang paling ingin kita buktikan: identitas node yang terkunci.
    """
    src = REAL_DATA_DIR / "domains" / "fastapi" / "nodes"
    shutil.copytree(src, tmp_path / "data" / "domains" / "fastapi" / "nodes")
    return tmp_path


# --------------------------------------------------------------------------- #
# 1. Trigger
# --------------------------------------------------------------------------- #
class _N:
    def __init__(self, i):
        self.id = i


def test_next_node_id_mewarisi_konvensi_domain():
    """Prefix & lebar angka diwarisi dari domain, bukan di-hardcode."""
    assert jobs._next_node_id([_N("n012_x"), _N("n013_y")], "get-route") == "n014_get_route"
    assert jobs._next_node_id([_N("m003_mse")], "adam-step") == "m004_adam_step"
    assert jobs._next_node_id([_N("r003_list")], "use-effect") == "r004_use_effect"


def test_probe_id_ikut_konvensi_tulisan_tangan():
    assert jobs._probe_id_for("n014_get_route", 1) == "n014_probe_01"
    assert jobs._probe_id_for("m004_adam_step", 1) == "m004_probe_01"


def test_trigger_menolak_domain_tanpa_node(session, materi):
    with pytest.raises(jobs.JobError, match="belum punya satu pun node"):
        jobs.trigger_r4_node(
            session,
            library_file=materi,
            slug="x",
            domain_id="docker",
            concept="c",
            source_ref_id="fastapi_docs_first_steps",
        )


def test_trigger_menolak_slug_bukan_kebab_case(session, materi):
    with pytest.raises(jobs.JobError, match="kebab-case"):
        jobs.trigger_r4_node(
            session,
            library_file=materi,
            slug="Get_Route",
            domain_id="fastapi",
            concept="c",
            source_ref_id="fastapi_docs_first_steps",
        )


def test_trigger_menolak_sumber_tanpa_snapshot(session, materi, monkeypatch):
    monkeypatch.setattr(jobs.grounding, "has_snapshot", lambda sid, **kw: False)
    with pytest.raises(jobs.JobError, match="belum di-snapshot"):
        jobs.trigger_r4_node(
            session,
            library_file=materi,
            slug="get-route",
            domain_id="fastapi",
            concept="c",
            source_ref_id="fastapi_docs_first_steps",
        )


def test_trigger_menolak_materi_yang_sudah_tertaut(session, materi, tmp_path, monkeypatch):
    (tmp_path / materi).write_text(
        MATERIAL.replace("node_ids: []", "node_ids: [n002_get_json_route]"), encoding="utf-8"
    )
    monkeypatch.setattr(jobs.grounding, "has_snapshot", lambda sid, **kw: True)
    with pytest.raises(jobs.JobError, match="sudah tertaut"):
        jobs.trigger_r4_node(
            session,
            library_file=materi,
            slug="get-route",
            domain_id="fastapi",
            concept="c",
            source_ref_id="fastapi_docs_first_steps",
        )


def test_trigger_menolak_sumber_yang_tak_dipakai_materinya(session, materi, monkeypatch):
    """Node dan materinya harus berdiri di sumber yang SAMA (KUNCI 6)."""
    monkeypatch.setattr(jobs.grounding, "has_snapshot", lambda sid, **kw: True)
    with pytest.raises(jobs.JobError, match="tak memuat"):
        jobs.trigger_r4_node(
            session,
            library_file=materi,
            slug="get-route",
            domain_id="fastapi",
            concept="c",
            source_ref_id="fastapi_docs_path_params",
        )


def test_trigger_menolak_berkas_di_luar_library(session, materi, monkeypatch):
    monkeypatch.setattr(jobs.grounding, "has_snapshot", lambda sid, **kw: True)
    with pytest.raises(jobs.JobError, match="bukan berkas di dalam library/"):
        jobs.trigger_r4_node(
            session,
            library_file="data/sources.yaml",
            slug="get-route",
            domain_id="fastapi",
            concept="c",
            source_ref_id="fastapi_docs_first_steps",
        )


def test_trigger_menolak_prereq_beda_domain(session, materi, monkeypatch):
    monkeypatch.setattr(jobs.grounding, "has_snapshot", lambda sid, **kw: True)
    with pytest.raises(jobs.JobError, match="tak ada di domain"):
        jobs.trigger_r4_node(
            session,
            library_file=materi,
            slug="get-route",
            domain_id="fastapi",
            concept="c",
            source_ref_id="fastapi_docs_first_steps",
            prereq_node_id="m001_softmax_stable",
        )


def test_trigger_membentuk_job_dengan_identitas_terkunci(
    session, materi, contoh_terjangkau, monkeypatch
):
    monkeypatch.setattr(jobs.grounding, "has_snapshot", lambda sid, **kw: True)
    job = jobs.trigger_r4_node(
        session,
        library_file=materi,
        slug="get-route",
        domain_id="fastapi",
        concept="GET route JSON",
        source_ref_id="fastapi_docs_first_steps",
    )
    assert job.role == Role.r4_challenge.value
    assert job.request["mode"] == "node"
    assert job.request["node_id"].startswith("n014_")
    assert job.request["variant_labels"] == ["variant_a", "variant_b"]
    assert job.request["probe_id"] == job.request["node_id"][:4] + "_probe_01"
    assert job.request["grader_type"] == "unit_test"
    assert job.request["file_ext"] == ".py"
    assert job.request["library_file"] == materi
    # Identitas ikut ke prompt supaya model tahu ia tak boleh menamai sendiri.
    assert job.request["node_id"] in (job.dir / "prompt.md").read_text(encoding="utf-8")


# --------------------------------------------------------------------------- #
# 2. Kontrak
# --------------------------------------------------------------------------- #
NODE_YAML = {
    "id": "n014_get_route",
    "domain_id": "fastapi",
    "concept": "GET route JSON 200",
    "description": "d",
    "grader_type": "unit_test",
    "estimated_minutes": 12,
    "timebox_seconds": 900,
    "status_default": "locked",
    "source_refs": ["fastapi_docs_first_steps"],
    "signature_contract": "@app.get(<path>) -> dict",
    "scaffold_level": "L2",
}
PROBE = {
    "id": "n014_probe_01",
    "node_id": "n014_get_route",
    "type": "predict_output",
    "question": "Status?",
    "options": ["200", "404"],
    "correct_answer": "200",
    "snippet": "x = 200\n",
    "expression": "x",
}
REQUEST = {
    "mode": "node",
    "node_id": "n014_get_route",
    "domain_id": "fastapi",
    "grader_type": "unit_test",
    "file_ext": ".py",
    "source_ref_id": "fastapi_docs_first_steps",
    "variant_labels": ["variant_a", "variant_b"],
    "probe_id": "n014_probe_01",
}


def _write(job_dir, files: dict[str, str]) -> None:
    for rel, content in files.items():
        target = job_dir / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")


def _genesis_files(**over) -> dict[str, str]:
    files = {
        "node.yaml": yaml.safe_dump(NODE_YAML),
        "probe.yaml": json.dumps(PROBE),
        "citation.json": json.dumps(
            {
                "source_ref_id": "fastapi_docs_first_steps",
                "claim": "route dideklarasikan lewat dekorator",
                "quote": "The simplest FastAPI file could look like this",
            }
        ),
    }
    for label in ("variant_a", "variant_b"):
        files[f"instances/{label}/prompt.md"] = f"# {label}\n"
        files[f"instances/{label}/starter_code.py"] = "# TODO:\n"
        files[f"instances/{label}/reference_solution.py"] = VALID_REFERENCE
        files[f"instances/{label}/hidden_test.py"] = VALID_TEST
    files.update(over)
    return files


def test_kontrak_menerima_artifact_lengkap(tmp_path):
    _write(tmp_path, _genesis_files())
    artifact = contracts.load_node_genesis(tmp_path, REQUEST)
    assert len(artifact.variants) == 2 and artifact.file_ext == ".py"


def test_min_variants_sejalan_dengan_loader():
    """Kontrak menolak SEBELUM eksekusi mahal; loader menolak sesudahnya. Angkanya
    diulang dengan sadar di dua tempat — test ini yang menjaganya tetap sama."""
    assert contracts._MIN_VARIANTS == node_loader._MIN_INSTANCES


def test_kontrak_menolak_id_karangan(tmp_path):
    """Artifact yang KONSISTEN di dalam dirinya tapi menamai ulang node-nya sendiri.

    Sengaja node.yaml DAN probe.node_id diganti bersamaan: kalau hanya salah satu,
    yang menangkapnya adalah pemeriksaan konsistensi internal (`_shape`), bukan
    penegak identitas — dan `_require_identity` jadi tak pernah benar-benar diuji.
    """
    files = _genesis_files()
    files["node.yaml"] = yaml.safe_dump({**NODE_YAML, "id": "n999_keren"})
    files["probe.yaml"] = json.dumps({**PROBE, "node_id": "n999_keren"})
    _write(tmp_path, files)
    with pytest.raises(contracts.ArtifactError, match="identitas node"):
        contracts.load_node_genesis(tmp_path, REQUEST)


def test_kontrak_menolak_grader_karangan(tmp_path):
    """Grader yang dikarang = memilih gerbang yang paling mudah dilewati."""
    files = _genesis_files()
    files["node.yaml"] = yaml.safe_dump({**NODE_YAML, "grader_type": "value_assert"})
    _write(tmp_path, files)
    with pytest.raises(contracts.ArtifactError, match="grader_type"):
        contracts.load_node_genesis(tmp_path, REQUEST)


def test_kontrak_menolak_satu_varian(tmp_path):
    _write(tmp_path, _genesis_files())
    req = {**REQUEST, "variant_labels": ["variant_a"]}
    with pytest.raises(contracts.ArtifactError, match="2 varian"):
        contracts.load_node_genesis(tmp_path, req)


def test_kontrak_menolak_probe_expected_value(tmp_path):
    files = _genesis_files()
    files["probe.yaml"] = json.dumps({**PROBE, "expected_value": "200"})
    _write(tmp_path, files)
    with pytest.raises(contracts.ArtifactError, match="expected_value"):
        contracts.load_node_genesis(tmp_path, REQUEST)


def test_kontrak_menolak_probe_tanpa_snippet(tmp_path):
    files = _genesis_files()
    files["probe.yaml"] = json.dumps(
        {k: v for k, v in PROBE.items() if k not in ("snippet", "expression")}
    )
    _write(tmp_path, files)
    with pytest.raises(contracts.ArtifactError, match="snippet"):
        contracts.load_node_genesis(tmp_path, REQUEST)


def test_kontrak_menolak_sitasi_di_luar_source_refs(tmp_path):
    files = _genesis_files()
    files["citation.json"] = json.dumps(
        {"source_ref_id": "fastapi_docs_body", "claim": "c", "quote": "q" * 30}
    )
    _write(tmp_path, files)
    with pytest.raises(contracts.ArtifactError):
        contracts.load_node_genesis(tmp_path, REQUEST)


def test_kontrak_menolak_hidden_test_yang_tak_menyentuh_solution(tmp_path):
    files = _genesis_files()
    files["instances/variant_b/hidden_test.py"] = "def test_x():\n    assert True\n"
    _write(tmp_path, files)
    with pytest.raises(contracts.ArtifactError, match="hidden_test"):
        contracts.load_node_genesis(tmp_path, REQUEST)


# --------------------------------------------------------------------------- #
# 3. Gerbang
# --------------------------------------------------------------------------- #
class FakeGrader:
    """Grader yang lolos hanya untuk daftar submisi tertentu (gaya test_gate_triad)."""

    def __init__(self, passes_for: set[str]) -> None:
        self._passes_for = passes_for

    def grade(self, instance: ChallengeInstance, submitted_code: str) -> GradeResult:
        return GradeResult(
            passed=submitted_code in self._passes_for,
            test_output="(fake)",
            timed_out=False,
            duration_seconds=0.01,
        )


@pytest.fixture
def job_at(tmp_path, monkeypatch):
    """Job palsu yang `dir`-nya menunjuk tmp_path (`Job.dir` adalah property)."""
    monkeypatch.setattr(Job, "dir", property(lambda self: tmp_path))
    return Job(
        id="r4-fake",
        role=Role.r4_challenge.value,
        status="running",
        created_at="",
        updated_at="",
        request=dict(REQUEST),
    )


def test_gate_lolos_saat_dua_varian_hijau(tmp_path, session, job_at, monkeypatch):
    _write(tmp_path, _genesis_files())
    monkeypatch.setattr(jobs, "get_grader", lambda t: FakeGrader({VALID_REFERENCE}))
    gate = jobs._gate_r4_node(job_at, session)
    assert gate["passed"] is True
    assert set(gate["variants"]) == {"variant_a", "variant_b"}
    assert gate["probe_verified"] is True


def test_gate_menolak_saat_varian_kedua_merah(tmp_path, session, job_at, monkeypatch):
    """Varian pertama hijau TIDAK cukup — tiap varian diuji sendiri."""
    files = _genesis_files()
    files["instances/variant_b/reference_solution.py"] = "# solusi salah\n"
    _write(tmp_path, files)
    monkeypatch.setattr(jobs, "get_grader", lambda t: FakeGrader({VALID_REFERENCE}))
    gate = jobs._gate_r4_node(job_at, session)
    assert gate["passed"] is False and "variant_b" in gate["reason"]
    assert gate["variants"]["variant_a"]["passed"] is True


def test_gate_menolak_starter_yang_sudah_lolos(tmp_path, session, job_at, monkeypatch):
    """Kerangka L2 yang sudah hijau = tantangan kosong yang MEMALSUKAN sinyal inti."""
    files = _genesis_files()
    files["instances/variant_a/starter_code.py"] = VALID_REFERENCE
    _write(tmp_path, files)
    monkeypatch.setattr(jobs, "get_grader", lambda t: FakeGrader({VALID_REFERENCE}))
    gate = jobs._gate_r4_node(job_at, session)
    assert gate["passed"] is False and "variant_a" in gate["reason"]


def test_gate_menolak_test_yang_hijau_di_berkas_kosong(tmp_path, session, job_at, monkeypatch):
    _write(tmp_path, _genesis_files())
    monkeypatch.setattr(
        jobs, "get_grader", lambda t: FakeGrader({VALID_REFERENCE, "# TODO:\n", ""})
    )
    gate = jobs._gate_r4_node(job_at, session)
    assert gate["passed"] is False


def test_gate_menolak_probe_berkunci_salah(tmp_path, session, job_at, monkeypatch):
    files = _genesis_files()
    files["probe.yaml"] = json.dumps({**PROBE, "correct_answer": "404"})
    _write(tmp_path, files)
    monkeypatch.setattr(jobs, "get_grader", lambda t: FakeGrader({VALID_REFERENCE}))
    gate = jobs._gate_r4_node(job_at, session)
    assert gate["passed"] is False and "probe" in gate["reason"]
