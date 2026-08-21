"""Registry grader: `grader_type` (§9) → instance Grader.

v1 hanya `unit_test` terdaftar (domain FastAPI). Grader lain (structural,
value_assert, metric_threshold, dom_behavior) ditambahkan di milestone domain
berikutnya TANPA menyentuh cara eksekusi (tetap lewat Executor M1).
"""

from app.graders.base import Grader
from app.graders.unit_test import UnitTestGrader

_REGISTRY: dict[str, Grader] = {
    "unit_test": UnitTestGrader(),
}


def get_grader(grader_type: str) -> Grader:
    grader = _REGISTRY.get(grader_type)
    if grader is None:
        raise ValueError(
            f"grader_type {grader_type!r} belum didukung (terdaftar: {sorted(_REGISTRY)})"
        )
    return grader
