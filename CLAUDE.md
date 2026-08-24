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
| Domain kedua & ketiga (M6) | React (`dom_behavior`, Node+vitest+jsdom) & ML (`value_assert`, numpy) | Menambah domain = menambah grader di balik `Executor`/`Grader` yang sama. Tak ada kolom DB baru, tak ada cabang per-domain di loop. |
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

# Muat seluruh node data/ ke SQLite (SEMUA domain; idempoten; dari repo root)
python scripts/load_nodes.py            # atau: python scripts/load_nodes.py react

# Gerbang mutu authoring — semua domain, lewat grader masing-masing (M6).
# DUA pemeriksaan per instance: referensi wajib HIJAU, starter wajib MERAH.
python scripts/verify_nodes.py                 # atau: ... verify_nodes.py ml
python scripts/verify_nodes.py --skip-starter  # 2x lebih cepat; JANGAN untuk commit

# Runtime grading React (M6) — sekali saja, sebelum node React bisa dinilai
cd runtime/react && npm install

# Frontend (M3+)
cd frontend && npm run dev
```

Halaman frontend (M4): `/` dashboard + KPI · `/node/[id]` sesi akuisisi L3→L0 ·
`/placement` menemukan lantai · `/review` sesi review jatuh tempo.
Halaman M5: `/authoring` meja review Isyah (antrean artifact Claude Code).

```bash
# Integrasi Claude Code (M5) — semuanya opsional bagi loop inti.
CLAUDE_INTEGRATION_ENABLED=0 uvicorn app.main:app --reload   # kill switch: trigger balas 503
```

Alur M5 satu artifact: `POST /authoring/{r2,r3,r4}` (balas `202`, job `pending`) →
Claude Code jalan di latar & menulis ke `artifacts/<role>/<stamp>/` → skema
(`contracts.py`) → gate otomatis R4 (eksekusi test) → `ready` → **Isyah approve di
`/authoring`** → promosi ke `data/`/DB. Tanpa approve, tak ada yang masuk sistem.
`artifacts/` git-ignored; yang di-commit adalah hasil promosinya di `data/`.

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

- **2026-08-21 · M2 · `DATABASE_URL` jadi path ABSOLUT (`backend/app.db`), bukan
  `sqlite:///./app.db` (cwd-relative) seperti default M0.** Alasan: uvicorn jalan
  dari `backend/`, sedangkan `scripts/*.py` jalan dari repo root — default relatif
  bikin DB terpecah jadi dua file (`./app.db` vs `backend/app.db`) tergantung cwd.
  Path absolut menunjuk satu DB stabil. *Ditolak:* memaksa semua entrypoint chdir
  (rapuh), atau env var `DATABASE_URL` wajib (beban setup untuk single-user local).

- **2026-08-21 · M2 · Tambah dependency `pyyaml`.** Alasan: node/edge/source store
  adalah YAML di `data/` (keputusan §2, PRD §11); loader butuh parser. Dep kecil,
  standar, hanya untuk membaca data — bukan untuk backend eksekusi (yang tetap
  stdlib-only per M1). *Ditolak:* parser YAML tulis-sendiri (buang waktu, rawan bug).

- **2026-08-21 · GERBANG 0 · Keputusan: LANJUT (build).** Isyah menginstruksikan
  eksekusi M4 setelah M3 selesai; per M4 §"Gerbang 0 wajib", keputusan build-vs-buy
  dicatat di sini sebagai **lanjut**, dan sejak titik ini mengikat: A2 + Fase 2 boleh
  jalan, biaya sesungguhnya (±20 node + FSRS + dashboard) diterima. *Ditolak:* berhenti
  di M3 dan memakai Execute Program (~$39/bln) saja — ia menutup primitif bahasa, tapi
  tidak menutup lapisan unit framework (FastAPI) yang justru jadi domain pertama, dan
  tak memberi sinyal `reproduce-without-AI` atas kurikulum milik Isyah sendiri.
  **Catatan jujur:** kalau ±1 bulan pemakaian Execute Program ternyata belum dijalankan,
  keputusan ini diambil tanpa data pembanding yang direncanakan PRD §12/RISK-5 —
  membalikkannya paling murah dilakukan SEKARANG, sebelum A2 (~30–60 jam) berjalan.

- **2026-08-22 · GERBANG 0 · Dikonfirmasi FINAL: BUILD sampai proyek selesai.** Isyah
  menegaskan M3 **tidak cukup** untuk kebutuhan Bryant; jalur build diteruskan sampai
  proyek rampung, bukan berhenti di M3. Ini menutup "catatan jujur" entri 2026-08-21:
  trial pembanding Execute Program **tidak akan** dijalankan sebagai gerbang — keputusan
  build diambil atas dasar konviksi kebutuhan (lapisan unit framework + sinyal
  `reproduce-without-AI` atas kurikulum sendiri tak tersedia di produk jadi). Konsekuensi:
  A2 (~30–60 jam authoring) & Fase 2+ berjalan penuh; titik pembalikan termurah dilepas
  secara sadar. *Ditolak:* menahan roadmap menunggu 1 bulan trial (menunda tanpa mengubah
  hasil, karena kebutuhan sudah jelas).

- **2026-08-21 · M4 · PRD Q5 · Hasil probe IKUT memberi rating FSRS, bukan sekadar
  gate.** Pemetaan tunggal di `services/scheduler.py`: test FAIL → `Again`; test PASS +
  probe SALAH → `Hard`; test PASS + probe BENAR → `Good`; test PASS tanpa probe
  (placement) → `Good`. Alasan: verdict biner membuang informasi yang sudah kita punya
  gratis — "bisa memproduksi tapi tak paham kenapa" jelas lebih rapuh daripada lolos
  bersih, dan itu persis yang dimodelkan `Hard`. **Batas keras:** probe hanya memengaruhi
  *interval*, tak pernah *menurunkan status* — hanya kegagalan eksekusi yang boleh
  membuat node `lapsed` (§2). `Easy` sengaja tak dipakai: tak ada sinyal deterministik
  ketiga; memakai durasi sebagai proksi = menjadwal dari angka berisik. *Ditolak:* probe
  murni gate (membuang sinyal), probe ikut menurunkan status (menggores §2).

- **2026-08-21 · M4 · PRD Q3 · `lapsed` kembali ke `acquired`, bukan `available`
  penuh.** Sekali pulih (lolos bersih lagi), node jadi `acquired` dengan
  `consecutive_success` direset ke 0 dan interval FSRS reset. Alasan: `available`
  berarti "belum pernah dibuktikan", padahal Bryant PERNAH memproduksinya — yang meluruh
  memorinya, bukan buktinya. Konsekuensi yang ikut diputuskan: **`lapsed` tidak mengunci
  ulang node hilirnya** (`progress.py` menganggap acquired/mastered/lapsed sama-sama
  "pernah dibuktikan"), supaya satu review buruk tak merobohkan separuh peta.
  *Ditolak:* turun ke `available` (menghapus bukti + thrashing lock di dashboard).

- **2026-08-21 · M4 · PRD Q4 · Placement maksimum 7 node per sesi
  (`PLACEMENT_MAX_NODES`), urutan menurun linear, berhenti di batas fail→pass pertama.**
  Sesi hampir selalu berhenti jauh lebih cepat; batas ini melindungi kasus terburuk
  (gagal terus sampai dasar) agar placement tak jadi maraton reproduksi yang justru
  merusak sinyalnya. Batas tercapai tanpa pass → `exhausted`, **tak ada status yang
  diberikan** ke node mana pun. *Ditolak:* binary search atas urutan node (lebih sedikit
  langkah, tapi menyimpang dari "rangkaian menurun" PRD dan sulit dibaca Bryant saat
  sesi berjalan), dan tanpa batas sama sekali.

- **2026-08-21 · M4 · Efek lantai placement: node lantai → `acquired`; prasyarat
  transitifnya hanya DIBUKA jadi `available`.** Node lantai lolos eksekusi tanpa
  scaffold apa pun — reproduksi lebih dingin daripada L0 di jalur akuisisi — jadi
  `acquired` tetap diputuskan eksekusi kode (§2 utuh) meski placement tak memakai probe.
  Prasyaratnya tak pernah dieksekusi, jadi maksimal dibuka; membuka ≠ mengklaim mastery.
  *Ditolak:* menandai seluruh prasyarat `acquired` (mengasumsikan — melanggar premis
  "lantai ditemukan"), atau membiarkannya `locked` (absurd: hilirnya sudah terbukti).

- **2026-08-21 · M4 · FSRS disetel tanpa learning/relearning steps & tanpa fuzzing.**
  Default py-fsrs punya learning step 1 menit & 10 menit — masuk akal untuk flashcard,
  absurd untuk tantangan reproduksi 20–40 menit; dikosongkan supaya interval berskala
  HARI sejak review pertama. Fuzzing dimatikan: single-user tak punya beban deck yang
  perlu disebar, sementara interval deterministik jauh lebih mudah di-debug & di-test.
  Algoritmanya tetap 100% milik py-fsrs (§2).

- **2026-08-21 · M4 · Tambah kolom: `ScheduleItem.fsrs_state/fsrs_step/last_review_at`
  dan `Attempt.session_id`; `db.init_db()` menambal kolom via `ALTER TABLE ADD COLUMN`.**
  py-fsrs butuh state+step+last_review untuk melanjutkan kartu (bukan cuma
  stability/difficulty/due); `Attempt.session_id` membuat tabel `Session` yang selama ini
  yatim jadi berguna — urutan attempt dalam SATU sesi placement-lah yang menentukan di
  mana batas fail→pass ditemukan. Migrasi ringan dipilih karena `create_all()` tak pernah
  menambah kolom ke tabel lama, dan tanpanya DB M3 milik Bryant harus dihapus (= progres
  hilang). *Ditolak:* Alembic (dep + direktori migrasi + ops untuk satu file .db
  single-user), dan "hapus app.db saja" (menghapus data sinyal inti).

- **2026-08-21 · M4 · KPI `reproduce-without-AI pass rate` dihitung HANYA dari attempt
  mode `verification`/`review`/`placement`.** Attempt mode `acquisition` (L3–L1, scaffold
  masih di layar) tidak dihitung. Alasan: memasukkannya menggelembungkan angkanya dengan
  latihan bersontekan — dan KPI yang menggelembung persis adalah illusion of competence
  yang produk ini dibangun untuk melawan.

- **2026-08-21 · M4 · Perbaikan bawaan M1/M2 yang ditemukan saat verifikasi di Windows.**
  (a) `SubprocessExecutor` gagal total di Windows karena `_ENV_WHITELIST` tak memuat
  `SYSTEMROOT` (Winsock gagal init → *semua* node FastAPI ter-grade FAIL), dan
  `os.killpg`/`SIGKILL` POSIX-only; sekarang whitelist punya cabang Windows dan timeout
  membunuh pohon proses lewat `taskkill /T`. (b) `node_loader._rel_to_repo` menyimpan
  `hidden_test_path` dengan `\` di Windows; sekarang selalu POSIX (`as_posix`) supaya
  pointer di DB tak berubah bentuk tergantung OS penulisnya. Tanpa keduanya, 6 test M1–M3
  merah dan M4 tak mungkin diverifikasi.

- **2026-08-21 · M2 · Format node dibekukan: `signature_contract` & `scaffold_level`
  hidup di `node.yaml` (level node), instance ditemukan dari folder `instances/*`.**
  Alasan: format M2 tak mendaftar file meta per-varian; varian berbagi konsep &
  kontrak yang sama (beda hanya data uji → transfer). `variant_label` = nama folder.
  Edge final dibaca dari `edges.yaml` (bukan dari blok `edges:` di node.yaml) supaya
  satu sumber kebenaran; blok edge di node.yaml (bila ada) hanya usulan, tak dimuat.

- **2026-08-22 · A2 · `test_node_loader` tak lagi mengunci JUMLAH node (5) & edge (4);
  ia menegakkan bentuk + subset node A1.** Batch A2 (n006–n013) membuat dua test M2 merah
  hanya karena kurikulum bertambah — padahal yang layak dijaga adalah invarian bentuk
  (≥2 varian/node, ≥1 probe/node, pointer `hidden_test_path` relatif POSIX, idempotensi),
  bukan ukuran kurikulum. Sekarang: batas bawah + `A1_NODE_IDS <= {node di DB}` (node A1
  tak boleh hilang), dan idempotensi dibandingkan terhadap hasil muatan pertama, bukan
  angka literal. *Ditolak:* menaikkan angka literal tiap batch authoring (test jadi
  pekerjaan rumah tiap node baru, dan tetap tak menangkap regresi bentuk).

- **2026-08-22 · A2 · Satu probe per node (probe_01), bukan 2–3.** `routers/nodes.py`
  dan `routers/review.py` mengambil probe dengan `.first()`, jadi probe kedua tak akan
  pernah tampil — menulisnya = konten mati yang tetap harus di-review. Urutan `options`
  juga sengaja divariasikan posisinya (UI `ProbeCard` merender apa adanya, tanpa
  pengacakan); jawaban benar yang selalu di posisi 1 melatih posisi, bukan konsep.
  *(Dicabut sebagian di M5: pemilihan probe kini bergilir — lihat entri `pick_probe`.)*

- **2026-08-22 · M5 · State job Claude Code hidup di FILE (`artifacts/<role>/<stamp>/job.json`),
  bukan tabel DB.** Artifact-lah sumber kebenaran integrasi (PRD §10 "async lewat file"),
  jadi menyalin statusnya ke DB berarti dua sumber yang bisa berbeda. Efek samping yang
  diinginkan: loop inti tak punya ketergantungan skema pada M5 — matikan integrasi, tak
  ada tabel yatim; hapus satu folder, hilang satu usulan. *Ditolak:* tabel `AuthoringJob`
  (query lebih enak, tapi menambah migrasi & bikin kill switch tak lagi bersih).

- **2026-08-22 · M5 · Approve Isyah WAJIB untuk ketiga peran — R3 tidak auto-approve.**
  M5 langkah 4 membuka kemungkinan "R3 auto dengan sitasi terverifikasi"; ditolak karena
  yang bisa diverifikasi mesin hanyalah bahwa `source_ref_id` ADA di `sources.yaml` —
  bukan bahwa klaimnya benar-benar ditopang sumber itu. Auto-approve atas dasar
  pemeriksaan yang lebih lemah dari namanya justru pintu masuk materi salah yang
  terlihat bersitasi. Konsekuensi yang diterima: materi baru muncul setelah Isyah
  meninjau, jadi kegagalan pertama Bryant mungkin belum berpendamping materi.

- **2026-08-22 · M5 · Materi R3 digerbangi server: `GET /nodes/{id}/explanation` balas 403
  selama node belum punya attempt GAGAL.** Kalau gerbangnya cuma di UI, `explanation.md`
  berubah jadi bab bacaan yang bisa dilahap sebelum mencoba — content library yang
  ditolak §8, lewat pintu belakang. Materi lahir dari kegagalan nyata atau tidak sama
  sekali. Trigger R3 pun menolak node tanpa attempt gagal.

- **2026-08-22 · M5 · Gate otomatis R4 punya DUA pemeriksaan, bukan satu.** Selain
  "hidden test hijau di `reference_solution`" (aturan §10 R4), soal juga ditolak bila
  `starter_code` SUDAH lolos hidden test — kerangka yang lolos berarti tantangannya
  kosong dan kelulusannya tak membuktikan apa pun. Keduanya eksekusi kode, keduanya
  jalan sebelum artifact sampai ke manusia.

- **2026-08-22 · M5 · `hypotheses.json` dengan daftar KOSONG adalah artifact yang SAH
  (+ field `note`).** Ditemukan saat uji CLI sungguhan: model yang tak bisa membaca repo
  menulis daftar kosong + penjelasan, dan skema lama menolaknya sebagai error. Itu salah
  arah — menolak "tak ada bukti" berarti menekan model mengarang hipotesis demi memuaskan
  skema, persis kegagalan termahal di peran ini (RISK-4). Sekarang kosong = `ready` dengan
  0 baris; alasannya tampil apa adanya ke Isyah. R3/R4 tetap wajib berisi.

- **2026-08-22 · M5 · Pemilihan probe BERGILIR (`services/scaffold.pick_probe`), tidak lagi
  `.first()`.** Begitu R4 bisa mengarang probe baru, `.first()` membuat setiap probe kedua
  jadi konten mati yang tetap memakan waktu review. Rotasi memakai jumlah attempt node
  sebagai indeks: deterministik (bisa di-test), tapi tak menyodorkan pertanyaan yang sama
  tiap node muncul lagi. *Ditolak:* acak (tak bisa di-test & tak bisa direproduksi).

- **2026-08-22 · M6 · Domain kedua/ketiga: React (`dom_behavior`) & ML (`value_assert`).
  Runtime React = Node + vitest + jsdom di `runtime/react/`, di balik `Executor` yang
  SAMA.** Interface M1 terbukti menyembunyikan bahasa runtime: `NodeExecutor` memenuhi
  Protocol yang sama dengan `SubprocessExecutor`, dan tak satu pun pemanggil (grader,
  loop, scheduler) tahu bedanya. Dependency JS ter-pin di `package.json` — analog venv
  ter-pin. *Ditolak:* menjalankan React lewat Pyodide/subprocess Python (mustahil),
  dan menyalin `node_modules` per grading (absurd) — direktori kerja grading justru
  ditaruh di bawah `runtime/react/.work/` supaya resolusi `node_modules` menaik normal.

- **2026-08-22 · M6 · `REACT_EXECUTION_TIMEOUT_SECONDS = 120`, bukan 10 seperti Python.**
  Bukan karena kode React lebih lambat, tapi karena start-up-nya: vitest menyalakan
  jsdom + mentransform JSX (±50 detik dingin, ±7 detik panas). Menyamakannya dengan
  10 detik akan membuat submisi BENAR ter-grade FAIL — kegagalan terburuk untuk sistem
  yang seluruh kepercayaannya bersandar pada sinyal pass/fail.

- **2026-08-22 · M6 · Toleransi numerik ML hidup di `data/` (`expected.json`:
  `rtol`/`atol`), BUKAN di kolom DB.** Kolom `rtol` akan jadi kolom khusus-ML pertama
  di skema yang sengaja tak tahu domainnya apa (§9/M0) — persis kebocoran yang M6 ada
  untuk mengujinya. Sebagai berkas di folder instance, ia ikut di-review & di-diff
  seperti kode. Grader `value_assert` merakitnya jadi modul `expected` yang di-import
  hidden test. *Ditolak:* menanam angka toleransi di dalam hidden test (tak terlihat
  saat review node) dan kolom DB baru.

- **2026-08-22 · M6 · `metric_threshold` TIDAK didaftarkan sama sekali; `structural`
  ditunda sampai ada node arsitektur.** `metric_threshold` mengukur HASIL — Bryant bisa
  menyalin training loop dan menembus ambang tanpa paham (§7.4/§8), jadi ia tak boleh
  jadi jalur termudah yang tersedia. `structural` ditunda karena grader tanpa node
  adalah kode yang tak pernah dijalankan, dan itu yang paling cepat membusuk.

- **2026-08-22 · M6 · Bahasa editor diturunkan dari BERKAS node, bukan dari `domain_id`.**
  `graders/files.editor_language` memetakan ekstensi (`.py`/`.jsx`) → mode Monaco, lalu
  ikut di response `LevelView`/`ReviewChallenge`/`PlacementChallenge`. Alternatif yang
  ditolak: `if domain == "react"` di UI (cabang per-domain pertama, dan pintu masuk
  untuk cabang berikutnya) atau kolom `language` baru di DB (menggores §9).

- **2026-08-23 · Gerbang authoring `verify_nodes.py` kini menuntut DUA hal: referensi
  hijau DAN `starter_code` merah.** Pemeriksaan kedua sebelumnya cuma dijalankan
  ad-hoc saat authoring A2/M6. Alasan menaikkannya jadi gerbang: kerangka L2 yang sudah
  lolos apa adanya membuat node itu bukan sekadar tak berguna — ia MEMALSUKAN sinyal
  inti produk, karena Bryant bisa menekan "Jalankan" tanpa memproduksi apa pun dan
  tercatat sebagai `reproduce-without-AI` yang berhasil. Aturan yang sama sudah berlaku
  untuk soal buatan AI sejak gate R4 (M5); tak ada alasan node tulisan tangan lolos
  dengan standar lebih rendah. Biayanya waktu run 2x lipat (±5 menit untuk 39 instance);
  disediakan `--skip-starter` untuk iterasi cepat, dengan peringatan tercetak agar tak
  dipakai sebagai dasar commit. *Ditolak:* menjadikannya peringatan saja (gerbang yang
  boleh diabaikan bukan gerbang).

- **2026-08-22 · M6 · Perbaikan kebocoran abstraksi yang baru terlihat saat ada domain
  kedua.** (a) `node_loader` mengenali berkas instance dari NAMA DASAR, bukan ekstensi
  `.py`. (b) `verify_nodes.py` kini memverifikasi lewat `get_grader(...)` — gerbang
  authoring menguji persis yang dinilai saat submit, bukan salinan aturannya sendiri.
  (c) `load_domain_into_db` hanya me-reset edge MILIK DOMAIN yang dimuat; versi lama
  menghapus seluruh tabel Edge, yang begitu domain kedua masuk akan diam-diam membuka
  node terkunci di domain pertama. (d) `Executor`/`Grader` Protocol jadi
  `runtime_checkable` supaya kontraknya bisa DIUJI, bukan cuma dipercaya.

- **2026-08-22 · M5 · R2 mendapat akses baca repo lewat `--add-dir`, bukan lewat cwd.**
  cwd proses Claude Code selalu direktori job — supaya satu-satunya tempat ia bisa
  menulis adalah `artifacts/`. Repo Bryant ditambahkan terpisah sebagai direktori yang
  boleh DIBACA. Argv lengkap disimpan ke `command.log` tiap job: saat artifact-nya aneh,
  pertanyaan pertama selalu "dipanggil dengan flag apa", dan menebaknya belakangan mahal
  (biaya ini sudah dibayar sekali saat verifikasi).

- **2026-08-23 · M-UI · Fondasi styling frontend = Tailwind CSS v3.4 + design tokens
  (CSS variables). DEVIASI SADAR dari §11 (stack condong ke yang sudah dikuasai).**
  Sampai M6 seluruh frontend memakai inline `style={{}}` (nol file CSS), warna Primer
  di-hardcode & diduplikasi di ~12 berkas, semua tombol default browser — akibatnya
  aksi terpenting produk (**Jalankan & Verifikasi**) tak terbedakan dari aksi sekunder,
  dan UI terasa "kosong & kaku". Isyah memilih Tailwind (bukan CSS murni yang
  direkomendasikan agent demi §11) untuk iterasi cepat + ekosistem. Mitigasi risiko §11:
  warna TIDAK di-hardcode di config — semua menunjuk CSS variable di `app/globals.css`
  (`:root`), jadi satu sumber kebenaran warna dan jalur dark mode nanti cukup tambah
  blok `.dark`. Dibangun komponen primitif (`app/components/ui/{Button,Card,Container,
  PageHeader,EmptyState,Badge,Icon}`) yang menutup duplikasi. **Batasan Isyah: TANPA
  emoji** (bikin tampilan terasa "AI slop") — status/verdict pakai warna token + ikon
  garis SVG inline (bukan icon-pack, bukan emoji); glyph `🎉`/`✓`/`✗`/`⏱`/`⚠` lama
  diganti. Perbaikan UX terukur ikut dikerjakan: CTA primer dibedakan, timebox slot
  lebar tetap (tak lagi menggeser layout), hint editor kosong, feedback "PASS tapi probe
  salah" diberi kalimat konsekuensi, peta progres dikelompokkan per domain (tetap DAFTAR
  LINEAR — §8 tak dilanggar, bukan DAG explorer). Invariant dijaga: SandboxEditor tetap
  matikan semua AI-assist (§2), TestOutput tetap menampilkan kegagalan (§7.6). Pass ini
  murni frontend — tak ada perubahan backend/DB/skema. *Ditolak:* CSS murni (lebih
  selaras §11 tapi iterasi lebih lambat & tanpa ekosistem utility), component library
  (shadcn/MUI — paling berat, menarik banyak dependency, paling jauh dari §11).

- **2026-08-24 · UI · Monaco di-self-host (dependency langsung `monaco-editor@0.55.1`),
  bukan diunduh runtime dari cdn.jsdelivr.** Alasan: `@monaco-editor/react` default
  memuat Monaco dari CDN publik saat runtime — melanggar klaim *local-first* (offline =
  editor tak pernah muncul) dan membiarkan versi/perilaku editor ditentukan CDN, risiko
  integritas untuk invariant §2 (jaminan "tanpa saran AI"). Kini di-bundle lokal via
  `loader.config({ monaco })` + worker `editor.worker` lewat `new Worker(new URL(...))`.
  Ter-code-split (First Load JS halaman tetap ~104 kB). *Ditolak:* tetap CDN (rapuh &
  tak ter-pin), meng-eject seluruh worker Monaco (tak perlu — layanan bahasa dimatikan).

- **2026-08-24 · UI · Token `--subtle` dinaikkan `#8c959f`→`#656d76` + pola `opacity-70`
  untuk menandai disabled diganti token `--fg-disabled`.** Alasan: `#8c959f` gagal WCAG
  AA (kontras 2.85 di canvas), dan `opacity-70` menumpuk di atasnya (turun ke ~2.0) untuk
  mayoritas kartu terkunci — praktis tak terbaca. Token eksplisit lulus AA & bisa diaudit.
  *Ditolak:* biarkan opacity (kontras tak terprediksi), turunkan target ke AA-large (teks
  kecil butuh 4.5).
