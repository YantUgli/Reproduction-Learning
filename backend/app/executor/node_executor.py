"""Executor kedua: Node + vitest + jsdom, untuk domain React (M6).

Ini validasi arsitektur M1: **interface `Executor` menyembunyikan bahasa runtime.**
Kontraknya identik (`files → pass/fail`); yang berbeda cuma proses yang dijalankan —
`vitest` di `runtime/react/`, bukan `pytest` di venv. Tak ada satu pun pemanggil
(grader, loop, scheduler) yang perlu tahu bedanya.

Kenapa direktori kerjanya di BAWAH `runtime/react/` dan bukan `tempfile` sistem:
resolusi `node_modules` di Node menaik lewat direktori induk. Tempdir di `%TEMP%`
tak akan menemukan react/vitest, dan menyalin `node_modules` per grading (~130 paket)
absurd. Jadi setiap grading dapat subfolder sendiri di `runtime/react/.work/` yang
dihapus setelah selesai — properti isolasinya sama (folder baru tiap panggilan),
hanya lokasinya yang berbeda.
"""

import shutil
import subprocess
import time
import uuid
from pathlib import Path

from app.config import REACT_RUNTIME_DIR
from app.executor.base import ExecutionResult
from app.executor.process import clean_env, group_kwargs, kill_process_group

_WORK_ROOT_NAME = ".work"


class NodeRuntimeMissingError(RuntimeError):
    """Runtime JS belum dipasang. Pesan WAJIB memberi tahu cara memperbaikinya."""


class NodeExecutor:
    """Implementasi `Executor` Protocol berbasis Node + vitest."""

    def __init__(self, runtime_dir: Path | None = None, node_path: str = "node") -> None:
        self._runtime = runtime_dir or REACT_RUNTIME_DIR
        self._node = node_path

    @property
    def vitest_entry(self) -> Path:
        return self._runtime / "node_modules" / "vitest" / "vitest.mjs"

    def available(self) -> bool:
        return self.vitest_entry.exists() and shutil.which(self._node) is not None

    def run(
        self,
        files: dict[str, str],
        test_entry: str,
        timeout_seconds: int,
    ) -> ExecutionResult:
        if not self.vitest_entry.exists():
            raise NodeRuntimeMissingError(
                f"runtime React belum dipasang di {self._runtime} — "
                "jalankan `cd runtime/react && npm install` sekali, lalu ulangi"
            )

        work_root = self._runtime / _WORK_ROOT_NAME
        work_root.mkdir(parents=True, exist_ok=True)
        work_dir = work_root / uuid.uuid4().hex
        work_dir.mkdir()

        try:
            for name, content in files.items():
                target = work_dir / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")

            # Path relatif terhadap runtime root: vitest memakai config di root itu
            # (jsdom + setup cleanup + transform JSX), jadi cwd-nya harus di sana.
            rel_entry = (work_dir / test_entry).relative_to(self._runtime).as_posix()
            cmd = [self._node, str(self.vitest_entry), "run", rel_entry]

            start = time.monotonic()
            proc = subprocess.Popen(
                cmd,
                cwd=self._runtime,
                env=clean_env({"CI": "1", "NO_COLOR": "1"}),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL,
                text=True,
                encoding="utf-8",
                errors="replace",
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
            return ExecutionResult(
                passed=(not timed_out) and exit_code == 0,
                stdout=_strip_work_paths(stdout or "", work_dir),
                stderr=_strip_work_paths(stderr or "", work_dir),
                duration_seconds=duration,
                timed_out=timed_out,
                exit_code=exit_code,
            )
        finally:
            shutil.rmtree(work_dir, ignore_errors=True)


def _strip_work_paths(text: str, work_dir: Path) -> str:
    """Buang path direktori kerja sementara dari output.

    Output test adalah cermin yang dibaca Bryant (§7.6). Nama folder acak seperti
    `.work/9f2c…/solution.test.jsx` tak berarti apa-apa baginya dan berubah tiap
    grading; yang tersisa cukup `solution.test.jsx`.
    """
    return text.replace(f"{work_dir.name}/", "").replace(f"{_WORK_ROOT_NAME}/", "")
