---
title: "Path parameter + 404"
course: fastapi-dasar
module: 01-routing-dasar
type: note
source_refs: [fastapi_docs_path_params, fastapi_docs_handling_errors]
node_ids: [n003_path_param_404]
status: captured
created: 2026-09-04
---

# Path parameter + 404

- Path param dideklarasikan dengan `{name}` di path + argumen fungsi ber-type hint
  (`item_id: int`) — FastAPI validasi & konversi otomatis.
- Kalau resource tak ada, jangan kembalikan dict kosong — angkat
  `HTTPException(status_code=404, detail=...)`.
- Handler yang benar membedakan "ada" (200 + body) vs "tidak ada" (404 + detail).

**Yang perlu diproduksi ulang tanpa AI:** route dengan path param yang mengembalikan
200 saat ditemukan dan 404 saat tidak.

**Sumber:** FastAPI — Path Parameters (`fastapi_docs_path_params`), Handling Errors
(`fastapi_docs_handling_errors`)
**Tempa di Forge:** node `n003_path_param_404` · balik ke [[_index|Routing Dasar]]
