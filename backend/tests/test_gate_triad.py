"""Test TRIAD gerbang mutu (M7 langkah 1).

Yang dibuktikan di sini:

- Triad menolak **hidden test yang lolos dengan solusi KOSONG**. Ini pemeriksaan
  baru M7, dan yang paling penting: node semacam itu MEMALSUKAN sinyal inti produk
  — Bryant menekan "Jalankan" tanpa memproduksi apa pun dan tercatat berhasil.
- Triad tetap menolak starter yang sudah lolos, dan referensi yang merah.
- Aturannya SATU salinan: `verify_nodes.py` (soal tulisan tangan) dan gate R4
  (`claude/jobs.py`, soal buatan AI) memanggil fungsi yang sama.
- Kontrak R4 tidak lagi mengasumsikan `.py` — artifact React (`.jsx`) diterima dan
  divalidasi dengan aturan bahasanya sendiri.

Sebagian besar memakai grader palsu: yang diuji adalah LOGIKA gerbangnya, dan
memakai subprocess sungguhan di sini cuma menambah detik tanpa menambah bukti.
Eksekusi sungguhan sudah diuji `test_grader_*` dan `verify_nodes.py`.
"""

import json
from pathlib import Path

import pytest
import yaml

from app.claude import contracts
from app.graders.base import GradeResult
from app.models import ChallengeInstance
from app.services.quality_gate import EMPTY, REFERENCE, STARTER, run_triad

REFERENCE_CODE = "def f():\n    return 1\n"
STARTER_CODE = "def f():\n    raise NotImplementedError\n"


class FakeGrader:
    """Grader yang lolos hanya untuk daftar submisi tertentu.

    Memakai isi submisi sebagai kunci membuat tiap skenario gerbang bisa ditulis
    sebagai satu kalimat: "test ini lolos untuk X" — termasuk skenario yang mustahil
    diarang dengan node sungguhan, seperti test yang lolos di berkas kosong.
    """

    def __init__(self, passes_for: set[str]) -> None:
        self._passes_for = passes_for
        self.graded: list[str] = []

    def grade(self, instance: ChallengeInstance, submitted_code: str) -> GradeResult:
        self.graded.append(submitted_code)
        return GradeResult(
            passed=submitted_code in self._passes_for,
            test_output="(fake)",
            timed_out=False,
            duration_seconds=0.01,
        )


@pytest.fixture()
def instance() -> ChallengeInstance:
    return ChallengeInstance(
        id="n999__variant_a",
        node_id="n999",
        variant_label="variant_a",
        prompt="",
        starter_code="",
        signature_contract="",
        hidden_test_path="data/domains/fastapi/nodes/_example/instances/variant_a/hidden_test.py",
        scaffold_level="L2",
    )


def _triad(instance, *, passes_for, starter=STARTER_CODE):
    grader = FakeGrader(passes_for)
    return grader, run_triad(grader, instance, reference=REFERENCE_CODE, starter=starter)


# --------------------------------------------------------------------------- #
# Triad
# --------------------------------------------------------------------------- #
def test_node_sehat_lolos_tiga_pemeriksaan(instance):
    grader, result = _triad(instance, passes_for={REFERENCE_CODE})

    assert result.ok
    assert [c.name for c in result.checks] == [REFERENCE, EMPTY, STARTER]
    assert all(c.ok for c in result.checks)
    # Tiga eksekusi, bukan dua: referensi, kosong, starter.
    assert grader.graded == [REFERENCE_CODE, "", STARTER_CODE]


def test_test_yang_lolos_dengan_solusi_kosong_ditolak(instance):
    """Pemeriksaan BARU M7: hidden test yang hijau di berkas kosong tak menguji apa pun.

    Ini lolos gerbang lama (referensi hijau, starter merah) — dan node seperti itu
    memberi Bryant "PASS" yang tak membuktikan apa pun.
    """
    _, result = _triad(instance, passes_for={REFERENCE_CODE, ""})

    assert not result.ok
    assert result.failing.name == EMPTY
    assert "KOSONG" in result.reason
    # Berhenti di kegagalan pertama: starter tak perlu dijalankan lagi.
    assert result.check(STARTER) is None


def test_starter_yang_sudah_lolos_ditolak(instance):
    _, result = _triad(instance, passes_for={REFERENCE_CODE, STARTER_CODE})

    assert not result.ok
    assert result.failing.name == STARTER
    assert "starter_code" in result.reason


def test_referensi_merah_ditolak_sebelum_pemeriksaan_lain(instance):
    grader, result = _triad(instance, passes_for=set())

    assert not result.ok
    assert result.failing.name == REFERENCE
    assert "MERAH" in result.reason
    # Referensi merah = node rusak; tak ada gunanya membayar dua eksekusi lagi.
    assert grader.graded == [REFERENCE_CODE]


def test_tanpa_starter_pemeriksaan_kosong_tetap_jalan(instance):
    """Node fixture boleh tak punya `starter_code` — tapi itu tak boleh jadi celah
    yang ikut mematikan pemeriksaan solusi kosong."""
    _, result = _triad(instance, passes_for={REFERENCE_CODE, ""}, starter=None)

    assert not result.ok
    assert result.failing.name == EMPTY


def test_skip_negatives_hanya_untuk_iterasi_cepat(instance):
    grader = FakeGrader({REFERENCE_CODE, "", STARTER_CODE})
    result = run_triad(
        grader,
        instance,
        reference=REFERENCE_CODE,
        starter=STARTER_CODE,
        check_negatives=False,
    )

    # Node yang jelas cacat "lolos" — persis kenapa flag ini tak boleh jadi dasar commit.
    assert result.ok
    assert grader.graded == [REFERENCE_CODE]
    assert [c.skipped for c in result.checks] == [False, True, True]


# --------------------------------------------------------------------------- #
# Satu salinan aturan, bukan dua
# --------------------------------------------------------------------------- #
def test_gerbang_authoring_dan_gate_r4_memakai_fungsi_yang_sama():
    """M6 pernah kena: `verify_nodes.py` punya salinan aturan eksekusinya sendiri dan
    memverifikasi sesuatu yang bukan persis yang dinilai saat submit. Test ini merah
    kalau salah satu pemanggil kembali menulis aturannya sendiri."""
    import app.claude.jobs as jobs_mod

    verify_src = (Path(__file__).resolve().parents[2] / "scripts" / "verify_nodes.py").read_text(
        encoding="utf-8"
    )

    assert "run_triad" in verify_src
    assert jobs_mod.run_triad is run_triad


# --------------------------------------------------------------------------- #
# Kontrak R4 tak lagi mengasumsikan Python
# --------------------------------------------------------------------------- #
REACT_TEST = (
    'import { expect, test } from "vitest";\n'
    'import { render, screen } from "@testing-library/react";\n'
    'import Component from "./solution.jsx";\n\n'
    'test("render", () => {\n  render(<Component />);\n'
    '  expect(screen.getByText("Halo")).toBeTruthy();\n});\n'
)
REACT_PROBE = {
    "id": "r001_probe_02",
    "node_id": "r001_state_counter",
    "type": "predict_output",
    "question": "Apa yang tampil setelah satu klik?",
    "options": ["0", "1"],
    "correct_answer": "1",
}


def _write_react_artifact(job_dir: Path, *, hidden_test: str = REACT_TEST) -> None:
    variant = job_dir / "variant"
    variant.mkdir(parents=True)
    (job_dir / "meta.json").write_text(json.dumps({"variant_label": "variant_c"}), encoding="utf-8")
    (job_dir / "probe.yaml").write_text(yaml.safe_dump(REACT_PROBE), encoding="utf-8")
    (variant / "prompt.md").write_text("Buat komponen.", encoding="utf-8")
    (variant / "starter_code.jsx").write_text("export default function C() {}\n", encoding="utf-8")
    (variant / "reference_solution.jsx").write_text(
        "export default function C() {\n  return <p>Halo</p>;\n}\n", encoding="utf-8"
    )
    (variant / "hidden_test.jsx").write_text(hidden_test, encoding="utf-8")


def test_artifact_react_diterima_kontrak_r4(tmp_path):
    """Sebelum M7 kontrak membaca `reference_solution.py` secara literal, jadi setiap
    artifact React ditolak di skema — sebelum gate eksekusi sempat berjalan."""
    _write_react_artifact(tmp_path)

    artifact = contracts.load_challenge(tmp_path, "r001_state_counter")

    assert artifact.file_ext == ".jsx"
    assert artifact.variant_label == "variant_c"


def test_hidden_test_react_yang_tak_menyentuh_solusi_ditolak(tmp_path):
    tanpa_import = (
        'import { test, expect } from "vitest";\n\n'
        'test("kosong", () => {\n  expect(1).toBe(1);\n});\n'
    )
    _write_react_artifact(tmp_path, hidden_test=tanpa_import)

    with pytest.raises(contracts.ArtifactError, match="solution.jsx"):
        contracts.load_challenge(tmp_path, "r001_state_counter")
