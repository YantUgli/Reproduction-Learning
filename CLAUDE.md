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
4. **Edge prerequisite tidak pernah berdiri di atas asersi LLM.** Kamu boleh
   *mengusulkan* kandidat node/edge; edge sah setelah berpaut sumber otoritatif **dan**
   lolos validasi mesin (bukti konstruk hulu terpakai di `reference_solution` hilir +
   validasi prediktif dari data `Attempt`). Approve Isyah tak lagi jadi gerbang blokir —
   lihat §7 entri 2026-08-31 (termasuk status implementasinya).
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
| R1 Ekstraksi kandidat node/edge | `nodes.proposed.yaml`, `edges.proposed.yaml` + sitasi | Validasi mesin: bukti konstruk + prediktif dari `Attempt` (§7 2026-08-31) |
| R2 Bukti codebase | `hypotheses.json` | Hipotesis; **wajib** diverifikasi Attempt |
| R3 Materi just-in-time | `explanation.md` + worked example bersitasi | Kutipan verbatim cocok dengan snapshot sumber; sampai ke Bryant hanya lewat gerbang 403 |
| R4 Generator soal | ChallengeInstance + hidden test + probe | Triad eksekusi (kosong MERAH, starter MERAH, referensi HIJAU) + probe terverifikasi eksekusi |

**Tidak pernah diberikan ke AI:** menyatakan mastery, menilai teks bebas, atau
menetapkan edge final dari asersi belaka (tanpa lolos validasi mesin — §7 2026-08-31).

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

# Gerbang mutu authoring — semua domain, lewat grader masing-masing (M6, TRIAD di M7).
# TIGA pemeriksaan per instance (referensi HIJAU, solusi kosong MERAH, starter MERAH)
# + tiap probe DIJALANKAN untuk membuktikan kunci jawabannya benar.
python scripts/verify_nodes.py                 # atau: ... verify_nodes.py ml
python scripts/verify_nodes.py --skip-starter  # 3x lebih cepat; JANGAN untuk commit

# Snapshot sumber otoritatif (L3) — bahan pembanding gerbang kutipan verbatim.
# WAJIB sebelum sebuah source_ref boleh dikutip peta Library ATAU dipakai gate R3.
# Isinya TIDAK PERNAH diketik manusia/AI: unduhan (`fetch`) atau berkas Bryant (`manual`).
python scripts/fetch_source.py --id fastapi_docs_first_steps
python scripts/fetch_source.py --all              # semua sumber ber-URL yang belum ada
python scripts/fetch_source.py --id buku_bab3 --from-file bab3.txt   # sumber non-URL

# Lajur Library (L1–L3) — scaffolder (gerbang TULIS) & validator (gerbang BACA)
python scripts/library_scaffold.py --spec <spec.yaml> [--dry-run]
python scripts/verify_library.py                  # atau: ... --capture <file>

# Runtime grading React (M6) — sekali saja, sebelum node React bisa dinilai
cd runtime/react && npm install

# Frontend (M3+)
cd frontend && npm run dev
```

Halaman frontend (M4): `/` dashboard + KPI · `/node/[id]` sesi akuisisi L3→L0 ·
`/placement` menemukan lantai · `/review` sesi review jatuh tempo.
Halaman M5: `/authoring` meja audit — node/edge tertandai telemetri + tombol pensiun
(dulu antrean approve blokir; §7 2026-08-31).

```bash
# Integrasi Claude Code (M5) — semuanya opsional bagi loop inti.
CLAUDE_INTEGRATION_ENABLED=0 uvicorn app.main:app --reload   # kill switch: trigger balas 503
CLAUDE_AUTO_PROMOTE=0 uvicorn app.main:app --reload          # M7: artifact berhenti di `ready`
```

Alur satu artifact (M5, diubah M7): `POST /authoring/{r2,r3,r4}` (balas `202`, job `pending`) →
Claude Code jalan di latar & menulis ke `artifacts/<role>/<stamp>/` → skema
(`contracts.py`) → gerbang mesin (triad eksekusi R4, probe DIJALANKAN, kutipan verbatim
R3) → `ready` → **promosi otomatis** ke `data/`/DB. Tanpa lolos gerbang mesin, tak ada yang
masuk sistem. Peninjauan manusia pindah ke belakang: `GET /authoring/audit` melaporkan node
tertandai telemetri + edge yang belum terkukuhkan (halaman frontend-nya belum ada).
`CLAUDE_AUTO_PROMOTE=0` mengembalikan alur lama (berhenti di `ready`, menunggu approve).
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

- **2026-08-28 · UI · Auto-indent editor DIHIDUPKAN: `autoIndent: "none"` → `"advanced"`
  (SandboxEditor).** Membalik keputusan lama (dulu `"none"` untuk mencegah `def f():`⏎`    x`
  jadi 8 spasi). Alasan pembalikan: `"none"` mematikan SELURUH auto-indent — termasuk
  "pertahankan indent baris sebelumnya" — sehingga tiap Enter di body fungsi melempar kursor
  ke kolom 0, menyakitkan untuk mengetik Python. `"advanced"` mengaktifkan `onEnterRules`
  bawaan Monaco per-bahasa (Python & JS/TS untuk React `.jsx`): indent otomatis setelah baris
  `…:` dan keep-indent. Aman §2 — whitespace deterministik, bukan saran solusi. Penggandaan
  8-spasi lama bukan perilaku otomatis; hanya muncul bila user mengetik spasi manual di atas
  indent otomatis (sama seperti di VSCode/IDE, dan Bryant sudah terbiasa tak melakukannya).
  *Ditolak:* `"full"` (ikut me-reindent baris SAAT mengetik → berisiko mengacak
  `starter_code` scaffold L2), dan meniru ekstensi "Python Indent" VSCode dari nol (auto-dedent
  sesudah `return/pass/break/raise` via onEnterRules kustom — ditunda; tak ada di built-in
  Monaco, bisa ditambahkan belakangan bila dirindukan). Perubahan satu opsi, murni frontend.

- **2026-08-31 · AUTONOMI · Approve Isyah dicabut sebagai gerbang BLOKIR; diganti
  tumpukan gerbang mesin + telemetri kurikulum. Membalik keputusan 2026-08-22 M5
  ("Approve Isyah WAJIB untuk ketiga peran") dan melonggarkan §1.4.** Tujuan yang
  diminta Isyah: Bryant bisa belajar dan mendapat materi **tanpa Isyah di jalur**.
  Yang membuat ini bisa diterima tanpa menggores inti: peran Isyah di sistem ini
  **tak pernah** gerbang *mastery* — verdict selalu eksekusi kode (§1.2) — melainkan
  gerbang **kualitas konten**. Maka §1.2 dan §1.3 tidak tersentuh sedikit pun; yang
  dilonggarkan hanya §1.4 dan gate approve M5. Asimetri yang menopangnya: **node buruk
  memakan waktu Bryant** (terlihat, terbatas, bisa dicabut retroaktif), **verdict
  mastery buruk menanam keyakinan palsu** (tak terlihat, korosif) — hanya kategori
  pertama yang diotomasi.

  **Gerbang pengganti** (semuanya mesin/eksekusi, jalan sebelum artifact masuk sistem):
  (a) dua-pemeriksaan R4 lama dinaikkan jadi **triad** — berkas kosong MERAH, starter
  MERAH, referensi HIJAU; (b) **probe wajib terverifikasi eksekusi** — `probe_*.yaml`
  mendapat field snippet/ekspresi, harness menjalankannya, `correct_answer` wajib sama
  dengan output nyata dan tiap distractor wajib berbeda (hari ini probe masih prosa,
  tak terperiksa mesin sama sekali); (c) **grounding R3 naik dari "ID sumber ada" ke
  "kutipan verbatim cocok"** — teks sumber di-snapshot ke `data/sources/<id>.md`, tiap
  klaim membawa kutipan yang dicek sebagai substring; (d) **edge butuh bukti, bukan
  asersi LLM** — konstruk hulu harus benar-benar terpakai di `reference_solution` hilir,
  dan klaim prasyarat divalidasi prediktif dari data `Attempt`; (e) deteksi
  tumpang-tindih — reference solution node lama tak boleh lolos hidden test node baru.

  **Pengganti mata Isyah di level kurikulum = telemetri, bukan audit manusia:** pass
  rate, waktu-sampai-lolos vs `estimated_minutes`, lapse rate FSRS, dan daya beda per
  node — semuanya dari data yang sudah tersimpan. Node lolos-100%-tanpa-pernah-gagal =
  trivia; node tak-pernah-lolos = rusak. Ini bisa dilakukan proyek ini dan **tak bisa**
  dilakukan sistem rujukan: Eero/Alter boleh full-AI-assisted justru karena tak ada satu
  momen pun di sistem mereka yang bisa ketahuan salah — gate mereka MCQ/"Test me" yang
  dinilai AI sendiri, jadi kurikulum buruk tak meninggalkan jejak. Metrik mereka ("terasa
  diajar") tak mungkin gagal; metrik proyek ini (pass rate reproduksi dingin) bisa turun.
  Keberhasilan mereka karena itu bukan bukti yang bisa dipinjam.

  **Batas yang diterima sadar:** (1) **n=1** — statistik per-node dari satu pelajar itu
  berisik, jadi telemetri hanya **MENANDAI** node curiga; **tak ada pensiun otomatis**,
  pencabutan selalu satu klik manusia. (2) **Relevansi terhadap tujuan tak punya oracle**
  di sistem mana pun; ia ditetapkan manusia **sekali per domain** (`destination`), bukan
  per node. `/authoring` berubah fungsi: dari antrean blokir jadi **meja audit + tombol
  pensiun**.

  **Konsekuensi untuk lajur KM** ([docs/brainstorm-knowledge-management-lane.md](docs/brainstorm-knowledge-management-lane.md)):
  tanpa manusia yang membaca materi generate sebelum sampai ke Bryant, gerbang **403**
  (materi hanya muncul setelah attempt gagal) menjadi **satu-satunya** perlindungan
  tersisa terhadap content library §8. Karena itu **prosa penjelasan buatan AI tidak
  pernah mendarat di `library/`** — ia hidup di `artifacts/` dan sampai hanya lewat 403;
  `library/` memuat tulisan/transkripsi Bryant + kerangka & indeks saja.

  **STATUS IMPLEMENTASI per 2026-09-01 (M7 dikerjakan):** (a) triad, (b) probe tereksekusi,
  (c) grounding verbatim, telemetri, dan promosi otomatis **SUDAH** terpasang. (d) bukti edge
  diturunkan jadi laporan dan (e) deteksi tumpang-tindih dibatalkan — keduanya dengan bukti
  pengukuran, lihat entri 2026-09-01. Yang BELUM: halaman audit frontend, tombol pensiun,
  `destination` per domain, dan snapshot `data/sources/<id>.md` (tanpa snapshot, job R3
  ditolak — itu perilaku yang diinginkan, bukan bug).

  *Ditolak:* (i) mempertahankan approve blokir (tujuan gagal total — Bryant menunggu
  manusia untuk tiap materi); (ii) audit manusia berkala ±15 menit per 20 node (usul awal
  agent; dicabut karena telemetri melakukannya lebih baik, terus-menerus, dan dari oracle
  yang sama yang memvonis mastery); (iii) nol manusia sepenuhnya termasuk `destination`
  (menghemat sangat sedikit, dan melepas satu-satunya pemeriksa arah kurikulum);
  (iv) pensiun otomatis dari telemetri (n=1 terlalu berisik — akan mencabut node bagus
  di hari Bryant sedang buruk).

- **2026-09-01 · M7 · Pelaksanaan gerbang mesin: tiga penyimpangan dari rencana, semuanya
  karena diuji atas kurikulum nyata sebelum dipasang.** Rencana M7 ditulis sebelum
  kodenya ada; tiga bagiannya tak selamat dari kontak dengan data.

  (a) **Bukti edge statis DITURUNKAN dari gerbang jadi laporan.** Rencana: konstruk khas
  hulu wajib muncul di `reference_solution` hilir, kalau tidak edge `hard` ditolak.
  Diukur atas 14 edge hard / 19 node, aturan itu menandai **6–7 edge dan hampir semuanya
  salah tuduh**. Sebabnya struktural, bukan ambang: sidik jari dibangun dari token yang
  JARANG (kalau tidak, `def`/`app` membuat semua edge "terbukti"), padahal konstruk yang
  benar-benar diwariskan node fondasi justru yang PALING SERING muncul — `@app.get` ada
  di hampir tiap node FastAPI. Filternya membuang persis bukti yang dicari. Kesimpulan
  yang dipegang: **kesamaan konstruk bisa MENGUKUHKAN edge, ketiadaannya tidak
  membuktikan edge itu salah.** Sekarang `edge_evidence.corroboration()` melaporkan
  (11/14 terkukuhkan, 3 belum) dan tak pernah memblokir. Pengganti gerbangnya adalah
  pembatasan AKIBAT: **edge usulan AI hanya boleh `soft`** — hanya `hard` yang mengunci
  urutan, jadi edge soft yang salah cuma saran keliru, sedangkan edge hard yang salah
  mengunci Bryant keluar dari node yang sebenarnya siap ia kerjakan.

  (b) **Deteksi tumpang-tindih (langkah 5) DIBATALKAN.** Aturannya ("reference solution
  lama tak boleh lolos hidden test baru") diuji lebih dulu: di `n001_paginate`, referensi
  `variant_a` LOLOS hidden test `variant_b` — dan kedua varian itu sah. Untuk node fungsi
  murni, kontraknya memang sama dan transfer diuji lewat DATA, jadi solusi umum yang benar
  wajar lolos semua varian. Aturan itu akan menolak pekerjaan yang benar. Deteksi duplikat
  antar-NODE tetap masuk akal, tapi belum ada jalur kode yang membuat node baru (R1 masih
  manual) — dan grader tanpa node adalah kode yang tak pernah dijalankan (preseden M6
  `structural`). *Ditolak:* memasangnya sebagai peringatan (peringatan yang 100% salah di
  satu kelas node akan diabaikan, lalu ikut menulikan peringatan lain).

  (c) **Probe dapat field `expected_value`, dan gate AI dibuat LEBIH KETAT daripada
  gerbang manusia.** Saat migrasi, ternyata banyak `correct_answer` bukan nilai yang
  diproduksi program melainkan prosa ("kosong (0 byte)") atau rumus (`(2/n) * X.T @ ...`).
  Templat "PROBE_RESULT == correct_answer" hanya cocok untuk 8 dari 19. `expected_value`
  memisahkan teks yang DITAMPILKAN dari nilai yang DIEKSEKUSI, sehingga klaim di balik
  opsi tetap dibuktikan (`m003` diverifikasi dengan membandingkan rumusnya terhadap
  gradien numerik). Batasnya: jembatan prosa→nilai ditulis manusia dan tak terperiksa
  mesin. Karena itu **probe buatan AI dilarang memakainya** — di jalur itu tak ada penulis
  yang bisa ditanya, jadi jawabannya wajib berupa nilai yang persis keluar dari eksekusi.

  Ikut ditemukan & diperbaiki (semuanya kebocoran `.py` yang baru terlihat saat gerbangnya
  benar-benar dijalankan lintas domain): gate R4 (`jobs._gate_r4`) menilai lewat
  `SubprocessExecutor` mentah + membaca `reference_solution.py` literal — artinya node
  React/ML **tak pernah benar-benar tergerbang**; `contracts.load_challenge` menolak
  artifact `.jsx` di skema sebelum gate sempat jalan; `review_queue` menulis varian hasil
  promosi dengan ekstensi `.py` mati. Plus satu bug fatal di gerbang authoring:
  `verify_nodes.py` MATI dengan `UnicodeEncodeError` saat mencetak output vitest (U+276F
  di konsol cp1252) — persis ketika sedang melaporkan kegagalan, jadi pesan yang paling
  dibutuhkan justru yang hilang.

- **2026-09-04 · L0 · Lajur Library dibuka kembali dari §8 — TAPI sebagai peta +
  catatan bersitasi, BUKAN bab materi. Batas keras: prosa penjelasan sintesis AI tak
  pernah mendarat di `library/`.** §8 menolak "content library/bab materi panjang"; L0
  membuka lajur `library/` tanpa menghidupkan yang ditolak itu, dengan menetapkan apa
  yang boleh & tak boleh mendarat di sana. Roadmap lengkap:
  [`docs/roadmap-library-lane.md`](docs/roadmap-library-lane.md); arah:
  [`docs/brainstorm-knowledge-management-lane.md`](docs/brainstorm-knowledge-management-lane.md).

  **Boleh di `library/`:** catatan & transkripsi tulisan Bryant sendiri, kerangka/indeks
  course, roadmap belajar, sitasi terkurasi ke sumber otoritatif (`id` di `data/sources.yaml`),
  dan `node_ids` (link ke node Forge). **TIDAK boleh:** prosa penjelasan yang disintesis
  AI — itu tetap hidup di `artifacts/` dan sampai ke Bryant **hanya lewat gerbang 403**
  (materi muncul sesudah attempt gagal). Ini menegakkan, bukan melonggarkan, konsekuensi
  entri 2026-08-31: tanpa manusia yang membaca materi generate sebelum sampai ke Bryant,
  403 adalah **satu-satunya** penjaga tersisa terhadap content library, jadi ia tak boleh
  di-bypass lewat pintu `library/`.

  **Dua penjaga yang menyertai pembukaan ini:** (1) **grounding** — apa pun yang generate
  di `library/` cuma peta + sitasi ke sumber otoritatif, bukan sintesis; "baca senyaman
  Dicoding" diarahkan ke sumber ASLI yang ditunjuk peta + catatan milik Bryant, bukan
  parafrase LLM. (2) **"% direproduksi, bukan % dibaca"** — status reproduksi TIDAK
  disimpan di frontmatter materi; ia dihitung dashboard (L5) dengan join `node_ids` → DB
  Forge. Menyimpannya di dua tempat = dua sumber kebenaran (pola yang sudah ditolak: job
  state di file, toleransi ML di `data/`).

  **Format beku (lihat `library/README.md`):** `library/` **di-commit ke git** (kebalikan
  `artifacts/` yang git-ignored) dan di-diff seperti `data/`; dibuka di Obsidian untuk
  graf. Bentuk: `library/<course>/<NN-modul>/<materi>.md` + `_index.md` per level.
  Frontmatter: `title, course, module, type (note|transcription|outline|roadmap),
  source_refs, node_ids, status (outline|captured), created`. `status` = status CATATAN
  (kerangka kosong vs sudah berisi), **bukan** status reproduksi.

  **Konsekuensi untuk roadmap:** L3 (`learn-intake`) di-reframe dari "generate bab materi
  → Library" menjadi "generate roadmap + sitasi + usul node → Library; sintesis penjelasan
  → artifacts/403". Roadmap docs diperbarui seiring entri ini.

  *Ditolak:* (i) materi generate sebagai bab yang dibaca di `library/` sebelum mencoba
  (membalik 2026-08-31; 403 tak lagi jadi penjaga tunggal, membuka §8 lewat pintu
  belakang); (ii) hybrid — simpan bab generate tapi kunci per-file gaya 403 (biaya build
  besar untuk kenyamanan yang justru sudah dijaga 403 di `artifacts/`, dan menduplikasi
  mekanisme gerbang); (iii) `status: forged` di frontmatter (dua sumber kebenaran dengan
  DB — status reproduksi hanya boleh datang dari eksekusi kode, §1.2).

- **2026-09-04 · L2 · `note-refine`: overwrite menggantikan create-only; guard lunak =
  disiplin skill + Bryant baca diff.** L1 aman *by construction* (scaffolder deterministik,
  nol prosa AI). L2 memang harus menulis ke stub yang sudah ada, jadi create-only pecah di
  sini — diganti dengan: `library/` di-commit ke git (beda `artifacts/` yang git-ignored),
  jadi git = undo kapan saja. Dua bagian mekanis tetap keluar dari tangan AI: (a) **flip
  `status`** hanya lewat `scripts/verify_library.py --capture` yang mengecek body berisi
  dulu (body masih stub → tolak), dan (b) **validasi refs ⊆ registry** (`source_refs` ⊆
  `data/sources.yaml`, `node_ids` ⊆ node `data/domains/`). AI berperan sebagai **editor**
  (perbaiki bahasa/struktur/format teks Bryant), bukan penulis: celah ditandai
  `> TODO: …`, tak pernah ditambal prosa. Format L0 beku dijaga: himpunan 8 field wajib
  persis, `type`/`status` hanya nilai sah; field asing atau hilang ditolak validator.
  **Batas yang diterima sadar:** L2 menaruh teks sentuhan-AI ke `library/`, tapi (a)
  input milik Bryant, (b) penjaga metrik bikin catatan rapi tak pernah menggerakkan mastery
  %, (c) Bryant reviewer atas tulisannya sendiri, (d) gerbang 403 tetap satu-satunya jalan
  prosa generate — dan L2 dilarang mensintesis. *Ditolak:* citation-teeth gaya R3
  (melebur L2→L3, terlalu berat), raw-preserved verbatim (dobel konten), refuse-on-dirty-tree
  (friksi commit tiap sesi), formatter nol-AI (turun jadi linter, tak merestruktur dikte).

- **2026-09-05 · L3 · `learn-intake`: peta belajar bersitasi masuk `library/` di balik
  DUA gerbang mesin (tulis + baca); snapshot sumber `data/sources/` akhirnya lahir —
  dan itu menghidupkan lajur R3 yang mati sejak M7.** L3 adalah fase pertama lajur
  Library yang menaruh teks hasil riset AI ke `library/`. Yang dibangun **bukan**
  generator materi melainkan **peta** yang menunjuk sumber asli. Gerbang penggantinya
  (semua mesin, tak ada approve manusia — sejalan §7 2026-08-31):

  (a) **Gerbang sitasi = snapshot + kutipan verbatim, bukan "id terdaftar".** Gerbang
  lama ("`source_ref` ADA di `sources.yaml`") *self-satisfying* begitu AI boleh menulis
  ke registry: karang sitasi, daftarkan id, lolos — celah yang diakui apa adanya di entri
  M5 2026-08-22. L3 memakai mesin yang **sama** dengan gate R3: `MIN_QUOTE_CHARS` &
  `normalize` **di-import** dari `backend/app/services/grounding.py`, tidak disalin (dua
  salinan gerbang = satu gerbang yang menyimpang diam-diam).
  (b) **Isi snapshot TIDAK PERNAH diketik AI.** `scripts/fetch_source.py` yang menulisnya:
  unduhan HTTP (`provenance: fetch`) atau berkas yang **Bryant** sediakan (`--from-file`,
  `provenance: manual`). Kalau AI boleh mengarang isi `data/sources/<id>.md`, pemeriksaan
  "kutipan ⊆ snapshot" jadi melingkar. Pola yang sama dengan L1 (scaffolder yang menulis)
  dan L2 (script yang flip status): **bagian yang menentukan dikeluarkan dari tangan AI.**
  (c) **AI boleh menambah entri ke `sources.yaml` tanpa menunggu manusia** — pendaftaran
  id bukan gerbangnya: URL karangan gagal diunduh → tak ada snapshot → tak ada kutipan
  yang bisa lolos.
  (d) **Penulis berkas tetap scaffolder deterministik.** AI merakit `spec.yaml`;
  `library_scaffold.py` yang menyentuh disk, create-only.
  (e) **Batas "peta vs bab" dibuat MEKANIS, bukan disiplin prompt:** dilarang code fence
  di file `type: roadmap` (fence di peta adalah sinyal paling jujur bahwa ia berubah jadi
  materi), prosa non-kutipan ≤ `MAX_ROADMAP_PROSE_CHARS = 3000` (preseden
  `EXPLANATION_MAX_CHARS = 2500`), `reproduce` ≤ 200 karakter, dan tiap file roadmap
  wajib punya `source_refs` non-kosong yang sudah ter-snapshot.
  (f) **Gerbang dipasang dua kali di dua waktu:** `check_grounding` (TULIS — peta cacat
  tak pernah lahir, nol berkas ditulis) dan `roadmap_errors` (BACA — menangkap suntingan
  tangan sesudahnya, dan snapshot yang berubah karena `--force`).

  **Kutipan hidup di file `type: roadmap`; catatan hidup di file `type: note`.** Aturan
  gerbang dikunci ke `type`, bukan ke tebakan isi. Konsekuensi yang harus disadari:
  **kutipan di file `note` TIDAK diverifikasi** — jadi sitasi generate dilarang di sana.
  Kandidat node ditulis sebagai **teks di body peta**, bukan field frontmatter ke-9 dan
  bukan `nodes.proposed.yaml`: belum ada konsumennya sampai L4, dan preseden M6
  (`structural`) + M7 langkah 5 sudah menghukum "pipa tanpa konsumen" sebagai kode yang
  tak pernah dijalankan. `node_ids` tetap kosong; node lahir di L4.

  **Efek samping yang disengaja: `data/sources/` menghidupkan R3.** Job R3 selama ini
  ditolak `NO_SNAPSHOT` (§7 2026-08-31 "Yang BELUM: … snapshot `data/sources/<id>.md`").
  Dua snapshot nyata sudah ter-commit; satu kerja, dua lajur.

  **Batas yang diterima sadar:** (1) kutipan verbatim membuktikan **kutipannya nyata**,
  bukan bahwa kutipan itu **menopang** entri petanya — itu penalaran, dan tak ada mesin
  di sini yang melakukannya (kalimat yang sama sudah tertulis apa adanya di
  `grounding.py`; jangan mengklaim lebih). (2) `--from-file` adalah lubang yang disisakan
  **sengaja** untuk sumber non-URL (buku, PDF, transkrip); penjaganya bukan mesin
  melainkan label `provenance: manual` yang tampak di diff + larangan keras di SKILL
  (AI tak pernah memasok berkasnya sendiri). (3) Halaman yang dirender JavaScript
  menghasilkan snapshot pendek; script **menolaknya** (< 500 karakter) alih-alih menyimpan
  snapshot palsu yang bisa dikutip sembarangan — jalan keluarnya `--from-file`, bukan
  menurunkan ambang. (4) `baseline` di peta adalah teks alasan cut-list, **bukan** klaim
  mastery: lantai sungguhan tetap `/placement` (§1.2 utuh), dan templat peta mencetak
  kalimat itu sendiri.

  *Ditolak:* (i) membiarkan gerbang lama "id terdaftar" (self-satisfying begitu AI menulis
  registry); (ii) AI menulis `data/sources/*.md` sendiri (gerbang jadi melingkar);
  (iii) AI menulis berkas `library/` langsung tanpa scaffolder (melepas penjaga terkuat
  L1 justru di fase paling berisiko); (iv) menyalin aturan kutipan ke `scripts/`
  alih-alih meng-import-nya dari `grounding.py`; (v) `nodes.proposed.yaml` di L3 (pipa
  tanpa konsumen); (vi) memperluas aturan roadmap ke file `note` (kutipan di catatan
  Bryant adalah tulisannya sendiri, bukan klaim generate).
