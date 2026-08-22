"""SkillHypothesis — hipotesis dari Claude Code (R2) dan nasibnya (M5 langkah 6).

INVARIANT (PRD §2/§10, RISK-4): hipotesis **tidak pernah** menjadi verdict.

- Ia masuk sistem berstatus `unverified`, apa pun `confidence`-nya.
- Yang boleh mengubah statusnya HANYA eksekusi kode: attempt `reproduce-without-AI`
  (verification / review / placement) pada node yang sama.
- Ia **tidak** menyentuh `ScheduleItem.status`, tidak memicu `acquired`, tidak
  membuka node terkunci. Fungsi di modul ini sengaja tak punya akses ke sana:
  satu-satunya tulisan yang dilakukannya adalah kolom `status` di baris hipotesis.

Kalau suatu saat muncul tekanan "confidence-nya 0.95, anggap saja dikuasai" —
jawabannya tetap tidak. Codebase Bryant mungkin ditulis dengan bantuan AI, jadi ia
bukti *pengenalan*, bukan bukti *produksi*.
"""

from sqlmodel import Session, select

from app.models import Attempt, HypothesisStatus, SkillHypothesis

#: Mode attempt yang dihitung sebagai bukti produksi. `acquisition` (L3–L1, scaffold
#: masih di layar) TIDAK termasuk — sama seperti KPI reproduce-without-AI (M4).
EVIDENCE_MODES = ("verification", "review", "placement")


def unverified_for_node(session: Session, node_id: str) -> list[SkillHypothesis]:
    return list(
        session.exec(
            select(SkillHypothesis).where(
                SkillHypothesis.node_id == node_id,
                SkillHypothesis.status == HypothesisStatus.unverified.value,
            )
        ).all()
    )


def apply_attempt(session: Session, attempt: Attempt) -> int:
    """Konfirmasi/bantah hipotesis node ini berdasarkan SATU attempt eksekusi.

    → jumlah hipotesis yang berubah status. Tak ada efek lain, di mana pun.
    """
    if attempt.mode not in EVIDENCE_MODES or attempt.result not in ("pass", "fail"):
        return 0

    new_status = (
        HypothesisStatus.confirmed_by_attempt.value
        if attempt.result == "pass"
        else HypothesisStatus.refuted_by_attempt.value
    )
    changed = 0
    for hypothesis in unverified_for_node(session, attempt.node_id):
        hypothesis.status = new_status
        session.add(hypothesis)
        changed += 1
    if changed:
        session.commit()
    return changed


def list_hypotheses(session: Session, *, node_id: str | None = None) -> list[SkillHypothesis]:
    stmt = select(SkillHypothesis)
    if node_id:
        stmt = stmt.where(SkillHypothesis.node_id == node_id)
    rows = list(session.exec(stmt).all())
    rows.sort(key=lambda h: (h.node_id, -h.confidence))
    return rows
