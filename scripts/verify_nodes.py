#!/usr/bin/env python3
"""GERBANG MUTU AUTHORING (M2 langkah 2).

Untuk SETIAP instance node: jalankan `hidden_test.py` lawan `reference_solution.py`
via SubprocessExecutor (M1). Semua HARUS PASS — ini penegak aturan PRD §10 R4
("hidden test wajib hijau di solusi referensi"). Node merah TIDAK BOLEH di-commit.

Termasuk node fixture `_example` (verifikasi harness itu sendiri).

Pemakaian:
    python scripts/verify_nodes.py
Exit 0 = semua hijau; 1 = ada yang merah/timeout.
"""

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "backend"))

from app.config import DATA_DIR  # noqa: E402
from app.executor import SubprocessExecutor  # noqa: E402

_TIMEOUT_SECONDS = 30


def _iter_instance_dirs(nodes_root: Path):
    for node_dir in sorted(p for p in nodes_root.iterdir() if p.is_dir()):
        instances = node_dir / "instances"
        if not instances.is_dir():
            continue
        for variant in sorted(p for p in instances.iterdir() if p.is_dir()):
            yield node_dir.name, variant


def main() -> int:
    executor = SubprocessExecutor()
    nodes_root = DATA_DIR / "domains" / "fastapi" / "nodes"
    if not nodes_root.is_dir():
        print(f"tidak ada folder nodes: {nodes_root}")
        return 1

    total = 0
    failed = 0
    for node_id, variant in _iter_instance_dirs(nodes_root):
        solution = variant / "reference_solution.py"
        hidden = variant / "hidden_test.py"
        if not (solution.exists() and hidden.exists()):
            print(f"[SKIP] {node_id}/{variant.name}: file tidak lengkap")
            continue

        total += 1
        result = executor.run(
            files={
                "solution.py": solution.read_text(encoding="utf-8"),
                "test_solution.py": hidden.read_text(encoding="utf-8"),
            },
            test_entry="test_solution.py",
            timeout_seconds=_TIMEOUT_SECONDS,
        )
        if result.passed:
            print(f"[PASS] {node_id}/{variant.name}  ({result.duration_seconds:.2f}s)")
        else:
            failed += 1
            verdict = "TIMEOUT" if result.timed_out else "FAIL"
            print(f"[{verdict}] {node_id}/{variant.name}  ({result.duration_seconds:.2f}s)")
            tail = (result.stdout + result.stderr).strip().splitlines()[-15:]
            for line in tail:
                print(f"    {line}")

    print(f"\n{total - failed}/{total} instance hijau.")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
