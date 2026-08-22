"""Test node_loader & node_schema (M2 langkah 6).

Membuktikan:
- Node valid (data/ nyata) termuat utuh & idempoten.
- Node cacat DITOLAK dengan pesan yang bisa ditindaklanjuti (probe & jumlah varian).
"""

import pytest
from pydantic import ValidationError
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from app.config import DATA_DIR
from app.models import ChallengeInstance, ComprehensionProbe, Edge, Node
from app.services.node_loader import (
    NodeValidationError,
    assemble_node,
    load_domain_into_db,
)
from app.services.node_schema import ProbeYaml

FASTAPI_DOMAIN = DATA_DIR / "domains" / "fastapi"

# Node A1 (M2) — fondasi yang tak boleh hilang dari data/. Batch berikutnya (A2+)
# hanya boleh MENAMBAH; karena itu test memakai subset, bukan kesamaan himpunan.
A1_NODE_IDS = {
    "n001_paginate",
    "n002_get_json_route",
    "n003_path_param_404",
    "n004_query_param_default",
    "n005_post_pydantic_body",
}


@pytest.fixture()
def session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


def test_load_real_nodes_full(session: Session):
    report = load_domain_into_db(session, FASTAPI_DOMAIN)

    # Batas BAWAH, bukan jumlah persis: authoring (A2, A3, ...) menambah node terus.
    # Test ini menjaga INVARIAN bentuk (>=2 varian, >=1 probe, pointer test relatif),
    # bukan ukuran kurikulum — angka persis akan usang tiap batch node baru.
    assert report.nodes >= len(A1_NODE_IDS)
    assert report.instances >= 2 * report.nodes  # >=2 varian/node
    assert report.probes >= report.nodes  # >=1 probe/node
    assert report.edges >= 1

    nodes = session.exec(select(Node)).all()
    assert A1_NODE_IDS <= {n.id for n in nodes}
    # Tiap node punya >=2 instance & >=1 probe.
    for n in nodes:
        insts = session.exec(
            select(ChallengeInstance).where(ChallengeInstance.node_id == n.id)
        ).all()
        assert len(insts) >= 2, n.id
        probes = session.exec(
            select(ComprehensionProbe).where(ComprehensionProbe.node_id == n.id)
        ).all()
        assert len(probes) >= 1, n.id

    # hidden_test_path adalah pointer relatif ke data/, bukan isi test.
    inst = session.exec(select(ChallengeInstance)).first()
    assert inst.hidden_test_path.startswith("data/domains/fastapi/nodes/")
    assert inst.hidden_test_path.endswith("hidden_test.py")

    # Edge endpoint valid & bertipe hard/soft.
    for e in session.exec(select(Edge)).all():
        assert e.type in {"hard", "soft"}


def test_load_is_idempotent(session: Session):
    r1 = load_domain_into_db(session, FASTAPI_DOMAIN)
    r2 = load_domain_into_db(session, FASTAPI_DOMAIN)
    assert r1.nodes == r2.nodes
    # Jalan dua kali tak menggandakan baris: jumlah di DB = jumlah SATU muatan.
    assert len(session.exec(select(Node)).all()) == r1.nodes
    assert len(session.exec(select(Edge)).all()) == r1.edges
    assert len(session.exec(select(ChallengeInstance)).all()) == r1.instances


def test_probe_rejects_answer_not_in_options():
    with pytest.raises(ValidationError) as exc:
        ProbeYaml.model_validate(
            {
                "id": "bad_probe",
                "node_id": "n001_paginate",
                "type": "predict_output",
                "question": "?",
                "options": ["200", "404"],
                "correct_answer": "500",  # tidak ada di options
            }
        )
    assert "correct_answer" in str(exc.value)


def test_node_folder_requires_two_variants(tmp_path):
    node_dir = tmp_path / "n999_broken"
    (node_dir).mkdir()
    (node_dir / "node.yaml").write_text(
        "\n".join(
            [
                "id: n999_broken",
                "domain_id: fastapi",
                "concept: broken",
                "grader_type: unit_test",
                "estimated_minutes: 5",
                "timebox_seconds: 300",
                "status_default: locked",
                "scaffold_level: L2",
            ]
        ),
        encoding="utf-8",
    )
    # Hanya satu varian -> harus ditolak dengan pesan soal jumlah varian.
    variant = node_dir / "instances" / "variant_a"
    variant.mkdir(parents=True)
    for f in ("prompt.md", "starter_code.py", "reference_solution.py", "hidden_test.py"):
        (variant / f).write_text("x = 1\n", encoding="utf-8")
    probe = node_dir / "probes"
    probe.mkdir()
    (probe / "probe_01.yaml").write_text(
        "\n".join(
            [
                "id: n999_probe_01",
                "node_id: n999_broken",
                "type: predict_output",
                "question: '?'",
                "options: ['a', 'b']",
                "correct_answer: 'a'",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(NodeValidationError) as exc:
        assemble_node(node_dir)
    assert "varian" in str(exc.value)
