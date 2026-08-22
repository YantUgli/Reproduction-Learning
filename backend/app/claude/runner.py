"""Panggilan Claude Code headless (M5 langkah 2).

Claude Code adalah **agent CLI async, bukan HTTP API** (PRD §10). Modul ini
memperlakukannya seperti job eksternal: satu panggilan subprocess dengan cwd =
direktori job, timeout keras, dan seluruh output mentah disimpan sebagai log.

Kontrak yang sengaja dijaga tipis:
- Runner TIDAK tahu apa-apa soal peran/kontrak artifact. Ia cuma menjalankan prompt
  dan melapor. Validasi ada di `contracts.py`, orkestrasi di `jobs.py`.
- Runner adalah `Protocol` (CLAUDE.md §3) supaya test memakai fake tanpa pewarisan
  dan tanpa pernah memanggil CLI sungguhan.
- CLI tak ada / gagal / timeout **bukan** exception yang merembet ke request UI —
  ia jadi `RunResult(ok=False)` dan berakhir sebagai job `failed` (RISK-3: kegagalan
  Claude Code tak boleh memblokir loop inti).
"""

import os
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from app.config import CLAUDE_CLI_PATH, CLAUDE_TIMEOUT_SECONDS

_IS_WINDOWS = os.name == "nt"


@dataclass
class RunResult:
    ok: bool
    stdout: str
    stderr: str
    exit_code: int | None
    timed_out: bool
    duration_seconds: float
    error: str = ""


class ClaudeRunner(Protocol):
    """Menjalankan satu prompt di direktori kerja `job_dir`."""

    def run(self, job_dir: Path, prompt: str, timeout_seconds: int) -> RunResult: ...


def cli_available(cli_path: str = CLAUDE_CLI_PATH) -> bool:
    return shutil.which(cli_path) is not None or Path(cli_path).exists()


class CliClaudeRunner:
    """Implementasi nyata: `claude -p <prompt>` dengan cwd = direktori job.

    Flag yang dipakai sengaja minimal — makin banyak flag, makin rapuh terhadap
    perubahan versi CLI:
      -p                      headless (print & exit)
      --output-format json    hasil terstruktur untuk log
      --permission-mode acceptEdits   boleh menulis file TANPA prompt interaktif
      --add-dir <job_dir>     batasi akses tulis ke direktori job

    Catatan: batas sesungguhnya bukan flag ini, melainkan bahwa aplikasi hanya
    membaca file DARI `job_dir` dan tak pernah mempromosikan apa pun tanpa gate.
    """

    def __init__(self, cli_path: str = CLAUDE_CLI_PATH, extra_dirs: tuple[str, ...] = ()) -> None:
        self._cli = cli_path
        self._extra_dirs = extra_dirs

    def run(
        self, job_dir: Path, prompt: str, timeout_seconds: int = CLAUDE_TIMEOUT_SECONDS
    ) -> RunResult:
        if not cli_available(self._cli):
            return RunResult(
                ok=False,
                stdout="",
                stderr="",
                exit_code=None,
                timed_out=False,
                duration_seconds=0.0,
                error=(
                    f"Claude Code CLI tak ditemukan ({self._cli!r}). Pasang CLI atau set "
                    "CLAUDE_CLI_PATH; loop M3/M4 tetap jalan tanpa integrasi ini."
                ),
            )

        cmd = [
            self._cli,
            "-p",
            prompt,
            "--output-format",
            "json",
            "--permission-mode",
            "acceptEdits",
            "--add-dir",
            str(job_dir),
        ]
        for d in self._extra_dirs:
            cmd += ["--add-dir", d]

        # Simpan argv apa adanya: waktu artifact-nya aneh, pertanyaan pertama selalu
        # "dipanggil dengan flag apa" — dan menebaknya belakangan mahal.
        (job_dir / "command.log").write_text(
            "\n".join(cmd[:2] + ["<prompt di prompt.md>"] + cmd[3:]), encoding="utf-8"
        )

        start = time.monotonic()
        try:
            proc = subprocess.Popen(
                cmd,
                cwd=job_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL,
                text=True,
                encoding="utf-8",
                errors="replace",
                **_group_kwargs(),
            )
        except OSError as e:
            return RunResult(
                ok=False,
                stdout="",
                stderr="",
                exit_code=None,
                timed_out=False,
                duration_seconds=time.monotonic() - start,
                error=f"gagal menjalankan Claude Code: {e}",
            )

        timed_out = False
        try:
            stdout, stderr = proc.communicate(timeout=timeout_seconds)
        except subprocess.TimeoutExpired:
            timed_out = True
            _kill_tree(proc)
            stdout, stderr = proc.communicate()

        duration = time.monotonic() - start
        exit_code = proc.returncode
        error = ""
        if timed_out:
            error = f"Claude Code melewati batas {timeout_seconds}s dan dihentikan"
        elif exit_code != 0:
            error = f"Claude Code keluar dengan kode {exit_code}"

        return RunResult(
            ok=(not timed_out) and exit_code == 0,
            stdout=stdout or "",
            stderr=stderr or "",
            exit_code=exit_code,
            timed_out=timed_out,
            duration_seconds=duration,
            error=error,
        )


def _group_kwargs() -> dict[str, object]:
    if _IS_WINDOWS:
        return {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
    return {"start_new_session": True}


def _kill_tree(proc: subprocess.Popen) -> None:
    """Sama seperti executor M1: timeout harus membunuh SELURUH pohon proses."""
    if _IS_WINDOWS:
        try:
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True, check=False
            )
        except OSError:
            pass
        try:
            proc.kill()
        except OSError:
            pass
        return
    try:
        os.killpg(os.getpgid(proc.pid), 9)
    except (ProcessLookupError, PermissionError, OSError):
        try:
            proc.kill()
        except OSError:
            pass
