# Roadmap — Lajur Library (Knowledge Management) + Jembatan ke Forge

> **Status:** rencana eksekusi bertahap. Turunan dari
> [`brainstorm-knowledge-management-lane.md`](brainstorm-knowledge-management-lane.md)
> (diskusi/arah, 2026-08-28) menjadi fase-fase yang bisa dikerjakan.
>
> **Bukan** pelonggaran invariant. Sumber kebenaran produk tetap
> [`../PRD-reproduction-learning-engine-v1.2.md`](../PRD-reproduction-learning-engine-v1.2.md)
> dan invariant [`../CLAUDE.md`](../CLAUDE.md) §1. Kalau ada konflik, **invariant menang**.
>
> Prefix milestone **`L`** (Library) sengaja dibedakan dari milestone Forge
> (**M0–M7**) yang sudah selesai. Forge = loop reproduksi yang ada sekarang;
> Library = lajur baru yang dibangun di dokumen ini.
> — **Dicatat:** 2026-09-04

---

## 0. Tujuan akhir (end-state)

Satu aplikasi lokal single-user dengan **dua lajur yang saling tarik**:

- **Library** (baru) — menangkap & menyusun materi yang *nyaman dikonsumsi*:
  generate materi tergrounding, mirror course luar (Dicoding/deeplearning),
  rapikan catatan mentah. Folder markdown di repo, dibuka di Obsidian untuk graf.
- **Forge** (yang sekarang) — *membuktikan*: reproduce-without-AI, scaffold
  memudar, FSRS. Oracle tetap **eksekusi kode**.

**Jembatan:** tiap bagian materi di Library mengusulkan node reproduksi di Forge.

**Satu kalimat:** *personal learning OS* — pintu masuk senyaman Dicoding, tapi
menolak menyebutmu "selesai" sampai kamu bisa menuliskan ulang kodenya dari nol
tanpa AI.

### Bryant bisa apa (end-state)
1. Intake tujuan → roadmap + materi tergrounding (belajar dari nol).
2. Mirror course luar → catatan dirapikan jadi arsip pribadi terstruktur.
3. Baca materi bersitasi ke sumber otoritatif (bukan halusinasi LLM).
4. Tempa tiap materi jadi node reproduksi, dibuktikan tanpa AI.
5. Lihat progres jujur: **"% direproduksi", bukan "% dibaca"**.

---

## 1. Garis yang tak bergerak (biar bukan "Dicoding jilid 2")

Diturunkan dari CLAUDE.md §1–§2 + dua penjaga brainstorm:

- Materi generate = **referensi bersitasi**, **tak pernah** verdict mastery.
- **Selesai = memproduksi ulang tanpa AI**, bukan menonton/membaca.
- AI = **editor + peneliti + penebak lantai awal**; **eksekusi kode** yang memvonis.
- **Penjaga metrik:** progres Library diukur dari **% direproduksi**, bukan % dibaca.
  Course tampil *berlubang* sampai node-nya di-Forge.

---

## 2. Peta fase

| Fase | Nama | Menyentuh generate? | Risiko invariant | Prasyarat |
|---|---|---|---|---|
| **L0** | Fondasi Library (format + keputusan) | — | — (menulis penjaga) | — |
| **L1** | `course-intake` | tidak | nol mastery | L0 |
| **L2** | `note-refine` | tidak (AI = editor) | nol mastery | L1 |
| **L3** | `learn-intake` + grounding ✅ | **ya** | §8 (content library) | L2 |
| **L4** | Jembatan Library→Forge | ya (usul node) | pakai gate M5/M7 | L3 |
| **L5** | Penjaga metrik (dashboard) ✅ | — | **wajib sebelum "selesai"** | L4 |

**Urutan tidak boleh dibalik.** Tiap fase memasang penjaga sebelum fase berikutnya
menambah risiko.

---

## 3. Detail per fase

### L0 — Fondasi (bekukan format + catat keputusan) — ✅ SELESAI 2026-09-04
- ✅ Entri CLAUDE.md §7 (2026-09-04): §8 dibuka kembali sebagai lajur referensi
  bersitasi + peta, dengan 2 penjaga (grounding + % direproduksi) DAN batas keras:
  **prosa penjelasan sintesis AI tak pernah mendarat di `library/`** (tetap di
  `artifacts/`, sampai hanya lewat 403). Ini menyelesaikan konflik roadmap↔log
  2026-08-31 — lihat "Reframe L3" di bawah.
- ✅ Format beku di [`../library/README.md`](../library/README.md): folder
  `library/<course>/<NN-modul>/<materi>.md` + `_index.md`; frontmatter
  `title, course, module, type, source_refs, node_ids, status(outline|captured),
  created`. **`status` = status catatan, BUKAN reproduksi** (reproduksi dihitung
  dashboard L5 dari join `node_ids`→DB — bukan `forged` di frontmatter).
- ✅ Course contoh tulis tangan: [`../library/fastapi-dasar/`](../library/fastapi-dasar/_index.md)
  (2 modul, sitasi ke `data/sources.yaml`, `node_ids` menunjuk node FastAPI nyata,
  wikilink antar-materi untuk graf Obsidian).
- **Acceptance:** `library/` git-tracked & di-diff seperti `data/`; wikilink terpasang
  untuk graf Obsidian; satu course contoh ada.

### L1 — `course-intake` — ✅ SELESAI & TERVERIFIKASI 2026-09-04
- Skill di `.claude/skills/course-intake/` + scaffolder deterministik
  `scripts/library_scaffold.py` (create-only). Silabus di-**paste** (bukan lewat
  AskUserQuestion) → spec → folder markdown kosong-terstruktur di `library/`.
- **Plan eksekusi lengkap:** [`execution-plan-L1-course-intake.md`](execution-plan-L1-course-intake.md)
  (spec, kode acuan, test, urutan build, DoD).
- **Acceptance:** dari silabus Dicoding → folder siap diisi, nol klaim mastery,
  **re-run aman** (tak menimpa catatan).

### L2 — `note-refine` — ✅ SELESAI & TERVERIFIKASI 2026-09-04
- Paste/dikte catatan mentah → Claude rapikan ke SATU stub target. AI = editor, bukan
  penilai/penulis: celah ditandai `> TODO:`, tak pernah ditambal (crux 1, 2026-09-04).
- Skill `note-refine` + **`scripts/verify_library.py`** (validator ⊆ registry + `--capture`
  yang flip `outline→captured` hanya bila body berisi). Overwrite ganti create-only
  (git = undo). `source_refs`/`node_ids` boleh, opsional, tervalidasi.
- **Plan eksekusi lengkap:** [`execution-plan-L2-note-refine.md`](execution-plan-L2-note-refine.md)
  (spec, kode acuan terbukti-jalan, test, smoke, DoD).
- **Acceptance:** catatan mentah → markdown rapi tertaut ke modul yang benar; status
  di-flip SCRIPT (bukan AI); validator hijau; nol klaim mastery.

### L3 — `learn-intake` + grounding (fase risiko) — ✅ SELESAI & TERVERIFIKASI 2026-09-05
- Template 5-keputusan (tujuan/baseline/cut-list/milestones) → **roadmap + kerangka +
  sitasi terkurasi + usul node** yang mendarat di `library/`. **BUKAN** bab materi
  yang dibaca. Sintesis penjelasan just-in-time tetap lewat `artifacts/` → gerbang 403
  (§7 2026-09-04); ia tak pernah diparkir di `library/` sebagai bacaan pra-attempt.
- **Gate keras (dinaikkan 2026-09-05):** bukan lagi sekadar "`source_ref` ADA di
  `data/sources.yaml`" — itu *self-satisfying* begitu AI boleh menulis ke registry.
  Sekarang: teks sumber wajib **di-snapshot** ke `data/sources/<id>.md` oleh script
  (`fetch_source.py`, isinya tak pernah diketik AI) dan tiap entri peta wajib membawa
  **kutipan verbatim** yang dicek substring lewat `app/services/grounding.py` — mesin
  yang sama dengan gate R3/M7. Efek samping yang disengaja: ini **menghidupkan lajur
  403/R3** yang mati sejak M7 karena snapshot belum pernah ada.
- **Plan eksekusi lengkap:** [`execution-plan-L3-learn-intake.md`](execution-plan-L3-learn-intake.md)
  (5 berkas, kode acuan, test, urutan build gerbang-dulu, smoke, DoD).
- **Acceptance:** roadmap generate punya sitasi + tiap bagian mengusulkan kandidat node;
  nol prosa penjelasan sintesis mendarat di `library/`.
- ✅ **Terkirim (2026-09-05):** `scripts/_console.py` · `scripts/fetch_source.py`
  (+ `test_fetch_source.py`) · `kind: roadmap` + `check_grounding()` di
  `library_scaffold.py` · `roadmap_errors()` di `verify_library.py` · skill
  `.claude/skills/learn-intake/`. Aturan kutipan **di-import** dari
  `app/services/grounding.py`, tidak disalin. 53 test hijau (24 lama tetap hijau),
  `ruff` tanpa temuan baru, smoke end-to-end lolos termasuk **dua uji penolakan**
  (kutipan diubah satu huruf → exit 2, nol berkas ditulis; blok kode di peta → gerbang
  baca exit 1). Keputusan tercatat di CLAUDE.md §7 (2026-09-05).
- ✅ **Bonus yang terbukti:** `data/sources/` kini berisi snapshot nyata yang ter-commit
  — bahan yang ditunggu gate R3 sejak M7 (`NO_SNAPSHOT`).

### L4 — Jembatan Library→Forge
- Usulan node dari L3 masuk **pipeline authoring yang sudah ada** (R4 → gate mesin
  M5/M7). Tidak bikin jalur baru.
- Link dua arah: materi ⇄ `node_ids`.
- **Koreksi 2026-09-06 (dari pembacaan kode, bukan asumsi):** pipeline yang ada **tak
  bisa melahirkan node** — `trigger_r4` menolak node tanpa instance dan `_promote_r4`
  hanya menulis varian ke node yang sudah ada; R1 tak pernah dibangun. Keputusan Isyah:
  **perluas R4 dengan mode `node`** (artifact = `node.yaml` + 2 varian + 1 probe),
  bukan bikin peran R5. Gerbangnya mendaur ulang yang sudah terbukti: `run_triad`
  dijalankan **per varian** + probe dieksekusi + sitasi verbatim (L3).
- **Plan eksekusi lengkap:** [`execution-plan-L4-library-forge-bridge.md`](execution-plan-L4-library-forge-bridge.md)
  (11 keputusan terkunci, kode acuan, test, urutan build gerbang-dulu, smoke, DoD).
- **Acceptance:** dari 1 materi Library lahir 1 node Forge terverifikasi hijau.
- ✅ **Terkirim (2026-09-06):** `NodeGenesisArtifact` + `load_node_genesis` +
  `_require_identity` (contracts) · `trigger_r4_node` + `_gate_r4_node` (jobs) ·
  `r4_node.md` (`r4node-v1`) · `_promote_node_genesis` + `_append_soft_edge`
  (review_queue) · `POST /authoring/node` · `verify_library.py --link/--candidates` ·
  skill `forge-node`. Aturan bentuk hidden test diekstrak jadi SATU salinan
  (`check_test_references_solution`) yang dipakai R4 varian & R4 node.
- **Test:** 185 backend hijau (naik dari 151 — +24 `test_node_genesis`, +9
  `test_promote_node` yang merupakan **test promosi pertama di repo**) dan 62 scripts
  hijau (+9 untuk `--link`/`--candidates`).
- ⏳ **Acceptance BELUM terpenuhi penuh:** seluruh uji penolakan, kill switch, dan jalur
  L3→L4 terbukti live, tapi **belum ada node sungguhan yang lahir** — panggilan CLI
  ketiga dibalas `HTTP 429` (kuota sesi habis), bukan ditolak gerbang. Selama tiga job
  smoke, `git status data/` tetap bersih. Cara menuntaskannya (tanpa perubahan kode) ada
  di [`execution-plan-L4-library-forge-bridge.md`](execution-plan-L4-library-forge-bridge.md) §15.
- **Ditemukan smoke:** `r4_node.md` tak mendaftar skema `ProbeYaml` utuh, jadi dua
  artifact lahir tanpa `node_id`/`type` dan **ditolak kontrak** — promptnya yang cacat,
  bukan gerbangnya. Sudah diperbaiki.

### L5 — Penjaga metrik (kunci anti-"Dicoding jilid 2")
- Dashboard hitung **"% direproduksi", bukan "% dibaca"**. Course tampil *belum
  selesai* sampai `node_ids`-nya terbukti.
- **Metrik dikunci 2026-09-06:** "direproduksi" = **pernah lolos attempt mode dingin**
  (`kpi.REPRODUCE_MODES`, di-import bukan disalin) — bukan "node ada", bukan status.
  Tiga keadaan per materi (belum tertempa · tertempa belum dibuktikan · direproduksi)
  + penanda `mastered`/`meluruh`. Materi tanpa `node_ids` **tetap masuk penyebut**
  (itu lubangnya), `_index` struktural tidak. `status` frontmatter (`outline`/`captured`)
  **tak pernah** masuk hitungan — dan itu **diuji**.
- **Arsitektur:** backend **MEMBACA** `library/` (`services/library_progress.py`,
  read-only) + `GET /library/progress` + halaman `/library`; dashboard cuma dapat satu
  kartu. Penulisnya tetap `scripts/` (L1–L3) & promosi L4 — tak ada berkas indeks
  yang di-commit (sumber kebenaran kedua).
- **Plan eksekusi lengkap:** [`execution-plan-L5-metric-guard.md`](execution-plan-L5-metric-guard.md)
  (10 keputusan terkunci, kode acuan terbukti-jalan, test anti-gaming, smoke, DoD).
- **Acceptance:** KPI baru muncul; membaca materi **tidak** menggerakkan progres.
- Dibangun terakhir, tapi **wajib ada sebelum sistem boleh disebut selesai**.
- ✅ **SELESAI 2026-09-06.** Terpasang: `config.LIBRARY_DIR`,
  `services/library_progress.py` (read-only), `GET /library/progress`, halaman
  `/library`, satu kartu KPI + tautan di dashboard. Bukti: **16 test baru**
  (`backend/tests/test_library_progress.py`) termasuk dua penjaga —
  `test_status_captured_tidak_menggerakkan_angka` (mengubah SELURUH materi jadi
  `captured` → angka identik) dan `test_membaca_tidak_pernah_menulis` (byte + mtime
  seluruh berkas tak berubah sesudah `compute`). Atas `library/` & DB nyata: **5 materi,
  0 direproduksi** — `fastapi-dasar` 4 `mapped_unproven` (node n002–n005 ada, DB Bryant
  belum punya satu pun attempt), `fastapi-produksi` **1 `unmapped` = lubang yang
  terlihat** (buah acceptance L4 yang belum tuntas). Catatan entri §7 CLAUDE.md
  2026-09-06 (L5).

---

## 4. Jalur kritis & titik pembalikan termurah

- **L0→L1→L2** aman total (nol mastery) — jalan cepat, membuktikan lajur Library nyata.
- **L3** titik masuk risiko §8 → di sinilah grounding wajib mengikat.
- **L5** tak boleh ditunda tanpa batas: tiap minggu L1–L4 hidup tanpa L5, Bryant
  berlatih mengukur "dibaca". Kalau berhenti di tengah, berhenti **setelah** L5. ✅
  **Peringatan ini berhenti berlaku 2026-09-06:** L5 hijau, jadi kenyamanan tak bisa lagi
  menyamar jadi kemajuan.

---

## 5. Langkah berikut

- ✅ **L0 SELESAI** (2026-09-04): entri §7, format beku (`library/README.md`), course
  contoh (`library/fastapi-dasar/`). Krux "isi Library" diputuskan = **peta + catatan
  saja**; prosa generate → `artifacts/`/403.
- ✅ **L1 SELESAI & TERVERIFIKASI** (2026-09-04): skill `course-intake` +
  `scripts/library_scaffold.py` + `scripts/test_library_scaffold.py`. 11 test hijau,
  ruff bersih, smoke end-to-end lulus (create-only terbukti). Detail & bukti:
  [`execution-plan-L1-course-intake.md`](execution-plan-L1-course-intake.md) §9.
- ✅ **L2 SELESAI & TERVERIFIKASI** (2026-09-04): skill `note-refine` +
  `scripts/verify_library.py` + `scripts/test_verify_library.py` + entri §7 CLAUDE.md.
  24 test hijau (13 L2 + 11 L1), ruff bersih, validator atas `library/` hijau, smoke lulus.
  5 crux diputuskan (TODO-marker · skill+verify_library · overwrite · target tunggal ·
  refs opsional-tervalidasi). Detail & bukti:
  [`execution-plan-L2-note-refine.md`](execution-plan-L2-note-refine.md) §9.
- ✅ **L3 SELESAI & TERVERIFIKASI** (2026-09-05): skill `learn-intake` +
  `scripts/fetch_source.py` + `scripts/_console.py` + perluasan `library_scaffold.py`
  (`kind: roadmap`, gerbang TULIS `check_grounding`) & `verify_library.py` (gerbang BACA
  `roadmap_errors`) + entri §7 CLAUDE.md. **53 test hijau** (24 lama tetap hijau + 9
  `fetch_source` + 9 validator L3 + 11 scaffolder L3), `ruff` tanpa temuan baru, validator
  atas `library/` hijau, smoke end-to-end lulus termasuk dua uji penolakan. `data/sources/`
  berisi 2 snapshot nyata yang ter-commit — R3 hidup lagi. Rencananya:
  [`execution-plan-L3-learn-intake.md`](execution-plan-L3-learn-intake.md). Pendekatan
  **A** ("peta ter-snapshot") dipilih dari 5 alternatif; 9 keputusan dikunci (KUNCI 1–9),
  di antaranya: gerbang = snapshot + kutipan verbatim (bukan "id terdaftar"), isi snapshot
  tak pernah diketik AI, penulis berkas tetap scaffolder, kutipan hanya hidup di file
  `type: roadmap`, dan batas "peta vs bab" dibuat mekanis (dilarang blok kode + batas
  prosa 3000 karakter). Urutan build: **gerbang dulu, penulisnya belakangan** — diikuti
  apa adanya saat eksekusi.
- ▶️ **L4 (jembatan Library→Forge) — plan eksekusi SIAP, belum dikerjakan** (2026-09-06):
  [`execution-plan-L4-library-forge-bridge.md`](execution-plan-L4-library-forge-bridge.md).
  Temuan yang membentuknya: pipeline R4 tak bisa melahirkan node (lihat koreksi di §3/L4);
  Isyah memilih **memperluas R4 dengan mode `node`** ketimbang menambah peran R5. 11
  keputusan dikunci, di antaranya: identitas node (id/label/probe/grader) ditetapkan
  **mesin**, node lahir **lengkap atau tidak sama sekali** (≥2 varian + 1 probe), gerbang =
  **triad per varian** + probe dieksekusi + kutipan verbatim, edge hasil AI **selalu
  `soft`**, `edges.yaml` ditambahi lewat **append teks** (komentar kurasi tak boleh hilang),
  dan tautan balik `node_ids` ditulis **script**, bukan AI.
- ✅ **L5 (penjaga metrik) SELESAI** (2026-09-06) —
  [`execution-plan-L5-metric-guard.md`](execution-plan-L5-metric-guard.md). 10 keputusan
  dikunci; yang menentukan: "direproduksi" = pernah lolos **attempt mode dingin** (definisi
  di-import dari `kpi.py`), tiga keadaan per materi, materi tanpa node **tetap masuk
  penyebut**, `lapsed` tetap terbukti tapi ditandai meluruh, backend **membaca** `library/`
  (tak pernah menulis), dan `status` catatan **tak pernah** masuk hitungan — dijaga test
  `test_status_captured_tidak_menggerakkan_angka`. Kode acuannya sudah diprototipekan atas
  `library/` & DB nyata: `fastapi-dasar` 4 materi, `fastapi-produksi` **1 materi berlubang**
  (buah dari acceptance L4 yang belum tuntas — tampil sebagai lubang, bukan disembunyikan).
  Hasil eksekusi & bukti test ada di §3/L5 di atas.
- ⏭️ **Sesudah L5:** menuntaskan acceptance L4 (satu node sungguhan lahir) dan sisa **M7**
  (meja audit + tombol pensiun + `destination`). Peringatan §4 berhenti berlaku begitu L5
  hijau — sejak titik itu, kenyamanan tak bisa lagi menyamar jadi kemajuan.
