# PROMPT — Authoring node A2 (FastAPI) untuk Reproduction Learning Engine

> Serahkan blok di bawah ini apa adanya ke agent lain. Ia self-contained, tapi
> agent WAJIB membaca `CLAUDE.md` dan `docs/milestones/M2-authoring-and-first-nodes.md`
> di repo sebelum mulai. Jangan ubah invariant.

---

## Tugasmu

Karang **batch node FastAPI baru (A2)** untuk kurikulum Reproduction Learning Engine,
melanjutkan node yang sudah ada (`n001`–`n005`). Target run ini: **6–8 node baru**
(`n006_…` dan seterusnya), masing-masing lengkap, terverifikasi hijau, siap dimuat.

Ini bukan menulis "materi bacaan". Ini mengarang **tantangan reproduksi**: spesifikasi
tajam + solusi referensi + hidden test deterministik + comprehension probe. Ukuran
keberhasilan produk adalah `reproduce-without-AI` — user memproduksi konsep dari nol,
dibuktikan dengan eksekusi kode.

## Garis merah (dari CLAUDE.md §1 — jangan dilanggar)

1. **Hanya eksekusi kode yang menilai mastery.** Grader = `pytest` deterministik
   (status/body HTTP itu biner). Tidak ada penilaian teks bebas. Tidak ada AI-as-judge.
2. **Probe harus deterministik** — tipe `predict_output` / `spot_bug` / `trace`, punya
   `correct_answer` yang PASTI dan wajib salah satu dari `options`.
3. **Kamu MENGUSULKAN edge, tidak memfinalkan.** `edges.yaml` adalah wewenang Isyah.
   Tulis usulan edge ke `data/domains/fastapi/edges.proposed.yaml` (bukan `edges.yaml`),
   tandai `type: hard|soft` sebagai USULAN. Jangan sentuh `edges.yaml`.
4. **Tetap satu domain: FastAPI, grader `unit_test`.** Jangan `metric_threshold`, jangan
   multi-domain, jangan quiz pilihan-ganda sebagai penilai utama.
5. **Node tanpa verifikasi hijau TIDAK BOLEH dianggap selesai.** Gate mutu = wajib.

## Format node (WAJIB persis — divalidasi `node_schema.py`)

Satu node = satu folder di `data/domains/fastapi/nodes/<id>/`:

```
nodes/n006_xxx/
  node.yaml
  instances/
    variant_a/
      prompt.md            # markdown (kini di-render: heading, list, bold, `code`, ```fence```)
      reference_solution.py
      hidden_test.py
      starter_code.py
    variant_b/             # WAJIB ≥ 2 varian (L0 verifikasi pakai varian BEDA → transfer)
      prompt.md
      reference_solution.py
      hidden_test.py
      starter_code.py
  probes/
    probe_01.yaml          # ≥ 1 probe
```

### `node.yaml` (field pasti; `extra` dilarang)
```yaml
id: n006_xxx                # sama dengan nama folder
domain_id: fastapi
concept: "<kalimat konsep singkat>"
description: >
  <1–3 kalimat, kenapa node ini & apa yang dilatih>
grader_type: unit_test
estimated_minutes: 12       # > 0
timebox_seconds: 900        # > 0 (batas BERPIKIR user; ≈ estimated_minutes × 60–90)
status_default: locked      # 'locked' bila punya prasyarat hard; 'available' bila independen
source_refs: [fastapi_official_docs]   # id dari data/sources.yaml (lihat di bawah)
signature_contract: "@app.get('<path>') def f(...) -> dict"
scaffold_level: L2          # L0..L3 — level awal scaffold node ini
```

### `instances/<variant>/reference_solution.py`
- Modul yang, saat di-`import` sebagai `solution`, mengekspos yang diuji.
- Untuk FastAPI: harus mendefinisikan `app = FastAPI()` + route sesuai prompt.
- Contoh (dari n002):
  ```python
  from fastapi import FastAPI
  app = FastAPI()

  @app.get("/status")
  def read_status():
      return {"service": "orders", "ok": True}
  ```

### `instances/<variant>/hidden_test.py`
- `pytest` yang meng-`import` dari modul `solution` (kode user/solusi disimpan sebagai
  `solution.py` saat grading).
- Untuk FastAPI pakai `TestClient`. Deterministik total — cek status code & body persis.
- Contoh:
  ```python
  from fastapi.testclient import TestClient
  from solution import app

  client = TestClient(app)

  def test_status_code_200():
      assert client.get("/status").status_code == 200

  def test_body_exact():
      assert client.get("/status").json() == {"service": "orders", "ok": True}
  ```
- **Varian A dan B harus menguji KONSEP sama dengan DATA berbeda** (mis. path/nilai
  beda), supaya lolos L0 = transfer, bukan hafalan.

### `instances/<variant>/starter_code.py`
- Kerangka L2: struktur ada, bagian inti dikosongkan dengan `# TODO:` sesuai prompt.

### `probes/probe_01.yaml`
```yaml
id: n006_probe_01
node_id: n006_xxx
type: predict_output        # atau spot_bug | trace
question: "<pertanyaan dengan jawaban pasti>"
options:                    # ≥ 2 opsi
  - "..."
  - "..."
correct_answer: "..."       # WAJIB persis sama dengan salah satu options
```

## Sumber (`source_refs`)
`node.yaml.source_refs` harus menunjuk `id` yang ADA di `data/sources.yaml`
(mis. `fastapi_official_docs`, `fastapi_docs_query_params`, `fastapi_docs_body`).
Kalau butuh sumber baru, **usulkan** dengan menambah entri ke `data/sources.yaml`
(format: `id`, `type` ∈ {cs2023_ku, textbook_toc, official_docs}, `citation`,
`url_or_locator`) — Isyah akan me-review.

## Topik yang diinginkan (A2 = perluasan setelah n001–n005)
n001–n005 menutup: fungsi murni+pytest, GET route dasar, path param+404, query param
default+422, POST body pydantic. Perluas ke konsep FastAPI deterministik berikutnya,
mis. (pilih 6–8, urut dari yang paling fondasional):
- `response_model` / pemfilteran field response
- status code eksplisit (`status_code=201`, `Response`)
- `HTTPException` dengan detail & status non-404 (400/403/409)
- validasi query constraint (`Query(..., min_length/gt/le)`) → 422
- validasi path constraint (`Path(..., gt=0)`)
- nested pydantic model / list body
- multiple path+query params bergabung
- header/cookie param sederhana
- form data / `Optional` field dengan default
- dependency sederhana (`Depends`) yang deterministik

Pilih yang **grader-nya biner** (status/body). Hindari apa pun yang butuh penilaian makna.

## Alur kerja WAJIB (verifikasi sebelum menyatakan selesai)

Environment: Windows, backend venv di `backend/.venv`. Dari **repo root**:

```bash
# 1. Gate mutu — SEMUA hidden test harus hijau lawan reference_solution:
backend/.venv/Scripts/python.exe scripts/verify_nodes.py     # WAJIB exit 0

# 2. Muat ke DB & cek ringkasan bertambah:
backend/.venv/Scripts/python.exe scripts/load_nodes.py

# 3. Jaga test & lint app tetap hijau:
cd backend && .venv/Scripts/python.exe -m pytest -q && .venv/Scripts/ruff.exe check .
```

**Kalau `verify_nodes.py` tidak exit 0, node itu belum selesai — perbaiki, jangan
lanjut.** Node merah tidak boleh diserahkan.

## Deliverable akhir (laporkan ke Isyah)
- 6–8 folder node baru lengkap (node.yaml + ≥2 varian + ≥1 probe).
- `edges.proposed.yaml` berisi usulan prasyarat antar node baru & ke node lama
  (jangan sentuh `edges.yaml`).
- Bukti `verify_nodes.py` exit 0 (tempel output ringkas).
- Ringkasan: id node, konsep, sumber, dan alasan urutan/prasyarat yang diusulkan.
- **Jangan commit** kecuali Isyah meminta; kalau diminta, satu commit per batch dengan
  pesan `A2: tambah N node FastAPI (nXXX–nYYY)` dan sertakan
  `Co-Authored-By:` sesuai konvensi repo.

## Jangan
- Jangan menulis materi/bab panjang (guardrail §8: content library ditolak).
- Jangan memfinalkan edge, menyatakan mastery, atau menilai teks bebas.
- Jangan menambah dependency baru; stack sudah cukup (fastapi, pytest, TestClient).
- Jangan mengaktifkan fitur AI-assist di mana pun.
