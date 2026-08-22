"""Konstanta terpusat.

Semua angka "ajaib" dari PRD masuk di sini, jangan sebar di kode.
"""

from pathlib import Path

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

# Origin frontend Next.js untuk CORS (dev).
FRONTEND_ORIGIN = "http://localhost:3000"
