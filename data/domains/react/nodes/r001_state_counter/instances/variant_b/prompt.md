# Counter dengan useState (varian B)

Buat komponen React (`export default`) yang menampilkan:

- teks berisi persis `Stok: <n>` (mulai dari **10**),
- tombol berlabel `Ambil` yang MENGURANGI `<n>` sebanyak 1 tiap klik,
- tombol berlabel `Isi ulang` yang mengembalikan `<n>` ke 10.

`<n>` tidak boleh turun di bawah 0: klik `Ambil` saat stok 0 tetap menampilkan
`Stok: 0`. Yang diuji adalah perilaku, bukan struktur JSX.
