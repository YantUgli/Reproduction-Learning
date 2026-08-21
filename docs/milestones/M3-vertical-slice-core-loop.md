# M3 — Vertical Slice / Core Loop (Fase 1)

> Peta PRD: Fase 1 · Dependency: M1, M2 · Estimasi: 2–3 minggu

## Tujuan

Membangun **loop reproduksi minimal yang jalan end-to-end** dengan 5 node dari M2:
Bryant membuka node → belajar (scaffold memudar) → memproduksi solusi dari nol di
sandbox editor tanpa AI → hidden test dijalankan → comprehension probe → hasil
dicatat sebagai `Attempt`. **Tujuan tunggal:** membuktikan sinyal
`reproduce-without-AI` benar-benar terbaca.

**Yang belum ada di M3 (sengaja):** FSRS, placement probe, dashboard mastery,
integrasi Claude Code otomatis. Scheduler masih manual/interval statis. Sistem
harus bernilai **bahkan kalau integrasi AI (M5) gagal total** (RISK-3).

## Konteks & alasan

Ini MVP sesungguhnya — inti yang dilindungi PRD dari scope creep. Semua guardrail
§8 mengerucut ke sini: loop reproduksi di-build, DAG/visualisasi **tidak**. M3
adalah akhir "slice pertama" (M0–M3, ~3–4 minggu) yang **non-blocking** terhadap
Gerbang 0. Kalau Execute Program ternyata cukup, roadmap boleh berhenti setelah M3.

## Prerequisite

- **M1 selesai** — `Executor` siap dipakai grader.
- **M2 selesai** — 5 node termuat ke DB, hidden test hijau.

## File / komponen yang dibuat

```
backend/app/
  graders/
    base.py              # Grader Protocol: grade(instance, submitted_code) -> GradeResult
    unit_test.py         # grader unit_test: rakit files -> Executor -> pass/fail
    registry.py          # grader_type -> Grader
  services/
    attempt_service.py   # orkestrasi: submit -> grade -> probe -> simpan Attempt
    scaffold.py          # ambil instance per scaffold_level utk sebuah node
  routers/
    nodes.py             # GET /nodes, GET /nodes/{id} (+instance sesuai scaffold)
    attempts.py          # POST /attempts (submit kode), GET riwayat
    probes.py            # GET probe, POST jawaban probe (cek deterministik)
frontend/app/
  page.tsx               # dashboard sederhana: daftar node + status
  node/[id]/page.tsx     # sesi node: penjelasan -> worked example -> faded -> VERIFY -> probe
  components/
    SandboxEditor.tsx    # Monaco; NO AI assist
    Timebox.tsx          # hitung mundur timebox_seconds
    ProbeCard.tsx        # render probe deterministik
backend/tests/
  test_grader_unit_test.py
  test_attempt_flow.py   # submit benar -> pass+acquired; salah -> fail
```

## Alur core loop yang diimplementasikan (§5–§6 PRD)

```
Sesi node:
  L3  Penjelasan just-in-time (pendek, dari data node) + worked example beranotasi
  L2  Faded reproduction: kerangka ada, bagian inti dikosongkan
  L1  Signature + spesifikasi saja
  L0  VERIFIKASI: instance BERBEDA, tanpa AI, timebox jalan, hidden test dijalankan
      → lalu comprehension probe
Hasil:
  lolos bersih (test PASS + probe benar) → status `acquired`
  gagal → kembali ke L-lebih-tinggi
```

## Langkah implementasi (berurutan)

1. **`graders/base.py` + `unit_test.py`.** `Grader` Protocol:
   `grade(instance, submitted_code) -> GradeResult(passed, test_output, ...)`.
   `UnitTestGrader` merakit `files` (`submitted_code` sebagai file solusi +
   `hidden_test.py` dari `hidden_test_path`), memanggil `Executor.run(...)` (M1)
   dengan `timeout = node.timebox_seconds` (atau timeout eksekusi terpisah — lihat
   Keputusan). `registry.py` memetakan `grader_type` → instance grader; v1 hanya
   `unit_test` terdaftar.

2. **`scaffold.py`.** Diberi `node_id` + `scaffold_level`, kembalikan instance yang
   tepat: L3 tampilkan worked example (reference beranotasi), L2/L1 tampilkan
   `starter_code` dengan derajat pengosongan berbeda, L0 pilih instance **varian
   berbeda** dari yang dipakai worked example (transfer, bukan hafalan — §6 3d).

3. **`attempt_service.py`.** Orkestrasi submit: terima `node_id`, `instance_id`,
   `scaffold_level`, `submitted_code`, `duration_seconds`. Panggil grader → jalankan
   probe (cek `correct_answer` deterministik) → simpan `Attempt` (`mode`,
   `result`, `test_output`, `probe_result`). Kalau L0 & `result=pass` & probe benar
   → set `ScheduleItem.status = acquired` (belum `mastered` — itu M4). Kalau gagal →
   tetap catat Attempt, arahkan UI naik scaffold.

4. **Router `nodes`, `attempts`, `probes`.** Endpoint REST tipis di atas service.
   `POST /attempts` adalah jantungnya. Pastikan response memuat `test_output` supaya
   UI bisa menampilkan kegagalan test ke Bryant (itu sinyal belajar, bukan hukuman).

5. **`SandboxEditor.tsx` (Monaco).** Editor kode di dalam aplikasi. **Wajib:
   nonaktifkan semua AI-assist/autocomplete cerdas** — ini penegakan invariant §2
   di UI. Sediakan tombol "Jalankan & Verifikasi" yang mengirim ke `POST /attempts`.

6. **`Timebox.tsx`.** Hitung mundur `timebox_seconds`. Saat habis, submit otomatis
   atau tandai attempt sebagai lewat-timebox. Timebox adalah bagian desain
   integritas (§7.6), bukan hiasan.

7. **`node/[id]/page.tsx`.** Rangkai alur L3→L0→probe. User selalu tahu posisinya
   (referensi UX e-learning yang jelas — tapi **flow** yang direferensi, bukan
   kenyamanan konsumsi; task tetap sulit — §6).

8. **`page.tsx` dashboard sederhana.** Daftar linear node + status (`locked/
   available/acquired`). **Bukan graf visual** (§8 Guardrails — gravitasi builder).
   Node `locked` bila `hard` edge prasyaratnya belum `acquired`.

9. **Scheduler statis sementara.** Tanpa FSRS: node yang `acquired` boleh
   dimunculkan ulang lewat interval tetap sederhana atau tombol "review". FSRS
   sungguhan menyusul di M4.

## Keputusan teknis penting

- **Grader di balik `Executor` M1, bukan eksekusi langsung.** Semua eksekusi lewat
  satu interface → M4/M6 tinggal menambah grader, bukan menyentuh cara eksekusi.
- **Verifikasi L0 memakai instance berbeda dari worked example.** Ini bukan detail
  kecil: inilah yang membedakan "transfer" dari "hafalan contoh" (§6 3d).
- **`acquired` ≠ `mastered`.** M3 hanya sampai `acquired` (lolos sekali). `mastered`
  butuh lolos berulang berjarak → itu M4 (FSRS). Jangan mengklaim mastery di M3.
- **Kegagalan test ditampilkan, bukan disembunyikan.** `test_output` ke UI. Produk
  adalah *cermin* (§7.6) — Bryant perlu melihat kenapa gagal.
- **Timeout eksekusi vs timebox UI.** Bedakan: `timebox_seconds` = batas waktu
  Bryant berpikir (UI). Timeout eksekusi runner = batas kode menggantung (mis. 10s).
  Keduanya beda; jangan disatukan.

## Hal yang harus diperhatikan

- **Ini titik paling rawan scope creep** (RISK-7). Tekanan menambah "materi yang
  nyaman", "peta DAG keren", "quiz konseptual" akan muncul. Semua ditolak §8.
  Kalau ragu, tanya: menutup jurang produksi atau bikin konsumsi nyaman?
- Editor Monaco default punya autocomplete; pastikan yang cerdas/AI dimatikan.
  Autocomplete sintaks dasar boleh, saran solusi tidak.
- Jangan bangun placement probe di sini (itu M4). M3 mulai dari daftar node manual.
- Simpan **setiap** Attempt (termasuk yang gagal & yang lewat-timebox) — itu data
  sinyal inti produk (`reproduce-without-AI pass rate`, §9 KPI).

## Testing / validasi

```bash
cd backend && pytest tests/test_grader_unit_test.py tests/test_attempt_flow.py -v
uvicorn app.main:app --reload
cd ../frontend && npm run dev
```
Uji manual end-to-end: buka node → lewati L3–L1 → di L0 tulis solusi benar dari nol
→ Verifikasi → test PASS → probe benar → status jadi `acquired`. Lalu ulangi dengan
solusi **salah** → FAIL → UI mengarahkan naik scaffold, Attempt gagal tercatat.

## Expected result

- Bryant bisa menyelesaikan satu node penuh dari L3 sampai L0 di dalam aplikasi,
  tanpa AI, dengan timebox berjalan.
- Submit di L0 menjalankan hidden test sungguhan dan menghasilkan verdict
  pass/fail yang benar, plus probe deterministik.
- Setiap Attempt tercatat di DB; status node berubah ke `acquired` saat lolos bersih.
- Dashboard menampilkan daftar node + status (bukan graf).

## Acceptance criteria

- [ ] Loop L3→L0→probe jalan end-to-end untuk kelima node M2 di UI nyata.
- [ ] `POST /attempts` menjalankan hidden test via `Executor` dan menyimpan `Attempt`
      lengkap (`result`, `test_output`, `probe_result`, `duration_seconds`, `mode`).
- [ ] Verifikasi L0 memakai instance berbeda dari worked example.
- [ ] Editor sandbox terbukti **tanpa** AI-assist; timebox berjalan & ter-enforce.
- [ ] Status `acquired` di-set hanya saat test PASS **dan** probe benar; `mastered`
      **tidak** diklaim di sini.
- [ ] Tidak ada graf visual/DAG explorer, tidak ada bab materi panjang (§8 bersih).
- [ ] `pytest` backend hijau; sinyal `reproduce-without-AI` terbaca dari data Attempt.
