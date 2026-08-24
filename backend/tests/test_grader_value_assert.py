"""Test grader `value_assert` (M6).

Yang dibuktikan:
- Toleransi node **benar-benar dipakai**: selisih di dalam `rtol` lolos, di luar gagal.
  Kalau toleransinya diabaikan, seluruh node numerik jadi lotere floating point.
- Toleransi hidup di `data/` (`expected.json`), bukan di kolom DB — skema tetap
  domain-agnostic (M6 §Hal yang harus diperhatikan).
- `expected.json` yang hilang gagal dengan pesan yang bisa ditindaklanjuti, bukan
  `KeyError` di tengah eksekusi.
"""

import json

import pytest

from app.graders.value_assert import ValueAssertGrader
from app.models import ChallengeInstance

HIDDEN_TEST = """
import numpy as np
from expected import ATOL, EXPECTED, RTOL
from solution import scale


def test_value_within_tolerance():
    np.testing.assert_allclose(scale(2.0), EXPECTED["scaled"], rtol=RTOL, atol=ATOL)
"""


def _instance(tmp_path, *, rtol: float, expected_value: float) -> ChallengeInstance:
    (tmp_path / "hidden_test.py").write_text(HIDDEN_TEST, encoding="utf-8")
    (tmp_path / "expected.json").write_text(
        json.dumps({"rtol": rtol, "atol": 0.0, "expected": {"scaled": expected_value}}),
        encoding="utf-8",
    )
    return ChallengeInstance(
        id="t001__variant_a",
        node_id="t001",
        variant_label="variant_a",
        prompt="",
        starter_code="",
        signature_contract="",
        hidden_test_path=str(tmp_path / "hidden_test.py"),
        scaffold_level="L2",
    )


SOLUTION = "def scale(x):\n    return x * 3.0\n"


def test_exact_value_passes(tmp_path):
    instance = _instance(tmp_path, rtol=1e-9, expected_value=6.0)
    result = ValueAssertGrader().grade(instance, SOLUTION)
    assert result.passed, result.test_output


def test_small_deviation_passes_when_tolerance_is_loose(tmp_path):
    # Selisih relatif ~1.7e-7; rtol node ini 1e-05 → masih dianggap benar.
    instance = _instance(tmp_path, rtol=1e-5, expected_value=6.000001)
    result = ValueAssertGrader().grade(instance, SOLUTION)
    assert result.passed, result.test_output


def test_same_deviation_fails_when_tolerance_is_tight(tmp_path):
    """Angka yang sama, toleransi berbeda → verdict berbeda. Inilah buktinya bahwa
    `rtol` node dipakai, bukan default tersembunyi di dalam grader."""
    instance = _instance(tmp_path, rtol=1e-12, expected_value=6.000001)
    result = ValueAssertGrader().grade(instance, SOLUTION)
    assert not result.passed
    assert "Mismatch" in result.test_output or "assert_allclose" in result.test_output


def test_wrong_implementation_fails(tmp_path):
    instance = _instance(tmp_path, rtol=1e-9, expected_value=6.0)
    result = ValueAssertGrader().grade(instance, "def scale(x):\n    return x + 3.0\n")
    assert not result.passed


def test_missing_expected_file_is_actionable(tmp_path):
    (tmp_path / "hidden_test.py").write_text(HIDDEN_TEST, encoding="utf-8")
    instance = ChallengeInstance(
        id="t001__variant_a",
        node_id="t001",
        variant_label="variant_a",
        prompt="",
        starter_code="",
        signature_contract="",
        hidden_test_path=str(tmp_path / "hidden_test.py"),
        scaffold_level="L2",
    )

    with pytest.raises(FileNotFoundError, match="expected.json"):
        ValueAssertGrader().grade(instance, SOLUTION)
