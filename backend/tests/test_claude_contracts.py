"""Test kontrak artifact Claude Code (M5 langkah 3).

Membuktikan satu hal: **artifact yang tak sesuai skema ditolak sebelum manusia
melihatnya.** Manusia me-review konten, bukan membetulkan format (M5 §Keputusan).

Semua test di sini murni file + skema — tak ada CLI, tak ada DB.
"""

import json

import pytest

from app.claude import contracts
from app.claude.prompts import load_template, render

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
VALID_PROBE = {
    "id": "n002_probe_02",
    "node_id": "n002_get_json_route",
    "type": "predict_output",
    "question": "Status GET /x?",
    "options": ["200", "404"],
    "correct_answer": "200",
}


def _write(job_dir, files: dict[str, str]) -> None:
    for rel, content in files.items():
        target = job_dir / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")


def _r3_files(**overrides) -> dict[str, str]:
    files = {
        "explanation.md": "Route GET wajib mengembalikan dict agar FastAPI menyerialisasi JSON.",
        "worked_example.py": "# contoh\napp = None\n",
        "citations.json": json.dumps(
            {
                "citations": [
                    {
                        "source_ref_id": "fastapi_docs_first_steps",
                        "locator": "First Steps",
                        "claim": "route dideklarasikan lewat dekorator @app.get",
                    }
                ]
            }
        ),
    }
    files.update(overrides)
    return files


def _r4_files(**overrides) -> dict[str, str]:
    files = {
        "meta.json": json.dumps({"variant_label": "variant_c"}),
        "probe.yaml": json.dumps(VALID_PROBE),  # JSON adalah subset YAML yang sah
        "variant/prompt.md": "# Varian C\n\nBuat GET /x.\n",
        "variant/starter_code.py": "from fastapi import FastAPI\n\napp = FastAPI()\n\n# TODO:\n",
        "variant/reference_solution.py": VALID_REFERENCE,
        "variant/hidden_test.py": VALID_TEST,
    }
    files.update(overrides)
    return files


# --------------------------------------------------------------------------- #
# R3 — materi just-in-time
# --------------------------------------------------------------------------- #
def test_r3_valid_artifact_accepted(tmp_path):
    _write(tmp_path, _r3_files())
    artifact = contracts.load_explanation(tmp_path, "n002_get_json_route")
    assert artifact.citations[0].source_ref_id == "fastapi_docs_first_steps"
    assert artifact.worked_example


def test_r3_without_citation_rejected(tmp_path):
    _write(tmp_path, _r3_files(**{"citations.json": json.dumps({"citations": []})}))
    with pytest.raises(contracts.ArtifactError, match="sitasi"):
        contracts.load_explanation(tmp_path, "n002_get_json_route")


def test_r3_too_long_rejected(tmp_path):
    """Guardrail §8 yang bisa diuji: materi panjang = content library, ditolak."""
    _write(tmp_path, _r3_files(**{"explanation.md": "x" * 5000}))
    with pytest.raises(contracts.ArtifactError, match="just-in-time"):
        contracts.load_explanation(tmp_path, "n002_get_json_route")


def test_r3_unknown_source_ref_rejected(tmp_path):
    _write(tmp_path, _r3_files())
    artifact = contracts.load_explanation(tmp_path, "n002_get_json_route")
    with pytest.raises(contracts.ArtifactError, match="tak ada di sources.yaml"):
        contracts.check_citations_known(artifact, {"sumber_lain"})


def test_r3_missing_file_rejected(tmp_path):
    files = _r3_files()
    del files["explanation.md"]
    _write(tmp_path, files)
    with pytest.raises(contracts.ArtifactError, match="explanation.md"):
        contracts.load_explanation(tmp_path, "n002_get_json_route")


# --------------------------------------------------------------------------- #
# R4 — generator soal
# --------------------------------------------------------------------------- #
def test_r4_valid_artifact_accepted(tmp_path):
    _write(tmp_path, _r4_files())
    artifact = contracts.load_challenge(tmp_path, "n002_get_json_route")
    assert artifact.variant_label == "variant_c"
    assert artifact.probe.correct_answer == "200"


def test_r4_probe_answer_outside_options_rejected(tmp_path):
    bad_probe = {**VALID_PROBE, "correct_answer": "500"}
    _write(tmp_path, _r4_files(**{"probe.yaml": json.dumps(bad_probe)}))
    with pytest.raises(contracts.ArtifactError, match="correct_answer"):
        contracts.load_challenge(tmp_path, "n002_get_json_route")


def test_r4_test_not_importing_solution_rejected(tmp_path):
    """Test yang tak meng-import `solution` tak akan pernah menguji kode user."""
    _write(tmp_path, _r4_files(**{"variant/hidden_test.py": "def test_x():\n    assert True\n"}))
    with pytest.raises(contracts.ArtifactError, match="solution"):
        contracts.load_challenge(tmp_path, "n002_get_json_route")


def test_r4_test_without_test_function_rejected(tmp_path):
    _write(tmp_path, _r4_files(**{"variant/hidden_test.py": "from solution import app\n"}))
    with pytest.raises(contracts.ArtifactError, match="test_"):
        contracts.load_challenge(tmp_path, "n002_get_json_route")


def test_r4_bad_variant_label_rejected(tmp_path):
    _write(tmp_path, _r4_files(**{"meta.json": json.dumps({"variant_label": "Varian C"})}))
    with pytest.raises(contracts.ArtifactError, match="variant_label"):
        contracts.load_challenge(tmp_path, "n002_get_json_route")


def test_r4_probe_for_other_node_rejected(tmp_path):
    other = {**VALID_PROBE, "node_id": "n001_paginate"}
    _write(tmp_path, _r4_files(**{"probe.yaml": json.dumps(other)}))
    with pytest.raises(contracts.ArtifactError, match="node_id"):
        contracts.load_challenge(tmp_path, "n002_get_json_route")


# --------------------------------------------------------------------------- #
# R2 — bukti codebase
# --------------------------------------------------------------------------- #
def _hypotheses(**overrides) -> dict:
    h = {
        "node_id": "n002_get_json_route",
        "confidence": 0.7,
        "rationale": "repo punya beberapa route GET yang mengembalikan dict",
        "evidence_locator": "app/routers/nodes.py:54",
    }
    h.update(overrides)
    return {"hypotheses": [h]}


def test_r2_valid_artifact_accepted(tmp_path):
    (tmp_path / "hypotheses.json").write_text(json.dumps(_hypotheses()), encoding="utf-8")
    artifact = contracts.load_hypotheses(tmp_path)
    assert artifact.hypotheses[0].confidence == 0.7


def test_r2_empty_list_with_note_is_valid(tmp_path):
    """"Tak ada bukti" harus BISA dinyatakan. Kalau daftar kosong dianggap error,
    skema-nya menekan model untuk mengarang hipotesis — kegagalan termahal di R2."""
    (tmp_path / "hypotheses.json").write_text(
        json.dumps({"hypotheses": [], "note": "akses baca ke repo ditolak"}),
        encoding="utf-8",
    )
    artifact = contracts.load_hypotheses(tmp_path)
    assert artifact.hypotheses == []
    assert "ditolak" in artifact.note


def test_r2_confidence_out_of_range_rejected(tmp_path):
    (tmp_path / "hypotheses.json").write_text(
        json.dumps(_hypotheses(confidence=1.5)), encoding="utf-8"
    )
    with pytest.raises(contracts.ArtifactError):
        contracts.load_hypotheses(tmp_path)


def test_r2_without_evidence_rejected(tmp_path):
    (tmp_path / "hypotheses.json").write_text(
        json.dumps(_hypotheses(evidence_locator="  ")), encoding="utf-8"
    )
    with pytest.raises(contracts.ArtifactError, match="evidence_locator"):
        contracts.load_hypotheses(tmp_path)


def test_r2_status_field_rejected(tmp_path):
    """Artifact tak boleh membawa status: status hanya lahir dari Attempt (RISK-4)."""
    payload = _hypotheses()
    payload["hypotheses"][0]["status"] = "confirmed_by_attempt"
    (tmp_path / "hypotheses.json").write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(contracts.ArtifactError):
        contracts.load_hypotheses(tmp_path)


def test_r2_unknown_node_rejected(tmp_path):
    (tmp_path / "hypotheses.json").write_text(json.dumps(_hypotheses()), encoding="utf-8")
    artifact = contracts.load_hypotheses(tmp_path)
    with pytest.raises(contracts.ArtifactError, match="node yang tak ada"):
        contracts.check_nodes_known(artifact, {"n001_paginate"})


# --------------------------------------------------------------------------- #
# Prompt terstruktur & versioned
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "name,prefix",
    [("r2_hypotheses", "r2-"), ("r3_explanation", "r3-"), ("r4_challenge", "r4-")],
)
def test_prompt_templates_are_versioned(name: str, prefix: str):
    version, body = load_template(name)
    assert version.startswith(prefix)
    assert body.strip()


def test_render_refuses_missing_placeholder():
    with pytest.raises(ValueError, match="placeholder tanpa nilai"):
        render("r2_hypotheses", {"repo_path": "/tmp/repo"})  # node_list hilang


def test_render_fills_placeholders():
    rendered = render("r2_hypotheses", {"repo_path": "/tmp/repo", "node_list": "- `n001`"})
    assert "/tmp/repo" in rendered.text
    assert "{{" not in rendered.text
