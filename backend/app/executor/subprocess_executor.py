"""Executor default v1: subprocess + venv (interpreter aplikasi) + tempdir.

Bukan Docker (lihat docs/README §1 & CLAUDE.md §2). Isolasi Docker "bukan soal
keamanan"; yang dibutuhkan hanya:
- reproducibility → interpreter/venv yang sama (`sys.executable -m pytest`),
- isolasi ringan → tempdir baru per panggilan + timeout yang benar-benar membunuh.

Stdlib saja (subprocess, tempfile). Jangan tambah dependency di sini — semua
verifikasi produk bergantung pada kesederhanaan komponen ini.
"""

import subprocess
import sys
import tempfile
import time
from pathlib import Path

from app.executor.base import ExecutionResult
from app.executor.process import clean_env, group_kwargs, kill_process_group


class SubprocessExecutor:
    """Implementasi `Executor` Protocol berbasis subprocess (pytest)."""

    def run(
        self,
        files: dict[str, str],
        test_entry: str,
        timeout_seconds: int,
    ) -> ExecutionResult:
        with tempfile.TemporaryDirectory(prefix="rle_exec_") as tmp:
            tmpdir = Path(tmp)
            for name, content in files.items():
                target = tmpdir / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")

            cmd = [sys.executable, "-m", "pytest", test_entry, "-q", "-p", "no:cacheprovider"]

            start = time.monotonic()
            proc = subprocess.Popen(
                cmd,
                cwd=tmpdir,
                env=clean_env(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                **group_kwargs(),
            )
            timed_out = False
            try:
                stdout, stderr = proc.communicate(timeout=timeout_seconds)
            except subprocess.TimeoutExpired:
                timed_out = True
                kill_process_group(proc)
                stdout, stderr = proc.communicate()
            duration = time.monotonic() - start

            exit_code = proc.returncode
            passed = (not timed_out) and exit_code == 0
            return ExecutionResult(
                passed=passed,
                stdout=stdout or "",
                stderr=stderr or "",
                duration_seconds=duration,
                timed_out=timed_out,
                exit_code=exit_code,
            )
