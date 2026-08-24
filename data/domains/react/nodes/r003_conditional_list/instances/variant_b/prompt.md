# Daftar + render bersyarat (varian B)

Buat komponen React (`export default`) berisi:

- input terkendali `aria-label="tamu"` dan tombol `Undang`,
- saat daftar kosong: teks persis `Daftar tamu kosong`,
- saat ada isi: satu `<li>` per tamu di dalam `<ul>`,
- klik `Undang` menambahkan isi input ke daftar lalu mengosongkan input,
- nama yang **sudah ada** di daftar tidak ditambahkan dua kali (input tetap
  dikosongkan), dan input kosong/spasi tidak menambah apa pun.
