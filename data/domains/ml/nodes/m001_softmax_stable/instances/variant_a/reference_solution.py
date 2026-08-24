import numpy as np


def softmax(x):
    """Softmax stabil: kurangi maksimum sebelum eksponensiasi."""
    x = np.asarray(x, dtype=float)
    shifted = x - np.max(x)
    exps = np.exp(shifted)
    return exps / np.sum(exps)
