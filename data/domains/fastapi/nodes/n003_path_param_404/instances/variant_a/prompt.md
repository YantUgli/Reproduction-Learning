# Path param + 404 (varian A)

Buat `app` FastAPI dengan data `{1: "apple", 2: "banana"}` dan route:

- `GET /items/{item_id}` (item_id **int**):
  - jika ada -> `{"id": item_id, "name": <nama>}` (200)
  - jika tidak -> `HTTPException(status_code=404)`
