# CLAUDE.md — Instruksi kerja untuk Claude Code di repo ini

Dokumen ini adalah konteks operasional untuk Claude Code (dan developer AI lain)
saat bekerja di repo **Reproduction Learning Engine**. Baca ini sebelum menulis
kode. Sumber kebenaran produk tetap
[`PRD-reproduction-learning-engine-v1.2.md`](PRD-reproduction-learning-engine-v1.2.md);
rencana teknis ada di [`docs/`](docs/README.md).

---

## 1. Invariant yang tidak boleh dilanggar (dari PRD §2 & §8)

Ini garis merah. Kalau sebuah tugas menyuruhmu melanggarnya, **berhenti dan
konfirmasi ke manusia** — kemungkinan besar tugasnya salah-baca, bukan invariant-nya.

1. **Ukuran belajar = `reproduce-without-AI`.** Bukan konsumsi materi, bukan lolos
   sekali jalan. Uji tiap fitur: menutup jurang produksi, atau bikin konsumsi
   nyaman? Kalau kedua → tolak/turunkan jadi pendukung.
2. **Hanya eksekusi kode yang boleh memutuskan mastery.** AI (termasuk kamu)
   **tidak pernah** menilai apakah user menguasai sebuah node. Kamu boleh
   mengusulkan hipotesis; hipotesis wajib diverifikasi lewat `Attempt` dan
   **tidak pernah** menjadi verdict.
3. **Tidak ada penilaian teks bebas.** Esai bebas butuh pemrosesan makna → pintu
   masuk AI-sebagai-hakim. Pemahaman diperiksa lewat **comprehension probe
   deterministik** (predict output / spot bug / trace) yang punya jawaban benar
   pasti. Refleksi teks bebas boleh disimpan sebagai catatan, **tak pernah jadi gate**.
4. **Edge prerequisite berasal dari sumber otoritatif + Isyah,** bukan dari LLM.
   Kamu boleh *mengusulkan* kandidat node/edge; Isyah yang prune & menandai
   `hard`/`soft`.
5. **Jangan bangun yang sudah ditolak di §8:** content library/bab materi panjang,
   AI penentu learning path, AI penilai mastery, esai sebagai gate, multi-domain/
   ingestion generik di v1, graf visual/DAG explorer di v1, `metric_threshold`
   sebagai grader ML utama, quiz pilihan ganda sebagai penilai utama.

**Gravitasi yang harus dilawan:** dorongan over-invest di DAG/visualisasi dan
under-build loop reproduksi. Loop reproduksi adalah MVP. DAG di v1 cukup daftar
node berurutan di file data.

---

## 2. Keputusan teknis yang sudah final (jangan diubah tanpa alasan tercatat)

| Keputusan | Nilai | Alasan singkat |
|---|---|---|
| Backend eksekusi test | **subprocess + venv + tempdir**, bukan Docker per attempt | Isolasi Docker "bukan soal keamanan" (PRD §11); kode milik pengguna sendiri. Disembunyikan di balik interface `Executor` agar bisa ditukar. |
| Bukan Pyodide untuk domain 1 | subprocess CPython asli | FastAPI/pydantic rapuh di WASM; varians WASM mengancam kepercayaan sinyal pass/fail |
| Scheduler | `py-fsrs` | Terbukti, open source. **Jangan tulis algoritma SR sendiri.** |
| DB | SQLite via SQLModel | Single-user local-first; SQLModel = SQLAlchemy+pydantic, idiom FastAPI |
| Node/edge store | YAML di `data/`, di-commit ke git | Kurasi manual, bisa di-diff & di-review seperti kode |
| Domain pertama | FastAPI (`unit_test`) | Grader paling deterministik (status/body HTTP itu biner) |
| Integrasi Claude Code | async via file artifact, bukan HTTP | Ia agent CLI (PRD §10). Fase 1/M3 harus jalan **tanpa** ini. |

Kalau kamu benar-benar perlu mengubah salah satu, catat di **§7 Log keputusan**
di bawah dengan alasan + alternatif yang ditolak (ikuti gaya PRD).

---

## 3. Konvensi kode

### Backend (Python / FastAPI)
- Python 3.11+. Package layout di bawah `backend/app/`.
- Pakai **SQLModel** untuk tabel; **pydantic** untuk skema request/response.
- Type hints wajib di boundary (fungsi publik, signature router, interface).
- Interface pakai `typing.Protocol` (mis. `Executor`, `Grader`), bukan ABC —
  supaya backend bisa ditukar tanpa pewarisan.
- Async hanya di router FastAPI; eksekusi subprocess boleh sync di thread pool.
- Format & lint: `ruff` (format + lint). Jalankan sebelum menyatakan selesai.
- Test: `pytest` di `backend/tests/`. Test aplikasi **terpisah** dari hidden test
  node (yang ada di `data/`).

### Frontend (Next.js)
- App Router. TypeScript. Komponen fungsional + hooks.
- Monaco dipakai sebagai editor sandbox. **Pastikan tidak ada fitur AI-assist /
  Copilot aktif** di editor sandbox — itu melanggar invariant §1.
- State server via fetch ke backend FastAPI; hindari state management berat di v1.

### Data (`data/`)
- Satu node = satu folder (lihat M2 untuk skema). Setiap `hidden_test` **wajib
  sudah terverifikasi hijau di `reference_solution`** sebelum di-commit — pakai
  harness M1. Node tanpa verifikasi hijau **tidak boleh masuk**.

### Umum
- Bahasa komentar & dokumen: **Indonesia** (konsisten dengan PRD & docs).
- Nama simbol kode: **Inggris** (idiom umum: `run_attempt`, `NodeLoader`).
- Commit message: imperatif singkat, sebut milestone bila relevan
  (`M1: add subprocess executor`).

---

## 4. Alur kerja yang diharapkan

1. **Selalu kerjakan dalam konteks satu milestone.** Buka
   [docs/milestones/](docs/milestones/), pastikan prerequisite-nya lolos.
2. Ikuti langkah implementasi milestone berurutan.
3. Sebelum menyatakan selesai: jalankan test + `ruff`, cek **acceptance criteria**
   milestone, dan pastikan tidak ada invariant §1 yang tergores.
4. Kalau menemukan keputusan tak terduga, catat di **§7 Log keputusan**.
5. Jangan menambah dependency besar tanpa alasan yang tercatat; stack sengaja
   condong ke yang sudah dikuasai Isyah (PRD §11) — stack asing = proyek mati.

---

## 5. Peran Claude Code di produk (bukan di repo) — untuk M5

Saat integrasi AI dibangun (M5), Claude Code punya peran terbatas & **async via
artifact** (PRD §10). Ringkas:

| Peran | Output | Gate |
|---|---|---|
| R1 Ekstraksi kandidat node/edge | `nodes.proposed.yaml`, `edges.proposed.yaml` + sitasi | Isyah prune & tandai hard/soft |
| R2 Bukti codebase | `hypotheses.json` | Hipotesis; **wajib** diverifikasi Attempt |
| R3 Materi just-in-time | `explanation.md` + worked example bersitasi | Sitasi wajib verifiable |
| R4 Generator soal | ChallengeInstance + hidden test + probe | Isyah review; test wajib deterministik & hijau di solusi referensi |

**Tidak pernah diberikan ke AI:** menetapkan edge final, menyatakan mastery,
menilai teks bebas.

---

## 6. Perintah cepat (diperbarui seiring milestone menyediakan komponen)

```bash
# Harness pytest telanjang (M1)
python harness/run.py <path-node-instance>

# Backend (M0+)
cd backend && uvicorn app.main:app --reload

# Test + lint backend
cd backend && pytest && ruff check .

# Frontend (M3+)
cd frontend && npm run dev
```

---

## 7. Log keputusan (append-only)

Catat di sini setiap keputusan teknis penting yang diambil selama implementasi,
terutama yang menyimpang dari PRD atau §2 di atas. Format: tanggal · keputusan ·
alasan · alternatif yang ditolak.

- **2026-08-21 · Backend eksekusi = subprocess+venv, bukan Docker per attempt.**
  Alasan: isolasi Docker "bukan soal keamanan" (PRD §11); reproducibility cukup
  dari venv ter-pin, isolasi cukup dari tempdir+timeout. *Ditolak:* Docker per
  attempt (latency & ops), Pyodide (rapuh untuk FastAPI, varians WASM merusak
  kepercayaan sinyal).
