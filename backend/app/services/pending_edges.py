"""Store usulan edge `hard` yang menunggu veto Isyah (Amandemen C, jalur ASYNC).

Rancangan lengkap: `docs/design-async-review-mechanism.md` + langkah di
`docs/execution-plan-async-review.md`. Ringkasnya: Amandemen B mengizinkan AI mengusulkan
edge `hard`, tapi `hard` yang salah **mengunci Bryant KELUAR** dari node yang siap ia
kerjakan — jadi usulan `hard` tak boleh langsung mendarat di `edges.yaml`. Ia menunggu di
`data/domains/<domain>/edges.pending.yaml` selama 7 hari; Isyah bisa memveto kapan saja,
dan bila tak diveto sampai matang ia boleh dipromosikan (script, MANUAL — bukan modul ini).

**Modul ini READ-ONLY.** Ia hanya membaca berkas pending + menghitung keadaan tiap entri.
Penulisannya milik dua pihak lain, sengaja dipisah:
- `_promote_node_genesis` (backend) menulis entri baru saat node lahir dengan usulan `hard`.
- `scripts/promote_pending_edges.py` (dijalankan Isyah) memveto & mempromosikan.

**Loop pembelajaran tak pernah membaca berkas ini.** `node_loader.load_edges` hanya membaca
`edges.yaml`, jadi selama sebuah edge masih menunggu di sini, ia tak ada untuk loop → node
tetap `available`, tak pernah terkunci. Itu seluruh alasan lajur pending ada.
"""

from datetime import UTC, datetime, timedelta
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, model_validator

from app.models import EdgeType

#: 7 hari kalender sejak masuk antrian (Amandemen B). Satu sumber untuk klok — bukan
#: diturunkan dari mtime berkas (rapuh) atau `job.created_at` (fana di `artifacts/`).
PENDING_REVIEW_DAYS = 7

#: Keadaan sebuah usulan. `diveto` menang atas `matang`: entri yang sudah diveto tak
#: pernah dianggap siap promosi walau umurnya sudah lewat 7 hari.
STATE_MENUNGGU = "menunggu"
STATE_MATANG = "matang"
STATE_DIVETO = "diveto"


class PendingEdge(BaseModel):
    """Satu usulan edge `hard` menunggu veto. Model SENDIRI, bukan `EdgeYaml`:
    `EdgeYaml` memakai `extra="forbid"` dan tak punya field antrian (`queued_at`,
    `job_id`, `vetoed_at`, ...), jadi memakainya di sini akan menolak berkas pending.
    """

    model_config = ConfigDict(extra="forbid")

    from_: str
    to: str
    type: EdgeType
    source_ref_id: str
    library_file: str
    job_id: str
    queued_at: datetime
    note: str = ""
    #: Diisi HANYA saat veto (veto ulang menimpa keduanya — idempoten, hasil = veto
    #: terakhir). Entri yang diveto TIDAK dihapus; jejak keputusan sengaja tinggal.
    vetoed_at: datetime | None = None
    veto_reason: str = ""

    @model_validator(mode="before")
    @classmethod
    def _accept_from_key(cls, data):
        # `from` adalah keyword Python; terima key "from" dari YAML → from_.
        # (Pola sama dengan node_schema.EdgeYaml, sengaja konsisten.)
        if isinstance(data, dict) and "from" in data and "from_" not in data:
            data = dict(data)
            data["from_"] = data.pop("from")
        return data

    @model_validator(mode="after")
    def _aware_utc(self):
        # Klok 7 hari harus membandingkan datetime yang sebanding. YAML boleh memberi
        # datetime naif (tanpa offset); anggap itu UTC, jangan meledak saat membandingkan.
        if self.queued_at.tzinfo is None:
            self.queued_at = self.queued_at.replace(tzinfo=UTC)
        if self.vetoed_at is not None and self.vetoed_at.tzinfo is None:
            self.vetoed_at = self.vetoed_at.replace(tzinfo=UTC)
        return self


def edge_id(entry: PendingEdge) -> str:
    """Identitas stabil sebuah usulan = pasangan `<from>__<to>`.

    Diverifikasi (design §8): pasangan from->to unik di seluruh kurikulum (0 duplikat
    dari 23+14 edge), dan id node sudah unik lintas domain (prefix n/m/r), jadi pasangan
    itu cukup — tak perlu hash atau timestamp di dalam id.
    """
    return f"{entry.from_}__{entry.to}"


def matures_at(entry: PendingEdge) -> datetime:
    """Kapan usulan ini boleh dipromosikan bila tak diveto."""
    return entry.queued_at + timedelta(days=PENDING_REVIEW_DAYS)


def state(entry: PendingEdge, now: datetime | None = None) -> str:
    """Keadaan entri: `diveto` | `matang` | `menunggu`.

    Urutan cek disengaja: veto DIPERIKSA lebih dulu, jadi entri yang diveto tetap
    `diveto` walau umurnya sudah lewat 7 hari — veto tak pernah kedaluwarsa jadi promosi.
    """
    now = now or datetime.now(UTC)
    if entry.vetoed_at is not None:
        return STATE_DIVETO
    if now >= matures_at(entry):
        return STATE_MATANG
    return STATE_MENUNGGU


def load_pending(path: Path) -> list[PendingEdge]:
    """Baca satu `edges.pending.yaml`. Berkas absen = belum ada usulan → list kosong.

    Agregasi lintas domain sengaja TIDAK di sini: belum ada konsumennya sampai audit
    (Langkah 3) & script (Langkah 2). Primitifnya satu-berkas; yang menggabung menambahkan
    saat butuh, supaya tak ada pipa tanpa konsumen.
    """
    if not path.exists():
        return []
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    entries = raw.get("edges") or []
    return [PendingEdge.model_validate(e) for e in entries]
