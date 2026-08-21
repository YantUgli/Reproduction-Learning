# Query param + default (varian A)

Buat `app` FastAPI dengan route:

- `GET /search` dengan query param `q: str = ""` dan `limit: int = 10`.
- Kembalikan `{"q": q, "limit": limit}`.

Catatan: `limit` bukan integer (mis. `?limit=abc`) -> FastAPI balas **422**.
