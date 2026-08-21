"""Executor default v1: subprocess + venv (interpreter aplikasi) + tempdir.

Bukan Docker (lihat docs/README §1 & CLAUDE.md §2). Isolasi Docker "bukan soal
keamanan"; yang dibutuhkan hanya:
- reproducibility → interpreter/venv yang sama (`sys.executable -m pytest`),
- isolasi ringan → tempdir baru per panggilan + timeout yang benar-benar membunuh.

Stdlib saja (subprocess, tempfile, os, signal). Jangan tambah dependency di sini —
semua verifikasi produk bergantung pada kesederhanaan komponen ini.
"""

import os
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from app.executor.base import ExecutionResult

# Variabel env minimal yang diwariskan ke subprocess. Sengaja whitelist, bukan
# blacklist: kredensial/API key (ANTHROPIC_API_KEY, dll) tak akan pernah bocor,
# dan environment test jadi deterministik.
_ENV_WHITELIST = ("PATH", "HOME", "LANG", "LC_ALL", "LC_CTYPE", "TMPDIR")


def _clean_env() -> dict[str, str]:
    env = {k: os.environ[k] for k in _ENV_WHITELIST if k in os.environ}
    # Nonaktifkan pengumpulan cache pytest & bytecode agar tempdir bersih.
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


class SubprocessExecutor:
    """Implementasi `Executor` Protocol berbasis subprocess."""

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

            # start_new_session=True menaruh subprocess di grup proses sendiri,
            # sehingga saat timeout kita bisa membunuh SELURUH grup (termasuk anak
            # yang mungkin di-spawn), tidak menyisakan proses menggantung/zombie.
            start = time.monotonic()
            proc = subprocess.Popen(
                cmd,
                cwd=tmpdir,
                env=_clean_env(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                start_new_session=True,
            )
            timed_out = False
            try:
                stdout, stderr = proc.communicate(timeout=timeout_seconds)
            except subprocess.TimeoutExpired:
                timed_out = True
                _kill_process_group(proc)
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


def _kill_process_group(proc: subprocess.Popen) -> None:
    """Bunuh seluruh grup proses subprocess (SIGKILL) lalu tunggu reap."""
    try:
        pgid = os.getpgid(proc.pid)
        os.killpg(pgid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        # Proses sudah mati, atau tak bisa akses grup — fallback ke kill langsung.
        try:
            proc.kill()
        except ProcessLookupError:
            pass
