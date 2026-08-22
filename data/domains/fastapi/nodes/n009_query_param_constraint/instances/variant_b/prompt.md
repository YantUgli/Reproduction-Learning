# Konstrain query param (varian B)

Buat `app` FastAPI dengan route `GET /users`:

- `name: str = Query(min_length=2)` -> **wajib**, minimal 2 karakter.
- `page: int = Query(default=1, ge=1, le=20)`.
- Kembalikan `{"name": name, "page": page}`.

`name` hilang / terlalu pendek, atau `page` di luar 1..20 -> **422**.
