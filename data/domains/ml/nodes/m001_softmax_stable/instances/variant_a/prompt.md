# Softmax stabil (varian A)

Tulis fungsi:

```python
def softmax(x: np.ndarray) -> np.ndarray
```

- Kembalikan distribusi peluang: semua elemen ≥ 0 dan **berjumlah 1**.
- Wajib **stabil secara numerik**: untuk input besar seperti `[1000, 1001, 1002]`
  hasilnya tetap berhingga (bukan `nan`). Kuncinya: kurangi nilai maksimum sebelum
  eksponensiasi — softmax tak berubah bila seluruh input digeser konstan.

Toleransi perbandingan node ini: `rtol=1e-09` (lihat `expected.json`).
