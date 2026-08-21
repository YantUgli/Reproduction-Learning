# Reproduction Learning Engine

Mesin latihan pribadi **single-user** yang membuktikan — lewat **eksekusi kode**,
bukan penilaian AI atau self-report — bahwa penggunanya benar-benar bisa
**memproduksi sebuah konsep dari nol tanpa AI**, lalu mempertahankannya dengan
spaced repetition.

Ini **bukan** e-learning, **bukan** course platform, dan **bukan** "AI pembuat
learning path". Ukuran keberhasilan tunggalnya adalah **`reproduce-without-AI`**.

> Spesifikasi lengkap & rasionalnya ada di
> [`PRD-reproduction-learning-engine-v1.2.md`](PRD-reproduction-learning-engine-v1.2.md).
> Rencana implementasi bertahap ada di [`docs/`](docs/README.md).

---

## Status

🚧 **Fase dokumentasi & fondasi.** Belum ada kode aplikasi. Milestone pertama
yang dikerjakan adalah **M0 (Scaffolding & Data Model)** — lihat
[docs/README.md](docs/README.md) untuk peta milestone.

---

## Konsep inti dalam 60 detik

- **Core loop:** `Ground → Hypothesize → VERIFY → Gap → Practice → Re-evaluate`.
  Hanya **VERIFY** (eksekusi kode) yang boleh memutuskan mastery.
- **Scaffold memudar:** dari worked example beranotasi (L3) sampai reproduksi
  penuh dari nol tanpa AI dengan timebox (L0).
- **Comprehension probe deterministik** (predict output / spot bug / trace) —
  pengganti esai, karena esai butuh AI untuk menilai (dilarang).
- **Mastery = lolos berulang berjarak** (default N=4), dijadwalkan pakai **FSRS**.
- **Grader pluggable** per node via `grader_type`
  (`unit_test`, `value_assert`, `structural`, `dom_behavior`, `metric_threshold`).

Dua peran manusia: **Bryant** (user tunggal) dan **Isyah** (builder & authority
yang mengkurasi graf & mereview soal). Bryant tidak pernah menyentuh definisi graf
prerequisite — self-report-nya tidak reliabel (illusion of competence).

---

## Tech stack

| Bagian | Pilihan |
|---|---|
| Frontend | Next.js (React) + Monaco Editor (sandbox, no-AI) |
| Backend | FastAPI (Python) |
| Database | SQLite (single-user, local-first) |
| Node/edge store | File YAML di `data/` (dikurasi manual, di-review seperti kode) |
| Scheduler / SR | `py-fsrs` (**jangan tulis algoritma SR sendiri**) |
| Eksekusi test | **Subprocess + venv + tempdir** (di balik interface `Executor`) |
| AI engine | Claude Code (headless CLI, async via file artifact) — opsional, mulai M5 |
| Deployment | Lokal di device pengguna; tanpa auth, tanpa cloud |

> **Catatan eksekusi:** PRD menyebut Docker per attempt; implementasi memakai
> subprocess karena isolasi Docker "bukan soal keamanan" (kode milik pengguna
> sendiri). Backend eksekusi ada di balik interface, bisa ditukar ke Docker/Pyodide
> nanti. Detail: [docs/README.md §1](docs/README.md).

---

## Struktur project (target — dibentuk di M0)

```
.
├── PRD-reproduction-learning-engine-v1.2.md   # sumber kebenaran produk
├── README.md                                  # file ini
├── CLAUDE.md                                   # instruksi untuk Claude Code
├── docs/                                       # dokumentasi implementasi per milestone
│   ├── README.md                               # peta milestone & strategi
│   └── milestones/
├── backend/                                    # FastAPI app + executor + graders
│   ├── app/
│   │   ├── main.py
│   │   ├── db.py
│   │   ├── models.py
│   │   ├── executor/                           # interface + subprocess backend
│   │   ├── graders/                            # unit_test, value_assert, ...
│   │   ├── routers/
│   │   └── services/                           # node_loader, scheduler
│   ├── tests/
│   └── pyproject.toml
├── frontend/                                   # Next.js + Monaco
├── data/                                       # node & edge (YAML), sumber otoritatif
│   └── domains/fastapi/
└── harness/                                    # runner pytest telanjang (M1)
```

---

## Cara menjalankan

> ⚠️ Perintah di bawah adalah **target** untuk setelah M0–M3. Saat ini repo baru
> berisi dokumentasi; belum ada yang bisa dijalankan. Instruksi ini akan diperbarui
> begitu tiap milestone menyediakan komponennya.

```bash
# Backend (FastAPI) — tersedia setelah M0
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e .
uvicorn app.main:app --reload            # http://localhost:8000

# Frontend (Next.js) — tersedia setelah M3
cd frontend
npm install
npm run dev                              # http://localhost:3000

# Harness pytest telanjang — tersedia setelah M1
python harness/run.py <path-node-instance>
```

---

## Untuk developer baru: baca dengan urutan ini

1. **[PRD §0–§2](PRD-reproduction-learning-engine-v1.2.md)** — apa & kenapa; anchor
   yang tak bisa ditawar.
2. **[PRD §8 Guardrails](PRD-reproduction-learning-engine-v1.2.md)** — ide yang sudah
   ditolak beserta alasannya. Membaca ini menghemat waktumu.
3. **[docs/README.md](docs/README.md)** — peta milestone & dependency.
4. **[CLAUDE.md](CLAUDE.md)** — konvensi & aturan kerja di repo ini.
5. Milestone aktif di [docs/milestones/](docs/milestones/).
