# Query param + default (varian B)

Buat `app` FastAPI dengan route:

- `GET /products` dengan query param `sort: str = "asc"` dan `page: int = 1`.
- Kembalikan `{"sort": sort, "page": page}`.

Catatan: `page` bukan integer -> **422**.
