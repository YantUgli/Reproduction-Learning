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

from app.config import MIN_VARIANTS_FOR_REVIEW
from app.graders.unit_test import reference_solution_path
from app.models import Attempt, ChallengeInstance, ComprehensionProbe, Node

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


@dataclass
class ReviewInstance:
    instance: ChallengeInstance
    previous_instance_id: str | None
    # True bila varian node ini terlalu sedikit sehingga rotasi cepat berulang —
    # sinyal untuk MENAIKKAN KE AUTHORING, bukan untuk memblokir review.
    needs_more_variants: bool


def review_instance(session: Session, node_id: str) -> ReviewInstance:
    """Instance untuk sesi review — WAJIB berbeda dari yang dipakai attempt terakhir.

    Mengulang instance yang sama mengubah reproduksi jadi hafalan jawaban (M4 §Hal yang
    harus diperhatikan). Rotasi mengikuti urutan varian dan melompati yang barusan
    dipakai. Kalau node cuma punya satu varian, tak ada pilihan lain selain memakainya
    lagi — dan itu ditandai lewat `needs_more_variants`.
    """
    rows = _instances(session, node_id)
    if not rows:
        raise ValueError(f"node {node_id!r} tak punya instance")

    last = session.exec(
        select(Attempt)
        .where(Attempt.node_id == node_id, Attempt.instance_id.is_not(None))
        .order_by(Attempt.id.desc())
    ).first()
    previous_id = last.instance_id if last else None

    chosen = rows[0]
    if previous_id is not None:
        ids = [i.id for i in rows]
        if previous_id in ids:
            chosen = rows[(ids.index(previous_id) + 1) % len(rows)]

    return ReviewInstance(
        instance=chosen,
        previous_instance_id=previous_id,
        needs_more_variants=len(rows) < MIN_VARIANTS_FOR_REVIEW,
    )


def pick_probe(session: Session, node_id: str) -> ComprehensionProbe | None:
    """Probe untuk satu attempt — BERGILIR bila node punya lebih dari satu.

    Sebelum M5, kedua pemanggil memakai `.first()`, jadi probe kedua dan seterusnya
    tak pernah tampil (probe hasil R4 akan jadi konten mati). Rotasi memakai jumlah
    attempt node sebagai indeks: deterministik (bisa di-test), tapi tak menyodorkan
    pertanyaan yang sama tiap kali node muncul lagi di review.
    """
    probes = sorted(
        session.exec(
            select(ComprehensionProbe).where(ComprehensionProbe.node_id == node_id)
        ).all(),
        key=lambda p: p.id,
    )
    if not probes:
        return None
    attempts = len(session.exec(select(Attempt).where(Attempt.node_id == node_id)).all())
    return probes[attempts % len(probes)]


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
