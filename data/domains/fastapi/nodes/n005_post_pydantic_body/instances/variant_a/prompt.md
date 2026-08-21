# POST body pydantic (varian A)

Buat `app` FastAPI:

- Model `Item` dengan `name: str`, `price: float`.
- `POST /items` (**status 201**) menerima `Item`, kembalikan
  `{"name": ..., "price": ...}`.

Body tak valid (field hilang / tipe salah) -> **422** (otomatis).
