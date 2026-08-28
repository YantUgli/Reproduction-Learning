# Brainstorm — Lajur Knowledge Management + tooling `pi` (Eero/Amos)

> **Status:** dokumen diskusi/desain, **bukan** milestone dan **bukan** keputusan.
> Tidak mengubah roadmap atau invariant apa pun. Ia merekam hasil brainstorm arah
> "learning system with AI" (KM lane) + analisis tooling `pi` milik Amos, dan
> memetakannya ke arsitektur proyek.
>
> Sumber kebenaran produk tetap [`../PRD-reproduction-learning-engine-v1.2.md`](../PRD-reproduction-learning-engine-v1.2.md)
> dan invariant di [`../CLAUDE.md`](../CLAUDE.md) §1. Kalau ada konflik, **invariant menang** —
> dokumen ini tidak berwenang melonggarkannya.
>
> Konteks lanjutan dari: [`reference-eero-ai-learning-video.md`](reference-eero-ai-learning-video.md)
> dan [`reference-alter-ai-learning-video.md`](reference-alter-ai-learning-video.md).
> Sumber tooling: `https://github.com/amosblomqvist/learn`
> — **Dicatat:** 2026-08-28

---

Sudah aku cek repo-nya. Ini penting karena menjawab langsung "tools apa itu" — dan
jawabannya membebaskanmu dari kebutuhan membangun banyak hal.

## Apa itu `pi` sebenarnya — dan kabar baiknya

Sistem Eero (`amosblomqvist/learn`) adalah folder `.pi/` berisi konfigurasi untuk
`pi`, sebuah agent CLI yang fungsinya mirip Claude Code. Isinya:

| Komponen di `pi` | Fungsi | Padanan yang **sudah kamu punya** |
|---|---|---|
| `ask-user-question` (popup interaktif) | Form tanya-jawab ke user | **AskUserQuestion** — native Claude Code (aku baru pakai turn lalu) |
| skill `teach` | System prompt Probe→Plan→Teach | Custom skill di `.claude/skills/` |
| agent `researcher` | Cek akurasi fakta (grounding) | Subagent + disiplin sitasi R3 (M5) |
| `svg-maker`/`mermaid-maker`, `visualize` | Diagram | Subagent + Obsidian graph |
| **`quiz` (MCQ bernilai)** | **Penilai pemahaman** | **← ini yang kamu GANTI dengan reproduce-without-AI** |
| output = file markdown | Vault (Obsidian buka foldernya) | Library markdown-mu |

**Punchline-nya: kamu sudah punya seluruh mesin Eero secara native di Claude Code.**
Popup interaktif, skill, subagent, output markdown — semua ada. Kamu tidak perlu
`pi`. Yang kamu bangun cuma **skill kustom + lem ke engine.**

Dan satu-satunya komponen Eero yang kamu **buang dengan sengaja** adalah `quiz`
(MCQ sebagai gate) — kamu menggantinya dengan reproduce-without-AI. Itu justru
keunggulanmu atas sistemnya: di titik Eero menaruh kuis, kamu menaruh oracle.

## Dua alur pemakaianmu — dipetakan, dengan batas ditandai

**Penggunaan 1 (belajar FastAPI dari nol):**

```
skill intake (AskUserQuestion): tujuan, baseline, cut-list, milestones
   └─ + pertanyaan "meninjau kemampuan"   ← [BATAS] ini menetapkan LANTAI AWAL, bukan mastery
generate materi + roadmap + learning path  → masuk LIBRARY (markdown, browsable, graph Obsidian)
   └─ tiap bagian materi mengusulkan node reproduksi  → FORGE
belajar e-learning + reproduce tanpa AI per materi     → verdict tetap di FORGE
```

Batas yang harus kamu pegang sadar: "meninjau kemampuan saya" itu **menentukan dari
mana kamu mulai** (ini persis placement / R2 yang sudah ada) — **bukan** memvonis
kamu sudah menguasai. AI menebak lantai; reproduksi yang membuktikan. Selama itu, aman.

Satu catatan jujur untuk Penggunaan 1: materinya **di-generate AI**, dan di sinilah
§8 dulu waspada ("AI sebagai content library"). Penawarnya adalah disiplin yang
kedua dokumen referensimu sendiri puji — **grounding**: materi generate **wajib
bersitasi** ke sumber otoritatif (docs FastAPI), bukan sekadar ingatan LLM. Itu
persis peran `researcher` Eero dan R3-mu. Jadi materi generate boleh, tapi
**tergrounding + berlabel Library (referensi)**, tak pernah verdict.

**Penggunaan 2 (mirror course deeplearning):**

```
skill course-scaffold: form nama course, silabus, modul  → folder LIBRARY kosong-terstruktur
skill note-refine: Bryant paste/dikte catatan mentah → Claude rapikan per silabus
course selesai di luar  =  catatan tersusun di proyek
   └─ berhenti di sini (arsip)  ATAU lanjut seperti Penggunaan 1 (tempa jadi reproduksi)
```

Ini **pilar paling aman** — murni tangkap + rapikan, nol mastery. Peran AI di sini
= **editor** (merapikan catatan agar jelas), **bukan** menilai pemahamanmu. Nilai
tersembunyinya besar: catatan course-mu jadi **ground-truth pribadimu** → bisa jadi
materi R3 yang muncul saat kamu gagal attempt. Course luar berubah jadi bahan bakar
engine.

## Satu penjaga yang menentukan apakah ini tetap "proyek-mu" atau jadi "Eero jilid 2"

Ini bagian terpenting, dan aku minta kamu tahan di kepala. Kedua alur menghasilkan
materi yang **nyaman dikonsumsi**. Bahaya terbesarnya bukan satu invariant jebol —
tapi kamu menghabiskan seluruh waktu di **Library yang nyaman** (baca materi
generate/refine, merasa belajar) dan **Forge yang tak nyaman** (reproduksi)
terbengkalai. Itu **persis** jebakan 88%-tak-menyelesaikan yang video Eero diagnosa.

Penjaganya satu, dan sederhana:

> **Progres materi diukur dari "% yang sudah direproduksi", bukan "% yang sudah
> dibaca."** Sebuah course di Library tampil belum-selesai sampai node-nya tertempa.
> Library terasa berlubang sampai di-Forge.

Kalau kamu mengukur kemajuan Library dari membaca, kamu sudah balik ke consumption
comfort — dan kehilangan satu hal yang bikin proyekmu istimewa. Kalau kamu
mengukurnya dari reproduksi, Library dan Forge tarik-menarik ke arah yang benar.

## Rekomendasi konkret irisan pertama

Jangan nyalakan semua. Skill yang perlu dibangun, urut dari paling aman & paling
cepat berguna:

1. **`course-intake`** (Penggunaan 2) — AskUserQuestion → folder markdown terstruktur
   dari silabus. Paling aman (nol mastery), langsung berguna, dan membuktikan lajur
   Library. Mulai dari sini.
2. **`note-refine`** — paste catatan mentah → Claude rapikan ke markdown per silabus.
   Melengkapi mirror course.
3. **`learn-intake`** (Penggunaan 1) — template 5-keputusan (tujuan/baseline/cut-list/
   milestones) → materi tergrounding + usulan node. Ini yang menyentuh generate
   materi; bangun setelah dua di atas stabil.
4. **Jembatan** — link catatan ↔ node, dan dashboard "tertangkap vs tertempa".
   Bangun terakhir; ini yang menjaga penjaga di atas.

Library = folder markdown di dalam repo (mis. `library/`), git-committed & di-diff
seperti `data/`, kamu buka di Obsidian untuk graph. Tidak ada aplikasi kedua.

---

**Langkah berikut (terbuka, belum diputuskan):** sketsa kontrak skill `course-intake`
(pertanyaan form apa saja, dan bentuk folder + frontmatter markdown yang ia
hasilkan) — irisan pertama yang paling aman dan paling cepat terasa. Alternatif:
bahas dulu penjaga "% direproduksi" sebelum turun ke skill.
