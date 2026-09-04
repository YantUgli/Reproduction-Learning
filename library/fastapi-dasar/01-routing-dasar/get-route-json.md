---
title: "GET route JSON dengan status 200"
course: fastapi-dasar
module: 01-routing-dasar
type: note
source_refs: [fastapi_docs_first_steps]
node_ids: [n002_get_json_route]
status: captured
created: 2026-09-04
---

# GET route JSON dengan status 200

Catatan konsep (bukan solusi — solusinya ditempa di Forge).

- Route GET didaftarkan dengan decorator `@app.get("<path>")` di atas fungsi handler.
- Kalau handler mengembalikan `dict`, FastAPI serialisasi ke JSON otomatis.
- Tanpa error & tanpa status eksplisit, status default response = **200**.
- Uji lokal pakai `TestClient(app)` → `client.get("<path>")`.

**Yang perlu diproduksi ulang tanpa AI:** definisi satu route GET yang mengembalikan
dict, dengan status 200 dan body persis.

**Sumber:** FastAPI — First Steps (`fastapi_docs_first_steps`)
**Tempa di Forge:** node `n002_get_json_route` · lanjut ke [[path-param-404|Path parameter + 404]]
