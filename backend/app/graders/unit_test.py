"""Grader `unit_test` — merakit file lalu delegasi ke Executor (M1).

Hidden test TETAP di `data/` (git); grader membacanya dari `hidden_test_path` dan
menyalin ke tempdir eksekusi sebagai `test_solution.py`. `submitted_code` menjadi
`solution.py` (hidden test meng-import `from solution import ...`).
"""

from app.config import EXECUTION_TIMEOUT_SECONDS
from app.executor import Executor, SubprocessExecutor
from app.graders.base import GradeResult
from app.graders.files import read_hidden_test
from app.models import ChallengeInstance

_SOLUTION_FILENAME = "solution.py"
_TEST_FILENAME = "test_solution.py"


def build_output(result, timeout_seconds: int) -> str:
    """stdout+stderr runner apa adanya — ini cermin buat user (§7.6), bukan ringkasan.

    Dipakai bersama oleh semua grader Python supaya pesan timeout-nya seragam.
    """
    output = result.stdout
    if result.stderr.strip():
        output = f"{output}\n{result.stderr}" if output else result.stderr
    if result.timed_out:
        output = (
            f"{output}\n\n[eksekusi dihentikan: melebihi {timeout_seconds}s "
            f"— kemungkinan loop tak berhenti]"
        ).strip()
    return output.strip()


class UnitTestGrader:
    def __init__(self, executor: Executor | None = None) -> None:
        self._executor = executor or SubprocessExecutor()

    def grade(self, instance: ChallengeInstance, submitted_code: str) -> GradeResult:
        result = self._executor.run(
            files={
                _SOLUTION_FILENAME: submitted_code,
                _TEST_FILENAME: read_hidden_test(instance),
            },
            test_entry=_TEST_FILENAME,
            # Timeout EKSEKUSI (kode menggantung), BUKAN timebox UI (§7.6).
            timeout_seconds=EXECUTION_TIMEOUT_SECONDS,
        )
        return GradeResult(
            passed=result.passed,
            test_output=build_output(result, EXECUTION_TIMEOUT_SECONDS),
            timed_out=result.timed_out,
            duration_seconds=result.duration_seconds,
        )
