---
name: note-refine
description: Rapikan catatan mentah/dikte Bryant menjadi markdown bersih di SATU stub library/ yang ia tunjuk, lalu flip status outline→captured lewat verify_library.py. AI = editor (perbaiki bahasa/struktur/format), BUKAN penulis materi: celah ditandai TODO, tak pernah ditambal. Gunakan saat mengisi stub hasil course-intake — BUKAN untuk generate materi baru (itu learn-intake) atau menilai penguasaan.
---

# note-refine — rapikan catatan Bryant ke `library/`

Mengubah catatan mentah yang **Bryant tulis/dikte** menjadi markdown rapi di **satu
stub target**, lalu status di-flip oleh script deterministik. **Nol klaim mastery.**
Format & batas: [`../../../library/README.md`](../../../library/README.md).

## Kapan dipakai / TIDAK
- PAKAI: "rapikan catatan ini ke materi X", "transkripsi dikte ini ke stub Y".
- JANGAN:
  - **generate materi/penjelasan yang Bryant tak sediakan** → itu learn-intake (L3);
    hasil sintesis ke `artifacts/` + gerbang 403, TAK PERNAH ke `library/` (§7 2026-08-31).
  - membuat node Forge / mengisi node dari nol (→ L4).
  - menyatakan Bryant menguasai apa pun (dilarang §1.2 — mastery hanya dari eksekusi kode).

## Alur (satu file per panggilan)
1. **Minta target + bahan.** Path stub eksplisit di `library/…/<materi>.md` + **paste/dikte
   catatan mentah**. Kalau Bryant tak menyebut file, USULKAN modul yang cocok tapi minta
   konfirmasi — jangan menyebar sendiri ke banyak file (bisa salah-tempat).
   **Kalau Bryant tak menyediakan bahan mentah: TOLAK.** Tak ada bahan = tak ada yang
   dirapikan; jangan mengarang isi.
2. **Baca isi file sekarang.** Kalau `status` sudah `captured`, INGATKAN ini akan
   menimpa (overwrite) — git adalah undo-nya; tunjukkan apa yang akan berubah.
3. **Rapikan HANYA teks Bryant.** Boleh: perbaiki ejaan/tata bahasa, restruktur kalimatnya
   sendiri, tambah heading, format blok kode, buang duplikat, padatkan. **DILARANG**:
   menambah fakta/penjelasan/contoh yang tak ada di input, "mengembangkan" catatan pendek
   jadi bab. **Celah → tandai `> TODO: …`, JANGAN tambal dengan prosa.**
4. **GANTI seluruh body dengan versi rapi** (pertahankan 8 field frontmatter; JANGAN
   ketik `status` sendiri). **Buang baris sentinel kerangka L1**
   (`` > `status: outline` — kerangka … ``) — selama ia ada, `--capture` menolak (guard
   stub). Boleh set `type` `note`↔`transcription`. Boleh isi `source_refs`/`node_ids`
   HANYA bila Bryant menyebut & id-nya ADA di registry (sources.yaml / data node) — kalau
   ragu, biarkan `[]`.
5. **Flip status (deterministik):**
   `backend/.venv/Scripts/python.exe scripts/verify_library.py --capture "<path stub>"`
   Script menolak bila body masih stub / field invalid — perbaiki lalu ulangi.
6. **Validasi menyeluruh & lapor:**
   `backend/.venv/Scripts/python.exe scripts/verify_library.py`
   Tunjukkan diff/ringkasan perubahan ke Bryant. Arahkan: buka `library/` di Obsidian.

## Batas yang dijaga (jangan dilanggar)
- **Editor, bukan penulis.** Tak menambah pengetahuan; celah jadi TODO, bukan tambalan.
- **Status hanya dari `--capture`** (script), tak pernah diketik AI (§1.2).
- **`source_refs` ⊆ sources.yaml, `node_ids` ⊆ node data/** — validator menolak id menggantung.
- **Tak ada prosa sintesis di `library/`.** Materi generate = artifacts/ + 403 (§7 2026-09-04).
