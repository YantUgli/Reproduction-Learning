# Path param + 404 (varian B)

Buat `app` FastAPI dengan data `{10: "ada", 20: "linus"}` dan route:

- `GET /users/{user_id}` (user_id **int**):
  - jika ada -> `{"id": user_id, "name": <nama>}` (200)
  - jika tidak -> `HTTPException(status_code=404)`
