"""Probe diverifikasi EKSEKUSI, bukan dipercaya (M7 langkah 2).

Sampai M6, satu-satunya pemeriksaan atas sebuah probe adalah `correct_answer` ADA di
dalam `options` (`node_schema.ProbeYaml`). Itu memastikan probe punya jawaban yang
bisa dipilih — **bukan** bahwa jawaban itu benar. Probe dengan kunci salah lolos
mulus, lalu menghukum Bryant karena menjawab benar; dan sejak R4 boleh mengarang
probe sendiri (M5), tak ada manusia yang wajib membacanya lagi (M7).

Cara kerjanya, dan kenapa bentuknya begini:

    solution.<ext>  = `snippet` probe + fungsi yang menghitung `expression`
    test.<ext>      = assert hasilnya == jawaban yang diharapkan

`expression` sengaja dievaluasi di dalam ruang nama `snippet` (dengan menempelkan
fungsinya ke berkas snippet), bukan di modul test: penulis probe menulis ekspresinya
di tempat yang sama dengan kodenya, persis seperti saat ia menjalankannya sendiri.
Pemanggilannya ditunda ke dalam badan test — bukan dievaluasi saat modul di-import —
karena probe React butuh jsdom yang baru siap di dalam test vitest.

Yang diharapkan = `correct_answer`, KECUALI probe mengisi `expected_value`. Bentuk
kedua itu untuk probe yang opsinya prosa ("body kosong (0 byte)") atau rumus, di mana
yang bisa dieksekusi adalah KLAIM di baliknya (`"0"`). Di bentuk itu jembatan
prosa->nilai ditulis manusia dan tak terperiksa mesin — karena itu probe buatan AI
dilarang memakainya (gate R4 di `claude/jobs.py`).

Yang TIDAK dilakukan di sini, dan kenapa: sempat ada pemeriksaan "tiap distractor
harus berbeda dari hasil eksekusi". Itu mustahil gagal — distractor didefinisikan
sebagai opsi yang bukan `correct_answer`, jadi begitu `correct_answer` sama dengan
hasil eksekusi, semuanya otomatis berbeda. Gerbang yang tak pernah bisa menolak apa
pun lebih buruk daripada tak ada gerbang: ia memberi rasa aman tanpa menahan apa pun.
Cacat yang sesungguhnya dituju (dua opsi yang sama-sama benar) ditangkap lebih murah
oleh validator `options` unik di `node_schema.ProbeYaml` — tanpa eksekusi sama sekali.

Kalau probe belum punya `snippet` (kurikulum lama, sebelum migrasi M7 langkah 6),
hasilnya `skipped` — bukan lolos, bukan gagal. Pemanggil yang memutuskan artinya.
"""

import json
from dataclasses import dataclass

from app.config import EXECUTION_TIMEOUT_SECONDS, REACT_EXECUTION_TIMEOUT_SECONDS
from app.executor import Executor, NodeExecutor, SubprocessExecutor
from app.services.node_schema import ProbeYaml


@dataclass
class ProbeVerdict:
    ok: bool
    reason: str
    skipped: bool = False
    duration_seconds: float = 0.0
    output: str = ""


@dataclass(frozen=True)
class _Lang:
    """Cara merakit berkas verifikasi untuk satu bahasa.

    Ini tabel ketiga (setelah `graders/files._EDITOR_LANGUAGE_BY_SUFFIX` dan
    `claude/contracts._TEST_RULES`) yang memetakan ekstensi berkas ke perilaku.
    Semuanya hidup di lapisan authoring/IO — bukan di loop — dan menambah domain
    berarti menambah satu baris di masing-masing, bukan cabang `if domain == ...`.
    """

    solution_file: str
    test_file: str
    timeout_seconds: int


_LANGS: dict[str, _Lang] = {
    ".py": _Lang("solution.py", "test_solution.py", EXECUTION_TIMEOUT_SECONDS),
    ".jsx": _Lang("solution.jsx", "solution.test.jsx", REACT_EXECUTION_TIMEOUT_SECONDS),
}

_MARKER = "# --- dirakit probe_verifier (M7) ---"

#: Nama fungsi yang dirakit di berkas snippet. Sengaja panjang & berawalan modul
#: supaya tak bertabrakan dengan nama apa pun yang ditulis penulis probe.
_ENTRY = "probe_verifier_result"


def supported_extensions() -> list[str]:
    return sorted(_LANGS)


def _python_solution(snippet: str, expression: str) -> str:
    return f"{snippet.rstrip()}\n\n{_MARKER}\ndef {_ENTRY}():\n    return str({expression})\n"


def _python_test(correct: str) -> str:
    lines = [
        f"from solution import {_ENTRY}",
        "",
        "",
        "def test_correct_answer_matches_execution():",
        f"    assert {_ENTRY}() == {json.dumps(correct)}",
    ]
    return "\n".join(lines) + "\n"


def _react_solution(snippet: str, expression: str) -> str:
    return (
        f"{snippet.rstrip()}\n\n{_MARKER.replace('#', '//')}\n"
        f"export function {_ENTRY}() {{\n  return String({expression});\n}}\n"
    )


def _react_test(correct: str) -> str:
    lines = [
        'import { expect, test } from "vitest";',
        f'import {{ {_ENTRY} }} from "./solution.jsx";',
        "",
        'test("correct answer matches execution", () => {',
        f"  expect({_ENTRY}()).toBe({json.dumps(correct)});",
        "});",
    ]
    return "\n".join(lines) + "\n"


_RENDER = {
    ".py": (_python_solution, _python_test),
    ".jsx": (_react_solution, _react_test),
}


def _default_executor(file_ext: str) -> Executor:
    return NodeExecutor() if file_ext == ".jsx" else SubprocessExecutor()


def verify_probe(
    probe: ProbeYaml,
    *,
    file_ext: str,
    executor: Executor | None = None,
) -> ProbeVerdict:
    """Jalankan probe dan bandingkan hasilnya dengan `correct_answer`.

    `file_ext` = ekstensi berkas instance node (".py"/".jsx"), diturunkan dari berkas
    node itu sendiri — bukan dari `domain_id`.
    """
    if not probe.snippet.strip() or not probe.expression.strip():
        return ProbeVerdict(
            ok=True,
            skipped=True,
            reason="probe belum punya snippet/expression — tak terverifikasi mesin",
        )

    lang = _LANGS.get(file_ext)
    if lang is None:
        return ProbeVerdict(
            ok=True,
            skipped=True,
            reason=(
                f"verifikasi probe belum didukung untuk berkas {file_ext!r} "
                f"(terdaftar: {supported_extensions()})"
            ),
        )

    render_solution, render_test = _RENDER[file_ext]
    expected = probe.expected_value or probe.correct_answer
    files = {
        lang.solution_file: render_solution(probe.snippet, probe.expression),
        lang.test_file: render_test(expected),
    }

    executor = executor or _default_executor(file_ext)
    result = executor.run(
        files=files,
        test_entry=lang.test_file,
        timeout_seconds=lang.timeout_seconds,
    )
    output = (result.stdout + "\n" + result.stderr).strip()

    if result.passed:
        bentuk = (
            "correct_answer cocok dengan hasil eksekusi snippet"
            if not probe.expected_value
            else f"klaim di balik jawaban terbukti (expected_value {expected!r})"
        )
        return ProbeVerdict(ok=True, reason=bentuk, duration_seconds=result.duration_seconds)

    if result.timed_out:
        reason = f"snippet probe tak berhenti dalam {lang.timeout_seconds}s"
    elif "correct_answer_matches_execution" in output or "correct answer matches" in output:
        reason = (
            f"nilai yang diharapkan {expected!r} TIDAK sama dengan hasil eksekusi "
            "snippet — kuncinya salah, atau snippet/expression tak menghitung yang ditanya"
        )
    else:
        reason = "snippet probe gagal dijalankan (lihat output)"

    return ProbeVerdict(
        ok=False,
        reason=reason,
        duration_seconds=result.duration_seconds,
        output="\n".join(output.splitlines()[-20:]),
    )
