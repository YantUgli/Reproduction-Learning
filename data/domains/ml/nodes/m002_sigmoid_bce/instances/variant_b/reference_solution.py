import numpy as np


def sigmoid(z):
    """Sigmoid tanpa overflow: pilih bentuk rumus sesuai tanda z."""
    z = np.asarray(z, dtype=float)
    out = np.empty_like(z)
    positive = z >= 0
    out[positive] = 1.0 / (1.0 + np.exp(-z[positive]))
    exp_z = np.exp(z[~positive])
    out[~positive] = exp_z / (1.0 + exp_z)
    return out


def binary_cross_entropy(y_true, y_pred, eps=1e-12):
    """BCE rata-rata; prediksi di-clip supaya log(0) tak pernah terjadi."""
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.clip(np.asarray(y_pred, dtype=float), eps, 1.0 - eps)
    return float(-np.mean(y_true * np.log(y_pred) + (1 - y_true) * np.log(1 - y_pred)))
