# Status code eksplisit (varian A)

Buat `app` FastAPI dengan dua route:

- `POST /jobs` -> status **202**, body `{"queued": true}`.
- `DELETE /jobs/{job_id}` (`job_id: int`) -> status **204**, **tanpa body**
  (handler mengembalikan `None`).

Status ditentukan lewat parameter `status_code=` pada dekorator, bukan dengan
menyusun objek `Response` sendiri.
