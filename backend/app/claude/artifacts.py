"""Konvensi direktori artifact + state job (M5 langkah 1).

Bentuk direktori (beku di sini):

    artifacts/<role>/<timestamp>-<rand>/
        job.json               # state job (ditulis APLIKASI, bukan Claude Code)
        prompt.md              # prompt terstruktur yang dikirim (audit trail)
        stdout.log / stderr.log
        <output Claude Code>   # nama file per peran, lihat contracts.py

KENAPA state job hidup di file, bukan tabel DB:
- Artifact-lah sumber kebenarannya (PRD §10: integrasi async lewat file). Menyalin
  statusnya ke DB berarti dua sumber yang bisa berbeda.
- Isyah bisa membuka, mem-`grep`, dan menghapus job dengan file manager biasa.
- Loop inti (M3/M4) tak boleh punya ketergantungan skema pada M5: matikan integrasi
  → tak ada tabel yatim, tak ada migrasi.

`job_id` = "<role>-<stamp>" dan memetakan 1:1 ke `artifacts/<role>/<stamp>/`.
"""

import json
import re
import secrets
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path

from app.config import ARTIFACTS_DIR

_STAMP_RE = re.compile(r"^[0-9]{8}T[0-9]{6}-[0-9a-f]{6}$")


class Role(StrEnum):
    """Peran Claude Code (PRD §10). R1 tetap manual/offline di v1."""

    r2_hypotheses = "r2"
    r3_explanation = "r3"
    r4_challenge = "r4"


class JobStatus(StrEnum):
    pending = "pending"  # dibuat, belum dijalankan
    running = "running"  # Claude Code sedang dipanggil
    ready = "ready"  # artifact valid + lolos gate otomatis → MENUNGGU ISYAH
    failed = "failed"  # CLI gagal/timeout, atau artifact tak lolos skema/gate
    approved = "approved"  # Isyah approve → sudah dipromosikan ke sistem
    rejected = "rejected"  # Isyah tolak (atau ditolak otomatis)


#: Status yang boleh di-approve. Apa pun di luar ini TIDAK boleh masuk sistem.
REVIEWABLE = (JobStatus.ready,)


def _utcnow_iso() -> str:
    return datetime.now(UTC).isoformat()


@dataclass
class Job:
    """State satu permintaan ke Claude Code. Serialisasi ke `job.json`."""

    id: str
    role: str
    status: str
    created_at: str
    updated_at: str
    prompt_version: str = ""
    # Konteks permintaan (node_id, attempt_id, repo_path, ...) — apa adanya, untuk audit.
    request: dict = field(default_factory=dict)
    # Ringkasan hasil validasi kontrak (nama file yang diterima, jumlah item, dll).
    summary: dict = field(default_factory=dict)
    # Hasil gate otomatis R4 (test hijau di solusi referensi). None = tak berlaku.
    gate: dict | None = None
    # Alasan gagal/ditolak — WAJIB terisi saat failed/rejected supaya bisa ditindak.
    error: str = ""
    attempts: int = 0

    @property
    def dir(self) -> Path:
        return job_dir(self.id)

    def to_json(self) -> str:
        return json.dumps(self.__dict__, indent=2, ensure_ascii=False)


def job_dir(job_id: str) -> Path:
    """`artifacts/<role>/<stamp>/` dari job_id. Menolak id yang bisa keluar direktori."""
    role, _, stamp = job_id.partition("-")
    if role not in tuple(Role) or not _STAMP_RE.match(stamp):
        raise ValueError(f"job_id tak valid: {job_id!r}")
    return ARTIFACTS_DIR / role / stamp


def new_job(role: Role, request: dict, prompt_version: str = "") -> Job:
    """Buat direktori job baru + `job.json` berstatus `pending`."""
    stamp = f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%S')}-{secrets.token_hex(3)}"
    job = Job(
        id=f"{role.value}-{stamp}",
        role=role.value,
        status=JobStatus.pending.value,
        created_at=_utcnow_iso(),
        updated_at=_utcnow_iso(),
        prompt_version=prompt_version,
        request=request,
    )
    job.dir.mkdir(parents=True, exist_ok=True)
    save_job(job)
    return job


def save_job(job: Job) -> Job:
    job.updated_at = _utcnow_iso()
    (job.dir / "job.json").write_text(job.to_json(), encoding="utf-8")
    return job


def read_job(job_id: str) -> Job:
    path = job_dir(job_id) / "job.json"
    if not path.exists():
        raise FileNotFoundError(f"job tak ditemukan: {job_id}")
    return Job(**json.loads(path.read_text(encoding="utf-8")))


def set_status(job: Job, status: JobStatus, *, error: str = "") -> Job:
    job.status = status.value
    if error:
        job.error = error
    return save_job(job)


def list_jobs(*, role: str | None = None, status: str | None = None) -> list[Job]:
    """Semua job, terbaru dulu. Direktori rusak dilewati (bukan alasan 500)."""
    jobs: list[Job] = []
    if not ARTIFACTS_DIR.is_dir():
        return jobs
    roles = [role] if role else [r.value for r in Role]
    for r in roles:
        role_dir = ARTIFACTS_DIR / r
        if not role_dir.is_dir():
            continue
        for d in role_dir.iterdir():
            if not d.is_dir() or not (d / "job.json").exists():
                continue
            try:
                job = Job(**json.loads((d / "job.json").read_text(encoding="utf-8")))
            except (ValueError, TypeError):
                continue
            if status and job.status != status:
                continue
            jobs.append(job)
    jobs.sort(key=lambda j: j.created_at, reverse=True)
    return jobs
