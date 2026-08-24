import numpy as np
from expected import ATOL, EXPECTED, RTOL
from solution import softmax


def test_basic_values():
    got = softmax(np.array([2.0, 1.0, 0.1]))
    np.testing.assert_allclose(got, EXPECTED["basic"], rtol=RTOL, atol=ATOL)


def test_sums_to_one():
    got = softmax(np.array([2.0, 1.0, 0.1]))
    np.testing.assert_allclose(float(np.sum(got)), 1.0, rtol=RTOL, atol=ATOL)


def test_stable_for_large_inputs():
    got = softmax(np.array([1000.0, 1001.0, 1002.0]))
    assert np.all(np.isfinite(got)), "softmax menghasilkan inf/nan untuk input besar"
    np.testing.assert_allclose(got, EXPECTED["large"], rtol=RTOL, atol=ATOL)


def test_shift_invariant():
    x = np.array([2.0, 1.0, 0.1])
    np.testing.assert_allclose(softmax(x + 7.0), softmax(x), rtol=RTOL, atol=ATOL)
