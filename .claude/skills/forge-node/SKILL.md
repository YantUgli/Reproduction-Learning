---
name: forge-node
description: Tempa satu entri peta Library menjadi node reproduksi Forge lewat pipeline authoring (R4 mode node) dan tautkan balik node_ids-nya. Gunakan saat Bryant ingin mengubah kandidat node di library/ menjadi node yang benar-benar bisa direproduksi. BUKAN untuk menulis materi (artifacts/ + 403), merapikan catatan (note-refine), atau menilai penguasaan.
---

# forge-node — dari kandidat di peta Library ke node Forge (L4)

Menempa **satu** kandidat per panggilan. Semua keputusan mutu dipegang **gerbang mesin**;
kamu cuma menyiapkan permintaan dan melaporkan hasilnya apa adanya. **Nol klaim mastery.**

## Kapan dipakai / TIDAK
- PAKAI: "tempa kandidat X jadi node", "bikin node dari materi peta ini".
- JANGAN:
  - menulis berkas ke `data/` sendiri (promosi hanya lewat pipeline yang digerbangi).
  - mengetik `node_ids` dengan tangan (hanya `verify_library.py --link`).
  - membuat domain baru (butuh grader baru — pekerjaan gaya M6, bukan L4).
  - menyatakan Bryant menguasai sesuatu (dilarang §1.2).

## Alur
1. **Pilih kandidat:**
   `backend/.venv/Scripts/python.exe scripts/verify_library.py --candidates`
   Bila ada beberapa, tanyakan mana yang mau ditempa (AskUserQuestion). Ambil dari
   laporan: path materi, slug kandidat, `source_refs`.
2. **Pastikan backend hidup** (skill `run-learning-engine`) dan integrasi menyala
   (`CLAUDE_INTEGRATION_ENABLED` tidak 0). Cek: `GET /authoring/status`.
3. **Kirim permintaan:**
   `POST /authoring/node` dengan `{library_file, slug, domain_id, concept,
   source_ref_id, prereq_node_id?}`. `domain_id` HARUS domain yang sudah ada
   (`fastapi`/`react`/`ml`); `source_ref_id` harus id yang ada di `source_refs`
   materinya dan sudah ter-snapshot (L3). Balasan `202` + `job_id`.
4. **Tunggu gerbang:** poll `GET /authoring/jobs/{job_id}` sampai statusnya
   `approved` (lolos + dipromosikan otomatis), `ready` (lolos, promosi manual),
   `rejected` (gagal gerbang mutu), atau `failed` (gagal memproduksi artifact).
   Gerbang menjalankan test SUNGGUHAN dua kali (satu per varian) — sabar, jangan
   mengulang trigger karena terasa lama.
5. **Kalau `rejected`/`failed`:** laporkan `gate.reason` + potongan output APA ADANYA.
   **Jangan** mengakali gerbang (mengubah test, melonggarkan probe, memakai
   `expected_value`). Yang boleh: perbaiki konsep/sumber lalu ulangi.
6. **Kalau lolos:** verifikasi & tautkan.
   `backend/.venv/Scripts/python.exe scripts/verify_nodes.py <domain>`
   `backend/.venv/Scripts/python.exe scripts/verify_library.py --link "<materi.md>" --node <node_id>`
   `backend/.venv/Scripts/python.exe scripts/verify_library.py`
7. **Lapor:** node_id, path yang ditulis, edge soft (bila ada), dan hasil verifikasi.
   Arahkan Bryant membuka node-nya di frontend (`/node/<id>`) untuk mencobanya.

## Batas yang dijaga (jangan dilanggar)
- **Gerbang mesin yang memutuskan**, bukan kamu: triad per varian + probe dieksekusi.
- **Identitas node ditetapkan server** (id, label, probe id, grader). Jangan menyarankan
  model menamainya sendiri.
- **Edge selalu `soft`** — usul AI tak pernah mengunci urutan (§7 2026-09-01).
- **`status` materi tak berubah** saat ditautkan; "% direproduksi" dihitung dari DB (L5).
