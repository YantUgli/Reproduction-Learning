# Gradien MSE (varian B)

Tulis fungsi:

```python
def mse_gradient(X, y, w, b) -> tuple[np.ndarray, float]
```

Model `y_hat = X @ w + b`, loss `mean((y_hat - y) ** 2)`. Kembalikan `(dw, db)`.

Di varian ini `X` punya **tiga** fitur — pastikan bentuk `dw` mengikuti jumlah
fitur, bukan jumlah baris.

Toleransi node ini: `rtol=1e-09`.
