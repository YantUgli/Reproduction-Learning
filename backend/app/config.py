"""Konstanta terpusat.

Semua angka "ajaib" dari PRD masuk di sini, jangan sebar di kode.
"""

from pathlib import Path

# Root repo = dua tingkat di atas file ini (backend/app/config.py -> repo/).
REPO_ROOT = Path(__file__).resolve().parents[2]

# Direktori data node/edge/domain (YAML, di-commit ke git).
DATA_DIR = REPO_ROOT / "data"

# Database SQLite single-user, local-first.
DATABASE_URL = "sqlite:///./app.db"

# Ambang mastery default: N sukses berjarak sebelum sebuah node dianggap dikuasai.
# (PRD §2 / CLAUDE.md — verifikasi via eksekusi, bukan AI.)
MASTERY_SUCCESSES_DEFAULT = 4

# Origin frontend Next.js untuk CORS (dev).
FRONTEND_ORIGIN = "http://localhost:3000"
