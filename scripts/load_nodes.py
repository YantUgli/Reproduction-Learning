#!/usr/bin/env python3
"""Muat seluruh `data/` ke SQLite (M2 langkah 6).

Panggil node_loader untuk domain fastapi. Idempoten. Cetak ringkasan.

Pemakaian:
    python scripts/load_nodes.py
"""

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "backend"))

from sqlmodel import Session  # noqa: E402

from app.config import DATA_DIR  # noqa: E402
from app.db import engine, init_db  # noqa: E402
from app.services.node_loader import load_domain_into_db  # noqa: E402


def main() -> int:
    init_db()
    domain_dir = DATA_DIR / "domains" / "fastapi"
    with Session(engine) as session:
        report = load_domain_into_db(session, domain_dir)
    print(
        "loaded: "
        f"{report.domains} domain, {report.sources} source, {report.nodes} node, "
        f"{report.instances} instance, {report.probes} probe, {report.edges} edge"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
