"""Telemetri kurikulum — mata pengganti Isyah (M7 langkah 7).

Gerbang mesin (triad, probe, grounding) menangkap node yang **rusak**. Ia tak bisa
menangkap node yang **sia-sia**: soal yang referensinya hijau dan starter-nya merah
masih bisa berupa trivia. Sampai M6, yang menangkap itu adalah mata Isyah saat
me-review. Sejak §7 2026-08-31 ia tak lagi di jalur.

Penggantinya bukan heuristik baru, melainkan **oracle yang sudah kita punya**: tiap
`Attempt` sudah merekam pass/fail dan durasi, tiap `ScheduleItem` merekam status &
riwayat review. Dari data itu, kualitas sebuah node bisa diukur SETELAH dipakai:

- Node yang **selalu lolos percobaan pertama** tak membedakan apa pun — trivia.
- Node yang **tak pernah lolos** rusak, salah scope, atau prasyaratnya bolong.
- Node yang **jauh lebih lama** dari `estimated_minutes` biasanya menggabung lebih
  dari satu konsep.
- Node yang **probenya selalu benar / selalu salah** punya probe mati atau menyesatkan.

Inilah yang tak bisa dilakukan sistem rujukan (Eero/Alter): mereka boleh sepenuhnya
dikemudikan AI justru karena tak ada satu momen pun di sistem mereka yang bisa
ketahuan salah. Ukuran sukses mereka ("terasa diajar") tak mungkin gagal; ukuran di
sini (pass rate reproduksi dingin) bisa turun, dan penurunannya meninggalkan jejak.

## Dua batas yang dipegang keras

1. **n=1.** Statistik per-node dari SATU pelajar itu berisik: Bryant gagal sebuah
   node bisa berarti nodenya buruk, bisa juga berarti harinya buruk. Karena itu tiap
   sinyal punya ambang jumlah attempt minimum, dan modul ini **hanya MENANDAI** —
   tak ada pensiun otomatis. Pencabutan selalu satu klik manusia.
2. **Ia mengukur daya beda & kesehatan node, bukan ARAH kurikulum.** Kalau 40 node
   trivia semuanya membedakan dengan rapi, telemetri melaporkan semuanya sehat.
   "Apakah ini kurikulum yang benar" tak punya oracle di sistem mana pun; itu
   ditetapkan manusia sekali per domain lewat `destination` di `domain.yaml`.
"""

from dataclasses import dataclass, field
from statistics import median

from sqlmodel import Session, select

from app.models import Attempt, AttemptMode, AttemptResult, Node, ScheduleItem

#: Attempt minimum sebelum sebuah sinyal berani bersuara. Sengaja longgar: dengan
#: satu pelajar, angka kecil berarti kebetulan, bukan pola.
MIN_ATTEMPTS = 4

#: Kelipatan `estimated_minutes` yang dianggap salah kalibrasi.
DURATION_FACTOR = 2.5

#: Probe minimum sebelum "selalu benar/selalu salah" dianggap sinyal.
MIN_PROBES = 4

#: Mode attempt yang dihitung: hanya reproduksi DINGIN, sama seperti KPI
#: `reproduce-without-AI` (§7 2026-08-21). Attempt `acquisition` masih berscaffold —
#: memasukkannya akan menggelembungkan pass rate dengan latihan bersontekan, dan
#: node trivia justru akan tampak sehat.
COLD_MODES = (
    AttemptMode.verification.value,
    AttemptMode.review.value,
    AttemptMode.placement.value,
)

TRIVIA = "trivia"
BROKEN = "rusak"
MISCALIBRATED = "salah_kalibrasi"
DEAD_PROBE = "probe_mati"


@dataclass
class NodeSignal:
    node_id: str
    kind: str
    detail: str
    samples: int


@dataclass
class NodeStats:
    node_id: str
    cold_attempts: int = 0
    cold_passes: int = 0
    first_try_passes: int = 0
    durations: list[int] = field(default_factory=list)
    probes_answered: int = 0
    probes_correct: int = 0

    @property
    def pass_rate(self) -> float | None:
        return self.cold_passes / self.cold_attempts if self.cold_attempts else None


def collect(session: Session) -> dict[str, NodeStats]:
    """Statistik mentah per node dari attempt DINGIN."""
    stats: dict[str, NodeStats] = {}
    seen_first: set[str] = set()

    attempts = session.exec(select(Attempt).order_by(Attempt.timestamp, Attempt.id)).all()
    for attempt in attempts:
        if attempt.mode not in COLD_MODES:
            continue
        if attempt.result not in (AttemptResult.passed.value, AttemptResult.failed.value):
            continue

        st = stats.setdefault(attempt.node_id, NodeStats(node_id=attempt.node_id))
        st.cold_attempts += 1
        lolos = attempt.result == AttemptResult.passed.value
        if lolos:
            st.cold_passes += 1
            if attempt.node_id not in seen_first:
                st.first_try_passes += 1
        seen_first.add(attempt.node_id)

        if attempt.duration_seconds > 0:
            st.durations.append(attempt.duration_seconds)
        if attempt.probe_result in ("correct", "incorrect"):
            st.probes_answered += 1
            if attempt.probe_result == "correct":
                st.probes_correct += 1

    return stats


def signals(session: Session) -> list[NodeSignal]:
    """Node yang layak dilihat manusia — TANDA, bukan vonis."""
    stats = collect(session)
    nodes = {n.id: n for n in session.exec(select(Node)).all()}
    out: list[NodeSignal] = []

    for node_id, st in sorted(stats.items()):
        node = nodes.get(node_id)
        if st.cold_attempts < MIN_ATTEMPTS:
            continue

        if st.cold_passes == st.cold_attempts:
            out.append(
                NodeSignal(
                    node_id=node_id,
                    kind=TRIVIA,
                    detail=(
                        f"lolos {st.cold_passes}/{st.cold_attempts} attempt dingin tanpa "
                        "pernah gagal — node ini tak membedakan apa pun"
                    ),
                    samples=st.cold_attempts,
                )
            )
        elif st.cold_passes == 0:
            out.append(
                NodeSignal(
                    node_id=node_id,
                    kind=BROKEN,
                    detail=(
                        f"tak pernah lolos dalam {st.cold_attempts} attempt — rusak, "
                        "salah scope, atau prasyaratnya bolong"
                    ),
                    samples=st.cold_attempts,
                )
            )

        if node and node.estimated_minutes > 0 and st.durations:
            median_min = median(st.durations) / 60
            if median_min > node.estimated_minutes * DURATION_FACTOR:
                out.append(
                    NodeSignal(
                        node_id=node_id,
                        kind=MISCALIBRATED,
                        detail=(
                            f"median {median_min:.0f} menit vs estimasi "
                            f"{node.estimated_minutes} menit — kemungkinan menggabung "
                            "lebih dari satu konsep"
                        ),
                        samples=len(st.durations),
                    )
                )

        if st.probes_answered >= MIN_PROBES and st.probes_correct in (0, st.probes_answered):
            selalu = "BENAR" if st.probes_correct else "SALAH"
            out.append(
                NodeSignal(
                    node_id=node_id,
                    kind=DEAD_PROBE,
                    detail=(
                        f"probe dijawab {st.probes_answered} kali dan selalu {selalu} — "
                        "probe mati (terlalu mudah) atau menyesatkan"
                    ),
                    samples=st.probes_answered,
                )
            )

    return out


def coverage(session: Session) -> dict:
    """Ringkasan seberapa banyak kurikulum yang PUNYA data untuk dinilai.

    Angka ini yang menjaga telemetri tetap jujur: dengan satu pelajar, sebagian besar
    node belum pernah dikerjakan dingin, dan "tak ada temuan" hampir selalu berarti
    "belum ada datanya" — bukan "semuanya sehat".
    """
    stats = collect(session)
    total = len(session.exec(select(Node)).all())
    dinilai = sum(1 for st in stats.values() if st.cold_attempts >= MIN_ATTEMPTS)
    lapsed = sum(1 for item in session.exec(select(ScheduleItem)).all() if item.status == "lapsed")
    return {
        "nodes": total,
        "nodes_with_cold_data": len(stats),
        "nodes_assessable": dinilai,
        "min_attempts": MIN_ATTEMPTS,
        "lapsed_now": lapsed,
    }
