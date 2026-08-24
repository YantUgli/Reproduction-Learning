import numpy as np
from expected import ATOL, EXPECTED, RTOL
from solution import binary_cross_entropy, sigmoid


def test_sigmoid_values():
    got = sigmoid(np.array([-5.0, -0.25, 1.5, 4.0]))
    np.testing.assert_allclose(got, EXPECTED["sigmoid"], rtol=RTOL, atol=ATOL)


def test_sigmoid_does_not_overflow():
    got = sigmoid(np.array([-900.0, 900.0]))
    assert np.all(np.isfinite(got)), "sigmoid meluap untuk |z| besar"
    np.testing.assert_allclose(got, [0.0, 1.0], rtol=RTOL, atol=1e-12)


def test_bce_value():
    got = binary_cross_entropy(np.array([0.0, 1.0, 1.0, 0.0]), np.array([0.1, 0.85, 0.55, 0.3]))
    np.testing.assert_allclose(got, EXPECTED["bce"], rtol=RTOL, atol=ATOL)


def test_bce_is_finite_at_the_edges():
    got = binary_cross_entropy(np.array([0.0, 1.0]), np.array([1.0, 0.0]))
    assert np.isfinite(got), "BCE tak berhingga: prediksi 0/1 belum di-clip"
    np.testing.assert_allclose(got, EXPECTED["bce_edge"], rtol=1e-06, atol=1e-09)
