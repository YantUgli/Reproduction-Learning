# Sigmoid + BCE (varian A)

Tulis dua fungsi:

```python
def sigmoid(z: np.ndarray) -> np.ndarray
def binary_cross_entropy(y_true, y_pred, eps=1e-12) -> float
```

- `sigmoid` wajib **tidak meluap**: `z = -800` dan `z = 800` harus menghasilkan
  angka berhingga (0.0 dan 1.0), bukan `inf`/`nan`.
- `binary_cross_entropy` mengembalikan **rata-rata**
  `-[y·log(p) + (1-y)·log(1-p)]`, dengan `y_pred` di-**clip** ke `[eps, 1-eps]`
  supaya `log(0)` tak pernah terjadi.

Toleransi node ini: `rtol=1e-09` (kasus tepi BCE dibandingkan dengan `rtol=1e-06`).
