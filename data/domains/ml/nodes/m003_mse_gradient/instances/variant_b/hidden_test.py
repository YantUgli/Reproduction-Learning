import numpy as np
from expected import ATOL, EXPECTED, RTOL
from solution import mse_gradient

X = np.array([[2.0, 0.0, 1.0], [1.0, 1.0, 3.0], [0.5, 2.0, 1.5]])
Y = np.array([1.0, 4.0, 2.5])
W = np.array([-0.3, 0.8, 0.2])
B = -0.5


def test_dw_matches_expected():
    dw, _ = mse_gradient(X, Y, W, B)
    np.testing.assert_allclose(dw, EXPECTED["dw"], rtol=RTOL, atol=ATOL)


def test_db_matches_expected():
    _, db = mse_gradient(X, Y, W, B)
    np.testing.assert_allclose(db, EXPECTED["db"], rtol=RTOL, atol=ATOL)


def test_gradient_agrees_with_finite_differences():
    def loss(w, b):
        return float(np.mean((X @ w + b - Y) ** 2))

    eps = 1e-06
    numeric_dw = np.array(
        [
            (loss(W + eps * unit, B) - loss(W - eps * unit, B)) / (2 * eps)
            for unit in np.eye(len(W))
        ]
    )
    numeric_db = (loss(W, B + eps) - loss(W, B - eps)) / (2 * eps)

    dw, db = mse_gradient(X, Y, W, B)
    np.testing.assert_allclose(dw, numeric_dw, rtol=1e-05, atol=1e-06)
    np.testing.assert_allclose(db, numeric_db, rtol=1e-05, atol=1e-06)


def test_zero_gradient_at_perfect_fit():
    perfect_w = np.array([2.0, 0.0, -1.0])
    x = np.array([[1.0, 3.0, 2.0], [0.0, 1.0, 1.0]])
    y = x @ perfect_w + 0.75
    dw, db = mse_gradient(x, y, perfect_w, 0.75)
    np.testing.assert_allclose(dw, [0.0, 0.0, 0.0], rtol=RTOL, atol=1e-12)
    np.testing.assert_allclose(db, 0.0, rtol=RTOL, atol=1e-12)
