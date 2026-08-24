"""Perkakas proses bersama untuk semua Executor (M1, dipakai bersama sejak M6).

Dua Executor (pytest via CPython, vitest via Node) butuh hal yang sama persis:
environment yang bersih dan timeout yang benar-benar membunuh SELURUH pohon proses.
Menyalin logika itu per-executor berarti dua tempat yang bisa berbeda diam-diam —
dan yang kedua biasanya yang lupa membunuh proses anak.

Stdlib saja. Jangan tambah dependency di lapisan ini.
"""

import os
import signal
import subprocess

IS_WINDOWS = os.name == "nt"

# Variabel env minimal yang diwariskan ke subprocess. Sengaja whitelist, bukan
# blacklist: kredensial/API key (ANTHROPIC_API_KEY, dll) tak akan pernah bocor ke
# kode yang dieksekusi, dan environment test jadi deterministik.
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
    # Node/vite menaruh cache di bawah direktori profil; tanpa ini ia jatuh ke
    # jalur fallback yang lebih lambat (dan berisik) di tiap grading.
    "APPDATA",
    "LOCALAPPDATA",
    "USERPROFILE",
)


def clean_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    names = _ENV_WHITELIST + (_ENV_WHITELIST_WINDOWS if IS_WINDOWS else ())
    env = {k: os.environ[k] for k in names if k in os.environ}
    # Nonaktifkan pengumpulan cache pytest & bytecode agar tempdir bersih.
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    if extra:
        env.update(extra)
    return env


def group_kwargs() -> dict[str, object]:
    """Taruh subprocess di grup proses sendiri supaya timeout bisa membunuh SELURUH
    pohon proses (termasuk anak yang di-spawn), bukan cuma prosesnya sendiri.

    POSIX: `start_new_session=True` (setsid). Windows: `start_new_session` diabaikan
    oleh subprocess, jadi pakai CREATE_NEW_PROCESS_GROUP.
    """
    if IS_WINDOWS:
        return {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
    return {"start_new_session": True}


def kill_process_group(proc: subprocess.Popen) -> None:
    """Bunuh seluruh pohon proses subprocess lalu tunggu reap."""
    if IS_WINDOWS:
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
        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        # Proses sudah mati, atau tak bisa akses grup — fallback ke kill langsung.
        try:
            proc.kill()
        except ProcessLookupError:
            pass
