# Evaluasi — Generate Materi dari Topik & Upload Catatan Kursus

> **Status:** dokumen evaluasi/analisis, **bukan** milestone dan **bukan** keputusan.
> Tidak mengubah roadmap atau invariant apa pun. Merekam evaluasi dua permintaan fitur
> baru terhadap kondisi kode & dokumen nyata per tanggal dicatat di bawah.
>
> Sumber kebenaran produk tetap [`../PRD-reproduction-learning-engine-v1.2.md`](../PRD-reproduction-learning-engine-v1.2.md)
> dan invariant di [`../CLAUDE.md`](../CLAUDE.md) §1. Kalau ada konflik, **invariant menang** —
> dokumen ini tidak berwenang melonggarkannya.
>
> Konteks lanjutan dari: [`roadmap-library-lane.md`](roadmap-library-lane.md) (L0–L5) dan
> [`brainstorm-knowledge-management-lane.md`](brainstorm-knowledge-management-lane.md).
> — **Dicatat:** 2026-09-16

---

## Ringkasan eksekutif

Kedua kebutuhan **secara struktural sudah punya fondasi kuat** — bukan mulai dari nol.
Skill `learn-intake` (L3), `course-intake` (L1), `note-refine` (L2), dan `forge-node` (L4)
sudah menutup sebagian besar alur yang diminta. Tapi **keduanya, seperti dideskripsikan
literal, meminta hal yang sistem ini secara sengaja menolak**:

- **Kebutuhan 1** meminta materi bacaan siap saji di muka → bertabrakan dengan gerbang 403
  (materi hanya boleh muncul *setelah* attempt gagal tercatat — CLAUDE.md §7 2026-08-31 &
  2026-09-04, PRD §8).
- **Kebutuhan 2** meminta graf prasyarat yang diputuskan otomatis oleh AI → bertabrakan
  dengan PRD §1/§5.1 ("Bryant tidak pernah menyentuh definisi graf prerequisite" —
  hanya Isyah yang menandai `hard`/`soft` edge) dan §8 ("AI menentukan learning
  path/urutan" ditolak).

Bagian yang bertabrakan itu **bukan pekerjaan development** — itu permintaan untuk
membuka kembali keputusan yang sudah dikunci dengan alasan tertulis, dan perlu diputuskan
Isyah secara sadar sebelum estimasi kompleksitas apa pun berarti.

---

## Kebutuhan 1: Generate Materi dari Topik yang Diminta Pengguna

**Alur yang diminta:** sebut topik → AI tanya goals/baseline/kedalaman → AI generate
bahan bacaan + soal latihan harian (L3→L0) → masuk sebagai node baru.

### 1. Bisa direalisasikan?
Sebagian. Dua bagian bertabrakan langsung dengan invariant, bukan sekadar "belum dibangun":

- Langkah *"AI bertanya dulu"* → **sudah ada padanannya**: skill `learn-intake` melakukan
  "5 keputusan" (tujuan, baseline, cut-list, milestone, waktu/minggu) lewat
  `AskUserQuestion`.
- Langkah *"generate bahan bacaan / penjelasan"* → **bermasalah**. `jobs.trigger_r3`
  mensyaratkan `Attempt` GAGAL yang sudah tercatat di DB sebelum materi boleh
  di-generate; `GET /nodes/{id}/explanation` balas `403` tanpa itu. Untuk topik baru,
  node-nya belum ada → tidak mungkin ada attempt gagal. Ini gerbang yang disengaja,
  bukan celah.
- Langkah *"soal latihan masuk L3→L0"* → **punya pipeline nyata**: `forge-node` (L4)
  via `POST /authoring/node` → gate mesin (triad × 2 varian + probe dieksekusi) →
  promosi otomatis.
- *"AI bertanya dulu"* hari ini terjadi **di sesi Claude Code (CLI/agent)**, bukan
  sebagai fitur chat di dalam aplikasi Next.js/FastAPI. Backend tidak punya satu pun
  endpoint chat/percakapan — semua endpoint `authoring/*` bersifat trigger-job-async +
  poll status, bukan tanya-jawab bolak-balik.

### 2. Apa yang sudah ada yang bisa dipakai?
- `learn-intake` → `scripts/fetch_source.py` (snapshot sumber) → `scripts/library_scaffold.py`
  (`kind: roadmap`, gerbang tulis `check_grounding`) → `scripts/verify_library.py`
  (gerbang baca). Jalur "topik → peta bersitasi di `library/`" sudah selesai & teruji
  (53 test hijau).
- `forge-node` → `POST /authoring/node` → `jobs.trigger_r4_node` →
  `contracts._require_identity` (id/grader/label dipaksa server) → `run_triad` × 2
  varian + probe dieksekusi → promosi otomatis (185 test backend hijau).
- `services/grounding.py` — satu mesin kutipan verbatim dipakai bersama R3, L3, L4.
- `GET /authoring/status`, `GET /authoring/jobs/{id}` untuk memantau job.

### 3. Apa yang perlu dibangun baru?
- **Kalau "bahan bacaan di muka" tetap diminta seperti tertulis** → bukan pekerjaan
  build, ini **keputusan desain** yang melonggarkan §1.3/§8 secara sadar — harus
  dicatat di CLAUDE.md §7 dengan alasan + alternatif ditolak, bukan ditambahkan diam-diam.
- **Kalau direformulasi jadi "peta bersitasi" (bukan bacaan)** → tidak perlu kode baru,
  tinggal pakai `learn-intake` apa adanya.
- **Percakapan intake di dalam aplikasi** (kalau harus jadi fitur klik-klik di browser) →
  endpoint chat baru + UI baru + cara memanggil Claude Code sinkron/streaming dari
  request HTTP — belum ada presedennya; semua integrasi AI sekarang async-via-file-artifact
  (PRD §10).
- **Orkestrasi "satu topik → beberapa node berurutan"** → `forge-node` menempa **satu
  kandidat per panggilan**; topik yang butuh 3–5 node berurutan = 3–5 panggilan
  terpisah + koordinasi manual.

### 4. Risiko / hal yang perlu diputuskan dulu
- **Konflik invariant langsung**: "generate bahan bacaan" vs gerbang 403/§8 — harus
  diputuskan Isyah dulu; default sistem menolak.
- **L4 belum terbukti selesai end-to-end**: per `roadmap-library-lane.md` §L4, smoke
  test ketiga dibalas `HTTP 429` (kuota habis), bukan ditolak gerbang — **belum pernah
  ada satu node pun yang benar-benar lahir lewat jalur ini**.
- **Edge dari kandidat AI selalu `soft`** (tak mengunci urutan) — kalau "loop L3→L0"
  diartikan harus terkunci otomatis, itu bertentangan dengan keputusan 2026-09-01.
- **`domain_id` harus domain yang sudah ada**, `grader_type` diwarisi dari node contoh
  di domain sama — topik yang tak cocok grader (`unit_test`/`dom_behavior`/
  `value_assert`) butuh grader baru (pekerjaan sekelas M6).

### 5. Estimasi kompleksitas
**Besar (perlu Fase tersendiri).** Mayoritas komponen sudah ada, tapi inti permintaan
(materi di muka + percakapan in-app) menabrak dua pilar arsitektur (gerbang 403,
integrasi AI async-via-artifact) yang butuh keputusan desain eksplisit dulu, ditambah
L4 sebagai fondasinya sendiri belum terbukti stabil.

---

## Kebutuhan 2: Upload Catatan Kursus → Jadi Modul Belajar Pribadi

**Alur yang diminta:** upload banyak file `.md` berhierarki → AI baca semua & pahami
struktur → jadi modul dengan node saling terhubung (prasyarat/urutan) → generate soal
latihan harian masuk loop.

### 1. Bisa direalisasikan?
Sebagian besar. Jalur manual/iteratif sudah bisa dijalankan **hari ini** tanpa kode
baru; versi "otomatis sekaligus" butuh orkestrasi baru, dan satu bagiannya (graf
prasyarat otomatis) bertentangan dengan pembagian wewenang PRD §1/§5.1.

- "Catatan berhierarki jadi folder modul" → **sudah persis** `course-intake` (L1):
  silabus → `library/<course>/<NN-modul>/` kosong-terstruktur, create-only, aman.
- "AI membaca & merapikan jadi materi" → **sudah ada** di `note-refine` (L2), tapi
  dibatasi ketat: **satu file per panggilan**, butuh bahan mentah eksplisit per file
  (paste/dikte), ditolak kalau bahan tak disediakan. **Tidak ada** kapabilitas "baca
  sekaligus N file yang sudah ada isinya lalu sebar otomatis ke banyak stub".
- "Generate soal latihan harian" → sama seperti Kebutuhan 1, lewat `forge-node`/L4,
  satu node per panggilan.
- "Node saling terhubung (prasyarat, urutan)" → **secara eksplisit ditolak** kalau
  berarti AI yang **memutuskan** urutan otomatis: PRD §8 menolak "AI menentukan
  learning path/urutan"; PRD §1/§5.1 menegaskan hanya Isyah yang boleh menandai
  `hard`/`soft` edge. Yang boleh: AI mengusulkan edge `soft` (tak mengunci apa pun) —
  sudah dibangun di L4 (`_append_soft_edge`).

### 2. Apa yang sudah ada yang bisa dipakai?
- `course-intake` → `scripts/library_scaffold.py` (bentuk pohon folder dari silabus,
  create-only).
- `note-refine` → `scripts/verify_library.py --capture` (flip status
  `outline→captured`, validator `source_refs`/`node_ids` ⊆ registry).
- `forge-node` → `POST /authoring/node` (mint node dari satu entri peta) +
  `scripts/verify_library.py --link` (tautkan `node_ids` balik, hanya lewat script).
- Format `library/README.md` (frontmatter 8 field baku) cocok menampung hasil upload
  sebagai *sumber isi* — asal lewat `note-refine`, bukan disalin mentah langsung.

**Jalur yang bisa dijalankan hari ini tanpa kode baru** (manual, satu-satu):
`course-intake` sekali untuk kerangka modul → `note-refine` berkali-kali (satu
panggilan per file catatan) untuk mengisi stub → `forge-node` berkali-kali (satu
panggilan per kandidat) untuk menempa node. Tidak elegan, tapi valid dan aman.

### 3. Apa yang perlu dibangun baru?
- **Mekanisme upload/ingest berkas** sesungguhnya — tidak ada endpoint HTTP untuk
  upload file apa pun; `library/` diisi lewat filesystem lokal + git via sesi Claude
  Code, bukan widget upload di Next.js.
- **Batch ingestion** — baca N file `.md` sekaligus, simpulkan struktur (hierarki file
  → modul/course), petakan ke kontrak `library/`. `note-refine` sengaja dibatasi satu
  file per panggilan (desain sadar, supaya AI tak "menyebar sendiri ke banyak file"
  karena "bisa salah-tempat").
- **Orkestrasi batch node-genesis** — panggil `forge-node`/L4 berkali-kali otomatis
  untuk semua kandidat, dengan penanganan gagal-sebagian & rate limit (masalah nyata
  yang sudah terjadi di smoke test L4).
- **Kalau "graf prasyarat otomatis" tetap diinginkan** — perlu mekanisme baru
  "promosi soft→hard" dengan konfirmasi manusia; belum ada di kode sekarang (edge
  dari AI selamanya `soft`).

### 4. Risiko / hal yang perlu diputuskan dulu
- **Batasan satu-file/satu-node per panggilan bukan bug** — itu penjaga yang disengaja.
  Mengotomasi jadi batch berarti melonggarkan titik kendali manusia; perlu keputusan
  eksplisit + pengaman pengganti.
- **Graf prasyarat otomatis dari AI bertentangan dengan §1/§5.1** — garis merah PRD,
  bukan sekadar belum dibangun.
- **L4 belum terbukti stabil** (sama seperti Kebutuhan 1) — orkestrasi batch di atas
  pipeline yang belum pernah berhasil melahirkan satu node pun menambah risiko
  gagal berantai.
- **Domain harus sudah ada + grader diwarisi dari node contoh** — catatan ML cocok
  (domain `ml` sudah ada), tapi topik di luar 3 grader yang ada butuh grader baru
  dulu (pekerjaan M6, eksplisit di luar ruang lingkup L4).

### 5. Estimasi kompleksitas
- **Versi manual/iteratif** (pakai skill yang sudah ada, satu-satu): **Kecil** — bisa
  dilakukan sekarang, nol kode baru, cocok masuk pekerjaan yang sedang berjalan
  (menuntaskan acceptance L4).
- **Versi "upload banyak file sekaligus → otomatis jadi modul + graf + soal"**:
  **Besar (perlu Fase tersendiri)** — butuh mekanisme upload baru, orkestrasi batch
  baru, dan satu komponennya (graf prasyarat mengikat otomatis) berbenturan langsung
  dengan pembagian wewenang inti PRD.

---

## Hal yang tidak bisa dipastikan dari dokumen yang ada

⚠️ Tidak ditemukan dokumen yang menyebut rencana konkret untuk fitur chat in-app atau
upload-file in-app di dalam repo ini. Kalau ini sudah pernah dibahas di luar dokumen
yang tersedia, evaluasi di atas belum memperhitungkannya.
