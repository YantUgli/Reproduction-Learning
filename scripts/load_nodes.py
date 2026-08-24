#!/usr/bin/env python3
"""Muat seluruh `data/` ke SQLite (M2 langkah 6, multi-domain sejak M6).

Memuat SETIAP domain di `data/domains/*`. Idempoten. Cetak ringkasan per domain.

Pemakaian:
    python scripts/load_nodes.py [domain ...]
"""

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "backend"))

from sqlmodel import Session  # noqa: E402

from app.config import DATA_DIR  # noqa: E402
from app.db import engine, init_db  # noqa: E402
from app.services.node_loader import load_domain_into_db  # noqa: E402


def main(argv: list[str]) -> int:
    init_db()
    root = DATA_DIR / "domains"
    domain_dirs = (
        [root / name for name in argv]
        if argv
        else sorted(p for p in root.iterdir() if p.is_dir())
    )

    with Session(engine) as session:
        for domain_dir in domain_dirs:
            report = load_domain_into_db(session, domain_dir)
            print(
                f"loaded {domain_dir.name}: "
                f"{report.nodes} node, {report.instances} instance, "
                f"{report.probes} probe, {report.edges} edge"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
