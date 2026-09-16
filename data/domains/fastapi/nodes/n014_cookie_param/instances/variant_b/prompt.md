# Cookie parameter (varian B)

Buat `app` FastAPI dengan satu route `GET /cart` yang membaca cookie
`cart_count` lewat `Cookie()`:

- Tipe `int`, default `0` bila cookie tak dikirim klien. FastAPI mengonversi
  nilai cookie (string) ke `int` seperti halnya `Query()`.
- Route mengembalikan `{"cart_count": cart_count}` apa adanya.

Cookie lain yang mungkin dikirim klien (nama selain `cart_count`) harus
diabaikan — jangan baca cookie itu.
