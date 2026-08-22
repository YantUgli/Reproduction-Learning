# Dependency sederhana (varian B)

Buat `app` FastAPI:

- Fungsi `listing(sort: str = "asc", limit: int = 5) -> dict` yang mengembalikan
  `{"sort": sort, "limit": limit, "reverse": sort == "desc"}`.
- Dua route, `GET /books` dan `GET /films`, yang **keduanya** memakai
  `Depends(listing)` dan mengembalikan dict itu apa adanya.

`?limit=abc` -> **422**. Jangan menulis ulang param di kedua route.
