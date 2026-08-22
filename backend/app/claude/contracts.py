"""Kontrak artifact Claude Code (M5 langkah 3) — skema KETAT per peran.

Prinsip (M5 §Keputusan teknis): **manusia me-review konten, bukan membetulkan
format.** Semua yang bisa dicek mesin dicek di sini, sebelum artifact menyentuh
antrean review. Output yang tak sesuai skema DITOLAK — tak pernah sampai ke Isyah.

Bentuk file per peran (sengaja file terpisah, bukan satu JSON raksasa: Isyah harus
bisa membuka artifact-nya langsung dan membacanya seperti kode):

    r3/  explanation.md      + citations.json
    r4/  variant/{prompt.md,starter_code.py,reference_solution.py,hidden_test.py}
         probe.yaml          + meta.json
    r2/  hypotheses.json

INVARIANT yang ditegakkan di sini:
- R3 wajib bersitasi ke `SourceRef` yang ADA di `data/sources.yaml` (§10: sitasi
  wajib bisa diverifikasi) dan wajib PENDEK (§8: bukan content library).
- R4 probe wajib deterministik (`correct_answer` ∈ `options`) — dipinjam dari
  `ProbeYaml` M2 supaya soal buatan AI dinilai skema yang sama dengan soal manusia.
- R2 tak punya field yang bisa dibaca sebagai verdict: hanya confidence + rationale
  + lokasi bukti. Status hipotesis TIDAK boleh datang dari artifact.
"""

import json
import re
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.config import EXPLANATION_MAX_CHARS
from app.services.node_schema import ProbeYaml

_VARIANT_RE = re.compile(r"^variant_[a-z0-9_]+$")
_SOLUTION_IMPORT_RE = re.compile(r"^\s*(from\s+solution\s+import|import\s+solution)", re.MULTILINE)


class ArtifactError(ValueError):
    """Artifact tak memenuhi kontrak. Pesan WAJIB bisa ditindaklanjuti."""


# --------------------------------------------------------------------------- #
# R3 — materi just-in-time
# --------------------------------------------------------------------------- #
class Citation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_ref_id: str
    locator: str = ""  # bagian/anchor spesifik di sumber (opsional tapi dianjurkan)
    claim: str  # klaim yang disitasi — supaya Isyah bisa mengecek, bukan menebak


class ExplanationArtifact(BaseModel):
    """`explanation.md` + `citations.json`."""

    model_config = ConfigDict(extra="forbid")

    node_id: str
    explanation_md: str
    worked_example: str = ""
    citations: list[Citation]

    @field_validator("explanation_md")
    @classmethod
    def _short_and_nonempty(cls, v: str) -> str:
        text = v.strip()
        if not text:
            raise ValueError("explanation.md kosong")
        if len(text) > EXPLANATION_MAX_CHARS:
            raise ValueError(
                f"explanation.md {len(text)} karakter, batas {EXPLANATION_MAX_CHARS} "
                "— materi harus just-in-time & pendek (§8 Guardrails), bukan bab"
            )
        return text

    @field_validator("citations")
    @classmethod
    def _at_least_one(cls, v: list[Citation]) -> list[Citation]:
        if not v:
            raise ValueError("materi tanpa sitasi ditolak (§10: sitasi wajib verifiable)")
        return v


# --------------------------------------------------------------------------- #
# R4 — generator soal
# --------------------------------------------------------------------------- #
class ChallengeArtifact(BaseModel):
    """Satu varian instance + satu probe, bentuknya SAMA dengan node folder M2."""

    model_config = ConfigDict(extra="forbid")

    node_id: str
    variant_label: str
    prompt_md: str
    starter_code: str
    reference_solution: str
    hidden_test: str
    probe: ProbeYaml

    @field_validator("variant_label")
    @classmethod
    def _label_shape(cls, v: str) -> str:
        if not _VARIANT_RE.match(v):
            raise ValueError(f"variant_label harus 'variant_<slug>', dapat {v!r}")
        return v

    @field_validator("prompt_md", "reference_solution")
    @classmethod
    def _nonempty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("field wajib ini kosong")
        return v

    @field_validator("hidden_test")
    @classmethod
    def _test_imports_solution(cls, v: str) -> str:
        if not _SOLUTION_IMPORT_RE.search(v):
            raise ValueError(
                "hidden_test.py harus meng-import modul `solution` "
                "(kode user disimpan sebagai solution.py saat grading)"
            )
        if "def test_" not in v:
            raise ValueError("hidden_test.py tak punya satu pun fungsi `test_*`")
        return v

    @model_validator(mode="after")
    def _probe_belongs_to_node(self):
        if self.probe.node_id != self.node_id:
            raise ValueError(
                f"probe.node_id {self.probe.node_id!r} != node_id artifact {self.node_id!r}"
            )
        return self


# --------------------------------------------------------------------------- #
# R2 — bukti codebase
# --------------------------------------------------------------------------- #
class Hypothesis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    node_id: str
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str
    evidence_locator: str

    @field_validator("rationale", "evidence_locator")
    @classmethod
    def _nonempty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError(
                "hipotesis tanpa rationale/evidence_locator tak bisa di-audit — ditolak"
            )
        return v


class HypothesesArtifact(BaseModel):
    """`hypotheses.json`. TIDAK punya field status: status selalu `unverified` di
    sistem, dan hanya Attempt yang boleh mengubahnya (§10, RISK-4).

    Daftar KOSONG adalah artifact yang SAH. "Tak ada bukti yang bisa dibaca" adalah
    jawaban jujur, dan menolaknya sebagai error hanya menekan model untuk mengarang
    hipotesis demi memuaskan skema — persis kegagalan yang paling mahal di peran ini.
    Alasannya ditulis di `note` dan tampil ke Isyah apa adanya.
    """

    model_config = ConfigDict(extra="forbid")

    hypotheses: list[Hypothesis] = []
    note: str = ""


# --------------------------------------------------------------------------- #
# Pembacaan artifact dari direktori job
# --------------------------------------------------------------------------- #
def _read(path: Path, *, required: bool = True) -> str:
    if not path.exists():
        if required:
            raise ArtifactError(f"file wajib tidak ada: {path.name}")
        return ""
    return path.read_text(encoding="utf-8")


def _wrap(fn, what: str):
    try:
        return fn()
    except ArtifactError:
        raise
    except Exception as e:  # noqa: BLE001 — semua kegagalan validasi jadi pesan tunggal
        raise ArtifactError(f"{what}: {e}") from e


def load_explanation(job_dir: Path, node_id: str) -> ExplanationArtifact:
    def build() -> ExplanationArtifact:
        raw_citations = json.loads(_read(job_dir / "citations.json"))
        if isinstance(raw_citations, dict):
            raw_citations = raw_citations.get("citations", raw_citations)
        return ExplanationArtifact(
            node_id=node_id,
            explanation_md=_read(job_dir / "explanation.md"),
            worked_example=_read(job_dir / "worked_example.py", required=False),
            citations=raw_citations,
        )

    return _wrap(build, "artifact R3 tak valid")


def load_challenge(job_dir: Path, node_id: str) -> ChallengeArtifact:
    variant_dir = job_dir / "variant"

    def build() -> ChallengeArtifact:
        meta = json.loads(_read(job_dir / "meta.json"))
        probe_raw = yaml.safe_load(_read(job_dir / "probe.yaml"))
        return ChallengeArtifact(
            node_id=node_id,
            variant_label=meta.get("variant_label", ""),
            prompt_md=_read(variant_dir / "prompt.md"),
            starter_code=_read(variant_dir / "starter_code.py"),
            reference_solution=_read(variant_dir / "reference_solution.py"),
            hidden_test=_read(variant_dir / "hidden_test.py"),
            probe=probe_raw,
        )

    return _wrap(build, "artifact R4 tak valid")


def load_hypotheses(job_dir: Path) -> HypothesesArtifact:
    def build() -> HypothesesArtifact:
        raw = json.loads(_read(job_dir / "hypotheses.json"))
        if isinstance(raw, list):
            raw = {"hypotheses": raw}
        return HypothesesArtifact(**raw)

    return _wrap(build, "artifact R2 tak valid")


# --------------------------------------------------------------------------- #
# Pemeriksaan yang butuh konteks repo (sumber & node yang ADA)
# --------------------------------------------------------------------------- #
def check_citations_known(artifact: ExplanationArtifact, known_source_ids: set[str]) -> None:
    """Sitasi wajib menunjuk SourceRef yang ada — kalau tidak, ia tak bisa diverifikasi."""
    unknown = sorted({c.source_ref_id for c in artifact.citations} - known_source_ids)
    if unknown:
        raise ArtifactError(
            f"sitasi menunjuk source_ref yang tak ada di sources.yaml: {', '.join(unknown)}"
        )


def check_nodes_known(artifact: HypothesesArtifact, known_node_ids: set[str]) -> None:
    unknown = sorted({h.node_id for h in artifact.hypotheses} - known_node_ids)
    if unknown:
        raise ArtifactError(f"hipotesis menunjuk node yang tak ada: {', '.join(unknown)}")
