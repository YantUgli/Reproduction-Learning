# Softmax stabil (varian B)

Tulis fungsi:

```python
def softmax(x: np.ndarray) -> np.ndarray
```

- Kembalikan distribusi peluang (elemen ≥ 0, berjumlah 1).
- Wajib stabil untuk input **sangat negatif** seperti `[-1200, -1201.5, -1199]`:
  hasilnya berhingga, bukan `nan`. Softmax tak berubah bila seluruh input digeser
  konstan — pakai sifat itu.

Toleransi node ini: `rtol=1e-09`.
