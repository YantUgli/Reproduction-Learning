# Gradien MSE (varian A)

Tulis fungsi:

```python
def mse_gradient(X, y, w, b) -> tuple[np.ndarray, float]
```

Model: `y_hat = X @ w + b`. Loss: `mean((y_hat - y) ** 2)` (rata-rata atas `n` baris).

Kembalikan `(dw, db)` — turunan loss terhadap `w` (array, sepanjang jumlah fitur)
dan terhadap `b` (skalar). Perhatikan faktor `2/n` yang lahir dari rata-rata kuadrat.

Test membandingkan hasilmu dengan nilai acuan **dan** dengan selisih hingga, jadi
gradien yang "hampir benar tapi salah faktor" akan ketahuan.

Toleransi node ini: `rtol=1e-09` (uji selisih hingga memakai `rtol=1e-05`).
