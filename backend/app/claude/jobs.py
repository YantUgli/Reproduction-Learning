"""Orkestrasi job Claude Code: trigger → jalankan → validasi → gate (M5 langkah 2 & 5).

Alur satu job (semuanya di latar, TAK PERNAH memblokir request UI):

    pending  --execute_job()-->  running  --runner-->  artifact di direktori job
                                              |
                       contracts.py (skema) --+--> tak lolos --> failed
                                              |
                       gate otomatis R4 (test hijau di solusi referensi)
                                              |
                                     merah --+--> rejected (tak pernah sampai ke Isyah)
                                              |
                                            ready  --> ANTREAN REVIEW ISYAH

Beda `failed` vs `rejected` disengaja: `failed` = tak berhasil memproduksi artifact
(CLI mati, timeout, format salah); `rejected` = artifact ada tapi tak lolos mutu.
Keduanya sama-sama tak masuk sistem, tapi yang kedua layak dibaca sebagai sinyal
kualitas prompt/model, bukan sinyal infrastruktur.
"""

import json
import re
from pathlib import Path

from sqlmodel import Session, select

from app.claude import contracts
from app.claude.artifacts import Job, JobStatus, Role, new_job, read_job, save_job, set_status
from app.claude.prompts import render
from app.claude.runner import ClaudeRunner, CliClaudeRunner
from app.config import (
    CLAUDE_MAX_RETRIES,
    CLAUDE_TIMEOUT_SECONDS,
    DATA_DIR,
    EXPLANATION_MAX_CHARS,
    REPO_ROOT,
)
from app.executor import Executor, SubprocessExecutor
from app.models import Attempt, ChallengeInstance, Node
from app.services.node_loader import load_sources

#: Timeout gate R4 — ini eksekusi pytest node, bukan panggilan agent.
_GATE_TIMEOUT_SECONDS = 30


class JobError(ValueError):
    """Permintaan job tak bisa dibentuk (node tak ada, konteks kurang, dll)."""


# --------------------------------------------------------------------------- #
# Trigger — membentuk prompt & direktori job. TIDAK memanggil Claude Code.
# --------------------------------------------------------------------------- #
def trigger_r3(session: Session, *, node_id: str, attempt_id: int | None = None) -> Job:
    """Materi just-in-time untuk satu attempt yang GAGAL."""
    node = _node(session, node_id)
    attempt = _failed_attempt(session, node_id, attempt_id)
    instance = (
        session.get(ChallengeInstance, attempt.instance_id) if attempt.instance_id else None
    ) or _first_instance(session, node_id)

    sources = load_sources(DATA_DIR / "sources.yaml")
    known = "\n".join(f"- `{s.id}` — {s.citation}" for s in sources)

    prompt = render(
        "r3_explanation",
        {
            "node_id": node.id,
            "concept": node.concept,
            "signature_contract": instance.signature_contract if instance else "",
            "prompt_md": instance.prompt if instance else "",
            "submitted_code": attempt.submitted_code or "(kosong)",
            "test_output": attempt.test_output or "(tak ada output)",
            "known_sources": known,
            "max_chars": str(EXPLANATION_MAX_CHARS),
        },
    )
    job = new_job(
        Role.r3_explanation,
        request={"node_id": node.id, "attempt_id": attempt.id},
        prompt_version=prompt.version,
    )
    (job.dir / "prompt.md").write_text(prompt.text, encoding="utf-8")
    return job


def trigger_r4(session: Session, *, node_id: str, variant_label: str | None = None) -> Job:
    """Varian soal baru untuk satu node (menutup 'varian menipis', M4)."""
    node = _node(session, node_id)
    instances = _instances(session, node_id)
    if not instances:
        raise JobError(f"node {node_id!r} belum punya satu pun instance untuk dicontoh")
    example = instances[0]
    example_dir = (REPO_ROOT / example.hidden_test_path).parent

    label = variant_label or _next_variant_label([i.variant_label for i in instances])
    probe_id = _next_probe_id(session, node_id)

    prompt = render(
        "r4_challenge",
        {
            "node_id": node.id,
            "concept": node.concept,
            "signature_contract": example.signature_contract,
            "variant_label": label,
            "existing_variants": ", ".join(i.variant_label for i in instances),
            "example_prompt": example.prompt,
            "example_reference": _read_or_empty(example_dir / "reference_solution.py"),
            "example_test": _read_or_empty(example_dir / "hidden_test.py"),
            "probe_id": probe_id,
        },
    )
    job = new_job(
        Role.r4_challenge,
        request={"node_id": node.id, "variant_label": label, "probe_id": probe_id},
        prompt_version=prompt.version,
    )
    (job.dir / "prompt.md").write_text(prompt.text, encoding="utf-8")
    return job


def trigger_r2(session: Session, *, repo_path: str, node_ids: list[str] | None = None) -> Job:
    """Bukti codebase → hipotesis (tak pernah verdict)."""
    path = Path(repo_path)
    if not path.is_dir():
        raise JobError(f"repo_path bukan direktori yang ada: {repo_path}")

    nodes = session.exec(select(Node)).all()
    if node_ids:
        wanted = set(node_ids)
        nodes = [n for n in nodes if n.id in wanted]
    if not nodes:
        raise JobError("tak ada node untuk dianalisis")

    prompt = render(
        "r2_hypotheses",
        {
            "repo_path": str(path),
            "node_list": "\n".join(f"- `{n.id}` · {n.concept}" for n in sorted(nodes, key=_by_id)),
        },
    )
    job = new_job(
        Role.r2_hypotheses,
        request={"repo_path": str(path), "node_ids": [n.id for n in nodes]},
        prompt_version=prompt.version,
    )
    (job.dir / "prompt.md").write_text(prompt.text, encoding="utf-8")
    return job


# --------------------------------------------------------------------------- #
# Eksekusi — dipanggil di latar (BackgroundTasks / thread), bukan dari handler UI.
# --------------------------------------------------------------------------- #
def execute_job(
    job_id: str,
    session: Session,
    *,
    runner: ClaudeRunner | None = None,
    executor: Executor | None = None,
) -> Job:
    job = read_job(job_id)
    if job.status not in (JobStatus.pending.value, JobStatus.failed.value):
        raise JobError(
            f"job {job_id} berstatus {job.status}, hanya pending/failed yang bisa dijalankan"
        )

    runner = runner or CliClaudeRunner(extra_dirs=_extra_dirs_for(job))
    prompt = (job.dir / "prompt.md").read_text(encoding="utf-8")

    last_error = ""
    for _ in range(1 + CLAUDE_MAX_RETRIES):
        job.attempts += 1
        set_status(job, JobStatus.running)

        result = runner.run(job.dir, prompt, CLAUDE_TIMEOUT_SECONDS)
        (job.dir / "stdout.log").write_text(result.stdout, encoding="utf-8")
        (job.dir / "stderr.log").write_text(result.stderr, encoding="utf-8")
        if not result.ok:
            last_error = result.error or "Claude Code gagal tanpa pesan"
            continue

        try:
            summary = _validate(job, session)
        except contracts.ArtifactError as e:
            last_error = str(e)
            continue

        if job.role == Role.r4_challenge.value:
            gate = _gate_r4(job, executor=executor)
            job.gate = gate
            if not gate["passed"]:
                last_error = gate["reason"]
                # Artifact ADA tapi tak lolos mutu → ditolak otomatis, tak ke Isyah.
                save_job(job)
                continue

        job.summary = summary
        job.error = ""
        return set_status(job, JobStatus.ready)

    # Semua percobaan habis.
    gate_failed = job.gate is not None and not job.gate.get("passed", False)
    return set_status(
        job,
        JobStatus.rejected if gate_failed else JobStatus.failed,
        error=last_error,
    )


def _validate(job: Job, session: Session) -> dict:
    """Validasi artifact sesuai peran. Raise ArtifactError bila tak lolos."""
    node_id = job.request.get("node_id", "")

    if job.role == Role.r3_explanation.value:
        artifact = contracts.load_explanation(job.dir, node_id)
        known = {s.id for s in load_sources(DATA_DIR / "sources.yaml")}
        contracts.check_citations_known(artifact, known)
        return {
            "explanation_chars": len(artifact.explanation_md),
            "citations": len(artifact.citations),
            "has_worked_example": bool(artifact.worked_example.strip()),
        }

    if job.role == Role.r4_challenge.value:
        artifact = contracts.load_challenge(job.dir, node_id)
        expected = job.request.get("variant_label")
        if expected and artifact.variant_label != expected:
            raise contracts.ArtifactError(
                f"variant_label {artifact.variant_label!r} != yang diminta {expected!r}"
            )
        return {
            "variant_label": artifact.variant_label,
            "probe_id": artifact.probe.id,
            "probe_options": len(artifact.probe.options),
        }

    artifact = contracts.load_hypotheses(job.dir)
    known_nodes = {n.id for n in session.exec(select(Node)).all()}
    contracts.check_nodes_known(artifact, known_nodes)
    return {
        "hypotheses": len(artifact.hypotheses),
        "nodes": sorted({h.node_id for h in artifact.hypotheses}),
        # Daftar kosong itu sah (lihat contracts.HypothesesArtifact) — catatannya
        # dinaikkan ke ringkasan supaya Isyah tahu KENAPA tanpa membuka artifact.
        "note": artifact.note,
    }


def _gate_r4(job: Job, *, executor: Executor | None = None) -> dict:
    """GATE OTOMATIS (M5 langkah 5): soal buatan AI diuji SEBELUM manusia melihatnya.

    Dua pemeriksaan, keduanya eksekusi kode:
      1. hidden test WAJIB hijau di reference_solution (aturan §10 R4 — sama persis
         dengan gerbang authoring manusia di `scripts/verify_nodes.py`).
      2. hidden test WAJIB merah di starter_code — kalau kerangka sudah lolos,
         tantangannya kosong dan lolosnya tak membuktikan apa pun.
    """
    executor = executor or SubprocessExecutor()
    variant = job.dir / "variant"
    hidden_test = (variant / "hidden_test.py").read_text(encoding="utf-8")
    reference = (variant / "reference_solution.py").read_text(encoding="utf-8")
    starter = (variant / "starter_code.py").read_text(encoding="utf-8")

    ref_run = executor.run(
        files={"solution.py": reference, "test_solution.py": hidden_test},
        test_entry="test_solution.py",
        timeout_seconds=_GATE_TIMEOUT_SECONDS,
    )
    if not ref_run.passed:
        return {
            "passed": False,
            "reason": "hidden test MERAH di reference_solution — ditolak otomatis (§10 R4)",
            "reference_passed": False,
            "starter_passed": None,
            "output": _tail(ref_run.stdout + ref_run.stderr),
        }

    starter_run = executor.run(
        files={"solution.py": starter, "test_solution.py": hidden_test},
        test_entry="test_solution.py",
        timeout_seconds=_GATE_TIMEOUT_SECONDS,
    )
    if starter_run.passed:
        return {
            "passed": False,
            "reason": "starter_code sudah LOLOS hidden test — tantangannya kosong",
            "reference_passed": True,
            "starter_passed": True,
            "output": _tail(starter_run.stdout),
        }

    return {
        "passed": True,
        "reason": "hidden test hijau di reference_solution & merah di starter_code",
        "reference_passed": True,
        "starter_passed": False,
        "output": _tail(ref_run.stdout),
    }


# --------------------------------------------------------------------------- #
# Helper
# --------------------------------------------------------------------------- #
def _by_id(node: Node) -> str:
    return node.id


def _node(session: Session, node_id: str) -> Node:
    node = session.get(Node, node_id)
    if node is None:
        raise JobError(f"node tak ditemukan: {node_id!r}")
    return node


def _instances(session: Session, node_id: str) -> list[ChallengeInstance]:
    rows = session.exec(
        select(ChallengeInstance).where(ChallengeInstance.node_id == node_id)
    ).all()
    return sorted(rows, key=lambda i: i.variant_label)


def _first_instance(session: Session, node_id: str) -> ChallengeInstance | None:
    rows = _instances(session, node_id)
    return rows[0] if rows else None


def _failed_attempt(session: Session, node_id: str, attempt_id: int | None) -> Attempt:
    """R3 hanya masuk akal untuk attempt yang GAGAL (§10: input = attempt gagal)."""
    if attempt_id is not None:
        attempt = session.get(Attempt, attempt_id)
        if attempt is None or attempt.node_id != node_id:
            raise JobError(f"attempt {attempt_id} bukan milik node {node_id!r}")
    else:
        attempt = session.exec(
            select(Attempt)
            .where(Attempt.node_id == node_id, Attempt.result == "fail")
            .order_by(Attempt.id.desc())
        ).first()
        if attempt is None:
            raise JobError(
                f"node {node_id!r} belum punya attempt yang gagal — materi just-in-time "
                "hanya dibuat untuk kegagalan nyata, bukan untuk dibaca lebih dulu"
            )
    if attempt.result != "fail":
        raise JobError(f"attempt {attempt.id} tidak gagal — R3 hanya untuk attempt gagal")
    return attempt


def _next_variant_label(existing: list[str]) -> str:
    used = set(existing)
    for letter in "abcdefghijklmnopqrstuvwxyz":
        label = f"variant_{letter}"
        if label not in used:
            return label
    return f"variant_{len(used) + 1}"


def _next_probe_id(session: Session, node_id: str) -> str:
    """Ikuti konvensi tulisan tangan: `n006_probe_02`, bukan nama node penuh."""
    from app.models import ComprehensionProbe

    count = len(
        session.exec(
            select(ComprehensionProbe).where(ComprehensionProbe.node_id == node_id)
        ).all()
    )
    match = re.match(r"^(n\d+)", node_id)
    prefix = match.group(1) if match else node_id
    return f"{prefix}_probe_{count + 1:02d}"


def _read_or_empty(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _extra_dirs_for(job: Job) -> tuple[str, ...]:
    """R2 perlu MEMBACA repo Bryant; peran lain tak butuh akses di luar job dir."""
    repo_path = job.request.get("repo_path")
    return (repo_path,) if job.role == Role.r2_hypotheses.value and repo_path else ()


def _tail(text: str, lines: int = 20) -> str:
    return "\n".join(text.strip().splitlines()[-lines:])


def job_artifact_files(job: Job) -> dict[str, str]:
    """Isi artifact untuk ditampilkan di UI review (teks apa adanya)."""
    out: dict[str, str] = {}
    for path in sorted(job.dir.rglob("*")):
        if not path.is_file() or path.name in {
            "job.json",
            "stdout.log",
            "stderr.log",
            "command.log",
        }:
            continue
        rel = path.relative_to(job.dir).as_posix()
        try:
            out[rel] = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            out[rel] = "(berkas biner — tak ditampilkan)"
    return out


def write_artifact_files(job: Job, files: dict[str, str]) -> None:
    """Dipakai test & mode offline: menaruh artifact seolah Claude Code yang menulis."""
    for rel, content in files.items():
        target = job.dir / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")


def dump_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
