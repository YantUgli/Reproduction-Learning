"""Orkestrasi Attempt (M3): submit → grade → (probe) → simpan.

INVARIANT:
- Hanya eksekusi kode (grader → Executor) yang menentukan `result` (§2).
- SETIAP attempt disimpan, termasuk gagal & lewat-timebox — itu data sinyal inti
  (`reproduce-without-AI pass rate`, §9 KPI).
- `acquired` di-set HANYA saat L0 (verification) `result=pass` DAN probe benar.
  `mastered` TIDAK diklaim di M3 (butuh FSRS berjarak — M4).
"""

from dataclasses import dataclass

from sqlmodel import Session, select

from app.graders import GradeResult, get_grader
from app.models import (
    Attempt,
    ChallengeInstance,
    ComprehensionProbe,
    Node,
    ScheduleItem,
    ScheduleStatus,
)


@dataclass
class SubmitResult:
    attempt: Attempt
    grade: GradeResult


def ensure_schedule_item(session: Session, node: Node) -> ScheduleItem:
    item = session.get(ScheduleItem, node.id)
    if item is None:
        item = ScheduleItem(node_id=node.id, status=node.status_default)
        session.add(item)
    return item


def submit_attempt(
    session: Session,
    *,
    node_id: str,
    instance_id: str,
    scaffold_level: str,
    submitted_code: str,
    duration_seconds: int,
    timebox_exceeded: bool = False,
) -> SubmitResult:
    node = session.get(Node, node_id)
    if node is None:
        raise ValueError(f"node tak ditemukan: {node_id!r}")
    instance = session.get(ChallengeInstance, instance_id)
    if instance is None or instance.node_id != node_id:
        raise ValueError(f"instance {instance_id!r} bukan milik node {node_id!r}")

    grader = get_grader(node.grader_type)
    grade = grader.grade(instance, submitted_code)

    # Level L0 = verifikasi; level lain = akuisisi (latihan berscaffold).
    mode = "verification" if scaffold_level == "L0" else "acquisition"

    test_output = grade.test_output
    if timebox_exceeded:
        test_output = (
            f"[timebox habis — jawaban dikumpulkan otomatis]\n\n{test_output}"
        ).strip()

    attempt = Attempt(
        node_id=node_id,
        instance_id=instance_id,
        mode=mode,
        scaffold_level=scaffold_level,
        duration_seconds=duration_seconds,
        submitted_code=submitted_code,
        result="pass" if grade.passed else "fail",
        test_output=test_output,
        probe_result=None,
    )
    session.add(attempt)
    # Pastikan baris jadwal ada (status awal) walau belum acquired.
    ensure_schedule_item(session, node)
    session.commit()
    session.refresh(attempt)
    return SubmitResult(attempt=attempt, grade=grade)


@dataclass
class ProbeOutcome:
    probe_correct: bool
    acquired: bool


def answer_probe(
    session: Session,
    *,
    attempt_id: int,
    probe_id: str,
    answer: str,
) -> ProbeOutcome:
    attempt = session.get(Attempt, attempt_id)
    if attempt is None:
        raise ValueError(f"attempt tak ditemukan: {attempt_id}")
    probe = session.get(ComprehensionProbe, probe_id)
    if probe is None or probe.node_id != attempt.node_id:
        raise ValueError(f"probe {probe_id!r} bukan milik node {attempt.node_id!r}")

    # Pengecekan DETERMINISTIK — cocokkan string jawaban dengan correct_answer.
    probe_correct = answer == probe.correct_answer
    attempt.probe_result = "correct" if probe_correct else "incorrect"

    acquired = False
    if attempt.mode == "verification" and attempt.result == "pass" and probe_correct:
        node = session.get(Node, attempt.node_id)
        item = ensure_schedule_item(session, node)
        item.status = ScheduleStatus.acquired.value
        item.consecutive_success = (item.consecutive_success or 0) + 1
        session.add(item)
        acquired = True

    session.add(attempt)
    session.commit()
    return ProbeOutcome(probe_correct=probe_correct, acquired=acquired)


def node_attempts(session: Session, node_id: str) -> list[Attempt]:
    return session.exec(
        select(Attempt).where(Attempt.node_id == node_id).order_by(Attempt.timestamp.desc())
    ).all()
