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
| **L5** | Penjaga metrik (dashboard) | — | **wajib sebelum "selesai"** | L4 |

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
- **Acceptance:** dari 1 materi Library lahir 1 node Forge terverifikasi hijau.

### L5 — Penjaga metrik (kunci anti-"Dicoding jilid 2")
- Dashboard hitung **"% direproduksi", bukan "% dibaca"**. Course tampil *belum
  selesai* sampai `node_ids`-nya `forged`.
- **Acceptance:** KPI baru muncul; membaca materi **tidak** menggerakkan progres.
- Dibangun terakhir, tapi **wajib ada sebelum sistem boleh disebut selesai**.

---

## 4. Jalur kritis & titik pembalikan termurah

- **L0→L1→L2** aman total (nol mastery) — jalan cepat, membuktikan lajur Library nyata.
- **L3** titik masuk risiko §8 → di sinilah grounding wajib mengikat.
- **L5** tak boleh ditunda tanpa batas: tiap minggu L1–L4 hidup tanpa L5, Bryant
  berlatih mengukur "dibaca". Kalau berhenti di tengah, berhenti **setelah** L5.

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
- ▶️ **Berikutnya: L4 (jembatan Library→Forge)**, lalu L5 (penjaga metrik). Peringatan §4
  berlaku makin keras sekarang: L3 membuat peta terasa seperti kurikulum, jadi tekanan
  untuk menyegerakan L5 ("% direproduksi, bukan % dibaca") naik justru setelah fase ini.
