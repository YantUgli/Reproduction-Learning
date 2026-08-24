"""Registry grader: `grader_type` (§9) → instance Grader.

**Ini satu-satunya tempat di seluruh aplikasi yang tahu ada lebih dari satu domain.**
Menambah domain = menambah satu baris di sini + satu grader di balik interface yang
sama (M6 §Keputusan). Loop, scaffold, scheduler, dan mastery tak pernah menanyakan
node ini domain apa — mereka cuma memanggil `get_grader(node.grader_type)`.

Belum terdaftar: `structural` & `metric_threshold`. `metric_threshold` sengaja
ditahan (§8 Guardrails: ia mengukur HASIL, bukan pemahaman); `structural` menunggu
node arsitektur yang benar-benar ada — grader tanpa node adalah kode yang tak pernah
dijalankan, dan itu justru yang paling mudah membusuk.
"""

from app.graders.base import Grader
from app.graders.dom_behavior import DomBehaviorGrader
from app.graders.unit_test import UnitTestGrader
from app.graders.value_assert import ValueAssertGrader

_REGISTRY: dict[str, Grader] = {
    "unit_test": UnitTestGrader(),  # FastAPI (M2/M3)
    "dom_behavior": DomBehaviorGrader(),  # React (M6)
    "value_assert": ValueAssertGrader(),  # ML komponen kecil (M6)
}


def get_grader(grader_type: str) -> Grader:
    grader = _REGISTRY.get(grader_type)
    if grader is None:
        raise ValueError(
            f"grader_type {grader_type!r} belum didukung (terdaftar: {sorted(_REGISTRY)})"
        )
    return grader
