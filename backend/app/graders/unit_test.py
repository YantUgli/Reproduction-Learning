"""Grader `unit_test` — merakit file lalu delegasi ke Executor (M1).

Hidden test TETAP di `data/` (git); grader membacanya dari `hidden_test_path` dan
menyalin ke tempdir eksekusi sebagai `test_solution.py`. `submitted_code` menjadi
`solution.py` (hidden test meng-import `from solution import ...`).
"""

from pathlib import Path

from app.config import EXECUTION_TIMEOUT_SECONDS, REPO_ROOT
from app.executor import Executor, SubprocessExecutor
from app.graders.base import GradeResult
from app.models import ChallengeInstance

_SOLUTION_FILENAME = "solution.py"
_TEST_FILENAME = "test_solution.py"


class UnitTestGrader:
    def __init__(self, executor: Executor | None = None) -> None:
        self._executor = executor or SubprocessExecutor()

    def grade(self, instance: ChallengeInstance, submitted_code: str) -> GradeResult:
        hidden_test_path = REPO_ROOT / instance.hidden_test_path
        if not hidden_test_path.exists():
            raise FileNotFoundError(
                f"hidden_test tidak ditemukan: {hidden_test_path} "
                f"(instance {instance.id})"
            )
        hidden_test = hidden_test_path.read_text(encoding="utf-8")

        result = self._executor.run(
            files={
                _SOLUTION_FILENAME: submitted_code,
                _TEST_FILENAME: hidden_test,
            },
            test_entry=_TEST_FILENAME,
            # Timeout EKSEKUSI (kode menggantung), BUKAN timebox UI (§7.6).
            timeout_seconds=EXECUTION_TIMEOUT_SECONDS,
        )

        output = result.stdout
        if result.stderr.strip():
            output = f"{output}\n{result.stderr}" if output else result.stderr
        if result.timed_out:
            output = (
                f"{output}\n\n[eksekusi dihentikan: melebihi {EXECUTION_TIMEOUT_SECONDS}s "
                f"— kemungkinan loop tak berhenti]"
            ).strip()

        return GradeResult(
            passed=result.passed,
            test_output=output.strip(),
            timed_out=result.timed_out,
            duration_seconds=result.duration_seconds,
        )


def reference_solution_path(instance: ChallengeInstance) -> Path:
    """Path reference_solution.py (sibling hidden_test) — untuk worked example L3."""
    return (REPO_ROOT / instance.hidden_test_path).parent / "reference_solution.py"
