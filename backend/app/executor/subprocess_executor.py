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

_IS_WINDOWS = os.name == "nt"

# Variabel env minimal yang diwariskan ke subprocess. Sengaja whitelist, bukan
# blacklist: kredensial/API key (ANTHROPIC_API_KEY, dll) tak akan pernah bocor,
# dan environment test jadi deterministik.
_ENV_WHITELIST = ("PATH", "HOME", "LANG", "LC_ALL", "LC_CTYPE", "TMPDIR")

# Windows menolak jalan tanpa beberapa variabel ini. SYSTEMROOT khususnya wajib:
# tanpanya inisialisasi Winsock gagal ("requested service provider could not be
# loaded or initialized") — dan itu mematikan seluruh node FastAPI yang di-grade
# lewat TestClient. Semuanya variabel sistem, bukan kredensial; whitelist tetap utuh.
_ENV_WHITELIST_WINDOWS = (
    "SYSTEMROOT",
    "SYSTEMDRIVE",
    "WINDIR",
    "COMSPEC",
    "PATHEXT",
    "TEMP",
    "TMP",
    "NUMBER_OF_PROCESSORS",
    "PROCESSOR_ARCHITECTURE",
)


def _clean_env() -> dict[str, str]:
    names = _ENV_WHITELIST + (_ENV_WHITELIST_WINDOWS if _IS_WINDOWS else ())
    env = {k: os.environ[k] for k in names if k in os.environ}
    # Nonaktifkan pengumpulan cache pytest & bytecode agar tempdir bersih.
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def _group_kwargs() -> dict[str, object]:
    """Taruh subprocess di grup proses sendiri supaya timeout bisa membunuh SELURUH
    pohon proses (termasuk anak yang di-spawn), bukan cuma pytest-nya.

    POSIX: `start_new_session=True` (setsid). Windows: `start_new_session` diabaikan
    oleh subprocess, jadi pakai CREATE_NEW_PROCESS_GROUP.
    """
    if _IS_WINDOWS:
        return {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
    return {"start_new_session": True}


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

            start = time.monotonic()
            proc = subprocess.Popen(
                cmd,
                cwd=tmpdir,
                env=_clean_env(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                **_group_kwargs(),
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
    """Bunuh seluruh pohon proses subprocess lalu tunggu reap."""
    if _IS_WINDOWS:
        # Windows tak punya killpg; taskkill /T membunuh proses + seluruh anaknya.
        try:
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                capture_output=True,
                check=False,
            )
        except OSError:
            pass
        # taskkill kadang meleset (proses sudah keburu keluar) — pastikan mati.
        try:
            proc.kill()
        except OSError:
            pass
        return

    try:
        pgid = os.getpgid(proc.pid)
        os.killpg(pgid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        # Proses sudah mati, atau tak bisa akses grup — fallback ke kill langsung.
        try:
            proc.kill()
        except ProcessLookupError:
            pass
