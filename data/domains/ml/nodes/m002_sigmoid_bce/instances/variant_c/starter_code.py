import numpy as np


def sigmoid(z):
    # TODO: rumus yang tak overflow untuk z sangat negatif maupun sangat positif.
    ...


def binary_cross_entropy(y_true, y_pred, eps=1e-12):
    # TODO: clip prediksi ke [eps, 1-eps], lalu rata-rata -[y log p + (1-y) log(1-p)].
    ...
