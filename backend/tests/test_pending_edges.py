"""Test Langkah 1 (execution-plan-async-review §3): reader `edges.pending.yaml`.

Yang dijaga: `edge_id`, tiga keadaan (`menunggu`/`matang`/`diveto`), `matures_at`,
berkas absen = kosong, parse roundtrip, dan — PENJAGA PENGAMAN §1 — bahwa loop
pembelajaran BUTA terhadap `edges.pending.yaml` (edge menunggu tak pernah mengunci Bryant).
"""

import shutil
from datetime import UTC, datetime, timedelta

from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from app.config import DATA_DIR
from app.models import Edge, EdgeType
from app.services import pending_edges as pe
from app.services.node_loader import load_domain_into_db


def _entry(**overrides) -> pe.PendingEdge:
    base = dict(
        from_="n004_query_param_default",
        to="n014_cookie_param",
        type=EdgeType.hard,
        source_ref_id="fastapi_docs_cookie_params",
        library_file="library/fastapi-produksi/01-parameter-request/cookie-param.md",
        job_id="r4-20260916T104348-eb79be",
        queued_at=datetime.now(UTC),
    )
    base.update(overrides)
    return pe.PendingEdge(**base)


def test_edge_id():
    assert pe.edge_id(_entry()) == "n004_query_param_default__n014_cookie_param"


def test_state_menunggu():
    entry = _entry(queued_at=datetime.now(UTC) - timedelta(days=1))
    assert pe.state(entry) == pe.STATE_MENUNGGU


def test_state_matang():
    entry = _entry(queued_at=datetime.now(UTC) - timedelta(days=8))
    assert pe.state(entry) == pe.STATE_MATANG


def test_state_diveto():
    # Umur sudah lewat 7 hari, TAPI sudah diveto → tetap `diveto` (veto menang).
    entry = _entry(
        queued_at=datetime.now(UTC) - timedelta(days=8),
        vetoed_at=datetime.now(UTC) - timedelta(days=1),
        veto_reason="prasyarat terlalu longgar",
    )
    assert pe.state(entry) == pe.STATE_DIVETO


def test_matures_at():
    q = datetime(2026, 9, 18, 10, 43, tzinfo=UTC)
    assert pe.matures_at(_entry(queued_at=q)) == q + timedelta(days=7)


def test_absent_returns_empty(tmp_path):
    assert pe.load_pending(tmp_path / "tak_ada.yaml") == []


def test_parse_roundtrip(tmp_path):
    path = tmp_path / "edges.pending.yaml"
    path.write_text(
        """edges:
  - from: n004_query_param_default
    to: n014_cookie_param
    type: hard
    source_ref_id: fastapi_docs_cookie_params
    library_file: library/fastapi-produksi/01-parameter-request/cookie-param.md
    job_id: r4-20260916T104348-eb79be
    queued_at: 2026-09-18T10:43:00+00:00
    note: "Usul L4 (AI) — menunggu veto."
""",
        encoding="utf-8",
    )
    entries = pe.load_pending(path)
    assert len(entries) == 1
    e = entries[0]
    assert e.from_ == "n004_query_param_default"
    assert e.to == "n014_cookie_param"
    assert e.type == EdgeType.hard
    assert e.job_id == "r4-20260916T104348-eb79be"
    assert e.library_file.endswith("cookie-param.md")
    assert isinstance(e.queued_at, datetime) and e.queued_at.tzinfo is not None
    assert e.vetoed_at is None  # belum diveto
    # State dihitung terhadap `now` terkontrol — deterministik, tak bergantung tanggal
    # jam dinding: 1 hari sesudah queued_at = menunggu; 8 hari sesudah = matang.
    assert pe.state(e, now=e.queued_at + timedelta(days=1)) == pe.STATE_MENUNGGU
    assert pe.state(e, now=e.queued_at + timedelta(days=8)) == pe.STATE_MATANG


def _load_fastapi_edges(domain_dir) -> int:
    """Muat satu domain ke DB in-memory bersih, kembalikan jumlah Edge."""
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        load_domain_into_db(s, domain_dir)
        return len(s.exec(select(Edge)).all())


def test_loop_buta_terhadap_pending(tmp_path):
    """PENGAMAN §1: `edges.pending.yaml` TAK PERNAH masuk loop.

    Salin domain fastapi nyata → tmp, hitung Edge (baseline). Lalu taruh
    `edges.pending.yaml` berisi satu usulan `hard` untuk pasangan node BARU
    (n001->n014, yang tak ada di `edges.yaml`) dan muat lagi ke DB bersih: jumlah Edge
    WAJIB tetap sama. Kalau loop diam-diam membacanya, angkanya akan naik satu.
    """
    src = DATA_DIR / "domains" / "fastapi"
    dst = tmp_path / "fastapi"
    shutil.copytree(src, dst)

    baseline = _load_fastapi_edges(dst)

    (dst / "edges.pending.yaml").write_text(
        """edges:
  - from: n001_paginate
    to: n014_cookie_param
    type: hard
    source_ref_id: fastapi_docs_cookie_params
    library_file: library/fastapi-produksi/01-parameter-request/cookie-param.md
    job_id: r4-test
    queued_at: 2026-09-18T10:43:00+00:00
""",
        encoding="utf-8",
    )

    after = _load_fastapi_edges(dst)
    assert after == baseline, "loop membaca edges.pending.yaml — pengaman §1 bocor"
