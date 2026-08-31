"""Test bukti edge (M7 langkah 4).

Yang dibuktikan, termasuk BATASNYA:
- Korroborasi menemukan konstruk jarang yang dipakai bersama hulu & hilir.
- "Tak terkukuhkan" TIDAK diperlakukan sebagai "salah" — dan tak ada temuan di
  modul ini yang blocking. Itu bukan kelalaian: diuji atas kurikulum nyata, versi
  yang memblokir menandai 6-7 dari 14 edge hard dengan alasan yang salah, karena
  konstruk node fondasi terlalu umum untuk lolos filter kejarangan.
- Bukti prediktif DIAM sampai datanya cukup (n=1).
"""

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.config import DATA_DIR
from app.models import Attempt, AttemptMode
from app.services import edge_evidence
from app.services.node_loader import load_domain_into_db


@pytest.fixture()
def session():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        load_domain_into_db(s, DATA_DIR / "domains" / "fastapi")
        yield s


def test_token_umum_tak_pernah_jadi_sidik_jari():
    """Tanpa filter kejarangan setiap edge akan "terbukti", dan gerbangnya tak
    pernah bisa merah."""
    peers = ["def f(): return app.get(1)"] * 10
    jarang = edge_evidence.rare_tokens("def g(): return app.get(2)", peers)

    # Yang dipakai semua node tersaring habis. (`g` — nama fungsi di teks ini —
    # memang jarang, dan itu benar: kejarangan diukur, bukan ditebak.)
    assert not ({"return", "app", "get"} & jarang)


def test_konstruk_jarang_terdeteksi():
    peers = ["def f(): pass"] * 10
    assert "HTTPException" in edge_evidence.rare_tokens("raise HTTPException(404)", peers)


def test_korroborasi_menemukan_konstruk_bersama(session):
    """n005 (pydantic BaseModel) -> n010 (response_model): keduanya memakai
    BaseModel, dan itu jarang di domainnya."""
    findings = {(f.from_node_id, f.to_node_id): f for f in edge_evidence.corroboration(session)}
    f = findings[("n005_post_pydantic_body", "n010_response_model_filter")]
    assert f.kind == "corroborated"
    assert "BaseModel" in f.reason


def test_tak_terkukuhkan_bukan_tuduhan_dan_tak_pernah_memblokir(session):
    findings = edge_evidence.corroboration(session)
    belum = [f for f in findings if f.kind == "uncorroborated"]

    assert belum, "kurikulum nyata memang punya edge yang tak terkukuhkan"
    assert all(not f.blocking for f in findings)
    assert all("BUKAN berarti salah" in f.reason for f in belum)


def test_prediktif_diam_sampai_datanya_cukup(session):
    for _ in range(2):
        session.add(
            Attempt(
                node_id="n003_path_param_404", mode=AttemptMode.verification.value, result="fail"
            )
        )
    session.commit()
    assert edge_evidence.predictive_evidence(session) == []


def test_prediktif_menandai_edge_yang_dibantah_data(session):
    """Hulu tak pernah gagal padahal hilir sering gagal: klaim prasyaratnya tak
    menjelaskan apa pun. Ditandai, tak pernah memblokir."""
    for _ in range(6):
        session.add(
            Attempt(
                node_id="n002_get_json_route", mode=AttemptMode.verification.value, result="pass"
            )
        )
        session.add(
            Attempt(
                node_id="n003_path_param_404", mode=AttemptMode.verification.value, result="fail"
            )
        )
    session.commit()

    findings = edge_evidence.predictive_evidence(session)
    pasangan = {(f.from_node_id, f.to_node_id) for f in findings}
    assert ("n002_get_json_route", "n003_path_param_404") in pasangan
    assert all(not f.blocking for f in findings)
