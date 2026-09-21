"""Test Langkah 3 (execution-plan-async-review §3): `GET /authoring/audit` membawa
`pending_edges` + `ready_to_promote`.

Dipanggil LANGSUNG (`authoring.audit(session)`), bukan lewat `TestClient` — pola sama
dengan test authoring lain di repo (`test_review_gate`, `test_promote_node`): `TestClient`
membaca `data/` + `app.db` sungguhan, jadi tak bisa menegakkan angka PRESISI. Di sini
`DATA_DIR` di-monkeypatch ke domain palsu berisi `edges.pending.yaml` buatan tangan.

Dua penjaga:
  - state benar (1 matang, 1 menunggu, 1 diveto) + `ready_to_promote == 1`.
  - backend TAK MENULIS: byte + mtime `edges.pending.yaml` identik sebelum/sesudah audit
    (pola `test_membaca_tidak_pernah_menulis` L5).
"""

from datetime import UTC, datetime, timedelta

import pytest
import yaml

from app.routers import authoring


def _entry(*, from_id: str, to_id: str, **overrides) -> dict:
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


def _iso_days_ago(days: float) -> str:
    return (datetime.now(UTC) - timedelta(days=days)).isoformat()


@pytest.fixture
def pending_path(tmp_path, monkeypatch):
    """Domain palsu `fastapi/` dengan `edges.pending.yaml`: 1 matang, 1 menunggu, 1 diveto."""
    d = tmp_path / "domains" / "fastapi"
    d.mkdir(parents=True)
    path = d / "edges.pending.yaml"
    entries = [
        # matang: 8 hari lalu, tak diveto
        _entry(from_id="a1", to_id="b1", queued_at=_iso_days_ago(8)),
        # menunggu: 1 hari lalu
        _entry(from_id="a2", to_id="b2", queued_at=_iso_days_ago(1)),
        # diveto: 8 hari lalu TAPI sudah diveto → tetap diveto (veto menang)
        _entry(
            from_id="a3",
            to_id="b3",
            queued_at=_iso_days_ago(8),
            vetoed_at=_iso_days_ago(1),
            veto_reason="prasyarat terlalu longgar",
        ),
    ]
    path.write_text(yaml.dump({"edges": entries}, sort_keys=False), encoding="utf-8")
    monkeypatch.setattr(authoring, "DATA_DIR", tmp_path)
    return path


def test_audit_pending_state_dan_ready(pending_path, session):
    out = authoring.audit(session)

    assert out.ready_to_promote == 1
    by_pair = {(p.from_node_id, p.to_node_id): p for p in out.pending_edges}
    assert by_pair[("a1", "b1")].state == "matang"
    assert by_pair[("a2", "b2")].state == "menunggu"
    assert by_pair[("a3", "b3")].state == "diveto"
    assert by_pair[("a3", "b3")].veto_reason == "prasyarat terlalu longgar"
    assert by_pair[("a1", "b1")].domain_id == "fastapi"
    # matures_at = queued_at + 7 hari (bukti klok bukan dari mtime berkas).
    p = by_pair[("a1", "b1")]
    assert datetime.fromisoformat(p.matures_at) == datetime.fromisoformat(p.queued_at) + timedelta(
        days=7
    )


def test_audit_tak_menulis_pending(pending_path, session):
    jejak = (pending_path.read_bytes(), pending_path.stat().st_mtime_ns)
    authoring.audit(session)
    assert (pending_path.read_bytes(), pending_path.stat().st_mtime_ns) == jejak
