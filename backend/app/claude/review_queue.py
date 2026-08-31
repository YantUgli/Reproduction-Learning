"""Antrean review Isyah + promosi ke sistem (M5 langkah 4).

INVARIANT (M5 §Expected result): **tidak ada artifact yang masuk sistem tanpa lolos
gate.** Gate berlapis:

    skema (contracts.py) → gate otomatis R4 (eksekusi test) → APPROVE ISYAH → promosi

Sebelum approve, artifact hanya ada sebagai file di `artifacts/` — tak satu baris pun
menyentuh `data/` atau DB. Fungsi promosi di bawah ini adalah SATU-SATUNYA jalur
masuk, dan semuanya menuntut `job.status == ready`.

Bentuk promosi per peran:
  R3 → `data/domains/<domain>/nodes/<node>/explanation.md` (+ worked_example.py)
       Materi ikut di-commit & di-diff seperti kode; disajikan just-in-time saat gagal.
  R4 → folder varian + probe di node yang bersangkutan, lalu node dimuat ulang ke DB
       (lewat node_loader — validasi M2 berlaku penuh, termasuk untuk output AI).
  R2 → baris `SkillHypothesis` berstatus `unverified`. Tidak pernah verdict.
"""

import shutil
from dataclasses import dataclass
from pathlib import Path

import yaml
from sqlmodel import Session, select

from app.claude import contracts
from app.claude.artifacts import REVIEWABLE, Job, JobStatus, Role, read_job, set_status
from app.config import DATA_DIR
from app.models import HypothesisSource, HypothesisStatus, Node, SkillHypothesis
from app.services.node_loader import assemble_node, load_domain_into_db

#: Berkas varian yang ditulis saat promosi. Ekstensi kode diambil dari artifact
#: (`.py` FastAPI/ML, `.jsx` React), bukan diasumsikan — versi M5 meng-hardcode `.py`
#: sehingga varian React akan mendarat dengan ekstensi yang salah dan node-nya jadi
#: tak sah (kebocoran yang sama dengan gate R4, ditutup di M7 langkah 1).
_PROMPT_FILE = "prompt.md"
_CODE_STEMS = ("starter_code", "reference_solution", "hidden_test")


class PromotionError(ValueError):
    """Promosi ditolak — pesan WAJIB menjelaskan apa yang harus diperbaiki."""


@dataclass
class Promotion:
    job_id: str
    role: str
    node_id: str
    # File `data/` yang berubah (relatif repo) — supaya Isyah bisa langsung `git diff`.
    written_paths: list[str]
    # Ringkasan efek di DB (mis. jumlah hipotesis yang masuk).
    db_effect: dict


def node_dir(session: Session, node_id: str) -> Path:
    node = session.get(Node, node_id)
    if node is None:
        raise PromotionError(f"node tak ditemukan: {node_id!r}")
    return DATA_DIR / "domains" / node.domain_id / "nodes" / node_id


def _require_reviewable(job: Job) -> None:
    if job.status not in tuple(s.value for s in REVIEWABLE):
        raise PromotionError(
            f"job {job.id} berstatus {job.status!r} — hanya {REVIEWABLE[0].value} yang boleh "
            "di-approve (artifact belum lolos skema/gate)"
        )


# --------------------------------------------------------------------------- #
# Approve / reject
# --------------------------------------------------------------------------- #
def promote(session: Session, job_id: str) -> Promotion:
    """Masukkan artifact ke sistem (`data/` + DB).

    Sejak M7 ini dipanggil OTOMATIS oleh `jobs.execute_job` begitu seluruh gerbang
    mesin lolos — bukan lagi oleh klik manusia. `approve()` tetap ada sebagai jalur
    manual untuk kasus yang perlu ditangani tangan; keduanya menjalankan pemeriksaan
    yang sama, jadi tak ada jalur masuk yang lebih longgar daripada yang lain.
    """
    job = read_job(job_id)
    _require_reviewable(job)

    if job.role == Role.r3_explanation.value:
        promotion = _promote_r3(session, job)
    elif job.role == Role.r4_challenge.value:
        promotion = _promote_r4(session, job)
    else:
        promotion = _promote_r2(session, job)

    job.summary = {**job.summary, "promotion": promotion.written_paths, **promotion.db_effect}
    set_status(job, JobStatus.approved)
    return promotion


#: Jalur manual. Namanya dipertahankan karena router & test M5 memakainya, dan
#: karena "approve" masih tepat untuk tindakan yang memang dilakukan manusia.
approve = promote


def reject(job_id: str, reason: str) -> Job:
    job = read_job(job_id)
    if job.status == JobStatus.approved.value:
        raise PromotionError("job sudah di-approve — tak bisa ditolak setelah dipromosikan")
    job.error = reason.strip() or "ditolak Isyah tanpa alasan tertulis"
    return set_status(job, JobStatus.rejected)


# --------------------------------------------------------------------------- #
# Promosi per peran
# --------------------------------------------------------------------------- #
def _promote_r3(session: Session, job: Job) -> Promotion:
    node_id = job.request["node_id"]
    artifact = contracts.load_explanation(job.dir, node_id)
    target_dir = node_dir(session, node_id)
    if not target_dir.is_dir():
        raise PromotionError(f"folder node tak ada: {target_dir}")

    body = artifact.explanation_md.rstrip()
    lines = [body, "", "## Sumber", ""]
    for c in artifact.citations:
        locator = f" — {c.locator}" if c.locator else ""
        lines.append(f"- `{c.source_ref_id}`{locator} · {c.claim}")
    lines += ["", f"<!-- artifact: {job.id} · prompt: {job.prompt_version} -->", ""]

    written: list[str] = []
    explanation_path = target_dir / "explanation.md"
    explanation_path.write_text("\n".join(lines), encoding="utf-8")
    written.append(_rel(explanation_path))

    if artifact.worked_example.strip():
        worked = target_dir / "worked_example.py"
        worked.write_text(artifact.worked_example, encoding="utf-8")
        written.append(_rel(worked))

    return Promotion(
        job_id=job.id, role=job.role, node_id=node_id, written_paths=written, db_effect={}
    )


def _promote_r4(session: Session, job: Job) -> Promotion:
    node_id = job.request["node_id"]
    artifact = contracts.load_challenge(job.dir, node_id)
    target_dir = node_dir(session, node_id)
    variant_dir = target_dir / "instances" / artifact.variant_label
    probe_path = target_dir / "probes" / f"{artifact.probe.id}.yaml"

    if variant_dir.exists():
        raise PromotionError(
            f"varian {artifact.variant_label!r} sudah ada di {node_id} — ganti label atau "
            "hapus varian lama lebih dulu"
        )
    if probe_path.exists():
        raise PromotionError(f"probe {artifact.probe.id!r} sudah ada di {node_id}")

    variant_dir.mkdir(parents=True)
    probe_path.parent.mkdir(parents=True, exist_ok=True)
    ext = artifact.file_ext
    isi = {
        _PROMPT_FILE: artifact.prompt_md,
        f"starter_code{ext}": artifact.starter_code,
        f"reference_solution{ext}": artifact.reference_solution,
        f"hidden_test{ext}": artifact.hidden_test,
    }
    if artifact.expected_json.strip():
        # Node ML membawa toleransi numeriknya di `expected.json` (M6) — tanpa ini
        # varian barunya tak bisa dinilai grader `value_assert`.
        isi["expected.json"] = artifact.expected_json
    written = [_rel(variant_dir / f) for f in isi] + [_rel(probe_path)]
    try:
        for nama, teks in isi.items():
            (variant_dir / nama).write_text(teks, encoding="utf-8")
        probe_path.write_text(
            yaml.dump(
                # mode="json": `type` adalah StrEnum, dan yaml tak bisa merepresentasikan
                # objek enum — file probe harus berisi string biasa seperti tulisan tangan.
                artifact.probe.model_dump(mode="json"),
                Dumper=_IndentedDumper,
                allow_unicode=True,
                sort_keys=False,
                width=200,
            ),
            encoding="utf-8",
        )
        # Validasi M2 berlaku PENUH untuk output AI: node harus tetap sah setelah
        # ditambahi varian ini, kalau tidak promosinya dibatalkan seutuhnya.
        assemble_node(target_dir)
        node = session.get(Node, node_id)
        load_domain_into_db(session, DATA_DIR / "domains" / node.domain_id, data_dir=DATA_DIR)
    except Exception as e:  # noqa: BLE001 — rollback file, lalu laporkan apa adanya
        shutil.rmtree(variant_dir, ignore_errors=True)
        probe_path.unlink(missing_ok=True)
        raise PromotionError(f"promosi dibatalkan, node akan menjadi tak sah: {e}") from e

    return Promotion(
        job_id=job.id,
        role=job.role,
        node_id=node_id,
        written_paths=written,
        db_effect={"variant_label": artifact.variant_label, "probe_id": artifact.probe.id},
    )


def _promote_r2(session: Session, job: Job) -> Promotion:
    artifact = contracts.load_hypotheses(job.dir)
    known = {n.id for n in session.exec(select(Node)).all()}
    contracts.check_nodes_known(artifact, known)

    inserted = 0
    for h in artifact.hypotheses:
        session.add(
            SkillHypothesis(
                node_id=h.node_id,
                source=HypothesisSource.codebase.value,
                confidence=h.confidence,
                rationale=h.rationale,
                evidence_locator=h.evidence_locator,
                # SELALU unverified. Artifact tak punya field status, dan kalaupun
                # punya, ia tak akan dipakai (§10 / RISK-4).
                status=HypothesisStatus.unverified.value,
            )
        )
        inserted += 1
    session.commit()

    return Promotion(
        job_id=job.id,
        role=job.role,
        node_id="",
        written_paths=[],
        db_effect={"hypotheses_inserted": inserted, "status": HypothesisStatus.unverified.value},
    )


class _IndentedDumper(yaml.SafeDumper):
    """List di-indent di bawah key-nya — supaya probe hasil AI ter-diff sama persis
    bentuknya dengan probe tulisan tangan."""

    def increase_indent(self, flow=False, indentless=False):
        return super().increase_indent(flow, False)


def _rel(path: Path) -> str:
    from app.config import REPO_ROOT

    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()
