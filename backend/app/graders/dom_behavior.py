"""Grader `dom_behavior` — React di-render, di-interaksi, lalu diperiksa PERILAKUnya.

Bentuknya sengaja kembar dengan `unit_test`: rakit dua berkas, serahkan ke Executor,
maknai hasilnya. Yang berbeda hanya Executor-nya (Node+vitest+jsdom) dan nama berkas
(`.jsx`). Itulah klaim domain-agnostic M6 dalam bentuk kode — kalau grader ini butuh
menyentuh loop/scaffold/scheduler untuk bekerja, klaimnya salah.

Hidden test meng-assert **perilaku**: teks yang muncul setelah klik, nilai input yang
berubah, tombol yang nonaktif. BUKAN struktur JSX (§M6 langkah 2) — karena struktur
punya banyak bentuk benar, sedangkan perilaku hanya satu.
"""

from app.config import REACT_EXECUTION_TIMEOUT_SECONDS
from app.executor import Executor, NodeExecutor
from app.graders.base import GradeResult
from app.graders.files import read_hidden_test
from app.graders.unit_test import build_output
from app.models import ChallengeInstance

_SOLUTION_FILENAME = "solution.jsx"
_TEST_FILENAME = "solution.test.jsx"


class DomBehaviorGrader:
    def __init__(self, executor: Executor | None = None) -> None:
        self._executor = executor or NodeExecutor()

    def grade(self, instance: ChallengeInstance, submitted_code: str) -> GradeResult:
        result = self._executor.run(
            files={
                _SOLUTION_FILENAME: submitted_code,
                _TEST_FILENAME: read_hidden_test(instance),
            },
            test_entry=_TEST_FILENAME,
            timeout_seconds=REACT_EXECUTION_TIMEOUT_SECONDS,
        )
        return GradeResult(
            passed=result.passed,
            test_output=build_output(result, REACT_EXECUTION_TIMEOUT_SECONDS),
            timed_out=result.timed_out,
            duration_seconds=result.duration_seconds,
        )
