# HTTPException 409 & 400 (varian A)

Buat `app` FastAPI dengan route `POST /accounts/{name}` (`name: str`):

- `name` == `"admin"` -> **409**, body `{"detail": "account already exists"}`.
- `name` lebih pendek dari 3 karakter -> **400**, body `{"detail": "name too short"}`.
- selain itu -> **200**, body `{"name": name}`.

Urutan pemeriksaan penting: bentrok (409) diperiksa lebih dulu daripada panjang nama.
Pakai `HTTPException`, jangan mengembalikan dict error buatan sendiri.
