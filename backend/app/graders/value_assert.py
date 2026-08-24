"""Grader `value_assert` — nilai numerik lawan expected, dengan TOLERANSI EKSPLISIT.

Bedanya dengan `unit_test` kecil tapi penting: selain solusi & hidden test, grader ini
menyalin `expected.json` milik instance ke direktori eksekusi. Berkas itu memuat nilai
acuan **dan** `rtol`/`atol` node tersebut, jadi hidden test bisa menulis

    from expected import EXPECTED, RTOL, ATOL
    np.testing.assert_allclose(softmax(x), EXPECTED["softmax_x"], rtol=RTOL, atol=ATOL)

Kenapa toleransi hidup di `data/`, bukan di kolom DB (M6 §Keputusan + §Hal yang harus
diperhatikan): skema sengaja tak tahu domainnya apa. Kolom `rtol` akan menjadi kolom
khusus-ML pertama di tabel yang domain-agnostic — persis kebocoran yang diuji M6.
Sebagai berkas di folder instance, ia ikut di-review & di-diff seperti kode.

Kenapa `value_assert`, bukan `metric_threshold` (§7.4 + §8): ambang metrik mengukur
HASIL. Bryant bisa menyalin training loop dan menembusnya tanpa paham apa pun.
Menuntut nilai `softmax`/gradien yang benar menuntut komponennya diproduksi sendiri.
"""

import json

from app.config import EXECUTION_TIMEOUT_SECONDS
from app.executor import Executor, SubprocessExecutor
from app.graders.base import GradeResult
from app.graders.files import read_hidden_test, sibling
from app.graders.unit_test import build_output
from app.models import ChallengeInstance

_SOLUTION_FILENAME = "solution.py"
_TEST_FILENAME = "test_solution.py"
_EXPECTED_MODULE = "expected.py"

#: Dipakai bila node tak menyebut toleransinya. Sengaja ketat: node yang butuh
#: longgar HARUS mengatakannya di `expected.json`, tertulis dan bisa di-review.
_DEFAULT_RTOL = 1e-7
_DEFAULT_ATOL = 0.0


class ValueAssertGrader:
    def __init__(self, executor: Executor | None = None) -> None:
        self._executor = executor or SubprocessExecutor()

    def grade(self, instance: ChallengeInstance, submitted_code: str) -> GradeResult:
        files = {
            _SOLUTION_FILENAME: submitted_code,
            _TEST_FILENAME: read_hidden_test(instance),
            _EXPECTED_MODULE: _expected_module(instance),
        }
        result = self._executor.run(
            files=files,
            test_entry=_TEST_FILENAME,
            timeout_seconds=EXECUTION_TIMEOUT_SECONDS,
        )
        return GradeResult(
            passed=result.passed,
            test_output=build_output(result, EXECUTION_TIMEOUT_SECONDS),
            timed_out=result.timed_out,
            duration_seconds=result.duration_seconds,
        )


def _expected_module(instance: ChallengeInstance) -> str:
    """`expected.json` instance → modul Python yang bisa di-import hidden test.

    Dirakit jadi modul (bukan disalin apa adanya) supaya hidden test tak perlu tahu
    cara membaca berkas dari direktori kerja — cukup `from expected import ...`.
    """
    path = sibling(instance, "expected")
    if path is None:
        raise FileNotFoundError(
            f"grader value_assert butuh `expected.json` di folder instance {instance.id} "
            "(berisi nilai acuan + rtol/atol node ini)"
        )
    data = json.loads(path.read_text(encoding="utf-8"))
    values = data.get("expected", {})
    rtol = data.get("rtol", _DEFAULT_RTOL)
    atol = data.get("atol", _DEFAULT_ATOL)
    return (
        "# Dihasilkan grader value_assert dari expected.json milik instance ini.\n"
        f"EXPECTED = {json.dumps(values)}\n"
        f"RTOL = {float(rtol)!r}\n"
        f"ATOL = {float(atol)!r}\n"
    )
