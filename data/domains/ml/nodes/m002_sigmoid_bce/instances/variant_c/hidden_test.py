import numpy as np
from expected import ATOL, EXPECTED, RTOL
from solution import binary_cross_entropy, sigmoid


def _reference_sigmoid(z):
    """Oracle stabil independen — dipakai untuk membandingkan PERILAKU, bukan bentuk kode."""
    z = np.asarray(z, dtype=float)
    out = np.empty_like(z)
    positive = z >= 0
    out[positive] = 1.0 / (1.0 + np.exp(-z[positive]))
    exp_z = np.exp(z[~positive])
    out[~positive] = exp_z / (1.0 + exp_z)
    return out


def _reference_bce(y_true, y_pred, eps=1e-12):
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.clip(np.asarray(y_pred, dtype=float), eps, 1.0 - eps)
    return float(-np.mean(y_true * np.log(y_pred) + (1 - y_true) * np.log(1 - y_pred)))


def test_sigmoid_values():
    z = np.array([-4.0, -1.0, 0.75, 2.5])
    np.testing.assert_allclose(sigmoid(z), _reference_sigmoid(z), rtol=RTOL, atol=ATOL)


def test_sigmoid_does_not_overflow():
    got = sigmoid(np.array([-700.0, 700.0]))
    assert np.all(np.isfinite(got)), "sigmoid meluap untuk |z| besar"
    np.testing.assert_allclose(got, EXPECTED["sigmoid_extremes"], rtol=RTOL, atol=1e-12)


def test_bce_value():
    y_true = np.array([1.0, 0.0, 0.0, 1.0])
    y_pred = np.array([0.7, 0.15, 0.4, 0.95])
    np.testing.assert_allclose(
        binary_cross_entropy(y_true, y_pred),
        _reference_bce(y_true, y_pred),
        rtol=RTOL,
        atol=ATOL,
    )


def test_bce_is_finite_at_the_edges():
    """Prediksi tepat 0/1 harus di-clip, bukan menghasilkan inf dari log(0)."""
    y_true = np.array([1.0, 0.0])
    y_pred = np.array([0.0, 1.0])
    got = binary_cross_entropy(y_true, y_pred)
    assert np.isfinite(got), "BCE tak berhingga: prediksi 0/1 belum di-clip"
    np.testing.assert_allclose(got, _reference_bce(y_true, y_pred), rtol=1e-06, atol=1e-09)
