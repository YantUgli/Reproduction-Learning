"""Konstanta terpusat.

Semua angka "ajaib" dari PRD masuk di sini, jangan sebar di kode.
"""

import os
from pathlib import Path


def _env_flag(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


# Root repo = dua tingkat di atas file ini (backend/app/config.py -> repo/).
REPO_ROOT = Path(__file__).resolve().parents[2]

# Direktori data node/edge/domain (YAML, di-commit ke git).
DATA_DIR = REPO_ROOT / "data"

# Database SQLite single-user, local-first.
# Path ABSOLUT (anchored di backend/app.db) supaya stabil apa pun cwd: uvicorn
# (dari backend/) & scripts/*.py (dari repo root) menunjuk DB yang sama.
# (Deviasi dari default M0 `sqlite:///./app.db` — dicatat di CLAUDE.md §7.)
DB_PATH = REPO_ROOT / "backend" / "app.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Ambang mastery default: N sukses berjarak sebelum sebuah node dianggap dikuasai.
# (PRD §2 / CLAUDE.md — verifikasi via eksekusi, bukan AI.)
MASTERY_SUCCESSES_DEFAULT = 4

# --------------------------------------------------------------------------- #
# FSRS (M4) — parameter scheduler. Algoritmanya milik py-fsrs; di sini HANYA
# penyetelan yang khas produk ini. Lihat app/services/scheduler.py.
# --------------------------------------------------------------------------- #
FSRS_DESIRED_RETENTION = 0.9

# Unit yang dijadwalkan adalah REPRODUKSI node (20–40 menit), bukan flashcard
# recognition (PRD §7.5). Default py-fsrs punya learning steps 1 menit & 10 menit —
# masuk akal untuk kartu, absurd untuk tantangan reproduksi. Dikosongkan supaya
# kartu langsung masuk state Review dan interval berskala HARI sejak awal.
FSRS_LEARNING_STEPS: tuple = ()
FSRS_RELEARNING_STEPS: tuple = ()

# Fuzzing = pengacakan ± interval supaya beban deck besar tersebar. Single-user
# dengan puluhan node tak punya masalah itu, sementara interval deterministik jauh
# lebih mudah di-debug & di-test. Dimatikan.
FSRS_ENABLE_FUZZING = False

# Placement (PRD open question Q4): batas node yang diuji dalam SATU sesi placement
# supaya tidak melelahkan. Placement berhenti lebih awal di batas fail→pass pertama;
# angka ini hanya melindungi kasus terburuk (gagal terus sampai dasar).
PLACEMENT_MAX_NODES = 7

# Ambang "varian menipis": review wajib memakai instance berbeda tiap jatuh tempo.
# Di bawah angka ini rotasi mulai berulang → sinyal untuk menaikkan ke authoring
# (PRD open question Q1, dugaan awal 3).
MIN_VARIANTS_FOR_REVIEW = 3

# BEDAKAN dua batas waktu (PRD §7.6, M3 Keputusan):
# - timebox_seconds (per node, di DB) = batas waktu Bryant BERPIKIR (UI countdown).
# - EXECUTION_TIMEOUT_SECONDS = batas kode MENGGANTUNG saat runner mengeksekusi.
# Keduanya beda dan tak boleh disatukan.
EXECUTION_TIMEOUT_SECONDS = 10

# --------------------------------------------------------------------------- #
# Domain kedua (M6) — React & ML. Menambah domain = menambah grader, TITIK:
# tak ada kolom DB baru, tak ada cabang per-domain di loop/scaffold/scheduler.
# --------------------------------------------------------------------------- #
# Runtime eksekusi hidden test React (Node + vitest + jsdom). Dependency ter-pin di
# `runtime/react/package.json` — analog venv ter-pin di sisi Python.
REACT_RUNTIME_DIR = REPO_ROOT / "runtime" / "react"

# Timeout eksekusi React JAUH lebih besar dari Python bukan karena kodenya lebih
# lambat, tapi karena start-up-nya: vitest harus menyalakan jsdom + mentransform JSX
# (~50 detik saat dingin, ~7 detik saat panas). Menyamakannya dengan 10s Python akan
# membuat submisi BENAR ter-grade FAIL — kegagalan terburuk yang bisa dipunyai
# sistem yang seluruh kepercayaannya bersandar pada sinyal pass/fail.
REACT_EXECUTION_TIMEOUT_SECONDS = 120

# Origin frontend Next.js untuk CORS (dev).
FRONTEND_ORIGIN = "http://localhost:3000"

# --------------------------------------------------------------------------- #
# Integrasi Claude Code (M5) — AKSELERATOR, BUKAN FONDASI (PRD §10, RISK-3).
# Semua di bawah ini boleh mati tanpa merusak loop M3/M4.
# --------------------------------------------------------------------------- #
# Direktori kerja output Claude Code. Claude Code menulis HANYA ke sini; promosi ke
# `data/`/DB cuma lewat gate (skema + test + approve Isyah). Git-ignored.
ARTIFACTS_DIR = REPO_ROOT / "artifacts"

# Kill switch. Dimatikan → endpoint trigger balas 503 dan loop inti tak tersentuh.
CLAUDE_INTEGRATION_ENABLED = _env_flag("CLAUDE_INTEGRATION_ENABLED", True)

# Promosi OTOMATIS artifact yang lolos seluruh gerbang mesin (M7 langkah 9).
# Sampai M6 tiap artifact berhenti di `ready` menunggu approve Isyah; sejak
# §7 2026-08-31 gerbang mesin yang memutuskan, dan peninjauan manusia pindah ke
# belakang (audit + pensiun). Dimatikan -> alurnya kembali seperti M5: artifact
# berhenti di `ready` dan menunggu klik manusia di `/authoring`.
CLAUDE_AUTO_PROMOTE = _env_flag("CLAUDE_AUTO_PROMOTE", True)

# Binary Claude Code headless. Tak ada di PATH → job `failed` dengan pesan jelas,
# bukan exception yang merembet ke request UI.
CLAUDE_CLI_PATH = os.environ.get("CLAUDE_CLI_PATH", "claude")

# Batas satu panggilan Claude Code. Ini agent CLI (bisa lama), bukan HTTP call —
# angkanya sengaja besar, dan pemanggilannya selalu di latar (job), tak pernah
# memblokir request UI.
CLAUDE_TIMEOUT_SECONDS = 900

# Retry TERBATAS (format output tak konsisten = risiko utama RISK-3). Satu ulangan
# saja: kalau dua kali gagal memenuhi kontrak, itu masalah prompt, bukan nasib.
CLAUDE_MAX_RETRIES = 1

# Batas panjang materi R3. Guardrail §8 (content library ditolak) yang bisa DIUJI:
# materi just-in-time, bukan bab. Artifact lebih panjang dari ini ditolak skema.
EXPLANATION_MAX_CHARS = 2500
