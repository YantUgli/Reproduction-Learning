import numpy as np


def mse_gradient(X, y, w, b):
    """Gradien MSE untuk model linear y_hat = X @ w + b."""
    X = np.asarray(X, dtype=float)
    y = np.asarray(y, dtype=float)
    w = np.asarray(w, dtype=float)
    n = X.shape[0]
    error = X @ w + b - y
    dw = (2.0 / n) * (X.T @ error)
    db = (2.0 / n) * float(np.sum(error))
    return dw, db
