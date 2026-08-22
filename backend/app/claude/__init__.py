"""Integrasi Claude Code (M5) — async lewat file artifact, di belakang gate.

Semua di paket ini adalah AKSELERATOR, bukan fondasi: matikan
`CLAUDE_INTEGRATION_ENABLED` dan loop M3/M4 harus tetap jalan penuh (RISK-3).

Batas yang tak boleh dilanggar (PRD §10 / CLAUDE.md §1):
Claude Code tak pernah menetapkan edge final, tak pernah menyatakan mastery, tak
pernah menilai teks bebas. Ia menulis ke `artifacts/`; yang memindahkannya ke sistem
hanya `review_queue.approve` setelah skema + test + Isyah.
"""

from app.claude.artifacts import Job, JobStatus, Role
from app.claude.contracts import ArtifactError
from app.claude.jobs import JobError, execute_job, trigger_r2, trigger_r3, trigger_r4
from app.claude.review_queue import PromotionError, approve, reject
from app.claude.runner import ClaudeRunner, CliClaudeRunner, RunResult, cli_available

__all__ = [
    "ArtifactError",
    "ClaudeRunner",
    "CliClaudeRunner",
    "Job",
    "JobError",
    "JobStatus",
    "PromotionError",
    "Role",
    "RunResult",
    "approve",
    "cli_available",
    "execute_job",
    "reject",
    "trigger_r2",
    "trigger_r3",
    "trigger_r4",
]
