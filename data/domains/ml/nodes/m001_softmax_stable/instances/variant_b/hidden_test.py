import numpy as np
from expected import ATOL, EXPECTED, RTOL
from solution import softmax


def test_basic_values():
    got = softmax(np.array([0.5, -1.5, 3.0, 0.0]))
    np.testing.assert_allclose(got, EXPECTED["basic"], rtol=RTOL, atol=ATOL)


def test_sums_to_one():
    got = softmax(np.array([0.5, -1.5, 3.0, 0.0]))
    np.testing.assert_allclose(float(np.sum(got)), 1.0, rtol=RTOL, atol=ATOL)


def test_stable_for_very_negative_inputs():
    got = softmax(np.array([-1200.0, -1201.5, -1199.0]))
    assert np.all(np.isfinite(got)), "softmax menghasilkan nan untuk input sangat negatif"
    np.testing.assert_allclose(got, EXPECTED["large"], rtol=RTOL, atol=ATOL)


def test_shift_invariant():
    x = np.array([0.5, -1.5, 3.0, 0.0])
    np.testing.assert_allclose(softmax(x - 4.0), softmax(x), rtol=RTOL, atol=ATOL)
