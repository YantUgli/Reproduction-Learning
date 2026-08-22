# HTTPException 409 & 400 (varian B)

Buat `app` FastAPI dengan route `POST /rooms/{code}` (`code: str`):

- `code` == `"r101"` -> **409**, body `{"detail": "room already booked"}`.
- `code` lebih pendek dari 4 karakter -> **400**, body `{"detail": "code too short"}`.
- selain itu -> **200**, body `{"code": code}`.

Bentrok (409) diperiksa lebih dulu. Pakai `HTTPException`.
