# Konstrain path param (varian B)

Buat `app` FastAPI dengan route:

- `GET /pages/{page_no}` dengan `page_no: int = Path(gt=0)`.
- Kembalikan `{"page_no": page_no}`.

Nilai <= 0 dan nilai non-integer -> **422**.
