import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
import library_scaffold as ls

SPEC = {
    "course": {"slug": "fastapi-dasar", "title": "FastAPI Dasar",
               "source": "Dicoding — X (url)"},
    "modules": [
        {"slug": "routing-dasar", "title": "Routing Dasar",
         "materials": [{"slug": "get-route-json", "title": "GET route JSON"}]},
        {"slug": "request-body", "title": "Request Body"},   # tanpa materials
    ],
}


@pytest.fixture
def lib(tmp_path, monkeypatch):
    monkeypatch.setattr(ls, "_REPO_ROOT", tmp_path)
    monkeypatch.setattr(ls, "_LIBRARY_ROOT", tmp_path / "library")
    return tmp_path / "library"


def test_creates_expected_tree(lib):
    _made, skipped = ls.scaffold(ls.parse_spec(SPEC), created="2026-09-04")
    assert (lib / "fastapi-dasar/_index.md").exists()
    assert (lib / "fastapi-dasar/01-routing-dasar/_index.md").exists()
    assert (lib / "fastapi-dasar/01-routing-dasar/get-route-json.md").exists()
    assert (lib / "fastapi-dasar/02-request-body/_index.md").exists()
    # modul tanpa materials: TIDAK ada file materi
    assert list((lib / "fastapi-dasar/02-request-body").glob("*.md")) == [
        lib / "fastapi-dasar/02-request-body/_index.md"]
    assert skipped == []


def test_frontmatter_shape_and_status_rule(lib):
    ls.scaffold(ls.parse_spec(SPEC), created="2026-09-04")
    stub = (lib / "fastapi-dasar/01-routing-dasar/get-route-json.md").read_text("utf-8")
    fm = yaml.safe_load(stub.split("---")[1])
    assert ls._REQUIRED_FM <= set(fm)
    assert fm["type"] == "note" and fm["status"] == "outline"     # stub materi
    assert fm["source_refs"] == [] and fm["node_ids"] == []
    idx = (lib / "fastapi-dasar/01-routing-dasar/_index.md").read_text("utf-8")
    assert yaml.safe_load(idx.split("---")[1])["status"] == "captured"  # _index


def test_create_only_never_overwrites(lib):
    course = ls.parse_spec(SPEC)
    ls.scaffold(course, created="2026-09-04")
    p = lib / "fastapi-dasar/01-routing-dasar/get-route-json.md"
    p.write_text("CATATAN BRYANT — jangan hilang", encoding="utf-8")
    made, skipped = ls.scaffold(course, created="2026-09-04")   # re-run
    assert p.read_text("utf-8") == "CATATAN BRYANT — jangan hilang"
    assert any("get-route-json" in s for s in skipped)
    assert not any("get-route-json" in s for s in made)


def test_nn_reuse_and_append(lib):
    ls.scaffold(ls.parse_spec(SPEC), created="d")
    spec2 = {**SPEC, "modules": SPEC["modules"] + [{"slug": "deps", "title": "Deps"}]}
    ls.scaffold(ls.parse_spec(spec2), created="d")
    assert (lib / "fastapi-dasar/01-routing-dasar").is_dir()
    assert (lib / "fastapi-dasar/02-request-body").is_dir()
    assert (lib / "fastapi-dasar/03-deps").is_dir()   # modul baru → NN berikutnya


@pytest.mark.parametrize("bad", ["../evil", "Routing", "a_b", "", "a/b", "a--"])
def test_rejects_bad_slug(bad):
    spec = {"course": {"slug": bad, "title": "X"},
            "modules": [{"slug": "m", "title": "M"}]}
    with pytest.raises(ls.SpecError):
        ls.parse_spec(spec)


def test_dry_run_writes_nothing(lib):
    made, _skipped = ls.scaffold(ls.parse_spec(SPEC), created="d", dry_run=True)
    assert made and not lib.exists()
