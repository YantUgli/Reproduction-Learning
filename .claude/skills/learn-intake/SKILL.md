---
name: learn-intake
description: Ubah tujuan belajar Bryant menjadi PETA belajar bersitasi di library/ — roadmap, kerangka modul, sitasi ke sumber otoritatif dengan kutipan terverifikasi, dan usul kandidat node Forge. Gunakan saat Bryant ingin belajar sesuatu dari nol dan butuh arah. BUKAN untuk menulis materi/penjelasan (itu artifacts/ + gerbang 403), mengisi catatan (note-refine), atau menilai penguasaan.
---

# learn-intake — peta belajar bersitasi ke `library/`

Mengubah tujuan Bryant menjadi **peta**: roadmap + modul + sitasi + kutipan verbatim +
kandidat node. **Bukan** bab materi. **Nol klaim mastery.**
Format & batas: [`../../../library/README.md`](../../../library/README.md).

## Kapan dipakai / TIDAK
- PAKAI: "aku mau bisa X, bikinkan peta belajarnya", "susun roadmap FastAPI sampai deploy".
- JANGAN:
  - **menulis penjelasan/materi** — dilarang di `library/` (§7 2026-09-04). Sintesis
    hidup di `artifacts/` dan sampai ke Bryant hanya lewat gerbang 403 (sesudah gagal).
  - mengisi isi catatan → `note-refine` (L2). Mirror course luar → `course-intake` (L1).
  - membuat node Forge → L4. Menyatakan Bryant menguasai sesuatu → dilarang §1.2.

## Alur
1. **Kumpulkan 5 keputusan** (AskUserQuestion untuk fork nyata; teks panjang di-paste):
   tujuan konkret · baseline (apa yang sudah bisa) · cut-list (yang sengaja ditunda) ·
   milestone · waktu per minggu. **Baseline = lantai awal, BUKAN mastery** — akhiri
   dengan mengarahkan Bryant ke `/placement` untuk lantai sungguhnya.
2. **Riset sumber otoritatif** (docs resmi, spesifikasi, buku). Untuk tiap sumber yang
   BELUM ada di `data/sources.yaml`, tambahkan entri:
   `id` (snake_case) · `type` ∈ `{cs2023_ku, textbook_toc, official_docs}` ·
   `citation` · `url_or_locator`. **Tanpa field lain** — skema `extra="forbid"`.
3. **Snapshot tiap sumber (WAJIB, lewat script):**
   `backend/.venv/Scripts/python.exe scripts/fetch_source.py --id <id>`
   Gagal unduh → sumber itu **tidak boleh dipakai**. JANGAN pernah menulis/menambal
   `data/sources/*.md` sendiri: isinya adalah bahan pembanding kutipan, dan kalau kamu
   yang mengarangnya, seluruh gerbang jadi melingkar.
4. **Ambil kutipan DARI BERKAS SNAPSHOT**, bukan dari ingatan atau halaman web. Baca
   `data/sources/<id>.md`, salin potongan **verbatim** ≥ 25 karakter, satu baris.
5. **Rakit `spec.yaml` ke scratchpad** (`kind: roadmap`) sesuai kontrak
   [`docs/execution-plan-L3-learn-intake.md`](../../../docs/execution-plan-L3-learn-intake.md) §3.3.
   Tiap materi: `source_ref` · `quote` · `reproduce` (satu kalimat, ≤200 karakter) ·
   `candidate_node` (kebab-case). Dilarang blok kode di teks mana pun.
6. **Jalankan scaffolder** (dia yang menulis berkas, bukan kamu):
   `backend/.venv/Scripts/python.exe scripts/library_scaffold.py --spec "$CLAUDE_SCRATCHPAD/spec.yaml"`
   Ditolak karena grounding → perbaiki kutipannya, jangan akali gerbangnya.
7. **Validasi & lapor:**
   `backend/.venv/Scripts/python.exe scripts/verify_library.py`
   Laporkan `dibuat`/`skip` apa adanya. Arahkan: buka `library/` di Obsidian; isi stub
   lewat `note-refine`; jalankan `/placement` untuk menemukan lantai.

## Batas yang dijaga (jangan dilanggar)
- **Peta, bukan bab.** Tanpa blok kode; prosa peta dibatasi mesin (3000 karakter
  non-kutipan). Kalau terasa perlu menjelaskan — itu tanda materinya milik 403, bukan peta.
- **Kutipan verbatim dari snapshot.** Mengarang kutipan = gerbang menolak; mengarang
  snapshot = dilarang keras (dan tak akan terlihat di diff sebagai apa pun selain itu).
- **Kutipan hanya di file `type: roadmap`.** Jangan menaruh sitasi generate di stub
  materi — di sana tak ada yang memeriksanya.
- **`node_ids` tetap kosong.** Kandidat node ditulis sebagai teks; node lahir di L4
  lewat pipeline R4 + gerbang mesin M7.
- **Tak pernah menulis `status`, mastery, atau apa pun ke DB Forge** (§1.2).
