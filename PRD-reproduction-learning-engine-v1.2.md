# PRD — Reproduction Learning Engine (working title)

> Status: v1.2 · 20 Agustus 2026 (dari frozen v1.0)
> Perubahan v1.1 (tidak mengubah §2 Anchor / §8 Guardrails): (a) penamaan risiko dipisah — `RISK-n` untuk risiko, `Rn` tetap untuk peran Claude Code, menutup bentrok makna `R3`; (b) §12 Roadmap: Fase 0 dipecah dengan harness pytest ditempatkan di depan karena authoring butuh runner untuk memverifikasi test "lolos di solusi referensi"; (c) gerbang build-vs-buy Execute Program dijadikan langkah eksplisit di depan roadmap.
> Perubahan v1.2 (juga tidak mengubah §2 / §8): (d) §12 dipisah jadi **dua sumbu paralel** — Track Authoring (A1/A2) dan Sumbu Engineering (Fase 1–5) — menghapus penomoran mundur 0a→1→0b→2 yang membingungkan; (e) semantik Gerbang 0 dikoreksi: **non-blocking** untuk slice pertama (A1+Fase 1), **blocking** sebelum A2+Fase 2; (f) A2 diberi estimasi kasar (~30–60 jam); (g) RISK-1 menegaskan draft R4 dipakai manual/offline; (h) Lampiran A ditambah 2 pertanyaan uji (harness-dulu & gerbang Execute Program); (i) propagasi konsistensi: RISK-5 disamakan dengan semantik gerbang dua tingkat, posisi A2 dikoreksi (di belakang Gerbang 0, paralel dengan Fase 2 dst — bukan dengan Fase 1), dan hubungan Harness ↔ runner Docker Fase 1 dinyatakan eksplisit supaya tidak terbaca sebagai pekerjaan ganda.
> Dokumen ini sengaja ditulis **self-contained**. Pembaca baru (manusia atau AI) harus bisa sampai ke kesimpulan yang sama tanpa membaca percakapan asal. Karena itu setiap keputusan disertai *alasan* dan *alternatif yang ditolak* — bukan hanya hasilnya.

---

## 0. Cara membaca dokumen ini

Ada dua hal yang gampang salah-baca dan membuat seluruh desain melenceng:

1. Ini **bukan** aplikasi e-learning / course platform, meskipun punya UI seperti itu.
2. Ini **bukan** "AI yang membuatkan learning path", meskipun AI dipakai berat di dalamnya.

Bagian **§2 (Anchor)** dan **§8 (Guardrails)** adalah bagian yang mencegah kedua salah-baca itu. Kalau sebuah usulan fitur bertabrakan dengan §2, fitur itu yang gugur — bukan §2.

---

## 1. Persona & pembagian peran

Dua sosok, sengaja dipisah karena kebutuhannya berbeda dan sering tertukar.

**Bryant — user tunggal & ruang masalah.**
Developer yang produktif dengan bantuan AI tapi mengalami dua kendala:
- Belajar otodidak tanpa goals/kurikulum yang jelas — tidak tahu apa dan urutan mana.
- Bisa *mengenali* solusi yang benar, tapi **blank ketika harus memproduksinya sendiri tanpa AI** (contoh konkret: gagal di technical interview online pada materi yang dipakainya sehari-hari).

**Isyah — builder & authority.**
Developer yang membangun sistem ini. Kompetensinya tidak dipertanyakan. Isyah yang mengarang kurasi graf pengetahuan dan mereview soal.

**Konsekuensi desain dari pemisahan ini (penting):**
Bryant tidak pernah menyentuh definisi graf prerequisite. Alasannya bukan hirarki, tapi validitas — premis proyek ini adalah Bryant mengalami *illusion of competence*, sehingga self-report Bryant tentang "aku sudah bisa X" adalah sinyal yang tidak reliabel. Yang menandai `hard`/`soft` edge harus pihak yang kalibrasinya bisa dipercaya, yaitu Isyah. Ini menutup risiko graf ikut terkontaminasi ilusi.

---

## 2. Anchor (invariant yang tidak bisa ditawar)

> **Ukuran belajar dalam sistem ini adalah `reproduce-without-AI`, bukan konsumsi materi dan bukan kelulusan sekali jalan.**

Setiap usulan fitur diuji dengan satu pertanyaan: *apakah fitur ini menutup jurang produksi, atau hanya membuat konsumsi terasa nyaman?* Kalau yang kedua, fitur itu ditolak atau diturunkan jadi pendukung.

Anchor ini berasal dari dua basis bukti di §3, dan menjadi alasan tunggal kenapa produk ini bukan e-learning biasa.

---

## 3. Basis bukti

Dua knowledge base yang jadi fondasi. Keduanya komplementer — satu memberi rangka, satu memberi otot.

**KB-1 — Learning path & sequencing.**
Prinsip yang dipakai: backward design (mulai dari outcome), prerequisite sebagai DAG dengan banyak topological sort yang sama-sama valid, pembedaan *hard* vs *soft* prerequisite, mastery learning, spaced + retrieval practice, Cognitive Load Theory (worked examples untuk pemula), scaffolding yang memudar.
Peringatan yang dipakai: LLM generatif punya tingkat fabrikasi sitasi tinggi dan cenderung menghasilkan urutan generik; bukti efektivitas LLM murni untuk menghasilkan learning path praktis tidak ada. Sistem yang terbukti (ITS, ALEKS/Knowledge Space Theory) adalah sistem terstruktur dengan prerequisite terkurasi ahli, bukan LLM bebas.

**KB-2 — Metacognitive traps (Prather et al., ICER 2024; Loksa et al., CHI 2016).**
Temuan yang dipakai: AI melebarkan jurang antar pelajar dan **menghapus sinyal** bahwa seseorang tidak paham (*illusion of competence*). Trap 6 (Progression) persis menggambarkan Bryant: AI menghasilkan kode kerja di atas level pemahaman, sehingga maju tanpa fondasi.
Solusi yang diadopsi jadi mekanik produk: *explain-or-reject*, uji retensi (tutup AI, tulis ulang dari ingatan), lindungi jeda berpikir, pisahkan "kode jalan" dari "aku paham".

**Ironi yang disadari dan diselesaikan secara arsitektural.**
KB-1 mengkritik AI untuk learning path, sementara sistem ini memakai Claude Code sebagai engine. Ini bukan kontradiksi karena penyelesaiannya bukan slogan "pakai AI dengan bijak", melainkan **pembatasan kepemilikan keputusan** di §5.

---

## 4. Tujuan & non-tujuan

**Tujuan utama.** Mengubah Bryant dari *mengenali* menjadi *memproduksi tanpa AI*, lalu mempertahankannya lewat spaced retrieval.

**Case yang harus terselesaikan:**

| Keluhan Bryant | Ditangani oleh |
|---|---|
| Otodidak tanpa kurikulum/goals jelas | Ground (§5.1) + Gap (§5.4) |
| Blank tanpa AI saat interview | Verify (§5.3) + Practice (§5.5) — **inti produk** |
| Illusion of competence | Grading objektif di Verify — satu-satunya grading yang kebal ilusi |
| Ilmu menguap setelah selesai | Spaced schedule + mastery berjarak (§5.5) |

**Non-tujuan (v1):**
- Bukan multi-user, bukan sertifikasi, bukan produk komersial.
- Bukan content library / CMS materi.
- Bukan sistem multi-domain sekarang (extensibility disiapkan di skema, bukan dibangun sebagai pipeline).
- Bukan AI yang menetapkan path.

---

## 5. Core loop & kepemilikan keputusan

Ini jantung dokumen. Enam langkah, dengan **pemilik** eksplisit di tiap langkah.

```
Ground → Assemble/Hypothesize → VERIFY → Gap → Practice → Re-evaluate
                                  ↑
                    satu-satunya hakim mastery
```

### 5.1 Ground — pemilik: sumber otoritatif + Isyah
Node dan edge prerequisite diturunkan dari sumber otoritatif (ACM/IEEE **CS2023** Knowledge Areas, daftar isi buku teks standar, dokumentasi resmi framework), bukan dari intuisi dan bukan dari LLM.
Claude Code boleh **mengusulkan** kandidat node/edge hasil ekstraksi; Isyah yang prune dan menandai `hard`/`soft`.
*Alasan:* menutup kelemahan LLM (urutan generik, prerequisite tak tervalidasi) yang didokumentasikan KB-1.

### 5.2 Assemble / Hypothesize — pemilik: Claude Code
Dua output:
- **Skill hypothesis** dari pembacaan codebase Bryant → dugaan node mana yang sudah/belum dikuasai.
- **Materi just-in-time**: penjelasan pendek bersumber + worked example untuk node yang gagal.

⚠️ **Batas keras:** hipotesis dari codebase **tidak pernah** menjadi verdict. Codebase Bryant mungkin ditulis dengan bantuan AI, sehingga ia bukti *pengenalan*, bukan *produksi*. Codebase menghasilkan hipotesis; hanya §5.3 yang membuktikan.

### 5.3 Verify — pemilik: eksekusi kode (bukan AI, bukan Bryant)
Bryant memproduksi solusi dari nol di dalam sandbox aplikasi, tanpa AI, dengan timebox. Hidden test dijalankan → pass/fail.
Ditambah **comprehension probe** yang deterministik (§7.3) untuk menangkap kasus "lolos test tapi tidak paham".
*Alasan:* satu-satunya bukti sahih bahwa seseorang bisa memproduksi konsep X tanpa AI adalah ia benar-benar memproduksinya dan kodenya terverifikasi mesin.

### 5.4 Gap — pemilik: sistem (deterministik)
Node yang gagal reproduce = *fringe* berikutnya (analogi knowledge state ALEKS/KST). Urutan menghormati `hard` edge saja; node independen bebas urutannya.

### 5.5 Practice — pemilik: scheduler
Scaffold memudar (§7.2) → verifikasi → masuk jadwal spaced. Mastery = **lolos berulang berjarak**, bukan lolos sekali (§7.5).

### 5.6 Re-evaluate — pemilik: Claude Code (usul) + eksekusi (putus)
Berkala: baca ulang codebase, perbarui hipotesis, jadwalkan ulang probe untuk node yang statusnya diragukan.

### Ringkasan kepemilikan

| Keputusan | Pemilik | AI boleh? |
|---|---|---|
| Node & edge prerequisite ada apa saja | Sumber otoritatif + Isyah | Mengusulkan saja |
| Materi & worked example | Claude Code (grounded, bersitasi) | ✅ |
| Hipotesis skill dari codebase | Claude Code | ✅ (sebagai hipotesis) |
| Membuat soal & hidden test | Claude Code (Isyah review) | ✅ |
| **Apakah Bryant sudah menguasai node X** | **Eksekusi kode** | ❌ **tidak pernah** |
| Penilaian jawaban teks bebas | — | ❌ fitur ini tidak ada (§7.3) |

---

## 6. User flow

Referensi UX: flow e-learning yang jelas (user selalu tahu posisinya, langkah berikutnya, dan progresnya). **Yang direferensi adalah layout dan flow, bukan kenyamanan konsumsi materi.** Flow boleh mulus; task-nya tetap harus sulit.

Seluruh proses belajar terjadi **di dalam aplikasi** (sandbox), bukan di IDE Bryant.

```
1. Placement probe (sekali di awal, dan berkala)
   Rangkaian tantangan reproduksi menurun: unit framework → primitif bahasa/logika.
   Berhenti di batas fail→pass pertama. Itu lantai awal Bryant.
   → Lantai DITEMUKAN, bukan diasumsikan. (Alasan: self-report Bryant tidak reliabel.)

2. Dashboard
   Node aktif · review yang jatuh tempo hari ini · peta progres (daftar linear, bukan graf visual di v1)

3. Sesi node (gagal → belajar → buktikan)
   a. Penjelasan just-in-time (pendek, bersumber) — bukan bab course
   b. Worked example: solusi minimal beranotasi untuk soal near-identical
   c. Faded reproduction: soal sama, bagian dikosongkan, makin lama makin banyak
   d. VERIFIKASI: instance soal BERBEDA, tanpa AI, timebox, hidden test dijalankan
   e. Comprehension probe (deterministik)

4. Hasil → scheduler
   Lolos bersih → status `acquired`, masuk jadwal spaced
   Gagal → kembali ke 3a dengan scaffold lebih tinggi

5. Sesi review (harian)
   Node yang jatuh tempo, verifikasi ulang dengan instance berbeda

6. Re-evaluasi berkala
   Claude Code baca codebase → usul penyesuaian → probe ulang
```

**Catatan desain 3b–3d:** akuisisi dan verifikasi adalah **aktivitas yang sama pada level scaffold berbeda**, bukan dua mode terpisah. Bryant memproduksi sejak langkah pertama; yang turun adalah scaffold-nya, bukan effort-nya. Ini yang mencegah produk berubah jadi "baca → tonton → coba".

**Catatan desain 3d:** verifikasi memakai *instance berbeda* dari worked example supaya lolos berarti transfer, bukan hafalan contoh.

---

## 7. Spesifikasi komponen

### 7.1 Grain node

Satu node = satu konsep yang bisa direproduksi **sekali duduk (±10–20 menit)** dan bisa di-grade dengan menjalankan kode.

- ✅ Node: "GET route dengan path param, return 404 kalau resource tidak ditemukan"
- ❌ Bukan node (ini epic): "CRUD + auth service"

Aturan pecah: kalau butuh lebih dari ±2 file test, atau tidak selesai sekali duduk → pecah jadi beberapa node.

### 7.2 Scaffold memudar (fase akuisisi)

| Level | Bentuk | Yang diproduksi Bryant |
|---|---|---|
| L3 | Penjelasan + worked example beranotasi | Membaca sambil menyalin-memahami |
| L2 | Faded: kerangka ada, bagian inti dikosongkan | Bagian inti |
| L1 | Signature + spesifikasi saja | Hampir seluruhnya |
| L0 | **Verifikasi**: instance baru, tanpa AI, timebox | Seluruhnya, dari nol |

Landasan: CLT (worked example efektif untuk pemula), 4C/ID (scaffolding menurun), desirable difficulty.

### 7.3 Comprehension probe (pengganti explain-or-reject berbasis esai)

**Keputusan:** artikulasi pemahaman **tidak** memakai esai teks bebas.
*Alasan:* esai bebas butuh pemrosesan makna → penilainya hanya bisa AI atau Bryant sendiri → melanggar aturan kepemilikan di §5. Ini satu-satunya titik yang sempat mengancam invariant, dan diselesaikan dengan mengganti bentuk soalnya, bukan dengan memberi konsesi ke AI.

Bentuk yang dipakai (semuanya punya jawaban benar deterministik):
- **Predict the output** — "route ini return status berapa kalau id tidak ada?"
- **Spot the bug** — pilih baris yang salah dari versi yang sengaja dirusak
- **Trace / attribution** — "baris mana yang menyebabkan perilaku X?"

Refleksi teks bebas boleh disimpan sebagai catatan pribadi, tapi **tidak pernah menjadi gate**.

### 7.4 Grader pluggable (satu engine, banyak grader)

**Keputusan:** tidak ada mode belajar terpisah untuk coding vs AI/ML. Flow, scaffold, scheduler, mastery — identik lintas domain. Yang berbeda hanya modul verifikasi, dipilih per node lewat field `grader_type`.

| `grader_type` | Cara verifikasi | Domain khas |
|---|---|---|
| `unit_test` | Hidden test suite dijalankan, pass/fail | FastAPI, backend, logika, primitif bahasa |
| `structural` | Cek struktur (shape tensor, jumlah/urutan layer) | Arsitektur model |
| `value_assert` | Assert nilai numerik lawan nilai yang diharapkan | Fungsi matematis ML (gradient, softmax, backprop) |
| `metric_threshold` | Capai ambang metrik pada dataset beku | Training loop end-to-end |
| `dom_behavior` | Render + interaksi, assert perilaku | React/Next.js |

⚠️ **Peringatan `metric_threshold`:** grader ini mengukur *hasil*, bukan *pemahaman* — Bryant bisa menyalin training loop dan tembus ambang tanpa paham. Untuk domain ML, **condongkan grain node ke `value_assert` pada komponen kecil** (implement backprop sendiri, assert gradiennya) alih-alih training end-to-end. `metric_threshold` dipakai sangat terbatas.

*Konsekuensi build-order:* FastAPI jadi domain pertama karena hanya butuh `unit_test` — assertion status/body HTTP itu biner dan tak ambigu. React butuh `dom_behavior` (timing effect, dependency array lebih halus). ML butuh 2–3 grader baru. Engine harus terbukti jalan dengan grader termudah dulu.

### 7.5 Mastery & scheduling

- Lolos verifikasi pertama → status `acquired` (**belum** `mastered`)
- Node masuk jadwal spaced; tiap jatuh tempo harus lolos lagi dengan **instance berbeda**
- `mastered` setelah N sukses berjarak (default N=4)
- Gagal di interval mana pun → status turun (`lapsed`), interval reset

**Algoritma:** pakai **FSRS** (Free Spaced Repetition Scheduler) via library `py-fsrs` atau `ts-fsrs` — open source, berbasis model DSR (difficulty/stability/retrievability), sudah jadi default modern menggantikan SM-2. **Jangan menulis algoritma SR sendiri.** Kalau Isyah sudah punya SR engine, nebeng ke situ.

Yang membedakan dari SR biasa: unit yang dijadwalkan adalah **reproduksi node**, bukan flashcard recognition.

### 7.6 Sandbox & integritas "tanpa AI"

Tiga lapis, karena "tanpa AI" **tidak bisa dijamin secara teknis** pada aplikasi single-user self-administered:

1. **Lingkungan** — challenge dikerjakan di editor sandbox milik aplikasi (Monaco), bukan di IDE Bryant. Di dalamnya memang tidak ada AI assist. Ini menyediakan ruang bersih by default, bukan pengawasan.
2. **Desain soal** — timebox ketat + comprehension probe, sehingga menyalin dari AI lebih mahal daripada memikirkan sendiri.
3. **Framing** — Bryant satu-satunya user; curang berarti menyabotase sinyal yang dia sendiri butuhkan. Produk diposisikan sebagai **cermin**, bukan ujian. Verifikasi objektif ada supaya *Bryant* tidak tertipu dirinya sendiri, bukan supaya sistem tidak tertipu.

**Batas jujur:** tidak akan pernah ada jaminan 100%. Untuk tujuan diagnosa pribadi, ini cukup; untuk sertifikasi, tidak — dan sertifikasi memang non-tujuan.

---

## 8. Guardrails (anti-drift)

Daftar ini ada karena setiap item pernah muncul sebagai ide yang masuk akal, lalu ditolak dengan alasan spesifik. Kalau muncul lagi, alasannya masih berlaku.

| Ditolak | Alasan |
|---|---|
| Content library / bab-bab materi yang nyaman dibaca | Mengoptimasi *recognition* — persis mode yang menciptakan masalah Bryant. Materi hanya boleh just-in-time & pendek. |
| AI menentukan learning path / urutan | KB-1: LLM menghasilkan urutan generik tanpa validasi prerequisite. Edge berasal dari sumber otoritatif. |
| AI menilai mastery | Codebase & judgment AI mengukur pengenalan; hanya eksekusi yang mengukur produksi. |
| Esai bebas sebagai gate | Butuh pemrosesan makna → pintu masuk AI-sebagai-hakim. |
| Multi-domain / ingestion generik di v1 | Bottleneck proyek ini adalah **kurasi data**, bukan kode. Generalisasi prematur membunuh v1. |
| Graf visual / DAG explorer di v1 | Gravitasi builder: enak di-engineer, kelihatan, tapi tidak menggerakkan Bryant. Versi builder dari avoidance trap. |
| `metric_threshold` sebagai grader utama ML | Mengukur hasil, bukan pemahaman. |
| Quiz pilihan ganda konseptual sebagai penilai utama | Mengukur recognition. Hanya boleh jadi sinyal pendukung. |

**Gravitasi yang harus dilawan sepanjang proyek:** dorongan meng-over-invest di bagian DAG/visualisasi dan under-build loop reproduksi. Loop reproduksi adalah MVP; DAG di v1 boleh sekadar daftar node berurutan dalam file data.

---

## 9. Model data

Domain-agnostic secara sengaja — tidak ada field yang meng-hardcode "FastAPI". Inilah bentuk extensibility yang dipilih (skema yang tidak tahu domainnya apa), bukan pipeline ingestion.

```
Domain
  id, name, status

SourceRef
  id, type (cs2023_ku | textbook_toc | official_docs)
  citation, url_or_locator

Node
  id, domain_id, concept, description
  grader_type (unit_test | structural | value_assert | metric_threshold | dom_behavior)
  source_refs[] → SourceRef
  estimated_minutes, timebox_seconds
  status_default

Edge
  from_node_id, to_node_id
  type (hard | soft)          # hanya `hard` yang mengikat urutan
  source_ref_id, note

ChallengeInstance             # >1 per node, untuk transfer & review
  id, node_id, variant_label
  prompt, starter_code, signature_contract
  hidden_test_path, scaffold_level (L3..L0)

ComprehensionProbe
  id, node_id, type (predict_output | spot_bug | trace)
  question, options[], correct_answer   # deterministik

Attempt
  id, node_id, instance_id, timestamp
  mode (placement | acquisition | verification | review)
  scaffold_level, duration_seconds
  submitted_code, result (pass | fail), test_output
  probe_result

SkillHypothesis               # dari Claude Code — TIDAK PERNAH jadi verdict
  id, node_id, source (codebase | research)
  confidence, rationale, evidence_locator, created_at
  status (unverified | confirmed_by_attempt | refuted_by_attempt)

ScheduleItem
  node_id, fsrs_stability, fsrs_difficulty, due_at
  review_count, consecutive_success
  status (locked | available | acquired | mastered | lapsed)

Session
  id, started_at, ended_at, mode, ai_available (selalu false utk verification)
```

**Metrik utama produk:** `reproduce-without-AI pass rate per node`, dan jumlah node berstatus `mastered` (lolos berjarak). Ini KPI yang bisa diukur — sesuatu yang, menurut KB-1, hampir tidak dimiliki sistem learning path lain.

---

## 10. Kontrak peran Claude Code

Claude Code adalah agent CLI, bukan HTTP API. Integrasi dilakukan **asinkron lewat file artifact**: aplikasi memanggil Claude Code (headless) dengan prompt terstruktur, Claude Code menulis output ke direktori kerja, aplikasi membaca dan memvalidasinya. Ini juga yang membuat output-nya bisa direview Isyah sebelum masuk sistem.

| Peran | Input | Output | Gate |
|---|---|---|---|
| **R1 · Ekstraksi kandidat** | CS2023 KA/KU + TOC buku + docs resmi | `nodes.proposed.yaml`, `edges.proposed.yaml` + sitasi | Isyah prune & tandai hard/soft |
| **R2 · Bukti codebase** | Path repo Bryant + daftar node | `hypotheses.json` (node_id, confidence, rationale, lokasi bukti) | Masuk sebagai hipotesis; wajib diverifikasi Attempt |
| **R3 · Materi just-in-time** | node_id + hasil attempt yang gagal | `explanation.md` (pendek, bersitasi) + worked example beranotasi | Sitasi wajib bisa diverifikasi |
| **R4 · Generator soal** | node_id + kontrak signature | ChallengeInstance varian + hidden test + ComprehensionProbe | Isyah review; test wajib deterministik & lolos di solusi referensi |

**Yang tidak pernah diberikan ke Claude Code:** menetapkan edge secara final, menyatakan mastery, menilai teks bebas.

Catatan: R1 dan R3 boleh memakai kemampuan research Claude Code (output .md bersumber). Grounding-nya sah karena objeknya adalah **materi**, yang memang bisa diverifikasi lewat sumber eksternal. Yang tidak bisa di-research adalah **kemampuan Bryant** — itu hanya bisa dibuktikan lewat eksekusi.

---

## 11. Tech stack

Dipilih condong ke yang sudah dikuasai Isyah, karena stack asing = proyek yang mati di bulan kedua.

| Bagian | Pilihan | Alasan |
|---|---|---|
| Frontend | Next.js + Monaco Editor | Sudah dikuasai; Monaco = editor sandbox standar |
| Backend | FastAPI | Sudah dikuasai; sekaligus domain pertama yang diajarkan |
| DB | SQLite | Single-user, local-first, zero-ops |
| Node/edge store | File YAML/JSON di git | Kurasi manual + bisa di-review & di-diff seperti kode |
| Eksekusi test | Docker container per attempt | Isolasi & reproducibility (bukan soal keamanan — kodenya milik Bryant sendiri) |
| Scheduler | `py-fsrs` | Terbukti, open source; jangan tulis sendiri |
| AI engine | Claude Code (headless CLI + file artifact) | Sesuai §10 |

Deployment: lokal di device Bryant. Tidak ada auth, tidak ada multi-tenancy, tidak ada cloud.

---

## 12. Roadmap

Fase 1 harus menghasilkan sesuatu yang **jalan end-to-end**, sekecil apa pun. Roadmap ini punya **dua sumbu yang jalan paralel**, bukan satu urutan tunggal — memisahkannya menghilangkan kebingungan "kenapa authoring dan engineering saling menyusul":

- **Sumbu Engineering (Fase 1–5)** — membangun loop, lalu mengotomasi & memperluasnya.
- **Track Authoring (A1, A2)** — mengarang node. Ini biaya sebenarnya (RISK-1), jalan paralel dengan engineering, **bukan blok di depan**.

Ditambah satu gerbang keputusan (Gerbang 0) dan satu prasyarat teknis kecil (Harness) di depan.

```
Gerbang 0 (Execute Program) ── non-blocking ──▶ [ A1 + Fase 1 ] ──┐
                                                                   │ putuskan lanjut/berhenti
                              ◀── blocking ──── sebelum ───────────┘
                                                                   ▼
                                                        [ A2 ∥ Fase 2 ] → Fase 3 → 4 → 5
```

**Gerbang 0 — Build-vs-buy (Execute Program).**
Uji apakah masalah Bryant sudah terjawab produk yang ada: Execute Program (±$39/bln) kemungkinan besar sudah menutup ~80% masalah untuk primitif bahasa (lihat RISK-5). **Pakai ±1 bulan** untuk primitif Python/JS/SQL. Semantik gerbangnya sengaja dua tingkat supaya koheren:
- **Non-blocking untuk A1 + Fase 1.** Slice pertama murah (~3–4 minggu) dan hasilnya berguna apa pun keputusan build-vs-buy-nya, jadi tak perlu menunggu. Jalankan Execute Program *sambil* menyalakan slice pertama.
- **Blocking sebelum A2 + Fase 2.** Di sinilah biaya sesungguhnya mulai keluar (±20 node + FSRS + dashboard). Keputusan lanjut-atau-berhenti **wajib** dibuat di titik ini. Kalau Execute Program ternyata sudah cukup untuk kebutuhan Bryant, roadmap boleh berhenti di sini.

**Harness (prasyarat Track Authoring).**
Authoring bukan murni non-koding: hidden test adalah pytest sungguhan dan kontrak signature adalah artefak teknis. PRD mensyaratkan tiap test **"lolos di solusi referensi"** (§10, R4) — dan itu tidak bisa dibuktikan tanpa runner. Karena itu **langkah pertama, sebelum authoring apa pun, adalah harness pytest telanjang** (jalankan test lawan solusi referensi → pass/fail). Tanpa ini, risikonya mengarang node yang test-nya belum pernah dijalankan sekali pun.
Harness ini **bukan pekerjaan ganda**: ia versi telanjang dari runner yang nanti dibungkus Docker di Fase 1. Kontraknya sama (ambil solusi + hidden test → pass/fail + output), sehingga Fase 1 tinggal menyelubunginya dengan isolasi container dan pencatatan Attempt, bukan menulis ulang dari nol. Selama Track Authoring berjalan, harness telanjang tetap dipakai karena jauh lebih cepat untuk memverifikasi test saat mengarang.

### Track Authoring (biaya sebenarnya — RISK-1)

**A1 — 5 node pertama (±4–5 hari, setelah harness).**
Karang **5 node** FastAPI (primitif → satu route sederhana): tiap node lengkap dengan prompt, kontrak signature, 2–3 varian instance, hidden test **yang sudah terverifikasi hijau di solusi referensi**, 1–2 comprehension probe. Edge ditandai hard/soft oleh Isyah, bersumber CS2023 + TOC buku + docs FastAPI. Boleh pakai Claude (peran R1, manual/offline) untuk draft; Isyah prune & review. **Inilah yang memberi makan Fase 1.**

**A2 — sisa ~20 node (di belakang Gerbang 0; paralel sepanjang Fase 2 dan seterusnya).**
Konsekuensi langsung dari "cukup 5 node untuk menyalakan Fase 1": begitu loop menyala, tiap node berikutnya diarang dengan sinyal reproduksi nyata sebagai umpan balik — authoring jadi lebih terinformasi, Bryant dapat nilai lebih cepat. **Ukuran kasar:** ±20 node × 1,5–3 jam/node = **~30–60 jam kerja**. Ini bobot yang tidak boleh diremehkan — RISK-1 menyebutnya pembunuh utama proyek. Draft boleh pakai peran R4 (manual/offline sampai Fase 3, lalu otomatis), Isyah tetap mereview.

### Sumbu Engineering

**Fase 1 — Vertical slice (target: bisa dipakai).**
5 node dari A1 saja. Sandbox editor + runner Docker + `unit_test` grader + comprehension probe + pencatatan Attempt. Scheduler masih manual/interval statis. Tanpa Claude Code otomatis, tanpa placement probe. **Tujuannya: membuktikan sinyal `reproduce-without-AI` benar-benar terbaca.**

**Fase 2 — Loop penuh (di belakang Gerbang 0).**
FSRS terpasang, seluruh node (A1 + A2) masuk, placement probe, dashboard, status mastery berjarak.

**Fase 3 — Claude Code masuk (integrasi otomatis).**
Peran R3 (materi just-in-time) dulu karena paling rendah risiko, lalu R4 (generator soal, dengan review Isyah), lalu R2 (bukti codebase). Peran R1 sudah dipakai sejak A1 secara manual/offline. (Ingat: `Rn` di sini adalah **peran** Claude Code, §10 — berbeda dari `RISK-n` di §13.)

**Fase 4 — Domain kedua.**
React/Next.js + `dom_behavior` grader. Setelah stabil: ML dengan `value_assert` pada komponen kecil.

**Fase 5 — Extensibility nyata.**
Baru di sini pertimbangkan ingestion yang lebih otomatis dan domain seperti Web3.

**Estimasi kasar** (asumsi: kerja malam/akhir pekan, ±10 jam/minggu):
- Gerbang 0: ±1 bulan pemakaian Execute Program — non-blocking di slice pertama; keputusan wajib sebelum A2 + Fase 2
- Harness: ±0,5–1 hari
- A1: ±4–5 hari (5 node)
- Fase 1: 2–3 minggu (paralel dengan/sesudah A1 — slice pertama total ~3–4 minggu)
- A2: ~30–60 jam kerja, dimulai setelah Gerbang 0 diputuskan, lalu paralel sepanjang Fase 2 dan seterusnya — *variabel terbesar, bergantung disiplin authoring; bukan blok sekuensial tersendiri*
- Fase 2: 2–3 minggu
- Fase 3: 3–4 minggu (integrasi paling tidak pasti)

---

## 13. Risiko & catatan jujur

> Catatan penamaan: `RISK-n` di bawah adalah **nomor risiko**, berbeda dari `Rn` (peran Claude Code, §10). Prefiks sengaja dipisah supaya `R3` tak lagi bermakna ganda (dulu ia sekaligus peran "materi just-in-time" dan risiko "integrasi Claude Code").

**RISK-1 · Biaya authoring adalah bottleneck sebenarnya (paling besar).**
Kode Fase 1 mungkin selesai dalam 2–3 minggu; mengarang ~25 node bermutu dengan hidden test bisa lebih lama (~30–60 jam, lihat A2 di §12). Proyek sejenis mati di sini, bukan di engineering. *Mitigasi:* batasi v1 ke satu vertical slice sempit; siapkan harness pytest lebih dulu supaya tiap test terverifikasi hijau di solusi referensi; arang hanya 5 node (A1) untuk menyalakan Fase 1, sisanya (A2) paralel; pakai peran R4 (manual/offline sampai Fase 3) untuk draft, Isyah cukup mereview.

**RISK-2 · Integritas "tanpa AI" tidak bisa dijamin.** Lihat §7.6. Ini batas nyata yang diterima secara sadar.

**RISK-3 · Integrasi Claude Code adalah bagian paling tidak pasti.**
Ia agent CLI asinkron, bukan API request/response. Latency, format output yang tidak konsisten, dan kebutuhan review manusia membuatnya lebih rumit dari yang terlihat. *Mitigasi:* Fase 1 sengaja tanpa Claude Code otomatis — sistem harus bernilai bahkan kalau integrasi ini gagal total.

**RISK-4 · Bukti codebase terkontaminasi.** Kode di repo Bryant mungkin ditulis dengan AI. Sudah ditangani secara arsitektural (hipotesis ≠ verdict), tapi jangan pernah dilonggarkan.

**RISK-5 · Prior art: Execute Program.**
Produk berbayar (±$39/bln) dengan konsep sangat dekat: pelajaran interaktif + spaced repetition + dependency antar-lesson, untuk Python, JavaScript, TypeScript, SQL, dan regex. **Untuk primitif bahasa, produk ini kemungkinan besar sudah menyelesaikan 80% masalah Bryant, hari ini, tanpa membangun apa pun.**
*Rekomendasi jujur:* dijadikan langkah eksplisit — lihat **Gerbang 0** di §12, dengan semantik dua tingkat: pakai ±1 bulan **sambil** menjalankan slice pertama (A1 + Fase 1, yang tetap jalan tanpa menunggu), lalu keputusan lanjut-atau-berhenti **wajib** dibuat sebelum A2 + Fase 2 — titik di mana biaya sesungguhnya mulai keluar.
Diferensiasi yang tetap valid: (a) domain yang tidak dicakup Execute Program — FastAPI, React/Next.js, ML; (b) soal berbentuk **produksi dari nol**, bukan isian/prediksi output; (c) grounding ke codebase Bryant sendiri; (d) local-first, data milik sendiri, node bisa dikarang sendiri.

**RISK-6 · Bukti efektivitas learning-path generation memang tipis (KB-1).**
Yang menyelamatkan proyek ini adalah KPI-nya berasal dari KB-2 (`reproduce-without-AI pass rate`), yang terukur — bukan dari klaim "path-nya optimal".

**RISK-7 · Scope creep ke arah e-learning.** Tekanan ini akan datang berulang karena UI-nya memang mirip. §2 dan §8 adalah penangkalnya.

---

## 14. Open questions (belum diputuskan, tidak memblokir slice pertama: A1 + Fase 1)

1. Berapa varian instance minimum per node supaya review tidak jadi hafalan? (dugaan awal: 3)
2. Timebox per node: fixed atau adaptif terhadap `estimated_minutes`?
3. Apakah `lapsed` menurunkan status ke `acquired` atau ke `available` penuh?
4. Placement probe: berapa node maksimum sebelum berhenti supaya tidak melelahkan?
5. Apakah hasil comprehension probe ikut memberi rating ke FSRS, atau hanya gate lulus/tidak?

---

## Lampiran A — Uji dokumen ini di chat baru

Dokumen ini dirancang agar pembaca baru sampai ke kesimpulan yang sama. Pertanyaan berikut bisa dipakai untuk mengetesnya. Jawaban yang benar ada di dalam dokumen.

1. Siapa yang memutuskan apakah user sudah menguasai sebuah node? *(Jawaban: eksekusi kode — bukan AI, bukan user.)*
2. Kenapa aplikasi ini tidak boleh dibuat nyaman seperti course biasa? *(§2, §8)*
3. Kalau Claude Code membaca codebase dan menyimpulkan user sudah menguasai auth, apa yang terjadi? *(Jadi hipotesis, wajib diverifikasi lewat Attempt — codebase bisa ditulis dengan AI.)*
4. Kenapa domain pertama FastAPI, bukan React atau ML? *(Hanya butuh `unit_test`; grader paling deterministik.)*
5. Apa beda produk ini dengan flashcard/Anki untuk coding? *(Unit yang dijadwalkan adalah reproduksi dari nol, bukan recognition.)*
6. Kenapa esai bebas tidak dipakai untuk mengecek pemahaman? *(§7.3)*
7. Apa bagian yang paling mungkin membunuh proyek ini? *(Biaya authoring node, bukan engineering — RISK-1.)*
8. Boleh tidak menambahkan visualisasi DAG interaktif di v1? *(Tidak — §8, gravitasi builder.)*
9. Apa langkah pertama sebelum mengarang node-node itu? *(Harness pytest telanjang — karena hidden test wajib terverifikasi hijau di solusi referensi sebelum dipakai. §12.)*
10. Apa yang harus dievaluasi sebelum memutuskan membangun, dan kapan keputusan itu mengikat? *(Execute Program lewat Gerbang 0 / RISK-5 — ~80% masalah primitif bahasa mungkin sudah terjawab; non-blocking di slice pertama, tapi wajib diputuskan sebelum A2 + Fase 2.)*

Kalau chat baru menjawab kesepuluh pertanyaan ini konsisten dengan dokumen, PRD-nya cukup self-contained.
