# M2 — Authoring Kit + 5 Node FastAPI (A1)

> Peta PRD: Track Authoring A1 · Dependency: M1 · Estimasi: 4–5 hari

## Tujuan

Menetapkan **format node di `data/`** dan mengarang **5 node FastAPI pertama**
(primitif → satu route sederhana), lengkap: prompt, kontrak signature, 2–3 varian
instance, hidden test **yang sudah terverifikasi hijau di solusi referensi** (via
harness M1), dan 1–2 comprehension probe per node. Plus tooling ringan untuk
memvalidasi & memuat node ke DB. **Inilah yang memberi makan M3.**

## Konteks & alasan

Authoring adalah **biaya sebenarnya** proyek ini (RISK-1) — bukan kodenya. 5 node
cukup untuk menyalakan vertical slice M3; sisanya (A2, ~20 node) diarang paralel
sepanjang M4+ setelah loop memberi umpan balik nyata. M2 juga memformalkan
**format data** yang dipakai selamanya, jadi bentuknya harus benar sejak awal.

Node harus **grain kecil**: satu konsep yang bisa direproduksi sekali duduk
(±10–20 menit) dan bisa di-grade dengan menjalankan kode (§7.1 PRD). Kalau butuh
lebih dari ±2 file test atau tak selesai sekali duduk → pecah.

## Prerequisite

- **M1 selesai.** Harness `harness/run.py` bisa memverifikasi node. Tanpa ini,
  aturan "hijau di solusi referensi" tak bisa ditegakkan — jangan mulai authoring.
- Akses ke sumber otoritatif: ACM/IEEE **CS2023** Knowledge Areas, TOC buku backend/
  FastAPI standar, **docs resmi FastAPI**.
- **Isyah** sebagai reviewer & penanda `hard`/`soft` edge.

## Format node (bekukan di sini)

Satu node = satu folder di bawah `data/domains/fastapi/nodes/`:

```
nodes/
  n001_get_route_path_param/
    node.yaml
    instances/
      variant_a/
        prompt.md
        starter_code.py          # kerangka sesuai scaffold_level
        reference_solution.py    # solusi benar (untuk verifikasi test)
        hidden_test.py           # pytest; TIDAK ditunjukkan ke user
      variant_b/ ...             # ≥2 varian untuk transfer & review
    probes/
      probe_01.yaml              # predict_output | spot_bug | trace
```

`node.yaml`:
```yaml
id: n001_get_route_path_param
domain_id: fastapi
concept: "GET route dengan path param, 404 jika resource tak ada"
description: "..."
grader_type: unit_test
estimated_minutes: 15
timebox_seconds: 1200
status_default: locked
source_refs: [cs2023_ku_ser, fastapi_docs_path_params]
edges:                      # diusulkan; Isyah yang finalkan hard/soft
  - to: n002_query_param
    type: soft
    source_ref_id: fastapi_docs_query
    note: "..."
```

`probes/probe_01.yaml`:
```yaml
id: n001_probe_01
node_id: n001_get_route_path_param
type: predict_output
question: "Route ini return status berapa jika id tidak ada?"
options: ["200", "404", "500", "400"]
correct_answer: "404"
```

## 5 node awal (usulan urutan; Isyah finalkan)

Urutan primitif → route, semuanya `grader_type: unit_test`:

1. `n001` — fungsi Python murni + pytest (mis. validasi/parse) — *primitif, tanpa
   FastAPI, untuk memastikan pipeline grading jalan.*
2. `n002` — GET route sederhana, return dict → 200 + body benar.
3. `n003` — GET route dengan **path param** + **404** jika tak ditemukan.
4. `n004` — **query param** dengan default & validasi tipe.
5. `n005` — **POST** dengan body pydantic, return 201 + echo tervalidasi.

Tiap node: 2–3 varian instance (angka/nama beda supaya lolos = transfer, bukan
hafalan), 1–2 probe.

## File / komponen yang dibuat

```
data/domains/fastapi/nodes/n001.../ ... n005.../   # 5 node lengkap
data/domains/fastapi/edges.yaml                    # edge antar 5 node (Isyah tandai)
backend/app/services/
  node_loader.py       # baca folder node → validasi → upsert ke DB (§9 tables)
  node_schema.py       # pydantic model utk memvalidasi node.yaml & probe.yaml
scripts/
  verify_nodes.py      # jalankan SEMUA hidden test lawan reference_solution (pakai M1)
  load_nodes.py        # panggil node_loader untuk seluruh data/
backend/tests/
  test_node_loader.py  # node valid termuat; node cacat ditolak dgn pesan jelas
```

## Langkah implementasi (berurutan)

1. **`node_schema.py`.** Model pydantic untuk `node.yaml` & `probe.yaml`. Validasi:
   `grader_type` & `probe.type` dalam enum §9; `correct_answer` ada di `options`;
   `timebox_seconds` > 0; tiap node punya ≥2 varian instance & ≥1 probe. Skema ini
   yang mencegah node cacat masuk sistem.

2. **`scripts/verify_nodes.py` — GERBANG MUTU AUTHORING.** Untuk tiap instance:
   jalankan `hidden_test.py` lawan `reference_solution.py` via `SubprocessExecutor`
   (M1). **Semua harus PASS.** Skrip ini adalah penegak aturan §10 R4 ("test wajib
   hijau di solusi referensi"). Node yang merah **tidak boleh** di-commit. Buat
   skrip ini **lebih dulu**, lalu arang node sambil menjalankannya berulang.

3. **Arang node satu per satu (Isyah + draft R1/R4 manual/offline).** Untuk tiap
   node: tulis `node.yaml`, prompt, `reference_solution.py`, `hidden_test.py`,
   varian, probe. Jalankan `verify_nodes.py` sampai hijau. Boleh pakai Claude untuk
   *draft* (peran R1/R4, manual/offline — belum terintegrasi), tapi **Isyah prune &
   review**; hidden test tetap wajib dibuktikan hijau oleh skrip, bukan oleh klaim.

4. **`edges.yaml`.** Isyah menandai edge antar 5 node sebagai `hard`/`soft` dengan
   sumber. Ingat: **hanya `hard` yang mengikat urutan**; node independen bebas.
   Bryant tidak pernah menyentuh file ini (validitas — §1 PRD).

5. **`node_loader.py`.** Baca semua folder node, validasi via `node_schema`, upsert
   ke tabel `Node`, `ChallengeInstance`, `ComprehensionProbe`, `Edge`, `SourceRef`.
   Idempoten (jalan ulang tak menggandakan). `hidden_test_path` disimpan sebagai
   path relatif ke folder instance (file test **tidak** masuk DB, tetap di `data/`).

6. **`scripts/load_nodes.py` & `test_node_loader.py`.** Skrip memuat seluruh `data/`
   ke DB. Test membuktikan: node valid termuat utuh; node yang sengaja dicacatkan
   (probe tanpa `correct_answer` di options) ditolak dengan pesan jelas.

## Keputusan teknis penting

- **`verify_nodes.py` dibuat sebelum node pertama.** Ini inti disiplin M2: tak ada
  node yang dipercaya sebelum test-nya hijau otomatis. (RISK-1 mitigasi.)
- **File test tetap di `data/` (git), tidak di DB.** Hidden test adalah artefak yang
  di-review & di-diff seperti kode; DB hanya menyimpan *pointer*-nya. Memudahkan
  audit Isyah.
- **≥2 varian per node.** Verifikasi (L0) memakai instance **berbeda** dari worked
  example supaya lolos = transfer, bukan hafalan (§6 catatan 3d PRD). Open question
  PRD: minimum varian (dugaan 3) — mulai 2–3, tinjau nanti.
- **Node pertama (`n001`) sengaja non-FastAPI.** Membuktikan pipeline grading
  bekerja pada kasus paling sederhana sebelum menambah kompleksitas HTTP.

## Hal yang harus diperhatikan

- **Jangan bikin node kegedean.** "CRUD + auth service" itu epic, bukan node (§7.1).
  Kalau butuh >2 file test → pecah.
- Prompt & materi harus **just-in-time & pendek** — bukan bab course (§8 Guardrails).
  Godaan menulis "materi lengkap yang enak dibaca" harus dilawan.
- Probe harus **benar-benar deterministik**. "Menurutmu kenapa..." bukan probe yang
  sah; "baris mana yang menyebabkan X" sah.
- Hidden test harus menguji **perilaku**, bukan bentuk kode (jangan assert nama
  variabel) — supaya ada banyak solusi benar yang valid.

## Testing / validasi

```bash
python scripts/verify_nodes.py          # SEMUA instance hijau di reference solution
cd backend && pytest tests/test_node_loader.py -v
python scripts/load_nodes.py            # 5 node termuat ke SQLite
sqlite3 backend/app.db "SELECT id, grader_type FROM node;"   # 5 baris
```

## Expected result

- 5 node FastAPI lengkap di `data/`, semua hidden test hijau di solusi referensi.
- `edges.yaml` ditandai hard/soft oleh Isyah, bersumber.
- `load_nodes.py` mengisi DB dengan 5 node + instance + probe + edge.
- Node cacat ditolak loader dengan pesan yang bisa ditindaklanjuti.

## Acceptance criteria

- [ ] Format folder node final & terdokumentasi (dokumen ini + contoh nyata).
- [ ] `scripts/verify_nodes.py` melaporkan **100% hijau** untuk 5 node.
- [ ] Tiap node punya ≥2 varian instance & ≥1 comprehension probe deterministik.
- [ ] `edges.yaml` diisi & ditandai hard/soft oleh Isyah dengan `source_ref`.
- [ ] `node_loader` memuat 5 node ke DB secara idempoten; node cacat ditolak.
- [ ] Tidak ada node yang melanggar grain §7.1 (sekali duduk, ≤2 file test).
