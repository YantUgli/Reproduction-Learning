# Sigmoid + BCE (varian C)

Tulis dua fungsi:

```python
def sigmoid(z: np.ndarray) -> np.ndarray
def binary_cross_entropy(y_true, y_pred, eps=1e-12) -> float
```

- `sigmoid` wajib berhingga untuk `z = -700` dan `z = 700` — hasilnya `0.0` dan `1.0`,
  bukan `inf`/`nan`.
- `binary_cross_entropy` = rata-rata `-[y·log(p) + (1-y)·log(1-p)]` dengan `y_pred`
  di-**clip** ke `[eps, 1-eps]` supaya `log(0)` tak pernah terjadi.

Data yang diuji berbeda dari varian sebelumnya: `sigmoid` dicek di
`z = [-4, -1, 0.75, 2.5]`, dan `binary_cross_entropy` di
`y_true = [1, 0, 0, 1]`, `y_pred = [0.7, 0.15, 0.4, 0.95]`.

Kasus tepi yang diuji: `y_true = [1, 0]` dengan `y_pred = [0.0, 1.0]` — kedua
prediksi sepenuhnya salah, tapi hasilnya wajib **berhingga** (bukti clipping bekerja).

Toleransi node ini: `rtol=1e-09` (kasus tepi BCE dibandingkan dengan `rtol=1e-06`).
