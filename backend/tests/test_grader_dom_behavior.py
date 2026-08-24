"""Test grader `dom_behavior` (M6) — React di-render sungguhan di jsdom.

Yang dibuktikan:
- Interface `Executor` menyembunyikan bahasa runtime: grader ini memakai kontrak yang
  sama (`files → pass/fail`) padahal yang jalan adalah Node+vitest, bukan pytest.
- Yang dinilai adalah PERILAKU: komponen yang menampilkan angka benar tapi tak
  bereaksi terhadap klik tetap GAGAL.
- Runtime JS yang belum dipasang gagal dengan pesan yang memberi tahu cara
  memperbaikinya, bukan stack trace yang membingungkan.

Test yang butuh runtime di-skip (bukan gagal) kalau `npm install` belum dijalankan —
biar checkout baru tidak merah tanpa sebab.
"""

import pytest

from app.config import REACT_RUNTIME_DIR
from app.executor import NodeExecutor, NodeRuntimeMissingError
from app.graders.dom_behavior import DomBehaviorGrader
from app.models import ChallengeInstance

RUNTIME_READY = (REACT_RUNTIME_DIR / "node_modules" / "vitest" / "vitest.mjs").exists()
needs_runtime = pytest.mark.skipif(
    not RUNTIME_READY, reason="runtime React belum dipasang (`cd runtime/react && npm install`)"
)

HIDDEN_TEST = """
import { expect, test } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import Component from "./solution.jsx";

test("mulai dari nol", () => {
  render(<Component />);
  expect(screen.getByText("Nilai: 0")).toBeTruthy();
});

test("klik menaikkan nilai", async () => {
  const user = userEvent.setup();
  render(<Component />);
  await user.click(screen.getByRole("button", { name: "Naik" }));
  expect(screen.getByText("Nilai: 1")).toBeTruthy();
});
"""

CORRECT = """
import { useState } from "react";

export default function Widget() {
  const [n, setN] = useState(0);
  return (
    <div>
      <p>Nilai: {n}</p>
      <button onClick={() => setN(n + 1)}>Naik</button>
    </div>
  );
}
"""

# Tampilannya benar saat pertama render, tapi state-nya tak pernah berubah — persis
# jenis kesalahan yang lolos kalau yang diperiksa struktur JSX, bukan perilaku.
STATIC = """
export default function Widget() {
  return (
    <div>
      <p>Nilai: 0</p>
      <button>Naik</button>
    </div>
  );
}
"""

LOOPING = """
export default function Widget() {
  while (true) {
    // sengaja menggantung
  }
}
"""


def _instance(tmp_path) -> ChallengeInstance:
    (tmp_path / "hidden_test.jsx").write_text(HIDDEN_TEST, encoding="utf-8")
    return ChallengeInstance(
        id="rtest__variant_a",
        node_id="rtest",
        variant_label="variant_a",
        prompt="",
        starter_code="",
        signature_contract="",
        hidden_test_path=str(tmp_path / "hidden_test.jsx"),
        scaffold_level="L2",
    )


@needs_runtime
def test_correct_component_passes(tmp_path):
    result = DomBehaviorGrader().grade(_instance(tmp_path), CORRECT)
    assert result.passed, result.test_output


@needs_runtime
def test_component_without_behaviour_fails(tmp_path):
    """Render pertamanya benar; interaksinya tidak. Verdict harus FAIL."""
    result = DomBehaviorGrader().grade(_instance(tmp_path), STATIC)
    assert not result.passed
    assert "Nilai: 1" in result.test_output  # output jadi cermin, bukan ringkasan


@needs_runtime
def test_output_is_shown_for_failure(tmp_path):
    result = DomBehaviorGrader().grade(_instance(tmp_path), STATIC)
    assert result.test_output.strip()
    # Nama folder kerja acak tak boleh bocor ke cermin yang dibaca user.
    assert ".work/" not in result.test_output


@needs_runtime
def test_hanging_component_is_killed_by_timeout(tmp_path):
    """Timeout eksekusi harus benar-benar membunuh proses Node, bukan menggantung."""
    executor = NodeExecutor()
    result = executor.run(
        files={"solution.jsx": LOOPING, "solution.test.jsx": HIDDEN_TEST},
        test_entry="solution.test.jsx",
        timeout_seconds=20,
    )
    assert not result.passed
    assert result.timed_out or "Nilai: 0" in (result.stdout + result.stderr)


def test_missing_runtime_is_actionable(tmp_path):
    executor = NodeExecutor(runtime_dir=tmp_path / "runtime-kosong")
    grader = DomBehaviorGrader(executor=executor)

    with pytest.raises(NodeRuntimeMissingError, match="npm install"):
        grader.grade(_instance(tmp_path), CORRECT)


def test_executor_contract_is_the_same_shape():
    """`NodeExecutor` memenuhi Protocol `Executor` yang sama dengan SubprocessExecutor."""
    from app.executor import Executor, SubprocessExecutor

    for executor in (NodeExecutor(), SubprocessExecutor()):
        assert isinstance(executor, Executor)
