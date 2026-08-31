"""Kontrak artifact Claude Code (M5 langkah 3) — skema KETAT per peran.

Prinsip (M5 §Keputusan teknis): **manusia me-review konten, bukan membetulkan
format.** Semua yang bisa dicek mesin dicek di sini, sebelum artifact menyentuh
antrean review. Output yang tak sesuai skema DITOLAK — tak pernah sampai ke Isyah.

Bentuk file per peran (sengaja file terpisah, bukan satu JSON raksasa: Isyah harus
bisa membuka artifact-nya langsung dan membacanya seperti kode):

    r3/  explanation.md      + citations.json
    r4/  variant/{prompt.md,starter_code.*,reference_solution.*,hidden_test.*}
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

#: Aturan "hidden test benar-benar menguji submisi user", per bahasa. Kunci = ekstensi
#: berkas hidden test artifact (ditemukan dari NAMA DASAR, bukan diasumsikan `.py`) —
#: sama seperti `graders/files.py`, supaya menambah domain berarti menambah satu baris
#: di sini, bukan cabang `if domain == ...`.
_TEST_RULES: dict[str, tuple[re.Pattern, re.Pattern, str]] = {
    ".py": (
        re.compile(r"^\s*(from\s+solution\s+import|import\s+solution)", re.MULTILINE),
        re.compile(r"def test_"),
        "meng-import modul `solution` (kode user disimpan sebagai solution.py) "
        "dan punya fungsi `test_*`",
    ),
    ".jsx": (
        re.compile(r"""from\s+["']\./solution\.jsx["']"""),
        re.compile(r"\b(test|it)\s*\("),
        'meng-import "./solution.jsx" (kode user disimpan sebagai solution.jsx) '
        "dan punya blok `test(...)`/`it(...)`",
    ),
}
_DEFAULT_TEST_EXT = ".py"


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
    #: Potongan VERBATIM dari sumber yang menopang klaim ini. Dicocokkan sebagai
    #: substring terhadap `data/sources/<id>.md` (lihat `services/grounding.py`).
    #: Sebelum M7 sitasi hanya perlu menunjuk sumber yang ADA — itu membuktikan
    #: sumbernya terdaftar, bukan bahwa klaimnya ditopang.
    quote: str = ""


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
    #: Ekstensi berkas instance (".py" FastAPI/ML, ".jsx" React). Diturunkan dari
    #: berkas yang BENAR-BENAR ditulis Claude Code, bukan dari `domain_id`.
    file_ext: str = _DEFAULT_TEST_EXT
    #: `expected.json` — hanya dipakai grader `value_assert` (ML). Kosong untuk domain lain.
    expected_json: str = ""

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

    @model_validator(mode="after")
    def _test_references_solution(self):
        """Hidden test WAJIB benar-benar memanggil submisi user.

        Ini murah tapi menutup satu kegagalan mahal: test yang tak pernah menyentuh
        `solution` bisa hijau di apa saja, termasuk di berkas kosong. Pemeriksaan
        eksekusinya sendiri (triad) ada di `services/quality_gate.py`; yang di sini
        cuma memastikan bentuknya masuk akal sebelum kita membayar ongkos eksekusi.
        """
        rule = _TEST_RULES.get(self.file_ext)
        if rule is None:
            raise ValueError(
                f"ekstensi berkas {self.file_ext!r} belum didukung kontrak R4 "
                f"(terdaftar: {sorted(_TEST_RULES)})"
            )
        imports_re, test_re, expectation = rule
        if not imports_re.search(self.hidden_test) or not test_re.search(self.hidden_test):
            raise ValueError(f"hidden_test{self.file_ext} harus {expectation}")
        return self

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


def _find(directory: Path, stem: str) -> Path:
    """Berkas `<stem>.<ekstensi apa pun>` — mencerminkan `node_loader.find_instance_file`."""
    matches = sorted(p for p in directory.glob(f"{stem}.*") if p.is_file())
    if not matches:
        raise ArtifactError(f"file wajib tidak ada: {stem}.* di {directory.name}/")
    return matches[0]


def _read_found(directory: Path, stem: str, *, required: bool = True) -> str:
    try:
        return _read(_find(directory, stem))
    except ArtifactError:
        if required:
            raise
        return ""


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
    """Baca artifact R4 dari direktori job.

    Berkas instance ditemukan dari NAMA DASAR (`reference_solution.*`), bukan dari
    ekstensi yang diasumsikan `.py` — kalau tidak, seluruh domain non-Python ditolak
    di sini sebelum gate eksekusi sempat berjalan (kebocoran yang M6 tutup di
    `node_loader` tapi terlewat di sini).
    """
    variant_dir = job_dir / "variant"

    def build() -> ChallengeArtifact:
        meta = json.loads(_read(job_dir / "meta.json"))
        probe_raw = yaml.safe_load(_read(job_dir / "probe.yaml"))
        hidden = _find(variant_dir, "hidden_test")
        return ChallengeArtifact(
            node_id=node_id,
            variant_label=meta.get("variant_label", ""),
            prompt_md=_read(variant_dir / "prompt.md"),
            starter_code=_read_found(variant_dir, "starter_code"),
            reference_solution=_read_found(variant_dir, "reference_solution"),
            hidden_test=_read(hidden),
            probe=probe_raw,
            file_ext=hidden.suffix,
            expected_json=_read_found(variant_dir, "expected", required=False),
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
