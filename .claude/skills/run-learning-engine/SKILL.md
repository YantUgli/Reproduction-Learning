---
name: run-learning-engine
description: Build, launch, and drive the Reproduction Learning Engine — FastAPI backend + Next.js frontend. Use when asked to run, start, serve, smoke-test, or screenshot the app (dashboard, node reproduction loop, placement, review), or to verify a change works in the real running app.
---

# Menjalankan Reproduction Learning Engine

Aplikasi dua-proses: **backend FastAPI** (`backend/`, venv + uvicorn, port 8000) yang
menyimpan sinyal ke SQLite, dan **frontend Next.js** (`frontend/`, `next dev`, port 3000)
yang mem-fetch backend dari BROWSER. Digerakkan oleh
[`driver.sh`](.claude/skills/run-learning-engine/driver.sh): ia meluncurkan kedua server,
menunggu keduanya sehat, lalu **menggerakkannya** — `curl` smoke atas endpoint backend
nyata + screenshot headless Chrome atas halaman frontend nyata.

**Semua path di dokumen ini relatif terhadap root repo** (`Project_Learn_Bryant/`).

## Prasyarat

Sudah tersedia di container ini — cek dulu sebelum memasang:

```bash
node --version        # v24 (via nvm) — butuh untuk frontend
python3 --version     # 3.12
google-chrome --version   # 149 — driver pakai ini untuk screenshot (BUKAN chromium-cli)
```

Tak ada `apt-get` yang diperlukan di container ini. `google-chrome` dipakai headless
dengan `--no-sandbox` (wajib sebagai root di container).

## Setup (dari clone bersih)

Kalau `backend/.venv`, `frontend/node_modules`, dan kurikulum penuh sudah ada
(cek: `curl -s localhost:8000/stats` menyebut 19 node), **lewati bagian ini**.

```bash
# 1. Backend: venv + editable install (menarik fastapi, uvicorn, sqlmodel, fsrs, numpy, pyyaml)
cd backend && python3 -m venv .venv && .venv/bin/pip install -e ".[dev]" && cd ..

# 2. Muat SELURUH kurikulum ke SQLite (19 node: fastapi+ml+react). Idempoten, jalankan dari root.
#    app.db yang ter-commit hanya berisi 5 node — langkah ini WAJIB untuk kurikulum penuh.
backend/.venv/bin/python scripts/load_nodes.py

# 3. Frontend deps. (Gejala kalau terlewat: halaman 500, "Cannot find module 'tailwindcss'".)
cd frontend && npm install && cd ..

# 4. HANYA jika akan menilai node React (domain dom_behavior): runtime grading JS.
#    Tidak perlu untuk sekadar menjalankan/men-screenshot UI.
cd runtime/react && npm install && cd ../..
```

## Run (jalur agent) — pakai driver

```bash
# Luncurkan keduanya + smoke backend + screenshot frontend. ~40 dtk (next dev compile saat hit pertama).
.claude/skills/run-learning-engine/driver.sh up

# Server sudah jalan, cuma mau ulang smoke+screenshot:
.claude/skills/run-learning-engine/driver.sh smoke

# Matikan kedua server:
.claude/skills/run-learning-engine/driver.sh down
```

Output (log + screenshot) mendarat di `$RUN_OUT` bila diset, else `$CLAUDE_SCRATCHPAD`,
else `./.run-artifacts/`. Untuk mengarahkannya ke scratchpad sesi:

```bash
RUN_OUT="$CLAUDE_SCRATCHPAD" .claude/skills/run-learning-engine/driver.sh up
```

Driver menghasilkan `frontend-{home,node,placement,review}.png` +
`backend.log` / `frontend.log`. **Buka screenshot-nya** — `home` yang ~115 KB+ berarti data
backend termuat; ~40 KB berarti kartu error "Tidak bisa menghubungi backend" (lihat Gotchas).
`node` menampilkan loop reproduksi inti: pemilih level L3→L0, contoh dikerjakan, dan editor
Monaco ber-syntax-highlight — inti MVP dan lapisan yang paling sering disentuh PR.

Smoke sukses dicetak `SMOKE OK`. Kalau server gagal naik, driver men-`tail` log yang relevan.

## Run (jalur manusia) — dua terminal

Berguna kalau mau berinteraksi langsung; tak berguna headless (tak ada layar).

```bash
# terminal 1
cd backend && .venv/bin/uvicorn app.main:app --reload
# terminal 2
cd frontend && npm run dev      # buka http://localhost:3000  (JANGAN 127.0.0.1 — lihat Gotchas)
```

## Test & lint (sanity, bukan acara utama)

```bash
cd backend && .venv/bin/pytest && .venv/bin/ruff check .
```

## Gotchas

- **Buka frontend lewat `localhost:3000`, JANGAN `127.0.0.1:3000`.** CORS backend hanya
  mengizinkan origin `http://localhost:3000` (`backend/app/config.py` `FRONTEND_ORIGIN`).
  Dari `127.0.0.1` origin browser tak cocok → tiap fetch klien diblokir → halaman merender
  kerangka lalu menampilkan kartu merah "Tidak bisa menghubungi backend", padahal backend
  sehat. Driver sudah memakai `localhost` di kedua URL justru karena jebakan ini.
- **`app.db` yang ter-commit hanya 5 node.** Kurikulum penuh (19) baru ada setelah
  `scripts/load_nodes.py`. Backend membaca file DB yang sama secara live, jadi menjalankan
  loader saat server hidup langsung mengubah `/stats` tanpa restart.
- **Screenshot pakai `google-chrome`, bukan `chromium-cli`** (tak terpasang di sini), dan
  wajib `--no-sandbox` (proses jalan sebagai root). `--virtual-time-budget=8000` memberi
  waktu fetch klien selesai sebelum jepret; kurang dari itu bisa menangkap keadaan pra-data.
- **`next dev` meng-compile saat request pertama**, bukan saat "Ready". Karena itu driver
  menunggu `GET /` mengembalikan 200 (bukan sekadar proses hidup) sebelum men-screenshot.
- **DB path absolut (`backend/app.db`)** dari mana pun cwd-nya (keputusan CLAUDE.md §7
  2026-08-21) — uvicorn dari `backend/` dan skrip dari root menunjuk file DB yang sama.
- **Monaco di-self-host** (bundled, bukan dari CDN) — editor tetap muncul offline; jangan
  "perbaiki" dengan mengembalikannya ke loader CDN (keputusan §7 2026-08-24).

## Troubleshooting

| Gejala | Sebab / Perbaikan |
|---|---|
| Frontend 500, log: `Cannot find module 'tailwindcss'` | `node_modules` parsial. `cd frontend && npm install`, lalu **restart** `next dev` (proses lama meng-cache kegagalan). |
| Halaman merender tapi kartu merah "Tidak bisa menghubungi backend" | Backend mati, ATAU frontend dibuka via `127.0.0.1` (CORS) — pakai `localhost`. |
| `/stats` menyebut 5 node, bukan 19 | Jalankan `backend/.venv/bin/python scripts/load_nodes.py`. |
| `uvicorn: command not found` | Aktifkan/rujuk venv: `backend/.venv/bin/uvicorn ...`, atau `pip install -e ".[dev]"` belum jalan. |
| Node React ter-grade FAIL padahal benar | Runtime React belum dipasang: `cd runtime/react && npm install` (hanya untuk penilaian node React). |
