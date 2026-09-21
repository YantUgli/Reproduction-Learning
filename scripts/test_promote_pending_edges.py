"""Test Langkah 2 (execution-plan-async-review §3): veto + promosi manual.

Yang dijaga: veto MENANDAI (tak menghapus, `edges.yaml` tak tersentuh), veto ulang
MENIMPA (selalu berhasil), promosi matang menulis `hard` + mempertahankan komentar
kurasi + menghapus dari pending, entri belum-matang/diveto TERTAHAN, rollback
byte-identik saat reparse gagal, dan idempotensi.
"""

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
import promote_pending_edges as ppe

CURATED_EDGES = (
    "# Edge prasyarat — difinalkan Isyah 2026-08-22.\n"
    "edges:\n"
    "  - from: n001_paginate\n"
    "    to: n002_get_json_route\n"
    "    type: hard\n"
)


def _entry(*, from_id: str = "n004_query_param_default", to_id: str = "n014_cookie_param",
           **overrides) -> dict:
    base = {
        "from": from_id,
        "to": to_id,
        "type": "hard",
        "source_ref_id": "fastapi_docs_cookie_params",
        "library_file": "library/fastapi-produksi/01-parameter-request/cookie-param.md",
        "job_id": "r4-test-job",
        "queued_at": "2026-09-18T10:43:00+00:00",
        "note": "Usul L4 (AI) — menunggu veto Isyah.",
    }
    base.update(overrides)
    return base


def _dump_pending(entries: list[dict]) -> str:
    return yaml.dump({"edges": entries}, sort_keys=False, allow_unicode=True)


@pytest.fixture
def domain(tmp_path, monkeypatch):
    """Satu domain palsu `fastapi/` dengan `edges.yaml` (komentar kurasi) + pending."""
    domains_dir = tmp_path / "domains"
    d = domains_dir / "fastapi"
    d.mkdir(parents=True)
    (d / "edges.yaml").write_text(CURATED_EDGES, encoding="utf-8")
    monkeypatch.setattr(ppe, "_DOMAINS_DIR", domains_dir)
    return d


def _iso_days_ago(days: float) -> str:
    return (datetime.now(UTC) - timedelta(days=days)).isoformat()


# --------------------------------------------------------------------------- #
# Veto
# --------------------------------------------------------------------------- #
def test_veto_menandai_tak_menghapus(domain):
    domain.joinpath("edges.pending.yaml").write_text(
        _dump_pending([_entry(queued_at=_iso_days_ago(1))]), encoding="utf-8"
    )
    edges_sebelum = (domain / "edges.yaml").read_text("utf-8")

    hasil = ppe.veto("n004_query_param_default__n014_cookie_param", "prasyarat terlalu longgar")

    assert hasil == "fastapi"
    entries = ppe.load_pending(domain / "edges.pending.yaml")
    assert len(entries) == 1  # tak dihapus
    assert entries[0].vetoed_at is not None
    assert entries[0].veto_reason == "prasyarat terlalu longgar"
    assert (domain / "edges.yaml").read_text("utf-8") == edges_sebelum  # live tak tersentuh


def test_veto_ulang_menimpa(domain):
    domain.joinpath("edges.pending.yaml").write_text(
        _dump_pending([_entry(queued_at=_iso_days_ago(1))]), encoding="utf-8"
    )
    eid = "n004_query_param_default__n014_cookie_param"

    ppe.veto(eid, "alasan pertama")
    ppe.veto(eid, "alasan kedua")
    hasil = ppe.veto(eid, "alasan ketiga")

    assert hasil == "fastapi"
    entries = ppe.load_pending(domain / "edges.pending.yaml")
    assert len(entries) == 1  # tak pernah ganda
    assert entries[0].veto_reason == "alasan ketiga"


def test_veto_tak_ditemukan(domain):
    domain.joinpath("edges.pending.yaml").write_text(
        _dump_pending([_entry(queued_at=_iso_days_ago(1))]), encoding="utf-8"
    )
    assert ppe.veto("tak_ada__di_pending", "x") is None


# --------------------------------------------------------------------------- #
# Promosi
# --------------------------------------------------------------------------- #
def test_promosi_matang_menulis_hard_dan_hapus_pending(domain):
    domain.joinpath("edges.pending.yaml").write_text(
        _dump_pending([_entry(queued_at=_iso_days_ago(8))]), encoding="utf-8"
    )

    report = ppe.promote_matured()

    assert len(report) == 1
    assert report[0]["from"] == "n004_query_param_default"
    raw = (domain / "edges.yaml").read_text("utf-8")
    assert "difinalkan Isyah 2026-08-22" in raw  # komentar kurasi utuh
    blok = raw[raw.rindex("n004_query_param_default") - 200 :]
    assert "type: hard" in blok
    assert ppe.load_pending(domain / "edges.pending.yaml") == []  # hilang dari pending


def test_promosi_menahan_yang_belum_matang(domain):
    domain.joinpath("edges.pending.yaml").write_text(
        _dump_pending([_entry(queued_at=_iso_days_ago(1))]), encoding="utf-8"
    )
    edges_sebelum = (domain / "edges.yaml").read_text("utf-8")

    report = ppe.promote_matured()

    assert report == []
    assert (domain / "edges.yaml").read_text("utf-8") == edges_sebelum
    assert len(ppe.load_pending(domain / "edges.pending.yaml")) == 1


def test_promosi_menahan_yang_diveto(domain):
    domain.joinpath("edges.pending.yaml").write_text(
        _dump_pending(
            [
                _entry(
                    queued_at=_iso_days_ago(8),
                    vetoed_at=_iso_days_ago(1),
                    veto_reason="tak relevan",
                )
            ]
        ),
        encoding="utf-8",
    )
    edges_sebelum = (domain / "edges.yaml").read_text("utf-8")

    report = ppe.promote_matured()

    assert report == []
    assert (domain / "edges.yaml").read_text("utf-8") == edges_sebelum
    assert len(ppe.load_pending(domain / "edges.pending.yaml")) == 1


def test_dry_run_tak_menulis(domain):
    domain.joinpath("edges.pending.yaml").write_text(
        _dump_pending([_entry(queued_at=_iso_days_ago(8))]), encoding="utf-8"
    )
    edges_sebelum = (domain / "edges.yaml").read_text("utf-8")
    pending_sebelum = (domain / "edges.pending.yaml").read_text("utf-8")

    report = ppe.promote_matured(dry_run=True)

    assert len(report) == 1
    assert (domain / "edges.yaml").read_text("utf-8") == edges_sebelum
    assert (domain / "edges.pending.yaml").read_text("utf-8") == pending_sebelum


def test_idempoten(domain):
    domain.joinpath("edges.pending.yaml").write_text(
        _dump_pending([_entry(queued_at=_iso_days_ago(8))]), encoding="utf-8"
    )

    first = ppe.promote_matured()
    second = ppe.promote_matured()

    assert len(first) == 1
    assert second == []  # sudah tak ada lagi yang matang — bukti tak ada duplikat
    raw = (domain / "edges.yaml").read_text("utf-8")
    assert raw.count("n004_query_param_default") == 1


def test_rollback_saat_reparse_gagal(domain):
    """Entri cacat (self-loop) → `load_edges` di dalam `append_edge` melempar →
    KEDUA berkas harus kembali byte-identik dengan semula (KUNCI L4 rollback)."""
    domain.joinpath("edges.pending.yaml").write_text(
        _dump_pending(
            [_entry(from_id="n014_cookie_param", to_id="n014_cookie_param", queued_at=_iso_days_ago(8))]
        ),
        encoding="utf-8",
    )
    edges_sebelum = (domain / "edges.yaml").read_text("utf-8")
    pending_sebelum = (domain / "edges.pending.yaml").read_text("utf-8")

    with pytest.raises(Exception):  # noqa: B017 — self-loop ditolak EdgeYaml
        ppe.promote_matured()

    assert (domain / "edges.yaml").read_text("utf-8") == edges_sebelum
    assert (domain / "edges.pending.yaml").read_text("utf-8") == pending_sebelum


def test_absent_pending_tak_meledak(domain):
    assert ppe.promote_matured() == []
    assert ppe.veto("apapun__apapun", "x") is None
