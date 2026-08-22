# Header param (varian A)

Buat `app` FastAPI dengan route `GET /whoami`:

- `x_token: str = Header()` -> **wajib**.
- `x_trace: str | None = Header(default=None)` -> opsional.
- Kembalikan `{"token": x_token, "trace": x_trace}`.

Ingat: underscore di nama param dipetakan ke hyphen di nama header
(`x_token` -> header `x-token`). Header wajib yang hilang -> **422**.
