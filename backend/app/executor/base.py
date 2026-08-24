"""Kontrak eksekusi test — BEKUKAN (M1).

Ini satu-satunya titik yang tahu *bagaimana* kode dieksekusi. Grader (M3) dan
harness CLI sama-sama memanggil `Executor.run(...)`. Backend eksekusi (subprocess
sekarang; Docker/Pyodide nanti) bisa ditukar tanpa mengubah pemanggil.
"""

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass
class ExecutionResult:
    passed: bool  # True hanya jika seluruh test lolos & exit code 0
    stdout: str
    stderr: str
    duration_seconds: float
    timed_out: bool
    exit_code: int | None


# runtime_checkable supaya kontraknya bisa DIUJI (`isinstance`), bukan cuma
# dipercaya — sejak M6 ada dua implementasi berbeda bahasa di baliknya.
@runtime_checkable
class Executor(Protocol):
    def run(
        self,
        # nama_file -> isi, mis. {"solution.py": ..., "test_solution.py": ...}
        files: dict[str, str],
        test_entry: str,  # nama file test yang dijalankan pytest
        timeout_seconds: int,
    ) -> ExecutionResult: ...
