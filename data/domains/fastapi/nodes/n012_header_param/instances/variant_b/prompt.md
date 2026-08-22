# Header param (varian B)

Buat `app` FastAPI dengan route `GET /ping`:

- `x_api_key: str = Header()` -> **wajib**.
- `x_client: str = Header(default="unknown")` -> opsional, default `"unknown"`.
- Kembalikan `{"key": x_api_key, "client": x_client}`.

Nama header: `x-api-key` dan `x-client`. Header wajib hilang -> **422**.
