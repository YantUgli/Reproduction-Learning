# M6 — Domain Kedua: React → ML (Fase 4)

> Peta PRD: Fase 4 · Dependency: M4 (M5 opsional) · Estimasi: variabel

## Tujuan

Membuktikan klaim **engine domain-agnostic** dengan menambah domain kedua **tanpa
mengubah loop, scaffold, scheduler, atau mastery** — hanya menambah **grader baru**
via `grader_type`. Urutan: **React/Next.js (`dom_behavior`)** dulu, lalu **ML
(`value_assert` pada komponen kecil)**.

## Konteks & alasan

§7.4 PRD: "tidak ada mode belajar terpisah untuk coding vs AI/ML. Flow, scaffold,
scheduler, mastery — identik lintas domain. Yang berbeda hanya modul verifikasi."
M6 adalah ujian nyata dari desain itu. Kalau menambah domain butuh menyentuh loop,
berarti ada kebocoran abstraksi yang harus diperbaiki — bukan di-*hardcode*.

**Build order dari PRD (§7.4):** FastAPI (`unit_test`, biner) → React
(`dom_behavior`, timing effect lebih halus) → ML (butuh 2–3 grader baru). Engine
harus terbukti dengan grader termudah dulu — itu sudah dilakukan di M3.

## Prerequisite

- **M4 selesai** (loop penuh + FSRS). M5 opsional (authoring bisa manual seperti M2).
- Untuk React: runtime eksekusi DOM (lihat Keputusan). Untuk ML: numpy di venv.

## File / komponen yang dibuat

```
backend/app/graders/
  dom_behavior.py       # render komponen + interaksi + assert perilaku (React)
  value_assert.py       # assert nilai numerik lawan expected (ML komponen kecil)
  structural.py         # cek shape tensor / jumlah & urutan layer (arsitektur model)
data/domains/react/     # node React (dom_behavior), format sama seperti M2
data/domains/ml/        # node ML (value_assert / structural)
backend/tests/
  test_grader_dom_behavior.py
  test_grader_value_assert.py
```

## Langkah implementasi (berurutan)

### Bagian A — React (`dom_behavior`)
1. **Pilih runtime eksekusi DOM.** React di-grade di lingkungan JS (browser-native /
   jsdom + testing-library), **bukan** subprocess Python. Ini konsisten dengan
   temuan diskusi: domain React memang jalan di browser — tak butuh Docker. Bungkus
   di balik interface `Executor` yang sama (kontrak `files → pass/fail`), backend
   berbeda (Node/jsdom).
2. **`dom_behavior.py` grader.** Render komponen submisi, jalankan interaksi
   (klik/isi), assert perilaku (teks muncul, state berubah). Assert **perilaku**,
   bukan struktur JSX.
3. **Node React (format M2).** Arang beberapa node dengan gerbang mutu sama: hidden
   test hijau di solusi referensi. Perhatikan timing effect & dependency array —
   lebih halus dari FastAPI (§7.4).

### Bagian B — ML (`value_assert`, lalu `structural`)
4. **`value_assert.py` grader.** Assert nilai numerik lawan expected dengan
   toleransi (mis. implement `softmax`/`backprop` sendiri, assert gradiennya).
   Condongkan node ke **komponen kecil**, bukan training end-to-end.
5. **`structural.py` grader (opsional).** Cek shape tensor / jumlah & urutan layer
   untuk node arsitektur model.
6. **⚠️ `metric_threshold` dipakai sangat terbatas.** Grader ini mengukur *hasil*,
   bukan *pemahaman* — Bryant bisa menyalin training loop dan tembus ambang tanpa
   paham (§7.4 peringatan). Untuk ML, **default ke `value_assert` pada komponen
   kecil**. Jangan jadikan `metric_threshold` grader utama (§8 Guardrails).

## Keputusan teknis penting

- **Menambah domain = menambah grader, titik.** Kalau kamu mendapati diri menyentuh
  `scheduler.py`, `mastery.py`, atau alur scaffold untuk domain baru — berhenti. Itu
  tanda abstraksi bocor; perbaiki interface, jangan bikin cabang per domain.
- **Grader React pakai backend JS di balik interface yang sama.** Interface
  `Executor`/`Grader` menyembunyikan bahasa runtime. Ini validasi arsitektur M1.
- **ML condong `value_assert` komponen kecil, bukan `metric_threshold`.** Ini
  keputusan produk (mengukur pemahaman, bukan hasil), bukan sekadar teknis.
- **Toleransi numerik eksplisit.** `value_assert` butuh `rtol/atol` yang
  didokumentasikan per node; jangan pakai perbandingan `==` untuk float.

## Hal yang harus diperhatikan

- Jangan tergoda membangun "pipeline ingestion multi-domain generik" di sini — itu
  Fase 5, dan §8 menolak generalisasi prematur ("bottleneck proyek ini kurasi data,
  bukan kode").
- React authoring lebih mahal per node karena `dom_behavior` lebih halus; alokasikan
  waktu lebih. Mulai dari komponen kecil deterministik.
- Untuk ML, hindari node yang butuh dataset besar/GPU — melanggar grain "sekali
  duduk" (§7.1) dan local-first (§11).
- Domain-agnostic skema (M0) harus tetap utuh: tidak ada kolom baru khusus React/ML.
  Kekhususan hidup di `grader_type` + isi `data/`.

## Testing / validasi

```bash
cd backend && pytest tests/test_grader_dom_behavior.py tests/test_grader_value_assert.py -v
```
Uji manual: selesaikan satu node React lewat loop yang **sama** dengan FastAPI
(L3→L0→probe, FSRS, mastery) — buktikan tak ada cabang khusus domain di loop. Ulangi
untuk satu node ML `value_assert`.

## Expected result

- Node React & ML berjalan melalui loop, scaffold, scheduler, dan mastery yang
  **identik** dengan FastAPI — hanya grader yang berbeda.
- `dom_behavior` meng-assert perilaku React; `value_assert` meng-assert nilai numerik
  dengan toleransi.
- `metric_threshold` tidak dipakai sebagai grader ML utama.

## Acceptance criteria

- [x] Grader `dom_behavior` & `value_assert` terpasang di balik interface yang sama.
      Keduanya memakai `Grader` Protocol yang sama dan mendelegasikan ke `Executor`;
      `NodeExecutor` (Node+vitest+jsdom) memenuhi Protocol yang sama dengan
      `SubprocessExecutor` — diuji lewat `isinstance` di `test_grader_dom_behavior.py`.
      **`structural` sengaja TIDAK dibuat**: belum ada node arsitektur, dan grader
      tanpa node adalah kode yang tak pernah dijalankan.
- [x] Node React & ML lengkap, hidden test hijau di solusi referensi.
      3 node React (`r001`–`r003`) + 3 node ML (`m001`–`m003`), masing-masing 2 varian
      & 1 probe. `verify_nodes.py` → **39/39 instance hijau** lintas 3 domain, dan
      seluruh `starter_code` terbukti GAGAL (tantangannya tidak kosong).
- [x] Loop/scaffold/scheduler/mastery **tidak diubah** untuk mendukung domain baru.
      `test_domain_agnostic_loop.py` membuktikannya dua lapis: node React & ML bergerak
      lewat `submit_attempt`/`answer_probe`/`apply_outcome` yang sama sampai `acquired`
      & `mastered`, DAN 10 modul loop diperiksa tak punya cabang atas
      `domain_id`/`grader_type` (test merah kalau ada yang menambahkannya).
- [x] ML memakai `value_assert` pada komponen kecil; `metric_threshold` **tidak
      terdaftar sama sekali** di registry. Toleransi eksplisit per node
      (`expected.json` → `rtol`/`atol`), diuji: angka yang sama lolos dengan `rtol`
      longgar dan gagal dengan `rtol` ketat.
- [x] Skema data tetap domain-agnostic — **nol kolom baru**. Yang berbeda antar domain
      hidup di `grader_type` + isi `data/` (termasuk toleransi ML dan ekstensi berkas).

## Yang ikut diperbaiki (kebocoran abstraksi yang baru terlihat saat domain kedua ada)

M6 §Keputusan: "kalau menambah domain butuh menyentuh loop, itu abstraksi bocor —
perbaiki interface". Tiga kebocoran ditemukan & ditutup, semuanya di lapisan
authoring/IO, bukan di loop:

1. **`node_loader` mengunci ekstensi `.py`.** Berkas instance kini dikenali dari nama
   dasar (`reference_solution.*`), jadi `.jsx` masuk tanpa perlakuan khusus.
2. **`verify_nodes.py` punya salinan aturan eksekusinya sendiri** (langsung memanggil
   `SubprocessExecutor`). Sekarang ia memakai `get_grader(node.grader_type)` — gerbang
   authoring memverifikasi persis yang dinilai saat Bryant submit.
3. **`load_domain_into_db` menghapus SELURUH tabel Edge tiap muat.** Benar untuk satu
   domain; begitu domain kedua dimuat ia menghapus edge domain pertama dan membuka
   node yang seharusnya terkunci. Kini hanya edge milik domain itu yang di-reset.

Ditambah satu perbaikan UI yang lahir dari domain kedua: editor sandbox tak lagi
mengunci `language="python"` — bahasanya diturunkan dari **berkas node** (bukan dari
`domain_id`), jadi node React dapat highlight JavaScript tanpa cabang per-domain.
