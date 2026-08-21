"""Smoke test skema §9: create + query balik SETIAP tabel.

Memvalidasi 10 tabel PRD §9 konsisten dan bisa dibuat di SQLite in-memory.
"""

from datetime import UTC, datetime

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from app.models import (
    Attempt,
    ChallengeInstance,
    ComprehensionProbe,
    Domain,
    Edge,
    Node,
    ScheduleItem,
    SkillHypothesis,
    SourceRef,
)
from app.models import (
    Session as LearningSession,
)


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


def test_all_ten_tables_created(session: Session):
    # Semua 10 tabel §9 harus ter-register di metadata.
    tables = set(SQLModel.metadata.tables.keys())
    expected = {
        "domain",
        "sourceref",
        "node",
        "edge",
        "challengeinstance",
        "comprehensionprobe",
        "attempt",
        "skillhypothesis",
        "scheduleitem",
        "session",
    }
    assert expected <= tables


def test_create_and_query_each_table(session: Session):
    domain = Domain(id="fastapi", name="FastAPI", status="draft")
    source = SourceRef(
        id="cs2023", type="cs2023_ku", citation="CS2023 KU", url_or_locator="https://example"
    )
    node = Node(
        id="n1",
        domain_id="fastapi",
        concept="path params",
        grader_type="unit_test",
        source_refs=["cs2023"],
        estimated_minutes=30,
        timebox_seconds=1800,
    )
    session.add_all([domain, source, node])
    session.commit()

    edge = Edge(from_node_id="n1", to_node_id="n1", type="hard", source_ref_id="cs2023")
    instance = ChallengeInstance(
        id="ci1",
        node_id="n1",
        variant_label="A",
        prompt="buat endpoint",
        hidden_test_path="data/domains/fastapi/nodes/n1/hidden_test.py",
        scaffold_level="L2",
    )
    probe = ComprehensionProbe(
        id="p1",
        node_id="n1",
        type="predict_output",
        question="apa output?",
        options=["a", "b"],
        correct_answer="a",
    )
    attempt = Attempt(
        node_id="n1",
        instance_id="ci1",
        mode="verification",
        scaffold_level="L0",
        duration_seconds=120,
        result="pass",
    )
    hypo = SkillHypothesis(node_id="n1", source="codebase", confidence=0.8, status="unverified")
    sched = ScheduleItem(node_id="n1", status="available", review_count=0)
    learning_session = LearningSession(
        started_at=datetime.now(UTC), mode="verification", ai_available=False
    )
    session.add_all([edge, instance, probe, attempt, hypo, sched, learning_session])
    session.commit()

    # Query balik tiap tabel.
    assert session.get(Domain, "fastapi").name == "FastAPI"
    assert session.get(SourceRef, "cs2023").type == "cs2023_ku"
    got_node = session.get(Node, "n1")
    assert got_node.source_refs == ["cs2023"]
    assert session.exec(select(Edge)).first().type == "hard"
    assert session.get(ChallengeInstance, "ci1").scaffold_level == "L2"
    assert session.get(ComprehensionProbe, "p1").options == ["a", "b"]
    assert session.exec(select(Attempt)).first().result == "pass"
    assert session.exec(select(SkillHypothesis)).first().confidence == 0.8
    assert session.get(ScheduleItem, "n1").status == "available"

    # Invariant §2: session verification tidak boleh punya AI.
    got_session = session.exec(select(LearningSession)).first()
    assert got_session.mode == "verification"
    assert got_session.ai_available is False
