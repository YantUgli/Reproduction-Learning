# Pagination (varian A)

Tulis `paginate(items, page, per_page)`:

- `page` **1-indexed** (halaman pertama = 1).
- Kembalikan potongan `items` untuk halaman itu.
- `page < 1` atau `per_page < 1` -> `raise ValueError`.
- Halaman melewati akhir data -> kembalikan `[]`.

Contoh: `paginate([1,2,3,4,5], 2, 2)` -> `[3, 4]`.
