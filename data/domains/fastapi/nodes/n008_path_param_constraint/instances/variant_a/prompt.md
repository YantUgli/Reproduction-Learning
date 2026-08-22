# Konstrain path param (varian A)

Buat `app` FastAPI dengan route:

- `GET /items/{item_id}` dengan `item_id: int = Path(gt=0)`.
- Kembalikan `{"item_id": item_id}`.

Konsekuensi yang diuji: `item_id` <= 0 (mis. `/items/0`, `/items/-3`) dan
nilai non-integer (`/items/abc`) -> **422**, tanpa masuk handler.
