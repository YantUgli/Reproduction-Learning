# POST body pydantic (varian B)

Buat `app` FastAPI:

- Model `User` dengan `name: str`, `age: int`.
- `POST /users` (**status 201**) menerima `User`, kembalikan
  `{"name": ..., "age": ...}`.

Body tak valid -> **422**.
