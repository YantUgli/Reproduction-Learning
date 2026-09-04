---
title: "Query parameter dengan default"
course: fastapi-dasar
module: 01-routing-dasar
type: note
source_refs: [fastapi_docs_query_params]
node_ids: [n004_query_param_default]
status: captured
created: 2026-09-04
---

# Query parameter dengan default

- Argumen fungsi yang **bukan** bagian dari path otomatis jadi query parameter.
- Beri nilai default (`limit: int = 10`) → parameter jadi opsional; tanpa default →
  wajib, dan absennya menghasilkan 422.
- Type hint menentukan validasi & konversi (`?limit=5` → `int` 5).

**Yang perlu diproduksi ulang tanpa AI:** route yang menerima query param opsional
berdefault dan memakainya di respons.

**Sumber:** FastAPI — Query Parameters (`fastapi_docs_query_params`)
**Tempa di Forge:** node `n004_query_param_default` · balik ke [[_index|Routing Dasar]]
