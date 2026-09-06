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


# ---------- L3: gerbang BACA untuk file `type: roadmap` ----------

SNAPSHOT = ("---\nsource_ref_id: fastapi_docs_first_steps\n---\n\n"
            "The simplest FastAPI file could look like this, with one decorator.\n")
QUOTE = "The simplest FastAPI file could look like this"


@pytest.fixture
def snaps(lib, tmp_path, monkeypatch):
    d = tmp_path / "data" / "sources"
    d.mkdir(parents=True)
    (d / "fastapi_docs_first_steps.md").write_text(SNAPSHOT, encoding="utf-8")
    monkeypatch.setattr(vl, "_SNAPSHOT_DIR", d)
    return d


def _roadmap_fm(**over):
    base = _fm(type="roadmap", source_refs=["fastapi_docs_first_steps"])
    base.update(over)
    return base


def _peta_body(quote=QUOTE, extra=""):
    return (f"\n# Routing dasar\n\n## Peta materi\n\n### [[get|GET route]]\n"
            f"**Reproduksi:** tulis route GET /.\n"
            f"**Sumber:** `fastapi_docs_first_steps`\n> \"{quote}\"\n{extra}")


def test_roadmap_kutipan_cocok_lolos(lib, snaps):
    p = _write(lib, "fastapi-dasar/01-routing-dasar/_index.md",
               _roadmap_fm(), _peta_body())
    assert vl.validate_file(p, SRC_IDS, NODE_IDS) == []


def test_roadmap_kutipan_karangan_ditolak(lib, snaps):
    p = _write(lib, "fastapi-dasar/01-routing-dasar/_index.md", _roadmap_fm(),
               _peta_body(quote="FastAPI otomatis membuat migrasi database untukmu"))
    assert any("TIDAK ada di snapshot" in e
               for e in vl.validate_file(p, SRC_IDS, NODE_IDS))


def test_roadmap_sumber_belum_di_snapshot_ditolak(lib, snaps):
    p = _write(lib, "fastapi-dasar/01-routing-dasar/_index.md",
               _roadmap_fm(source_refs=["fastapi_official_docs"]), _peta_body())
    errs = vl.validate_file(p, SRC_IDS, NODE_IDS)
    assert any("belum di-snapshot" in e for e in errs)


def test_roadmap_blok_kode_ditolak(lib, snaps):
    p = _write(lib, "fastapi-dasar/01-routing-dasar/_index.md", _roadmap_fm(),
               _peta_body(extra="\n```python\napp = FastAPI()\n```\n"))
    assert any("blok kode" in e for e in vl.validate_file(p, SRC_IDS, NODE_IDS))


def test_roadmap_tanpa_source_refs_ditolak(lib, snaps):
    p = _write(lib, "fastapi-dasar/01-routing-dasar/_index.md",
               _roadmap_fm(source_refs=[]), "\n# Peta kosong\n\nsatu baris.\n")
    assert any("minimal satu source_refs" in e
               for e in vl.validate_file(p, SRC_IDS, NODE_IDS))


def test_roadmap_kutipan_terlalu_pendek_ditolak(lib, snaps):
    p = _write(lib, "fastapi-dasar/01-routing-dasar/_index.md", _roadmap_fm(),
               _peta_body(quote="FastAPI file"))
    assert any("terlalu pendek" in e for e in vl.validate_file(p, SRC_IDS, NODE_IDS))


def test_roadmap_prosa_kepanjangan_ditolak(lib, snaps):
    p = _write(lib, "fastapi-dasar/01-routing-dasar/_index.md", _roadmap_fm(),
               _peta_body(extra="\n" + ("penjelasan panjang. " * 200)))
    assert any("sudah jadi bab" in e for e in vl.validate_file(p, SRC_IDS, NODE_IDS))


def test_aturan_roadmap_tak_menyentuh_file_note(lib, snaps):
    """Kutipan di catatan Bryant adalah tulisannya sendiri — bukan klaim generate."""
    p = _write(lib, "fastapi-dasar/01-routing-dasar/get.md", _fm(),
               '\n# GET\n\ncatatanku.\n\n> "kutipan bebas yang tak ada di snapshot"\n')
    assert vl.validate_file(p, SRC_IDS, NODE_IDS) == []


# ---------- L4: jembatan Library -> Forge (--link / --candidates) ----------

def _peta_dengan_kandidat(kandidat="get-route-json", materi="get-route-json"):
    return (f"\n# Routing dasar\n\n## Peta materi\n\n### [[{materi}|GET route]]\n"
            f"**Reproduksi:** tulis route GET /.\n"
            f"**Sumber:** `fastapi_docs_first_steps`\n> \"{QUOTE}\"\n"
            f"**Kandidat node:** `{kandidat}` — belum ditempa (L4).\n")


def test_link_mengisi_node_ids(lib):
    p = _write(lib, "fastapi-dasar/01-routing-dasar/get.md", _fm(), "\nCatatan nyata.\n")
    assert vl.link_node(p, SRC_IDS, NODE_IDS, "n002_get_json_route") == []
    import yaml
    fm = yaml.safe_load(p.read_text("utf-8").split("---")[1])
    assert fm["node_ids"] == ["n002_get_json_route"]


def test_link_menolak_node_yang_tak_ada(lib):
    """Hanya node yang benar-benar lahir & termuat boleh ditautkan."""
    p = _write(lib, "fastapi-dasar/01-routing-dasar/get.md", _fm(), "\nCatatan nyata.\n")
    reasons = vl.link_node(p, SRC_IDS, NODE_IDS, "n999_karangan")
    assert reasons and "tak ada di data/" in reasons[0]
    import yaml
    assert yaml.safe_load(p.read_text("utf-8").split("---")[1])["node_ids"] == []


def test_link_idempoten(lib):
    p = _write(lib, "fastapi-dasar/01-routing-dasar/get.md",
               _fm(node_ids=["n002_get_json_route"]), "\nCatatan nyata.\n")
    sebelum = p.read_text("utf-8")
    assert vl.link_node(p, SRC_IDS, NODE_IDS, "n002_get_json_route") == []
    assert p.read_text("utf-8") == sebelum      # tak ditulis ulang


def test_link_tidak_mengubah_status(lib):
    """Menautkan node BUKAN klaim reproduksi — `status` harus tetap seperti semula."""
    p = _write(lib, "fastapi-dasar/01-routing-dasar/get.md",
               _fm(status="outline"), "\nCatatan nyata.\n")
    assert vl.link_node(p, SRC_IDS, NODE_IDS, "n002_get_json_route") == []
    import yaml
    fm = yaml.safe_load(p.read_text("utf-8").split("---")[1])
    assert fm["status"] == "outline" and fm["node_ids"] == ["n002_get_json_route"]


def test_link_mempertahankan_8_field_beku(lib):
    p = _write(lib, "fastapi-dasar/01-routing-dasar/get.md", _fm(), "\nCatatan nyata.\n")
    vl.link_node(p, SRC_IDS, NODE_IDS, "n002_get_json_route")
    assert vl.validate_file(p, SRC_IDS, NODE_IDS) == []


def test_candidates_menemukan_kandidat_belum_tertaut(lib, snaps):
    _write(lib, "fastapi-dasar/01-routing-dasar/_index.md",
           _fm(type="roadmap", source_refs=["fastapi_docs_first_steps"]),
           _peta_dengan_kandidat())
    _write(lib, "fastapi-dasar/01-routing-dasar/get-route-json.md", _fm(status="outline"),
           "\nCatatan nyata.\n")
    rows = vl.candidates()
    assert len(rows) == 1
    assert rows[0]["kandidat"] == "get-route-json"
    assert rows[0]["node_ids"] == [] and rows[0]["ada"] is True


def test_candidates_melewati_yang_sudah_tertaut(lib, snaps):
    _write(lib, "fastapi-dasar/01-routing-dasar/_index.md",
           _fm(type="roadmap", source_refs=["fastapi_docs_first_steps"]),
           _peta_dengan_kandidat())
    _write(lib, "fastapi-dasar/01-routing-dasar/get-route-json.md",
           _fm(node_ids=["n002_get_json_route"]), "\nCatatan nyata.\n")
    rows = vl.candidates()
    assert rows[0]["node_ids"] == ["n002_get_json_route"]


def test_candidates_melaporkan_materi_yang_berkasnya_tak_ada(lib, snaps):
    """Gotcha #9: entri yang menunjuk berkas hilang dilaporkan APA ADANYA,
    bukan dilewati diam-diam."""
    _write(lib, "fastapi-dasar/01-routing-dasar/_index.md",
           _fm(type="roadmap", source_refs=["fastapi_docs_first_steps"]),
           _peta_dengan_kandidat(materi="tak-ada"))
    rows = vl.candidates()
    assert len(rows) == 1 and rows[0]["ada"] is False


def test_candidates_melewati_file_note(lib, snaps):
    """Kandidat hidup di PETA (`type: roadmap`), bukan di catatan Bryant."""
    _write(lib, "fastapi-dasar/01-routing-dasar/get.md", _fm(), _peta_dengan_kandidat())
    assert vl.candidates() == []
