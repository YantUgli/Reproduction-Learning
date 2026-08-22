"""Skema data domain-agnostic (PRD §9).

Kontrak lintas-milestone. Ubah HANYA lewat Log keputusan di CLAUDE.md.

Catatan invariant:
- Skema ini sengaja *tidak tahu* domainnya apa. Tidak boleh ada kolom seperti
  `http_method`. Kekhususan domain hidup di `grader_type` + isi `data/`.
- Enum disimpan sebagai **string biasa** (kolom TEXT), bukan tipe enum DB.
  Kelas Enum di bawah dipakai untuk validasi di boundary (skema request/response),
  bukan untuk memaksa tipe kolom — supaya mudah di-diff & di-migrasi manual.
"""

from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    return datetime.now(UTC)


# --------------------------------------------------------------------------- #
# Enum nilai (str) — dipakai untuk validasi di boundary, bukan tipe kolom DB.
# --------------------------------------------------------------------------- #
class DomainStatus(StrEnum):
    draft = "draft"
    active = "active"
    archived = "archived"


class SourceType(StrEnum):
    cs2023_ku = "cs2023_ku"
    textbook_toc = "textbook_toc"
    official_docs = "official_docs"


class GraderType(StrEnum):
    unit_test = "unit_test"
    structural = "structural"
    value_assert = "value_assert"
    metric_threshold = "metric_threshold"
    dom_behavior = "dom_behavior"


class EdgeType(StrEnum):
    hard = "hard"  # hanya `hard` yang mengikat urutan
    soft = "soft"


class ProbeType(StrEnum):
    predict_output = "predict_output"
    spot_bug = "spot_bug"
    trace = "trace"


class AttemptMode(StrEnum):
    placement = "placement"
    acquisition = "acquisition"
    verification = "verification"
    review = "review"


class AttemptResult(StrEnum):
    passed = "pass"
    failed = "fail"


class HypothesisSource(StrEnum):
    codebase = "codebase"
    research = "research"


class HypothesisStatus(StrEnum):
    unverified = "unverified"
    confirmed_by_attempt = "confirmed_by_attempt"
    refuted_by_attempt = "refuted_by_attempt"


class ScheduleStatus(StrEnum):
    locked = "locked"
    available = "available"
    acquired = "acquired"
    mastered = "mastered"
    lapsed = "lapsed"


# --------------------------------------------------------------------------- #
# Tabel (PRD §9)
# --------------------------------------------------------------------------- #
class Domain(SQLModel, table=True):
    id: str = Field(primary_key=True)
    name: str
    status: str = Field(default=DomainStatus.draft.value)


class SourceRef(SQLModel, table=True):
    id: str = Field(primary_key=True)
    # type ∈ {cs2023_ku, textbook_toc, official_docs}
    type: str
    citation: str
    url_or_locator: str


class Node(SQLModel, table=True):
    id: str = Field(primary_key=True)
    domain_id: str = Field(foreign_key="domain.id")
    concept: str
    description: str = ""
    # grader_type ∈ {unit_test, structural, value_assert, metric_threshold, dom_behavior}
    grader_type: str
    # daftar id SourceRef (bukti otoritatif) — disimpan sebagai JSON list.
    source_refs: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    estimated_minutes: int = 0
    timebox_seconds: int = 0
    # status_default: status awal node saat masuk jadwal.
    status_default: str = Field(default=ScheduleStatus.locked.value)


class Edge(SQLModel, table=True):
    # PK surrogate; pasangan (from, to) unik secara logis tapi tak dipaksa di v1.
    id: int | None = Field(default=None, primary_key=True)
    from_node_id: str = Field(foreign_key="node.id")
    to_node_id: str = Field(foreign_key="node.id")
    # type ∈ {hard, soft} — hanya `hard` yang mengikat urutan.
    type: str
    source_ref_id: str | None = Field(default=None, foreign_key="sourceref.id")
    note: str = ""


class ChallengeInstance(SQLModel, table=True):
    id: str = Field(primary_key=True)
    node_id: str = Field(foreign_key="node.id")
    variant_label: str
    prompt: str
    starter_code: str = ""
    signature_contract: str = ""
    hidden_test_path: str
    # scaffold_level: L3..L0 (disimpan sebagai string mis. "L2").
    scaffold_level: str


class ComprehensionProbe(SQLModel, table=True):
    id: str = Field(primary_key=True)
    node_id: str = Field(foreign_key="node.id")
    # type ∈ {predict_output, spot_bug, trace}
    type: str
    question: str
    # options JSON; jawaban benar pasti (deterministik).
    options: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    correct_answer: str


class Attempt(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    node_id: str = Field(foreign_key="node.id")
    instance_id: str | None = Field(default=None, foreign_key="challengeinstance.id")
    # Sesi pemilik attempt (M4). Wajib untuk placement: urutan attempt dalam SATU
    # sesi placement-lah yang menentukan di mana batas fail→pass ditemukan.
    session_id: int | None = Field(default=None, foreign_key="session.id")
    timestamp: datetime = Field(default_factory=_utcnow)
    # mode ∈ {placement, acquisition, verification, review}
    mode: str
    scaffold_level: str = ""
    duration_seconds: int = 0
    submitted_code: str = ""
    # result ∈ {pass, fail} — HANYA eksekusi kode yang boleh mengisi ini (PRD §2).
    result: str | None = None
    test_output: str = ""
    probe_result: str | None = None


class SkillHypothesis(SQLModel, table=True):
    # Dari Claude Code — TIDAK PERNAH jadi verdict; wajib diverifikasi Attempt.
    id: int | None = Field(default=None, primary_key=True)
    node_id: str = Field(foreign_key="node.id")
    # source ∈ {codebase, research}
    source: str
    confidence: float = 0.0
    rationale: str = ""
    evidence_locator: str = ""
    created_at: datetime = Field(default_factory=_utcnow)
    # status ∈ {unverified, confirmed_by_attempt, refuted_by_attempt}
    status: str = Field(default=HypothesisStatus.unverified.value)


class ScheduleItem(SQLModel, table=True):
    # Satu baris jadwal per node (PK = node_id).
    # Yang dijadwalkan adalah REPRODUKSI node, bukan kartu untuk dikenali (PRD §7.5).
    node_id: str = Field(primary_key=True, foreign_key="node.id")
    fsrs_stability: float | None = None
    fsrs_difficulty: float | None = None
    due_at: datetime | None = None
    review_count: int = 0
    consecutive_success: int = 0
    # status ∈ {locked, available, acquired, mastered, lapsed}
    status: str = Field(default=ScheduleStatus.locked.value)
    # --- Sisa state kartu FSRS (M4) ---
    # py-fsrs butuh state+step+last_review untuk melanjutkan kartu, bukan cuma
    # stability/difficulty/due. Disimpan supaya kartu bisa dipulihkan utuh dari DB.
    # fsrs_state ∈ {Learning, Review, Relearning} (nama State py-fsrs).
    fsrs_state: str | None = None
    fsrs_step: int | None = None
    last_review_at: datetime | None = None


class Session(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    started_at: datetime = Field(default_factory=_utcnow)
    ended_at: datetime | None = None
    # mode ∈ {placement, acquisition, verification, review}
    mode: str
    # INVARIANT (PRD §2): untuk mode `verification`, ai_available WAJIB False.
    # Bukan sekadar flag — ini representasi "mastery hanya dibuktikan tanpa AI".
    ai_available: bool = False
