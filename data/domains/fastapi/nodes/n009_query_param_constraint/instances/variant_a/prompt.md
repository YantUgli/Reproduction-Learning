# Konstrain query param (varian A)

Buat `app` FastAPI dengan route `GET /search`:

- `q: str = Query(min_length=3)` -> **wajib** (tak punya default), minimal 3 karakter.
- `limit: int = Query(default=10, ge=1, le=50)`.
- Kembalikan `{"q": q, "limit": limit}`.

Konsekuensi yang diuji: `q` hilang, `q` terlalu pendek, atau `limit` di luar
rentang 1..50 -> **422**.
