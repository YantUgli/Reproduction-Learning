# Sigmoid + BCE (varian B)

Tulis dua fungsi:

```python
def sigmoid(z: np.ndarray) -> np.ndarray
def binary_cross_entropy(y_true, y_pred, eps=1e-12) -> float
```

- `sigmoid` wajib berhingga untuk `z = -900` dan `z = 900`.
- `binary_cross_entropy` = rata-rata `-[y·log(p) + (1-y)·log(1-p)]` dengan `y_pred`
  di-clip ke `[eps, 1-eps]`.

Kasus tepi yang diuji: `y_true = [0, 1]` dengan `y_pred = [1.0, 0.0]` — prediksi
sepenuhnya salah, tapi hasilnya wajib **berhingga**.

Toleransi node ini: `rtol=1e-09`.
