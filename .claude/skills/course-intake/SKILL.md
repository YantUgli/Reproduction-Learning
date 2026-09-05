---
name: course-intake
description: Scaffold sebuah course eksternal (mis. Dicoding, deeplearning.ai) menjadi kerangka folder library/ kosong-terstruktur untuk diisi catatan. Gunakan saat Bryant ingin "mirror"/menyalin struktur course luar ke dalam Library — BUKAN untuk mengisi materi (itu note-refine) atau menilai penguasaan.
---

# course-intake — mirror struktur course luar ke `library/`

Menghasilkan pohon `library/<course>/` kosong-terstruktur dari silabus yang
di-paste Bryant, lewat scaffolder deterministik `scripts/library_scaffold.py`.
**Nol klaim mastery.** Format & batas: [`../../../library/README.md`](../../../library/README.md).

## Kapan dipakai / TIDAK
- PAKAI: "bikinkan kerangka course X dari silabus ini", "mirror course Dicoding …".
- JANGAN: mengisi isi catatan (→ note-refine, L2), generate materi (→ learn-intake, L3),
  atau menyatakan Bryant sudah menguasai apa pun (dilarang §1.2).

## Alur
1. **Minta bahan.** Nama course + sumber (URL/platform) + **paste silabus** (daftar
   modul; boleh dengan judul materi per modul). Jangan mencoba menampung silabus lewat
   AskUserQuestion — silabus itu teks yang di-paste.
2. **AskUserQuestion untuk fork nyata saja:**
   - Granularitas: "sampai level materi (bikin stub per materi)" vs "modul saja".
   - Konfirmasi `slug` course (kebab-case) yang kamu turunkan dari nama.
3. **Rakit `spec.yaml` ke scratchpad** sesuai kontrak (docs/execution-plan-L1). Turunkan
   slug modul/materi dari judul (kebab-case; a-z0-9-). source_refs & node_ids DIKOSONGKAN
   oleh scaffolder — jangan isi manual.
4. **Jalankan scaffolder:**
   `backend/.venv/Scripts/python.exe scripts/library_scaffold.py --spec "$CLAUDE_SCRATCHPAD/spec.yaml"`
   (opsional dulu `--dry-run` untuk pratinjau).
5. **Laporkan** daftar `dibuat`/`skip` apa adanya. Ingatkan: file yang sudah ada TIDAK
   ditimpa (create-only). Arahkan Bryant: buka `library/` di Obsidian; isi stub lewat
   `note-refine` (L2).

## Batas yang dijaga (jangan dilanggar)
- Provenance course luar → teks `Sumber:` di _index, BUKAN id source_refs (source_refs
  hanya untuk id yang ADA di data/sources.yaml).
- `status` tak pernah diisi "forged"/"mastered" — reproduksi hanya dari eksekusi kode.
- Jangan menulis prosa penjelasan materi ke library/ (itu artifacts/ + 403, §7 2026-09-04).
