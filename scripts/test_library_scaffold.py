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


# ---------- L3: kind: roadmap (gerbang TULIS + templat peta) ----------

SNAPSHOT = ("---\nsource_ref_id: demo_docs\n---\n\n"
            "The simplest FastAPI file could look like this, with one decorator.\n")
QUOTE = "The simplest FastAPI file could look like this"


def _roadmap_spec(**mat_over):
    mat = {"slug": "get-route", "title": "GET route JSON",
           "source_ref": "demo_docs", "quote": QUOTE,
           "reproduce": "tulis route GET / yang mengembalikan JSON 200",
           "candidate_node": "get-route-json"}
    mat.update(mat_over)
    return {"course": {"slug": "fastapi-produksi", "title": "FastAPI Produksi",
                       "source": "roadmap generate (L3)", "kind": "roadmap",
                       "goal": "bisa men-deploy API CRUD kecil",
                       "baseline": "Python dasar oke", "cut_list": ["websockets"]},
            "modules": [{"slug": "routing-dasar", "title": "Routing dasar",
                         "materials": [mat]}]}


@pytest.fixture
def snaps(tmp_path, monkeypatch):
    d = tmp_path / "data" / "sources"
    d.mkdir(parents=True)
    (d / "demo_docs.md").write_text(SNAPSHOT, encoding="utf-8")
    monkeypatch.setattr(ls, "_SNAPSHOT_DIR", d)
    monkeypatch.setattr(ls, "load_source_ids", lambda: {"demo_docs"})
    return d


def test_roadmap_menghasilkan_peta_bersitasi(lib, snaps):
    course = ls.parse_spec(_roadmap_spec())
    assert ls.check_grounding(course) == []
    ls.scaffold(course, "2026-09-05")
    peta = (lib / "fastapi-produksi/01-routing-dasar/_index.md").read_text("utf-8")
    assert "type: roadmap" in peta
    assert f'> "{QUOTE}"' in peta
    assert "Kandidat node:" in peta
    stub = (lib / "fastapi-produksi/01-routing-dasar/get-route.md").read_text("utf-8")
    assert "type: note" in stub and "status: outline" in stub
    assert "demo_docs" in stub and "kerangka" in stub      # sentinel L1 dipertahankan
    assert QUOTE not in stub                                # kutipan hanya di peta


def test_roadmap_course_index_memuat_tujuan_dan_cut_list(lib, snaps):
    ls.scaffold(ls.parse_spec(_roadmap_spec()), "2026-09-05")
    idx = (lib / "fastapi-produksi/_index.md").read_text("utf-8")
    assert "type: roadmap" in idx
    assert "**Tujuan:** bisa men-deploy API CRUD kecil" in idx
    assert "websockets" in idx
    assert "/placement" in idx          # baseline TIDAK diklaim sebagai mastery


def test_roadmap_tanpa_goal_ditolak(lib, snaps):
    spec = _roadmap_spec()
    spec["course"]["goal"] = ""
    with pytest.raises(ls.SpecError):
        ls.parse_spec(spec)


def test_roadmap_tanpa_quote_ditolak(lib, snaps):
    with pytest.raises(ls.SpecError):
        ls.parse_spec(_roadmap_spec(quote=""))


def test_roadmap_quote_terlalu_pendek_ditolak(lib, snaps):
    with pytest.raises(ls.SpecError):
        ls.parse_spec(_roadmap_spec(quote="FastAPI file"))


def test_roadmap_reproduce_kepanjangan_ditolak(lib, snaps):
    with pytest.raises(ls.SpecError):
        ls.parse_spec(_roadmap_spec(reproduce="x" * 201))


def test_roadmap_blok_kode_di_spec_ditolak(lib, snaps):
    with pytest.raises(ls.SpecError):
        ls.parse_spec(_roadmap_spec(reproduce="tulis ```python app=FastAPI()```"))


def test_roadmap_candidate_node_bukan_kebab_case_ditolak(lib, snaps):
    with pytest.raises(ls.SpecError):
        ls.parse_spec(_roadmap_spec(candidate_node="n002_get_json_route"))


def test_grounding_menolak_kutipan_yang_tak_ada_di_snapshot(lib, snaps):
    course = ls.parse_spec(_roadmap_spec(
        quote="FastAPI otomatis membuat migrasi database untukmu"))
    assert any("TIDAK ada di snapshot" in p for p in ls.check_grounding(course))


def test_grounding_menolak_sumber_tanpa_snapshot(lib, snaps, monkeypatch):
    monkeypatch.setattr(ls, "load_source_ids", lambda: {"demo_docs", "lain"})
    course = ls.parse_spec(_roadmap_spec(source_ref="lain"))
    assert any("belum di-snapshot" in p for p in ls.check_grounding(course))


def test_grounding_menolak_source_ref_tak_terdaftar(lib, snaps):
    course = ls.parse_spec(_roadmap_spec(source_ref="karangan_docs"))
    assert any("tak ada di sources.yaml" in p for p in ls.check_grounding(course))


def test_jalur_L1_tak_berubah(lib):
    """Regresi: spec tanpa `kind` tetap menghasilkan course biasa (type: outline)."""
    spec = {"course": {"slug": "c", "title": "C", "source": "x"},
            "modules": [{"slug": "m", "title": "M",
                         "materials": [{"slug": "a", "title": "A"}]}]}
    course = ls.parse_spec(spec)
    assert course.kind == "course" and ls.check_grounding(course) == []
    ls.scaffold(course, "2026-09-05")
    assert "type: outline" in (lib / "c/01-m/_index.md").read_text("utf-8")
