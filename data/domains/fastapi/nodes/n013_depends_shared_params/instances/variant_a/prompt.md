# Dependency sederhana (varian A)

Buat `app` FastAPI:

- Fungsi `pagination(page: int = 1, size: int = 20) -> dict` yang mengembalikan
  `{"page": page, "size": size, "offset": (page - 1) * size}`.
- Dua route, `GET /posts` dan `GET /comments`, yang **keduanya** memakai
  `Depends(pagination)` dan mengembalikan dict itu apa adanya.

Param dependency tetap dibaca sebagai query param: `?page=abc` -> **422**.
Jangan menulis ulang param di kedua route.
