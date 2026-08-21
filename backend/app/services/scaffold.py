"""Scaffold: pilih instance & rakit tampilan per level untuk satu node (§6 PRD).

Alur pemudaran scaffold (L3 → L0):
  L3  worked example (reference_solution beranotasi) + penjelasan pendek
  L2  faded reproduction: starter_code (kerangka, bagian inti kosong)
  L1  signature + spesifikasi saja
  L0  VERIFIKASI: instance VARIAN BERBEDA, editor kosong, timebox jalan

INVARIANT (§6 3d): L0 memakai instance BERBEDA dari worked example → lolos = transfer,
bukan hafalan contoh. Kalau node hanya punya 1 varian, L0 terpaksa memakai yang sama
(node semacam ini seharusnya ditolak M2 karena butuh ≥2 varian).
"""

from dataclasses import dataclass

from sqlmodel import Session, select

from app.graders.unit_test import reference_solution_path
from app.models import ChallengeInstance, Node

LEVELS = ["L3", "L2", "L1", "L0"]


@dataclass
class LevelView:
    level: str
    kind: str  # worked_example | faded | signature | verify
    title: str
    prompt: str
    code: str  # worked example / starter / kosong tergantung level
    signature_contract: str
    instance_id: str
    editable: bool
    show_timebox: bool
    timebox_seconds: int


def _instances(session: Session, node_id: str) -> list[ChallengeInstance]:
    rows = session.exec(
        select(ChallengeInstance).where(ChallengeInstance.node_id == node_id)
    ).all()
    return sorted(rows, key=lambda i: i.variant_label)


def teaching_instance(session: Session, node_id: str) -> ChallengeInstance:
    """Instance untuk L3–L1 (varian pertama, mis. variant_a)."""
    rows = _instances(session, node_id)
    if not rows:
        raise ValueError(f"node {node_id!r} tak punya instance")
    return rows[0]


def verification_instance(session: Session, node_id: str) -> ChallengeInstance:
    """Instance untuk L0 — VARIAN BERBEDA dari teaching bila tersedia (transfer)."""
    rows = _instances(session, node_id)
    if not rows:
        raise ValueError(f"node {node_id!r} tak punya instance")
    teaching = rows[0]
    for inst in rows[1:]:
        if inst.variant_label != teaching.variant_label:
            return inst
    return teaching  # fallback: hanya 1 varian


def build_level_view(session: Session, node: Node, level: str) -> LevelView:
    if level not in LEVELS:
        raise ValueError(f"level tak dikenal: {level!r} (harus salah satu {LEVELS})")

    teaching = teaching_instance(session, node.id)

    if level == "L3":
        ref_path = reference_solution_path(teaching)
        worked = ref_path.read_text(encoding="utf-8") if ref_path.exists() else ""
        return LevelView(
            level=level,
            kind="worked_example",
            title="L3 · Contoh dikerjakan",
            prompt=teaching.prompt,
            code=worked,
            signature_contract=teaching.signature_contract,
            instance_id=teaching.id,
            editable=False,
            show_timebox=False,
            timebox_seconds=node.timebox_seconds,
        )

    if level == "L2":
        return LevelView(
            level=level,
            kind="faded",
            title="L2 · Reproduksi dengan kerangka",
            prompt=teaching.prompt,
            code=teaching.starter_code,
            signature_contract=teaching.signature_contract,
            instance_id=teaching.id,
            editable=True,
            show_timebox=False,
            timebox_seconds=node.timebox_seconds,
        )

    if level == "L1":
        return LevelView(
            level=level,
            kind="signature",
            title="L1 · Hanya signature + spesifikasi",
            prompt=teaching.prompt,
            code="",
            signature_contract=teaching.signature_contract,
            instance_id=teaching.id,
            editable=True,
            show_timebox=False,
            timebox_seconds=node.timebox_seconds,
        )

    # L0 — verifikasi pada varian berbeda, timebox jalan.
    verify = verification_instance(session, node.id)
    return LevelView(
        level=level,
        kind="verify",
        title="L0 · Verifikasi (tanpa AI, timebox jalan)",
        prompt=verify.prompt,
        code="",
        signature_contract=verify.signature_contract,
        instance_id=verify.id,
        editable=True,
        show_timebox=True,
        timebox_seconds=node.timebox_seconds,
    )
