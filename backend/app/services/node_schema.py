"""Skema pydantic untuk memvalidasi `node.yaml`, `probe_*.yaml`, `edges.yaml`,
`sources.yaml` sebelum masuk DB.

Ini gerbang yang mencegah node cacat masuk sistem (M2 langkah 1). Validasi struktur
& enum di sini; verifikasi *hijau di solusi referensi* dilakukan `verify_nodes.py`
(itu hanya bisa dibuktikan dengan menjalankan kode — bukan skema).
"""

import re

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.models import (
    EdgeType,
    GraderType,
    ProbeType,
    ScheduleStatus,
    SourceType,
)

_SCAFFOLD_RE = re.compile(r"^L[0-3]$")


class SourceRefYaml(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    type: SourceType
    citation: str
    url_or_locator: str


class EdgeYaml(BaseModel):
    model_config = ConfigDict(extra="forbid")

    from_: str
    to: str
    type: EdgeType
    source_ref_id: str | None = None
    note: str = ""

    @model_validator(mode="before")
    @classmethod
    def _accept_from_key(cls, data):
        # `from` adalah keyword Python; terima key "from" dari YAML → from_.
        if isinstance(data, dict) and "from" in data and "from_" not in data:
            data = dict(data)
            data["from_"] = data.pop("from")
        return data

    @model_validator(mode="after")
    def _no_self_loop(self):
        if self.from_ == self.to:
            raise ValueError(f"edge tidak boleh self-loop: {self.from_} -> {self.to}")
        return self


class ProbeYaml(BaseModel):
    """Comprehension probe deterministik (PRD §9). `correct_answer` WAJIB salah satu
    dari `options` — kalau tidak, probe tak punya jawaban benar pasti.

    Skema hanya bisa membuktikan jawabannya BISA DIPILIH. Bahwa jawabannya BENAR
    dibuktikan dengan menjalankan `snippet` (M7) — sama seperti mastery: yang
    memutuskan adalah eksekusi kode, bukan pembacaan."""

    model_config = ConfigDict(extra="forbid")

    id: str
    node_id: str
    type: ProbeType
    question: str
    options: list[str]
    correct_answer: str
    #: Kode yang MENGHASILKAN jawabannya, dan ekspresi yang dibaca sebagai jawaban.
    #: Dengan keduanya, `correct_answer` bisa dibuktikan lewat EKSEKUSI, bukan cuma
    #: dicek "ada di options" (lihat `services/probe_verifier.py`). Masih opsional
    #: selama migrasi kurikulum lama (M7 langkah 6); begitu semua node termigrasi,
    #: keduanya dinaikkan jadi wajib.
    snippet: str = ""
    expression: str = ""
    #: Nilai yang WAJIB dihasilkan `expression`. Kosong = sama dengan `correct_answer`
    #: (bentuk terkuat: kunci jawabannya sendiri yang dieksekusi).
    #:
    #: Diisi HANYA bila opsi probe berupa prosa, bukan nilai — mis. jawaban "body
    #: kosong (0 byte)" yang klaim terukurnya `"0"`. Dalam bentuk itu mesin
    #: membuktikan KLAIM DI BALIK opsi, dan jembatan prosa->nilai tetap tanggung
    #: jawab penulisnya. Karena jembatan itu tak terperiksa mesin, probe buatan AI
    #: TIDAK BOLEH memakainya (lihat gate R4 di `claude/jobs.py`) — di sana tak ada
    #: manusia yang menulis jembatannya.
    expected_value: str = ""

    @field_validator("options")
    @classmethod
    def _min_two_options(cls, v: list[str]) -> list[str]:
        if len(v) < 2:
            raise ValueError("probe harus punya >= 2 options")
        return v

    @field_validator("options")
    @classmethod
    def _options_unique(cls, v: list[str]) -> list[str]:
        """Opsi kembar = dua pilihan yang sama-sama benar (atau sama-sama salah).

        Kalau yang kembar itu jawaban benarnya, Bryant bisa memilih yang benar dan
        tetap ter-grade salah — kegagalan yang tak akan pernah terlihat dari membaca
        YAML-nya, tapi gratis ditangkap di sini.
        """
        duplikat = sorted({o for o in v if v.count(o) > 1})
        if duplikat:
            raise ValueError(f"options punya isi kembar: {duplikat}")
        return v

    @model_validator(mode="after")
    def _answer_in_options(self):
        if self.correct_answer not in self.options:
            raise ValueError(
                f"correct_answer {self.correct_answer!r} tidak ada di options {self.options!r}"
            )
        return self

    @model_validator(mode="after")
    def _snippet_and_expression_together(self):
        """Satu tanpa yang lain tak bisa dijalankan — dan probe yang setengah
        termigrasi diam-diam lolos sebagai "belum termigrasi", padahal penulisnya
        mengira sudah terverifikasi."""
        if bool(self.snippet.strip()) != bool(self.expression.strip()):
            raise ValueError(
                "probe harus punya `snippet` DAN `expression` sekaligus, atau tak "
                "punya keduanya (probe setengah termigrasi tak pernah diverifikasi)"
            )
        return self


class NodeYaml(BaseModel):
    """Metadata node. Instance & probe ditemukan dari folder (bukan didaftar di sini)."""

    model_config = ConfigDict(extra="forbid")

    id: str
    domain_id: str
    concept: str
    description: str = ""
    grader_type: GraderType
    estimated_minutes: int
    timebox_seconds: int
    status_default: ScheduleStatus
    source_refs: list[str] = []
    signature_contract: str = ""
    scaffold_level: str

    @field_validator("timebox_seconds")
    @classmethod
    def _timebox_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("timebox_seconds harus > 0 (integritas timebox, PRD §7.6)")
        return v

    @field_validator("estimated_minutes")
    @classmethod
    def _minutes_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("estimated_minutes harus > 0")
        return v

    @field_validator("scaffold_level")
    @classmethod
    def _scaffold_valid(cls, v: str) -> str:
        if not _SCAFFOLD_RE.match(v):
            raise ValueError(f"scaffold_level harus L0..L3, dapat {v!r}")
        return v
