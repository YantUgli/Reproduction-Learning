"""Test gate M5: TAK ADA artifact yang masuk sistem tanpa lolos semua lapis.

Lapisnya: skema (contracts) → gate otomatis R4 (eksekusi test) → APPROVE ISYAH.

Yang dibuktikan di sini:
- Job `ready` sekalipun **belum** menyentuh `data/` atau DB — approve-lah yang menulis.
- Soal R4 yang hidden test-nya merah di solusi referensi ditolak OTOMATIS, tak pernah
  sampai ke antrean manusia.
- Hipotesis R2 masuk `unverified` dan HANYA Attempt yang mengubahnya; ia tak pernah
  menggerakkan status/jadwal node.
- Claude Code mati/hilang → job `failed` dengan pesan yang bisa ditindak, loop inti
  (submit attempt) tetap jalan.

Semua memakai salinan `data/` di tmp_path + runner palsu — tak pernah memanggil CLI
sungguhan dan tak pernah menyentuh repo.
"""

import json
import shutil
from dataclasses import dataclass
from pathlib import Path

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from app.claude import artifacts, jobs, review_queue
from app.claude.artifacts import JobStatus, read_job
from app.claude.runner import CliClaudeRunner, RunResult
from app.config import DATA_DIR
from app.models import (
    Attempt,
    ChallengeInstance,
    ComprehensionProbe,
    HypothesisStatus,
    ScheduleItem,
    SkillHypothesis,
)
from app.services.attempt_service import submit_attempt
from app.services.node_loader import load_domain_into_db
from app.services.scaffold import pick_probe

NODE = "n002_get_json_route"

GOOD_REFERENCE = (
    "from fastapi import FastAPI\n\napp = FastAPI()\n\n\n"
    '@app.get("/health")\ndef read_health():\n    return {"service": "billing", "ok": True}\n'
)
GOOD_TEST = (
    "from fastapi.testclient import TestClient\n"
    "from solution import app\n\n"
    "client = TestClient(app)\n\n\n"
    "def test_status_code_200():\n"
    '    assert client.get("/health").status_code == 200\n\n\n'
    "def test_body_exact():\n"
    '    assert client.get("/health").json() == {"service": "billing", "ok": True}\n'
)
STARTER = "from fastapi import FastAPI\n\napp = FastAPI()\n\n# TODO: route GET sesuai prompt.\n"
PROBE = {
    "id": "n002_probe_02",
    "node_id": NODE,
    "type": "predict_output",
    "question": "GET /health mengembalikan status berapa?",
    "options": ["404", "200"],
    "correct_answer": "200",
}

CORRECT_N002 = (
    "from fastapi import FastAPI\n\napp = FastAPI()\n\n\n"
    '@app.get("/status")\ndef read_status():\n    return {"service": "orders", "ok": True}\n'
)


# --------------------------------------------------------------------------- #
# Perkakas test
# --------------------------------------------------------------------------- #
@dataclass
class Env:
    session: Session
    data_dir: Path

    def node_dir(self, node_id: str = NODE) -> Path:
        return self.data_dir / "domains" / "fastapi" / "nodes" / node_id


class FakeRunner:
    """Meniru Claude Code: menulis file ke direktori job, lalu selesai."""

    def __init__(self, files: dict[str, str] | None = None, ok: bool = True, error: str = ""):
        self.files = files or {}
        self.ok = ok
        self.error = error
        self.calls = 0

    def run(self, job_dir: Path, prompt: str, timeout_seconds: int) -> RunResult:
        self.calls += 1
        for rel, content in self.files.items():
            target = job_dir / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        return RunResult(
            ok=self.ok,
            stdout="{}",
            stderr="",
            exit_code=0 if self.ok else 1,
            timed_out=False,
            duration_seconds=0.1,
            error=self.error,
        )


@pytest.fixture()
def env(tmp_path, monkeypatch) -> Env:
    data_dir = tmp_path / "data"
    shutil.copytree(DATA_DIR, data_dir)
    monkeypatch.setattr(review_queue, "DATA_DIR", data_dir)
    monkeypatch.setattr(artifacts, "ARTIFACTS_DIR", tmp_path / "artifacts")

    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        load_domain_into_db(s, data_dir / "domains" / "fastapi", data_dir=data_dir)
        yield Env(session=s, data_dir=data_dir)


def r4_files(*, reference: str = GOOD_REFERENCE, starter: str = STARTER, probe=None) -> dict:
    return {
        "meta.json": json.dumps({"variant_label": "variant_c"}),
        "probe.yaml": json.dumps(probe or PROBE),
        "variant/prompt.md": "# Varian C\n\nBuat `GET /health`.\n",
        "variant/starter_code.py": starter,
        "variant/reference_solution.py": reference,
        "variant/hidden_test.py": GOOD_TEST,
    }


def r3_files() -> dict:
    return {
        "explanation.md": "Handler wajib mengembalikan dict agar FastAPI menyerialisasinya.",
        "worked_example.py": "# contoh beranotasi\n",
        "citations.json": json.dumps(
            {
                "citations": [
                    {
                        "source_ref_id": "fastapi_docs_first_steps",
                        "locator": "First Steps",
                        "claim": "route dideklarasikan lewat dekorator",
                    }
                ]
            }
        ),
    }


def r2_files(node_id: str = NODE, confidence: float = 0.8) -> dict:
    return {
        "hypotheses.json": json.dumps(
            {
                "hypotheses": [
                    {
                        "node_id": node_id,
                        "confidence": confidence,
                        "rationale": "repo memakai route GET yang mengembalikan dict",
                        "evidence_locator": "app/routers/nodes.py:54",
                    }
                ]
            }
        )
    }


def _fail_once(env: Env) -> Attempt:
    """Satu attempt GAGAL — prasyarat R3 (materi hanya untuk kegagalan nyata)."""
    instance = env.session.exec(
        select(ChallengeInstance).where(ChallengeInstance.node_id == NODE)
    ).first()
    res = submit_attempt(
        env.session,
        node_id=NODE,
        instance_id=instance.id,
        scaffold_level="L0",
        submitted_code="app = None\n",
        duration_seconds=10,
    )
    assert res.attempt.result == "fail"
    return res.attempt


# --------------------------------------------------------------------------- #
# R4 — gate otomatis + approve
# --------------------------------------------------------------------------- #
def test_ready_job_has_not_touched_system(env: Env):
    job = jobs.trigger_r4(env.session, node_id=NODE)
    before = len(env.session.exec(select(ChallengeInstance)).all())

    done = jobs.execute_job(job.id, env.session, runner=FakeRunner(r4_files()))

    assert done.status == JobStatus.ready.value
    assert done.gate["passed"] is True
    # Belum ada apa pun yang masuk sistem — approve-lah yang menulis.
    assert not (env.node_dir() / "instances" / "variant_c").exists()
    assert len(env.session.exec(select(ChallengeInstance)).all()) == before


def test_approve_promotes_variant_and_probe(env: Env):
    job = jobs.trigger_r4(env.session, node_id=NODE)
    jobs.execute_job(job.id, env.session, runner=FakeRunner(r4_files()))

    promotion = review_queue.approve(env.session, job.id)

    variant_dir = env.node_dir() / "instances" / "variant_c"
    assert (variant_dir / "hidden_test.py").exists()
    assert (env.node_dir() / "probes" / "n002_probe_02.yaml").exists()
    assert promotion.db_effect["variant_label"] == "variant_c"
    assert env.session.get(ChallengeInstance, f"{NODE}__variant_c") is not None
    assert env.session.get(ComprehensionProbe, "n002_probe_02") is not None
    assert read_job(job.id).status == JobStatus.approved.value


def test_red_hidden_test_is_auto_rejected_before_human(env: Env):
    """Aturan §10 R4 ditegakkan mesin: test merah di solusi referensi = ditolak."""
    broken_reference = (
        "from fastapi import FastAPI\n\napp = FastAPI()\n\n\n"
        '@app.get("/health")\ndef read_health():\n    return {"service": "salah"}\n'
    )
    job = jobs.trigger_r4(env.session, node_id=NODE)

    done = jobs.execute_job(
        job.id, env.session, runner=FakeRunner(r4_files(reference=broken_reference))
    )

    assert done.status == JobStatus.rejected.value
    assert done.gate["passed"] is False
    assert "MERAH" in done.gate["reason"]
    assert not (env.node_dir() / "instances" / "variant_c").exists()


def test_starter_that_already_passes_is_rejected(env: Env):
    """Kerangka yang sudah lolos = tantangan kosong; lolosnya tak membuktikan apa pun."""
    job = jobs.trigger_r4(env.session, node_id=NODE)

    done = jobs.execute_job(
        job.id, env.session, runner=FakeRunner(r4_files(starter=GOOD_REFERENCE))
    )

    assert done.status == JobStatus.rejected.value
    assert "starter_code" in done.gate["reason"]


def test_contract_violation_never_reaches_review(env: Env):
    bad_probe = {**PROBE, "correct_answer": "500"}
    job = jobs.trigger_r4(env.session, node_id=NODE)

    done = jobs.execute_job(job.id, env.session, runner=FakeRunner(r4_files(probe=bad_probe)))

    assert done.status == JobStatus.failed.value
    assert "correct_answer" in done.error


@pytest.mark.parametrize("status", ["pending", "failed", "rejected"])
def test_approve_refuses_job_that_is_not_ready(env: Env, status: str):
    job = jobs.trigger_r4(env.session, node_id=NODE)
    artifacts.set_status(job, JobStatus(status), error="x")

    with pytest.raises(review_queue.PromotionError, match="ready"):
        review_queue.approve(env.session, job.id)


def test_second_probe_becomes_reachable_after_promotion(env: Env):
    """Kalau probe kedua tak pernah tampil, output R4 jadi konten mati — makanya
    pemilihan probe bergilir."""
    job = jobs.trigger_r4(env.session, node_id=NODE)
    jobs.execute_job(job.id, env.session, runner=FakeRunner(r4_files()))
    review_queue.approve(env.session, job.id)

    seen = set()
    for _ in range(4):
        probe = pick_probe(env.session, NODE)
        seen.add(probe.id)
        env.session.add(Attempt(node_id=NODE, mode="review", result="pass"))
        env.session.commit()

    assert seen == {"n002_probe_01", "n002_probe_02"}


# --------------------------------------------------------------------------- #
# R3 — materi just-in-time
# --------------------------------------------------------------------------- #
def test_r3_requires_a_real_failure(env: Env):
    with pytest.raises(jobs.JobError, match="gagal"):
        jobs.trigger_r3(env.session, node_id=NODE)


def test_r3_approve_writes_explanation_with_sources(env: Env):
    _fail_once(env)
    job = jobs.trigger_r3(env.session, node_id=NODE)
    done = jobs.execute_job(job.id, env.session, runner=FakeRunner(r3_files()))
    assert done.status == JobStatus.ready.value
    assert not (env.node_dir() / "explanation.md").exists()  # belum, sebelum approve

    review_queue.approve(env.session, job.id)

    text = (env.node_dir() / "explanation.md").read_text(encoding="utf-8")
    assert "## Sumber" in text
    assert "fastapi_docs_first_steps" in text
    assert (env.node_dir() / "worked_example.py").exists()


def test_r3_with_unverifiable_citation_is_rejected(env: Env):
    _fail_once(env)
    files = r3_files()
    files["citations.json"] = json.dumps(
        {"citations": [{"source_ref_id": "sumber_karangan", "locator": "", "claim": "x"}]}
    )
    job = jobs.trigger_r3(env.session, node_id=NODE)

    done = jobs.execute_job(job.id, env.session, runner=FakeRunner(files))

    assert done.status == JobStatus.failed.value
    assert "sources.yaml" in done.error


# --------------------------------------------------------------------------- #
# R2 — hipotesis TIDAK PERNAH jadi verdict
# --------------------------------------------------------------------------- #
def test_r2_hypotheses_enter_unverified_and_do_not_move_status(env: Env):
    job = jobs.trigger_r2(env.session, repo_path=str(env.data_dir), node_ids=[NODE])
    jobs.execute_job(job.id, env.session, runner=FakeRunner(r2_files(confidence=0.99)))

    assert env.session.exec(select(SkillHypothesis)).all() == []  # belum di-approve

    review_queue.approve(env.session, job.id)

    rows = env.session.exec(select(SkillHypothesis)).all()
    assert [r.status for r in rows] == [HypothesisStatus.unverified.value]
    # Confidence 0.99 sekalipun tak menggerakkan status node satu milimeter.
    item = env.session.get(ScheduleItem, NODE)
    assert item is None or item.status in ("locked", "available")


def test_only_execution_confirms_or_refutes_hypothesis(env: Env):
    job = jobs.trigger_r2(env.session, repo_path=str(env.data_dir), node_ids=[NODE])
    jobs.execute_job(job.id, env.session, runner=FakeRunner(r2_files()))
    review_queue.approve(env.session, job.id)

    verify = env.session.exec(
        select(ChallengeInstance).where(ChallengeInstance.node_id == NODE)
    ).first()
    submit_attempt(
        env.session,
        node_id=NODE,
        instance_id=verify.id,
        scaffold_level="L0",
        submitted_code=CORRECT_N002,
        duration_seconds=30,
    )
    rows = env.session.exec(select(SkillHypothesis)).all()
    assert rows[0].status == HypothesisStatus.confirmed_by_attempt.value

    # Hipotesis baru + attempt gagal → dibantah.
    job2 = jobs.trigger_r2(env.session, repo_path=str(env.data_dir), node_ids=[NODE])
    jobs.execute_job(job2.id, env.session, runner=FakeRunner(r2_files()))
    review_queue.approve(env.session, job2.id)
    submit_attempt(
        env.session,
        node_id=NODE,
        instance_id=verify.id,
        scaffold_level="L0",
        submitted_code="app = None\n",
        duration_seconds=5,
    )
    fresh = [r for r in env.session.exec(select(SkillHypothesis)).all() if r.id == 2]
    assert fresh[0].status == HypothesisStatus.refuted_by_attempt.value


def test_scaffolded_practice_is_not_evidence(env: Env):
    """Attempt `acquisition` (scaffold masih di layar) tak boleh mengonfirmasi apa pun."""
    job = jobs.trigger_r2(env.session, repo_path=str(env.data_dir), node_ids=[NODE])
    jobs.execute_job(job.id, env.session, runner=FakeRunner(r2_files()))
    review_queue.approve(env.session, job.id)

    teaching = env.session.exec(
        select(ChallengeInstance).where(ChallengeInstance.node_id == NODE)
    ).first()
    submit_attempt(
        env.session,
        node_id=NODE,
        instance_id=teaching.id,
        scaffold_level="L2",  # → mode acquisition
        submitted_code=CORRECT_N002,
        duration_seconds=30,
    )

    rows = env.session.exec(select(SkillHypothesis)).all()
    assert rows[0].status == HypothesisStatus.unverified.value


# --------------------------------------------------------------------------- #
# Kegagalan integrasi tak boleh menjatuhkan loop inti (RISK-3)
# --------------------------------------------------------------------------- #
def test_missing_cli_fails_job_without_breaking_loop(env: Env):
    job = jobs.trigger_r4(env.session, node_id=NODE)
    runner = CliClaudeRunner(cli_path="claude-yang-tak-ada-di-mana-mana")

    done = jobs.execute_job(job.id, env.session, runner=runner)

    assert done.status == JobStatus.failed.value
    assert "CLI tak ditemukan" in done.error
    # Loop inti tetap hidup setelah integrasi gagal.
    verify = env.session.exec(
        select(ChallengeInstance).where(ChallengeInstance.node_id == NODE)
    ).first()
    res = submit_attempt(
        env.session,
        node_id=NODE,
        instance_id=verify.id,
        scaffold_level="L0",
        submitted_code=CORRECT_N002,
        duration_seconds=30,
    )
    assert res.attempt.result == "pass"


def test_failed_job_is_retriable_and_retries_are_bounded(env: Env):
    from app.config import CLAUDE_MAX_RETRIES

    job = jobs.trigger_r4(env.session, node_id=NODE)
    runner = FakeRunner({}, ok=False, error="CLI mati")

    done = jobs.execute_job(job.id, env.session, runner=runner)

    assert done.status == JobStatus.failed.value
    assert runner.calls == 1 + CLAUDE_MAX_RETRIES  # retry terbatas, bukan tak terhingga


def test_kill_switch_blocks_triggers_but_not_the_loop(env: Env, monkeypatch):
    from fastapi import BackgroundTasks, HTTPException

    from app.routers import authoring

    monkeypatch.setattr(authoring, "CLAUDE_INTEGRATION_ENABLED", False)

    with pytest.raises(HTTPException) as exc:
        authoring.trigger_r4(
            authoring.TriggerR4In(node_id=NODE), BackgroundTasks(), session=env.session
        )
    assert exc.value.status_code == 503

    verify = env.session.exec(
        select(ChallengeInstance).where(ChallengeInstance.node_id == NODE)
    ).first()
    res = submit_attempt(
        env.session,
        node_id=NODE,
        instance_id=verify.id,
        scaffold_level="L0",
        submitted_code=CORRECT_N002,
        duration_seconds=30,
    )
    assert res.attempt.result == "pass"
