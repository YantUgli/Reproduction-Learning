# response_model memfilter field (varian A)

Buat `app` FastAPI:

- Model input `UserIn`: `username: str`, `password: str`, `email: str`.
- Model output `UserOut`: `username: str`, `email: str`.
- `POST /users` dengan **`response_model=UserOut`** dan **status 201**, menerima
  `UserIn`, dan mengembalikan objek input itu **apa adanya**.

Yang diuji: `password` **tidak boleh** muncul di body respons — pemfilteran
dikerjakan `response_model`, bukan dengan menyusun dict manual di handler.
Body input tak valid -> **422**.
