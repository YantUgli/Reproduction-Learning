import numpy as np
from expected import ATOL, EXPECTED, RTOL
from solution import binary_cross_entropy, sigmoid


def test_sigmoid_values():
    got = sigmoid(np.array([-2.0, 0.0, 0.5, 3.0]))
    np.testing.assert_allclose(got, EXPECTED["sigmoid"], rtol=RTOL, atol=ATOL)


def test_sigmoid_does_not_overflow():
    got = sigmoid(np.array([-800.0, 800.0]))
    assert np.all(np.isfinite(got)), "sigmoid meluap untuk |z| besar"
    np.testing.assert_allclose(got, [0.0, 1.0], rtol=RTOL, atol=1e-12)


def test_bce_value():
    got = binary_cross_entropy(np.array([1.0, 0.0, 1.0, 1.0]), np.array([0.9, 0.2, 0.6, 0.75]))
    np.testing.assert_allclose(got, EXPECTED["bce"], rtol=RTOL, atol=ATOL)


def test_bce_is_finite_at_the_edges():
    """Prediksi tepat 0/1 harus di-clip, bukan menghasilkan inf dari log(0)."""
    got = binary_cross_entropy(np.array([1.0, 0.0]), np.array([1.0, 0.0]))
    assert np.isfinite(got), "BCE tak berhingga: prediksi 0/1 belum di-clip"
    np.testing.assert_allclose(got, EXPECTED["bce_edge"], rtol=1e-06, atol=1e-09)
