"""Orkestrasi Attempt (M3, diperluas M4): submit → grade → (probe) → simpan.

INVARIANT:
- Hanya eksekusi kode (grader → Executor) yang menentukan `result` (§2).
- SETIAP attempt disimpan, termasuk gagal & lewat-timebox — itu data sinyal inti
  (`reproduce-without-AI pass rate`, §9 KPI).
- `acquired` di-set HANYA saat `result=pass` DAN probe benar.
- M5: attempt juga mengonfirmasi/membantah `SkillHypothesis` (R2) — satu-satunya
  jalan hipotesis Claude Code berubah status. Arahnya searah: eksekusi memutuskan
  nasib hipotesis, hipotesis tak pernah memutuskan apa pun.

M4: transisi status & penjadwalan TIDAK lagi dikerjakan di sini — semuanya lewat
`services/mastery.apply_outcome`, supaya jalur akuisisi (L0 + probe), review harian,
dan placement memakai aturan yang PERSIS sama.
"""

from dataclasses import dataclass

from sqlmodel import Session, select

from app.graders import GradeResult, get_grader
from app.models import Attempt, ChallengeInstance, ComprehensionProbe, Node
from app.services.hypotheses import apply_attempt
from app.services.mastery import Outcome, apply_outcome, ensure_schedule_item

__all__ = [
    "SubmitResult",
    "ProbeOutcome",
    "ensure_schedule_item",
    "submit_attempt",
    "answer_probe",
    "node_attempts",
]


@dataclass
class SubmitResult:
    attempt: Attempt
    grade: GradeResult


def submit_attempt(
    session: Session,
    *,
    node_id: str,
    instance_id: str,
    scaffold_level: str,
    submitted_code: str,
    duration_seconds: int,
    timebox_exceeded: bool = False,
    mode: str | None = None,
    session_id: int | None = None,
) -> SubmitResult:
    node = session.get(Node, node_id)
    if node is None:
        raise ValueError(f"node tak ditemukan: {node_id!r}")
    instance = session.get(ChallengeInstance, instance_id)
    if instance is None or instance.node_id != node_id:
        raise ValueError(f"instance {instance_id!r} bukan milik node {node_id!r}")

    grader = get_grader(node.grader_type)
    grade = grader.grade(instance, submitted_code)

    # Mode boleh dipaksa oleh pemanggil (review/placement); default dari scaffold:
    # L0 = verifikasi, level lain = akuisisi (latihan berscaffold).
    if mode is None:
        mode = "verification" if scaffold_level == "L0" else "acquisition"

    test_output = grade.test_output
    if timebox_exceeded:
        test_output = (
            f"[timebox habis — jawaban dikumpulkan otomatis]\n\n{test_output}"
        ).strip()

    attempt = Attempt(
        node_id=node_id,
        instance_id=instance_id,
        session_id=session_id,
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

    # M5: eksekusi kode adalah SATU-SATUNYA yang boleh memutuskan nasib hipotesis
    # Claude Code (R2). Ini pembukuan murni — tak menyentuh status/jadwal node.
    apply_attempt(session, attempt)

    return SubmitResult(attempt=attempt, grade=grade)


@dataclass
class ProbeOutcome:
    probe_correct: bool
    acquired: bool
    outcome: Outcome | None  # None bila attempt ini bukan attempt bergerbang


# Mode yang hasilnya menggerakkan status & jadwal. Attempt berscaffold (`acquisition`)
# sengaja TIDAK ikut: itu latihan, bukan bukti reproduce-without-AI.
_GATED_MODES = ("verification", "review")


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
    session.add(attempt)
    session.commit()

    outcome: Outcome | None = None
    if attempt.mode in _GATED_MODES:
        outcome = apply_outcome(
            session,
            node_id=attempt.node_id,
            test_passed=attempt.result == "pass",
            probe_correct=probe_correct,
        )

    acquired = bool(outcome and outcome.status in ("acquired", "mastered"))
    return ProbeOutcome(probe_correct=probe_correct, acquired=acquired, outcome=outcome)


def node_attempts(session: Session, node_id: str) -> list[Attempt]:
    return session.exec(
        select(Attempt).where(Attempt.node_id == node_id).order_by(Attempt.timestamp.desc())
    ).all()
