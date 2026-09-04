import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
import verify_library as vl

SRC_IDS = {"fastapi_docs_first_steps", "fastapi_official_docs"}
NODE_IDS = {"n002_get_json_route", "m001_softmax_stable"}


def _write(root: Path, rel: str, fm: dict, body: str) -> Path:
    import yaml
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    dumped = yaml.safe_dump(fm, sort_keys=False, allow_unicode=True).strip()
    p.write_text(f"---\n{dumped}\n---\n{body}", encoding="utf-8")
    return p


def _fm(**over) -> dict:
    base = {"title": "GET route", "course": "fastapi-dasar",
            "module": "01-routing-dasar", "type": "note",
            "source_refs": [], "node_ids": [], "status": "captured",
            "created": "2026-09-04"}
    base.update(over)
    return base


@pytest.fixture
def lib(tmp_path, monkeypatch):
    monkeypatch.setattr(vl, "_REPO_ROOT", tmp_path)
    monkeypatch.setattr(vl, "_LIBRARY_ROOT", tmp_path / "library")
    monkeypatch.setattr(vl, "load_source_ids", lambda: set(SRC_IDS))
    monkeypatch.setattr(vl, "load_node_ids", lambda: set(NODE_IDS))
    return tmp_path / "library"


def test_valid_captured_note_passes(lib):
    p = _write(lib, "fastapi-dasar/01-routing-dasar/get.md",
               _fm(source_refs=["fastapi_docs_first_steps"],
                   node_ids=["n002_get_json_route"]),
               "\n# GET route\n\nRoute GET dasar mengembalikan dict jadi JSON.\n")
    assert vl.validate_file(p, SRC_IDS, NODE_IDS) == []


def test_missing_field_fails(lib):
    fm = _fm()
    del fm["created"]
    p = _write(lib, "fastapi-dasar/01-routing-dasar/get.md", fm, "\nisi nyata.\n")
    errs = vl.validate_file(p, SRC_IDS, NODE_IDS)
    assert any("created" in e for e in errs)


def test_extra_field_fails(lib):
    p = _write(lib, "fastapi-dasar/01-routing-dasar/get.md",
               _fm(extra="x"), "\nisi nyata.\n")
    assert any("field asing" in e for e in vl.validate_file(p, SRC_IDS, NODE_IDS))


def test_bad_source_ref_fails(lib):
    p = _write(lib, "fastapi-dasar/01-routing-dasar/get.md",
               _fm(source_refs=["tidak_ada"]), "\nisi nyata.\n")
    assert any("source_refs" in e for e in vl.validate_file(p, SRC_IDS, NODE_IDS))


def test_bad_node_id_fails(lib):
    p = _write(lib, "fastapi-dasar/01-routing-dasar/get.md",
               _fm(node_ids=["n999_bogus"]), "\nisi nyata.\n")
    assert any("node_ids" in e for e in vl.validate_file(p, SRC_IDS, NODE_IDS))


def test_bad_type_and_status_fail(lib):
    p = _write(lib, "fastapi-dasar/01-routing-dasar/get.md",
               _fm(type="forged", status="mastered"), "\nisi nyata.\n")
    errs = vl.validate_file(p, SRC_IDS, NODE_IDS)
    assert any("type" in e for e in errs) and any("status" in e for e in errs)


def test_course_mismatch_fails(lib):
    p = _write(lib, "fastapi-dasar/01-routing-dasar/get.md",
               _fm(course="salah-course"), "\nisi nyata.\n")
    assert any("course" in e for e in vl.validate_file(p, SRC_IDS, NODE_IDS))


def test_captured_but_stub_fails(lib):
    body = "\n# GET route\n\n> `status: outline` — kerangka. Isi lewat note-refine.\n"
    p = _write(lib, "fastapi-dasar/01-routing-dasar/get.md", _fm(), body)
    assert any("stub" in e for e in vl.validate_file(p, SRC_IDS, NODE_IDS))


def test_capture_flips_when_body_present(lib):
    p = _write(lib, "fastapi-dasar/01-routing-dasar/get.md",
               _fm(status="outline"), "\n# GET route\n\nCatatan nyata Bryant.\n")
    assert vl.capture(p, SRC_IDS, NODE_IDS) == []
    import yaml
    fm = yaml.safe_load(p.read_text("utf-8").split("---")[1])
    assert fm["status"] == "captured"


def test_capture_refuses_stub(lib):
    body = "\n# GET route\n\n> `status: outline` — kerangka. Isi lewat note-refine.\n"
    p = _write(lib, "fastapi-dasar/01-routing-dasar/get.md", _fm(status="outline"), body)
    reasons = vl.capture(p, SRC_IDS, NODE_IDS)
    assert reasons and any("stub" in r for r in reasons)
    import yaml
    fm = yaml.safe_load(p.read_text("utf-8").split("---")[1])
    assert fm["status"] == "outline"          # tak berubah


def test_capture_refuses_bad_ref_without_flipping(lib):
    p = _write(lib, "fastapi-dasar/01-routing-dasar/get.md",
               _fm(status="outline", node_ids=["n999_bogus"]),
               "\nCatatan nyata.\n")
    assert vl.capture(p, SRC_IDS, NODE_IDS)   # ditolak
    import yaml
    fm = yaml.safe_load(p.read_text("utf-8").split("---")[1])
    assert fm["status"] == "outline"


def test_capture_missing_file_is_clean_error(lib):
    reasons = vl.capture(lib / "tak-ada.md", SRC_IDS, NODE_IDS)
    assert reasons == ["file tak ditemukan"]


def test_index_captured_is_not_stub(lib):
    # _index bertipe outline/roadmap dikecualikan dari aturan captured-wajib-berisi
    p = _write(lib, "fastapi-dasar/_index.md",
               _fm(module="", type="outline", status="captured"),
               "\n# FastAPI Dasar\n\n## Modul\n- [[01-routing-dasar/_index|01 · Routing]]\n")
    assert vl.validate_file(p, SRC_IDS, NODE_IDS) == []
