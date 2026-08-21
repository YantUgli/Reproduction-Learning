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

# BEDAKAN dua batas waktu (PRD §7.6, M3 Keputusan):
# - timebox_seconds (per node, di DB) = batas waktu Bryant BERPIKIR (UI countdown).
# - EXECUTION_TIMEOUT_SECONDS = batas kode MENGGANTUNG saat runner mengeksekusi.
# Keduanya beda dan tak boleh disatukan.
EXECUTION_TIMEOUT_SECONDS = 10

# Origin frontend Next.js untuk CORS (dev).
FRONTEND_ORIGIN = "http://localhost:3000"
