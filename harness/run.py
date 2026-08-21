#!/usr/bin/env python3
"""Harness pytest telanjang (M1).

Alat yang dipakai Isyah saat mengarang node (M2): ambil folder instance node,
jalankan hidden_test terhadap reference_solution, cetak PASS/FAIL + output.

Kontrak PRD §10 R4: sebuah hidden test hanya boleh masuk sistem kalau HIJAU di
solusi referensi. Alat ini yang membuktikannya.

Pemakaian:
    python harness/run.py <path-folder-instance>
    # mis. python harness/run.py data/domains/fastapi/nodes/_example/instances/variant_a

Exit code: 0 kalau PASS, 1 kalau FAIL/timeout (bisa dipakai di skrip/CI authoring).
"""

import sys
from pathlib import Path

# Harness hidup di root repo; backend package ada di ./backend. Pakai interpreter
# & venv yang sama dengan aplikasi (environment test = environment app).
_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "backend"))

from app.executor import SubprocessExecutor  # noqa: E402

# Nama file yang ditulis ke tempdir. Test meng-import `solution` (nama modul),
# jadi reference_solution.py disalin sebagai solution.py.
_SOLUTION_FILENAME = "solution.py"
_TEST_FILENAME = "test_solution.py"
_DEFAULT_TIMEOUT_SECONDS = 30


def _read(path: Path) -> str:
    if not path.exists():
        sys.exit(f"error: file tidak ditemukan: {path}")
    return path.read_text(encoding="utf-8")


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        sys.exit("pemakaian: python harness/run.py <path-folder-instance>")

    instance_dir = Path(argv[1]).resolve()
    if not instance_dir.is_dir():
        sys.exit(f"error: bukan folder: {instance_dir}")

    solution = _read(instance_dir / "reference_solution.py")
    hidden_test = _read(instance_dir / "hidden_test.py")

    files = {_SOLUTION_FILENAME: solution, _TEST_FILENAME: hidden_test}

    result = SubprocessExecutor().run(
        files=files,
        test_entry=_TEST_FILENAME,
        timeout_seconds=_DEFAULT_TIMEOUT_SECONDS,
    )

    verdict = "PASS" if result.passed else ("TIMEOUT" if result.timed_out else "FAIL")
    print(f"[{verdict}] {instance_dir}")
    print(f"durasi: {result.duration_seconds:.2f}s  exit_code={result.exit_code}")
    if result.stdout.strip():
        print("--- stdout ---")
        print(result.stdout.rstrip())
    if result.stderr.strip():
        print("--- stderr ---")
        print(result.stderr.rstrip())

    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
