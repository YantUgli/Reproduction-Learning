# Daftar + render bersyarat (varian A)

Buat komponen React (`export default`) berisi:

- input terkendali `aria-label="tugas"` dan tombol `Tambah`,
- saat daftar kosong: teks persis `Belum ada tugas`,
- saat ada isi: satu elemen `<li>` per tugas (pakai `<ul>`), berisi teks tugas apa
  adanya,
- klik `Tambah` menambahkan isi input ke daftar lalu **mengosongkan** input,
- input kosong (atau hanya spasi) **tidak** menambah apa pun.
