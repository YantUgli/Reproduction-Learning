"""Test telemetri kurikulum (M7 langkah 7).

Yang dibuktikan:
- Node trivia (selalu lolos) & node rusak (tak pernah lolos) tertangkap.
- Attempt BERSCAFFOLD tidak dihitung — kalau dihitung, node trivia justru akan
  tampak sehat, dan telemetri jadi cermin yang memuji.
- Ambang n minimum dipatuhi: dengan satu pelajar, dua attempt bukan pola.
- Telemetri MENANDAI, tak pernah mengubah status/jadwal node apa pun.
"""

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from app.config import DATA_DIR
from app.models import Attempt, AttemptMode, ScheduleItem
from app.services import telemetry
from app.services.node_loader import load_domain_into_db

NODE = "n002_get_json_route"
LAIN = "n003_path_param_404"


@pytest.fixture()
def session():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        load_domain_into_db(s, DATA_DIR / "domains" / "fastapi")
        yield s


def _attempts(session, node_id, results, *, mode=AttemptMode.verification.value, probe=None):
    for hasil in results:
        session.add(
            Attempt(
                node_id=node_id,
                mode=mode,
                result=hasil,
                duration_seconds=60,
                probe_result=probe,
            )
        )
    session.commit()


def _kinds(session, node_id):
    return {s.kind for s in telemetry.signals(session) if s.node_id == node_id}


def test_node_yang_selalu_lolos_ditandai_trivia(session):
    _attempts(session, NODE, ["pass"] * 5)
    assert telemetry.TRIVIA in _kinds(session, NODE)


def test_node_yang_tak_pernah_lolos_ditandai_rusak(session):
    _attempts(session, NODE, ["fail"] * 5)
    assert telemetry.BROKEN in _kinds(session, NODE)


def test_node_sehat_tidak_ditandai(session):
    _attempts(session, NODE, ["fail", "fail", "pass", "pass", "pass"])
    assert _kinds(session, NODE) == set()


def test_attempt_berscaffold_tidak_dihitung(session):
    """Attempt `acquisition` masih menampilkan scaffold di layar. Memasukkannya
    membuat node trivia tampak membedakan sesuatu — persis kebalikan dari gunanya."""
    _attempts(session, NODE, ["pass"] * 8, mode=AttemptMode.acquisition.value)

    assert _kinds(session, NODE) == set()
    assert telemetry.coverage(session)["nodes_with_cold_data"] == 0


def test_di_bawah_ambang_tidak_menyimpulkan_apa_pun(session):
    """n=1: dua kali lolos itu kebetulan, bukan bukti node ini trivia."""
    _attempts(session, NODE, ["pass", "pass"])
    assert _kinds(session, NODE) == set()


def test_probe_yang_selalu_salah_ditandai(session):
    _attempts(session, NODE, ["pass", "fail", "pass", "fail", "pass"], probe="incorrect")
    assert telemetry.DEAD_PROBE in _kinds(session, NODE)


def test_durasi_jauh_di_atas_estimasi_ditandai(session):
    for _ in range(5):
        session.add(
            Attempt(
                node_id=LAIN,
                mode=AttemptMode.verification.value,
                result="pass",
                duration_seconds=60 * 60 * 3,  # 3 jam
            )
        )
    session.commit()
    assert telemetry.MISCALIBRATED in _kinds(session, LAIN)


def test_telemetri_tidak_menyentuh_status_atau_jadwal(session):
    """Batas keras §7 2026-08-31: MENANDAI, bukan memensiunkan. Tak ada node yang
    berubah status hanya karena telemetri melihatnya."""
    _attempts(session, NODE, ["fail"] * 6)
    sebelum = {i.node_id: i.status for i in session.exec(select(ScheduleItem)).all()}

    assert telemetry.signals(session)  # ada temuan

    sesudah = {i.node_id: i.status for i in session.exec(select(ScheduleItem)).all()}
    assert sebelum == sesudah


def test_coverage_jujur_soal_ketiadaan_data(session):
    """ "Tak ada temuan" hampir selalu berarti "belum ada datanya" — dan angkanya
    harus terlihat, kalau tidak diam akan terbaca sebagai sehat."""
    cov = telemetry.coverage(session)
    assert cov["nodes"] > 0
    assert cov["nodes_assessable"] == 0
