"""Test SubprocessExecutor — tiga kasus wajib (M1).

1. solusi benar  → passed=True, timed_out=False
2. solusi rusak  → passed=False
3. loop tak henti → timed_out=True, passed=False, dan proses benar-benar berhenti
   (< 5s wall-clock, tidak menggantung).
"""

import time

from app.executor import ExecutionResult, SubprocessExecutor

_TEST_FILE = "test_solution.py"

_HIDDEN_TEST = """\
from solution import add


def test_add():
    assert add(2, 3) == 5
    assert add(-1, 1) == 0
"""


def _run(solution: str, timeout: int = 30) -> ExecutionResult:
    files = {"solution.py": solution, _TEST_FILE: _HIDDEN_TEST}
    return SubprocessExecutor().run(files=files, test_entry=_TEST_FILE, timeout_seconds=timeout)


def test_solusi_benar_pass():
    result = _run("def add(a, b):\n    return a + b\n")
    assert result.passed is True
    assert result.timed_out is False
    assert result.exit_code == 0


def test_solusi_rusak_fail():
    # add mengurangi, bukan menjumlah → test gagal.
    result = _run("def add(a, b):\n    return a - b\n")
    assert result.passed is False
    assert result.timed_out is False
    assert result.exit_code not in (0, None)


def test_error_import_fail():
    # solution.py tak mendefinisikan add → ImportError, tetap passed=False.
    result = _run("x = 1\n")
    assert result.passed is False
    assert result.timed_out is False


def test_loop_tak_henti_timeout():
    # while True saat import solution → pytest menggantung; timeout wajib membunuhnya.
    hanging = "while True:\n    pass\n\ndef add(a, b):\n    return a + b\n"
    start = time.monotonic()
    result = _run(hanging, timeout=2)
    elapsed = time.monotonic() - start

    assert result.timed_out is True
    assert result.passed is False
    # Proses benar-benar dibunuh: total wall-clock jauh di bawah 5s.
    assert elapsed < 5.0
