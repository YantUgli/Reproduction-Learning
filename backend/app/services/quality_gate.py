"""Gerbang mutu satu instance — TRIAD eksekusi (M7 langkah 1).

Tiga pemeriksaan, semuanya eksekusi kode lewat grader node itu sendiri:

1. **`reference_solution` HIJAU.** Test yang belum pernah dibuktikan hijau bukan
   test, cuma niat (aturan PRD §10 R4).
2. **Solusi KOSONG merah.** Kalau hidden test lolos tanpa kode sama sekali, ia tak
   menguji apa pun — biasanya karena semua test ter-skip, salah nama fungsi test,
   atau assert-nya tautologi. Pemeriksaan inilah yang membedakan "test ada" dari
   "test menguji sesuatu".
3. **`starter_code` MERAH.** Kerangka L2 yang sudah lolos apa adanya membuat node
   memalsukan sinyal inti produk: Bryant menekan "Jalankan" tanpa memproduksi apa
   pun dan tercatat sebagai `reproduce-without-AI` yang berhasil.

Kenapa modul terpisah, bukan disalin di dua tempat: gerbang authoring
(`scripts/verify_nodes.py`) dan gate otomatis R4 (`app/claude/jobs.py`) HARUS
menegakkan aturan yang sama persis. M6 sudah pernah kena persoalan ini — waktu itu
`verify_nodes.py` punya salinan aturan eksekusinya sendiri dan memverifikasi sesuatu
yang bukan persis yang dinilai saat Bryant submit.

Modul ini tak tahu node-nya domain apa: ia menerima `Grader` yang sudah dipilih
pemanggil lewat `get_grader(node.grader_type)`.
"""

from dataclasses import dataclass, field

from app.graders.base import Grader
from app.models import ChallengeInstance

#: Nama pemeriksaan — dipakai sebagai kunci di hasil (dan di pesan error).
REFERENCE = "reference"
EMPTY = "empty"
STARTER = "starter"

#: Solusi "kosong" yang dipakai pemeriksaan 2. Betul-betul kosong: berkas nol byte
#: adalah kasus terlemah yang mungkin, jadi hidden test yang meloloskannya pasti
#: tidak menguntungkan siapa pun.
EMPTY_SOLUTION = ""


@dataclass
class TriadCheck:
    """Satu pemeriksaan. `ok` = pemeriksaan TERPENUHI, bukan "test hijau" —
    untuk `empty`/`starter` yang terpenuhi justru saat test MERAH."""

    name: str
    ok: bool
    test_passed: bool | None = None
    duration_seconds: float = 0.0
    timed_out: bool = False
    output: str = ""
    skipped: bool = False


@dataclass
class TriadResult:
    ok: bool
    reason: str
    checks: list[TriadCheck] = field(default_factory=list)

    def check(self, name: str) -> TriadCheck | None:
        return next((c for c in self.checks if c.name == name), None)

    @property
    def failing(self) -> TriadCheck | None:
        return next((c for c in self.checks if not c.ok and not c.skipped), None)


def _tail(text: str, lines: int = 15) -> str:
    return "\n".join(text.strip().splitlines()[-lines:])


def run_triad(
    grader: Grader,
    instance: ChallengeInstance,
    *,
    reference: str,
    starter: str | None,
    check_negatives: bool = True,
) -> TriadResult:
    """Jalankan triad untuk satu instance.

    `starter=None` (node fixture yang memang tak punya kerangka) melewati pemeriksaan
    3 saja; pemeriksaan 2 tetap jalan karena ia tak butuh berkas apa pun.

    `check_negatives=False` hanya untuk iterasi cepat saat mengarang (lihat
    `--skip-starter`). JANGAN dipakai sebagai dasar commit atau sebagai gate.

    Berhenti di kegagalan pertama: pemeriksaan berikutnya tak menambah informasi
    dan tiap pemeriksaan berharga detik (React ±7 detik saat panas).
    """
    checks: list[TriadCheck] = []

    ref = grader.grade(instance, reference)
    checks.append(
        TriadCheck(
            name=REFERENCE,
            ok=ref.passed,
            test_passed=ref.passed,
            duration_seconds=ref.duration_seconds,
            timed_out=ref.timed_out,
            output=_tail(ref.test_output),
        )
    )
    if not ref.passed:
        why = "TIMEOUT saat" if ref.timed_out else "MERAH di"
        return TriadResult(
            ok=False,
            reason=f"hidden test {why} reference_solution — ditolak (§10 R4)",
            checks=checks,
        )

    if not check_negatives:
        checks.append(TriadCheck(name=EMPTY, ok=True, skipped=True))
        checks.append(TriadCheck(name=STARTER, ok=True, skipped=True))
        return TriadResult(
            ok=True, reason="referensi hijau (pemeriksaan negatif dilewati)", checks=checks
        )

    empty = grader.grade(instance, EMPTY_SOLUTION)
    checks.append(
        TriadCheck(
            name=EMPTY,
            ok=not empty.passed,
            test_passed=empty.passed,
            duration_seconds=empty.duration_seconds,
            timed_out=empty.timed_out,
            output=_tail(empty.test_output),
        )
    )
    if empty.passed:
        return TriadResult(
            ok=False,
            reason=(
                "hidden test LOLOS dengan solusi KOSONG — test ini tidak menguji apa pun "
                "(cek: nama fungsi `test_*`, test ter-skip, atau assert yang selalu benar)"
            ),
            checks=checks,
        )

    if starter is None:
        checks.append(TriadCheck(name=STARTER, ok=True, skipped=True))
        return TriadResult(
            ok=True, reason="referensi hijau, kosong merah (tanpa starter_code)", checks=checks
        )

    starter_run = grader.grade(instance, starter)
    checks.append(
        TriadCheck(
            name=STARTER,
            ok=not starter_run.passed,
            test_passed=starter_run.passed,
            duration_seconds=starter_run.duration_seconds,
            timed_out=starter_run.timed_out,
            output=_tail(starter_run.test_output),
        )
    )
    if starter_run.passed:
        return TriadResult(
            ok=False,
            reason=(
                "starter_code sudah LOLOS hidden test — tantangannya kosong. "
                "Kosongkan bagian inti kerangka, atau perketat hidden test."
            ),
            checks=checks,
        )

    return TriadResult(
        ok=True,
        reason="referensi hijau; solusi kosong & starter_code merah",
        checks=checks,
    )
