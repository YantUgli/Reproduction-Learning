# Input terkendali (varian B)

Buat komponen React (`export default`) berisi:

- satu `<input>` **terkendali** dengan `aria-label="pesan"`, awalnya kosong,
- teks berisi persis `Sisa: <n>` dengan `<n>` = 20 dikurangi jumlah karakter yang
  diketik,
- input **menolak** karakter melebihi 20: mengetik lebih panjang tetap menyisakan
  20 karakter pertama dan `Sisa: 0`.
