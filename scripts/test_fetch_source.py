import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
import fetch_source as fs  # noqa: E402

ENTRY = {"id": "demo_docs", "type": "official_docs", "citation": "Demo",
         "url_or_locator": "https://example.test/demo"}
BOOK = {"id": "demo_buku", "type": "textbook_toc", "citation": "Buku",
        "url_or_locator": "textbook:demo/toc"}
LONG = "Kalimat sumber yang cukup panjang untuk lolos ambang minimum. " * 20


class Args:
    """Pengganti argparse.Namespace supaya test tak perlu mem-parse CLI."""

    def __init__(self, **over):
        self.id, self.all, self.from_file = "demo_docs", False, None
        self.force = self.dry_run = False
        self.__dict__.update(over)


@pytest.fixture
def snap(tmp_path, monkeypatch):
    d = tmp_path / "data" / "sources"
    monkeypatch.setattr(fs, "_SNAPSHOT_DIR", d)
    monkeypatch.setattr(fs, "load_registry", lambda: {"demo_docs": ENTRY,
                                                      "demo_buku": BOOK})
    return d


def test_html_to_text_buang_script_style_dan_rapikan(snap):
    html = ("<html><head><style>p{color:red}</style></head>"
            "<body><p>Halo dunia</p><script>x=1</script><p>Baris dua</p></body></html>")
    out = fs.html_to_text(html)
    assert "Halo dunia" in out and "Baris dua" in out
    assert "color:red" not in out and "x=1" not in out


def test_fetch_menulis_snapshot_dengan_provenance_fetch(snap, monkeypatch):
    monkeypatch.setattr(fs, "fetch_url", lambda url: LONG)
    status, _ = fs.snapshot_one("demo_docs", ENTRY, Args(), "2026-09-05T00:00:00+00:00")
    assert status == "created"
    text = (snap / "demo_docs.md").read_text("utf-8")
    assert "provenance: fetch" in text and "source_ref_id: demo_docs" in text
    assert LONG.strip()[:40] in text


def test_skip_bila_snapshot_sudah_ada(snap, monkeypatch):
    monkeypatch.setattr(fs, "fetch_url", lambda url: LONG)
    fs.snapshot_one("demo_docs", ENTRY, Args(), "t")
    status, msg = fs.snapshot_one("demo_docs", ENTRY, Args(), "t")
    assert status == "skipped" and "--force" in msg


def test_force_menimpa(snap, monkeypatch):
    monkeypatch.setattr(fs, "fetch_url", lambda url: LONG)
    fs.snapshot_one("demo_docs", ENTRY, Args(), "t")
    monkeypatch.setattr(fs, "fetch_url", lambda url: LONG + "TAMBAHAN")
    status, _ = fs.snapshot_one("demo_docs", ENTRY, Args(force=True), "t")
    assert status == "created"
    assert "TAMBAHAN" in (snap / "demo_docs.md").read_text("utf-8")


def test_hasil_terlalu_pendek_ditolak(snap, monkeypatch):
    monkeypatch.setattr(fs, "fetch_url", lambda url: "dinding JS")
    status, msg = fs.snapshot_one("demo_docs", ENTRY, Args(), "t")
    assert status == "failed" and "JavaScript" in msg
    assert not (snap / "demo_docs.md").exists()


def test_locator_bukan_url_minta_from_file(snap):
    status, msg = fs.snapshot_one("demo_buku", BOOK, Args(id="demo_buku"), "t")
    assert status == "failed" and "--from-file" in msg


def test_from_file_ditandai_provenance_manual(snap, tmp_path):
    src = tmp_path / "bab3.txt"
    src.write_text(LONG, encoding="utf-8")
    status, _ = fs.snapshot_one("demo_buku", BOOK,
                                Args(id="demo_buku", from_file=src), "t")
    assert status == "created"
    assert "provenance: manual" in (snap / "demo_buku.md").read_text("utf-8")


def test_id_tak_dikenal_exit_2(snap):
    assert fs.main(["--id", "tak_ada"]) == 2


def test_dry_run_tak_menulis(snap, monkeypatch):
    monkeypatch.setattr(fs, "fetch_url", lambda url: LONG)
    status, _ = fs.snapshot_one("demo_docs", ENTRY, Args(dry_run=True), "t")
    assert status == "created" and not (snap / "demo_docs.md").exists()
