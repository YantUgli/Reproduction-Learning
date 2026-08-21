"""Kontrak grader (M3).

Grader menerjemahkan `submitted_code` + sebuah `ChallengeInstance` menjadi verdict
pass/fail — TETAPI eksekusi sebenarnya selalu lewat `Executor` (M1). Grader hanya
merakit file & memaknai hasil; ia tak pernah mengeksekusi kode sendiri. Ini menjaga
invariant §2: hanya eksekusi kode (bukan AI, bukan heuristik teks) yang memutuskan.
"""

from dataclasses import dataclass
from typing import Protocol

from app.models import ChallengeInstance


@dataclass
class GradeResult:
    passed: bool
    test_output: str  # stdout+stderr runner, ditampilkan ke user (cermin — §7.6)
    timed_out: bool
    duration_seconds: float


class Grader(Protocol):
    def grade(self, instance: ChallengeInstance, submitted_code: str) -> GradeResult: ...
