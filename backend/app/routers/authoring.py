"""Router authoring (M5): trigger peran Claude Code + antrean review Isyah.

Dua sifat yang menentukan bentuk router ini:

1. **Async.** Trigger hanya MEMBUAT job (`pending`) lalu balas seketika; panggilan
   Claude Code jalan di `BackgroundTasks`. Tak ada `await` sinkron ke agent CLI di
   jalur request (M5 §Keputusan teknis).
2. **Bisa dimatikan.** `CLAUDE_INTEGRATION_ENABLED=0` → seluruh endpoint trigger
   balas 503, dan tak satu pun jalur M3/M4 berubah. Antrean tetap bisa dibaca &
   di-approve (artifact lama tak jadi sandera kill switch).
"""

import yaml
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from app.claude import jobs, review_queue
from app.claude.artifacts import Job, JobStatus, list_jobs, read_job
from app.claude.runner import cli_available
from app.config import CLAUDE_INTEGRATION_ENABLED, DATA_DIR
from app.db import engine, get_session
from app.models import Domain, HypothesisStatus
from app.services import edge_evidence, telemetry
from app.services.hypotheses import list_hypotheses

router = APIRouter(prefix="/authoring", tags=["authoring"])


class IntegrationStatus(BaseModel):
    enabled: bool
    cli_available: bool
    counts: dict[str, int]
    # Ringkas & jujur: apa yang TIDAK dilakukan integrasi ini.
    never_does: list[str]


class JobOut(BaseModel):
    id: str
    role: str
    status: str
    created_at: str
    updated_at: str
    prompt_version: str
    request: dict
    summary: dict
    gate: dict | None
    error: str
    attempts: int

    @classmethod
    def of(cls, job: Job) -> "JobOut":
        return cls(**{k: v for k, v in job.__dict__.items()})


class JobDetail(JobOut):
    prompt: str
    files: dict[str, str]
    # Isi file `data/` yang akan DIGANTI bila job ini di-approve (kosong = file baru).
    existing: dict[str, str]


class TriggerR3In(BaseModel):
    node_id: str
    attempt_id: int | None = None


class TriggerR4In(BaseModel):
    node_id: str
    variant_label: str | None = None


class TriggerNodeIn(BaseModel):
    """L4 — lahirkan node baru dari satu entri peta Library."""

    library_file: str
    slug: str
    domain_id: str
    concept: str
    source_ref_id: str
    prereq_node_id: str | None = None


class TriggerR2In(BaseModel):
    repo_path: str
    node_ids: list[str] | None = None


class RejectIn(BaseModel):
    reason: str = ""


class ApproveOut(BaseModel):
    job_id: str
    role: str
    node_id: str
    written_paths: list[str]
    db_effect: dict


class HypothesisOut(BaseModel):
    id: int
    node_id: str
    source: str
    confidence: float
    rationale: str
    evidence_locator: str
    status: str
    created_at: str


def _require_enabled() -> None:
    if not CLAUDE_INTEGRATION_ENABLED:
        raise HTTPException(
            status_code=503,
            detail=(
                "integrasi Claude Code dimatikan (CLAUDE_INTEGRATION_ENABLED=0). "
                "Loop akuisisi/review/placement tetap jalan penuh tanpa ini."
            ),
        )


def _run_job_in_background(job_id: str) -> None:
    """Jalankan job dengan session SENDIRI — session request sudah ditutup di sini."""
    with Session(engine) as session:
        try:
            jobs.execute_job(job_id, session)
        except Exception:  # noqa: BLE001 — job gagal tak boleh menjatuhkan server
            from app.claude.artifacts import set_status

            try:
                set_status(read_job(job_id), JobStatus.failed, error="job crash saat dijalankan")
            except OSError:
                pass


@router.get("/status", response_model=IntegrationStatus)
def integration_status() -> IntegrationStatus:
    counts: dict[str, int] = {}
    for job in list_jobs():
        counts[job.status] = counts.get(job.status, 0) + 1
    return IntegrationStatus(
        enabled=CLAUDE_INTEGRATION_ENABLED,
        cli_available=cli_available(),
        counts=counts,
        never_does=[
            "menetapkan edge prerequisite final",
            "menyatakan mastery / mengubah status node",
            "menilai teks bebas",
        ],
    )


@router.post("/r3", response_model=JobOut, status_code=202)
def trigger_r3(
    body: TriggerR3In, tasks: BackgroundTasks, session: Session = Depends(get_session)
) -> JobOut:
    _require_enabled()
    try:
        job = jobs.trigger_r3(session, node_id=body.node_id, attempt_id=body.attempt_id)
    except jobs.JobError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    tasks.add_task(_run_job_in_background, job.id)
    return JobOut.of(job)


@router.post("/r4", response_model=JobOut, status_code=202)
def trigger_r4(
    body: TriggerR4In, tasks: BackgroundTasks, session: Session = Depends(get_session)
) -> JobOut:
    _require_enabled()
    try:
        job = jobs.trigger_r4(session, node_id=body.node_id, variant_label=body.variant_label)
    except jobs.JobError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    tasks.add_task(_run_job_in_background, job.id)
    return JobOut.of(job)


@router.post("/node", response_model=JobOut, status_code=202)
def trigger_node(
    body: TriggerNodeIn, tasks: BackgroundTasks, session: Session = Depends(get_session)
) -> JobOut:
    """L4 — satu entri peta Library → satu node Forge, lewat R4 mode `node`.

    Tunduk pada kill switch yang sama (`_require_enabled`): L4 mati bersama integrasi
    lainnya, sesuai PRD §10 (akselerator, bukan fondasi).
    """
    _require_enabled()
    try:
        job = jobs.trigger_r4_node(
            session,
            library_file=body.library_file,
            slug=body.slug,
            domain_id=body.domain_id,
            concept=body.concept,
            source_ref_id=body.source_ref_id,
            prereq_node_id=body.prereq_node_id,
        )
    except jobs.JobError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    tasks.add_task(_run_job_in_background, job.id)
    return JobOut.of(job)


@router.post("/r2", response_model=JobOut, status_code=202)
def trigger_r2(
    body: TriggerR2In, tasks: BackgroundTasks, session: Session = Depends(get_session)
) -> JobOut:
    _require_enabled()
    try:
        job = jobs.trigger_r2(session, repo_path=body.repo_path, node_ids=body.node_ids)
    except jobs.JobError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    tasks.add_task(_run_job_in_background, job.id)
    return JobOut.of(job)


@router.get("/jobs", response_model=list[JobOut])
def list_authoring_jobs(role: str | None = None, status: str | None = None) -> list[JobOut]:
    return [JobOut.of(j) for j in list_jobs(role=role, status=status)]


@router.get("/jobs/{job_id}", response_model=JobDetail)
def get_job(job_id: str, session: Session = Depends(get_session)) -> JobDetail:
    try:
        job = read_job(job_id)
    except (FileNotFoundError, ValueError) as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    prompt_path = job.dir / "prompt.md"
    return JobDetail(
        **JobOut.of(job).model_dump(),
        prompt=prompt_path.read_text(encoding="utf-8") if prompt_path.exists() else "",
        files=jobs.job_artifact_files(job),
        existing=_existing_targets(session, job),
    )


@router.post("/jobs/{job_id}/approve", response_model=ApproveOut)
def approve_job(job_id: str, session: Session = Depends(get_session)) -> ApproveOut:
    try:
        promotion = review_queue.approve(session, job_id)
    except (FileNotFoundError, ValueError) as e:
        # PromotionError & ArtifactError keduanya turunan ValueError.
        raise HTTPException(status_code=400, detail=str(e)) from e
    return ApproveOut(
        job_id=promotion.job_id,
        role=promotion.role,
        node_id=promotion.node_id,
        written_paths=promotion.written_paths,
        db_effect=promotion.db_effect,
    )


@router.post("/jobs/{job_id}/reject", response_model=JobOut)
def reject_job(job_id: str, body: RejectIn) -> JobOut:
    try:
        job = review_queue.reject(job_id, body.reason)
    except (FileNotFoundError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return JobOut.of(job)


@router.get("/hypotheses", response_model=list[HypothesisOut])
def get_hypotheses(
    node_id: str | None = None, session: Session = Depends(get_session)
) -> list[HypothesisOut]:
    """Hipotesis R2 + statusnya. `unverified` sampai eksekusi kode bicara."""
    return [
        HypothesisOut(
            id=h.id,
            node_id=h.node_id,
            source=h.source,
            confidence=h.confidence,
            rationale=h.rationale,
            evidence_locator=h.evidence_locator,
            status=h.status,
            created_at=h.created_at.isoformat(),
        )
        for h in list_hypotheses(session, node_id=node_id)
    ]


def _existing_targets(session: Session, job: Job) -> dict[str, str]:
    """Isi file `data/` yang akan tertimpa/ditambahi — bahan diff untuk Isyah."""
    node_id = job.request.get("node_id")
    if not node_id:
        if job.role == "r2":
            unverified = [
                h for h in list_hypotheses(session) if h.status == HypothesisStatus.unverified.value
            ]
            return {"(hipotesis unverified saat ini)": str(len(unverified))}
        return {}
    try:
        target_dir = review_queue.node_dir(session, node_id)
    except review_queue.PromotionError:
        return {}

    out: dict[str, str] = {}
    if job.role == "r3":
        existing = target_dir / "explanation.md"
        if existing.exists():
            out["explanation.md"] = existing.read_text(encoding="utf-8")
    elif job.role == "r4":
        label = job.request.get("variant_label", "")
        variant_dir = target_dir / "instances" / label
        if variant_dir.is_dir():
            for f in sorted(variant_dir.iterdir()):
                if f.is_file():
                    out[f"instances/{label}/{f.name}"] = f.read_text(encoding="utf-8")
    return out


# --------------------------------------------------------------------------- #
# Meja AUDIT (M7 langkah 8)
#
# Sampai M6 halaman `/authoring` adalah antrean BLOKIR: tak ada artifact yang masuk
# sistem sebelum Isyah menekan approve. Sejak §7 2026-08-31 gerbang mesin yang
# memutuskan, dan peran manusia pindah ke belakang: melihat node yang sudah dipakai
# Bryant dan menandai mana yang ternyata tak layak.
#
# Yang ditampilkan di sini sengaja BUKAN dashboard atau graf (§8 menolak DAG
# explorer): ia daftar bertanda, dengan alasan dan angkanya, supaya keputusan
# pensiun bisa diambil dalam hitungan detik.
# --------------------------------------------------------------------------- #
class AuditSignal(BaseModel):
    node_id: str
    kind: str
    detail: str
    samples: int


class AuditEdge(BaseModel):
    from_node_id: str
    to_node_id: str
    kind: str
    reason: str


class AuditOut(BaseModel):
    # Seberapa banyak kurikulum yang PUNYA data untuk dinilai. Tanpa angka ini,
    # "tak ada temuan" mudah dibaca sebagai "semuanya sehat", padahal dengan satu
    # pelajar ia hampir selalu berarti "belum ada datanya".
    coverage: dict
    node_signals: list[AuditSignal]
    edge_findings: list[AuditEdge]
    # Satu-satunya hal di M7 yang memang menunggu manusia: arah kurikulum per domain.
    # Tak ada oracle untuk "apakah ini kurikulum yang benar" — di sistem mana pun.
    domains_without_destination: list[str]


@router.get("/audit", response_model=AuditOut)
def audit(session: Session = Depends(get_session)) -> AuditOut:
    edges = edge_evidence.corroboration(session) + edge_evidence.predictive_evidence(session)
    return AuditOut(
        coverage=telemetry.coverage(session),
        node_signals=[
            AuditSignal(node_id=s.node_id, kind=s.kind, detail=s.detail, samples=s.samples)
            for s in telemetry.signals(session)
        ],
        edge_findings=[
            AuditEdge(
                from_node_id=f.from_node_id,
                to_node_id=f.to_node_id,
                kind=f.kind,
                reason=f.reason,
            )
            for f in edges
            if f.kind != "corroborated"
        ],
        domains_without_destination=_domains_without_destination(session),
    )


def _domains_without_destination(session: Session) -> list[str]:
    """Domain yang belum punya `destination` di `domain.yaml`.

    `destination` sengaja TIDAK diisi otomatis: ia adalah keputusan "mau jadi apa",
    dan itu justru satu-satunya bagian yang tak bisa diserahkan ke mesin (§7
    2026-08-31). Ditetapkan sekali per domain, bukan per node.
    """
    out = []
    for domain in session.exec(select(Domain)).all():
        meta_path = DATA_DIR / "domains" / domain.id / "domain.yaml"
        if not meta_path.exists():
            continue
        meta = yaml.safe_load(meta_path.read_text(encoding="utf-8")) or {}
        if not str(meta.get("destination", "")).strip():
            out.append(domain.id)
    return sorted(out)
