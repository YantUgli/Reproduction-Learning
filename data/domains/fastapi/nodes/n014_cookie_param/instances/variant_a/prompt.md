# Cookie parameter (varian A)

Buat `app` FastAPI dengan satu route `GET /profile` yang membaca cookie
`session_id` lewat `Cookie()`:

- Tipe `str`, default `"guest"` bila cookie tak dikirim klien.
- Route mengembalikan `{"session_id": session_id}` apa adanya.

Cookie lain yang mungkin dikirim klien (nama selain `session_id`) harus
diabaikan — jangan baca cookie itu.
