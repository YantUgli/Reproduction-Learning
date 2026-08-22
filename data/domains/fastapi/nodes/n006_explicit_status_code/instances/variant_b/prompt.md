# Status code eksplisit (varian B)

Buat `app` FastAPI dengan dua route:

- `POST /emails` -> status **202**, body `{"accepted": true}`.
- `DELETE /emails/{email_id}` (`email_id: int`) -> status **204**, **tanpa body**.

Status ditentukan lewat parameter `status_code=` pada dekorator.
