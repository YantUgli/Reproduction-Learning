#!/usr/bin/env python3
"""GERBANG MUTU AUTHORING (M2 langkah 2, diperluas M6, jadi TRIAD di M7).

Untuk SETIAP instance node di SETIAP domain, TIGA pemeriksaan — keduanya eksekusi kode,
lewat grader yang sama dengan yang dipakai aplikasi (`grader_type` node → registry):

1. **Hidden test HIJAU di `reference_solution`.** Penegak aturan PRD §10 R4. Test yang
   belum pernah dibuktikan hijau bukan test, cuma niat.
2. **Hidden test MERAH di solusi KOSONG.** Kalau hidden test lolos tanpa kode sama
   sekali, ia tak menguji apa pun (test ter-skip, salah nama `test_*`, assert
   tautologi). Ini pemeriksaan yang membedakan "test ada" dari "test menguji sesuatu".
3. **Hidden test MERAH di `starter_code`.** Kalau kerangka L2 sudah lolos apa adanya,
   tantangannya kosong: Bryant bisa menekan "Jalankan" tanpa memproduksi apa pun dan
   sistem akan mencatatnya sebagai `reproduce-without-AI` yang berhasil. Node seperti
   itu tak cuma tak berguna — ia MEMALSUKAN sinyal inti produk ini.

Node yang gagal salah satunya TIDAK BOLEH di-commit.

Kenapa lewat grader, bukan memanggil Executor langsung (seperti versi M2): sejak ada
domain kedua, "cara menjalankan test" berbeda per grader (pytest vs vitest, file
tambahan seperti `expected.json`). Kalau skrip ini punya salinan aturannya sendiri,
ia akan memverifikasi sesuatu yang bukan persis yang dinilai saat Bryant submit.

Aturan triad-nya sendiri hidup di `app/services/quality_gate.py` dan dipakai BERSAMA
dengan gate otomatis R4 (`app/claude/jobs.py`) — supaya soal tulisan tangan dan soal
buatan AI dinilai aturan yang sama persis, bukan dua salinan yang bisa berbeda.

Pemakaian:
    python scripts/verify_nodes.py [domain ...] [--skip-starter]
Exit 0 = semua hijau; 1 = ada yang merah/timeout/starter-lolos.
"""

import argparse
import sys
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "backend"))

from app.config import DATA_DIR  # noqa: E402
from app.graders import get_grader  # noqa: E402
from app.graders.files import reference_solution_path, repo_pointer  # noqa: E402
from app.models import ChallengeInstance  # noqa: E402
from app.services.node_loader import (  # noqa: E402
    NodeValidationError,
    assemble_node,
    find_instance_file,
)
from app.services.node_schema import ProbeYaml  # noqa: E402
from app.services.probe_verifier import verify_probe  # noqa: E402
from app.services.quality_gate import (  # noqa: E402
    EMPTY,
    REFERENCE,
    STARTER,
    TriadResult,
    run_triad,
)

#: Nama pemeriksaan triad -> tag yang dicetak, supaya kegagalannya bisa dibedakan
#: sekilas saat membaca output panjang.
_TAG = {
    REFERENCE: "FAIL",
    EMPTY: "KOSONG-LOLOS",
    STARTER: "STARTER-LOLOS",
}


def _timing(triad: TriadResult) -> str:
    parts = [f"{c.name} {c.duration_seconds:.2f}s" for c in triad.checks if not c.skipped]
    return " | ".join(parts)


def _instance_for(node_dir: Path, node_id: str, meta, variant_dir: Path) -> ChallengeInstance:
    """ChallengeInstance in-memory (tak menyentuh DB) — grader hanya butuh pointer."""
    hidden = find_instance_file(variant_dir, "hidden_test")
    return ChallengeInstance(
        id=f"{node_id}__{variant_dir.name}",
        node_id=node_id,
        variant_label=variant_dir.name,
        prompt="",
        starter_code="",
        signature_contract=meta.signature_contract,
        hidden_test_path=repo_pointer(hidden),
        scaffold_level=meta.scaffold_level,
    )


def _probes_of(node_dir: Path) -> list[ProbeYaml]:
    """Probe node dari folder `probes/`. Dibaca ulang di sini (bukan lewat
    `assemble_node`) supaya node fixture yang tak lolos skema node tetap bisa
    diperiksa probenya kalau kebetulan punya."""
    probes_dir = node_dir / "probes"
    if not probes_dir.is_dir():
        return []
    out = []
    for path in sorted(probes_dir.glob("*.yaml")):
        out.append(ProbeYaml.model_validate(yaml.safe_load(path.read_text(encoding="utf-8"))))
    return out


def _domain_dirs(names: list[str]) -> list[Path]:
    root = DATA_DIR / "domains"
    if names:
        return [root / name for name in names]
    return sorted(p for p in root.iterdir() if p.is_dir())


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gerbang mutu authoring node.")
    parser.add_argument("domains", nargs="*", help="nama domain (default: semua)")
    parser.add_argument(
        "--skip-starter",
        action="store_true",
        help=(
            "lewati pemeriksaan NEGATIF (solusi kosong & starter harus gagal); "
            "kira-kira 3x lebih cepat. Untuk iterasi cepat saat mengarang."
        ),
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    # Output runner bisa memuat karakter di luar codepage konsol Windows (vitest
    # memakai U+276F). Tanpa ini, gerbang authoring MATI dengan UnicodeEncodeError
    # justru saat sedang melaporkan kegagalan — dan pesan yang paling dibutuhkan
    # adalah yang hilang.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    args = _parse_args(argv)
    total = 0
    failed = 0
    probes_total = 0
    probes_unverified = 0

    for domain_dir in _domain_dirs(args.domains):
        nodes_root = domain_dir / "nodes"
        if not nodes_root.is_dir():
            print(f"[SKIP] {domain_dir.name}: tak ada folder nodes")
            continue

        for node_dir in sorted(p for p in nodes_root.iterdir() if p.is_dir()):
            # Node fixture `_example` tak wajib punya 2 varian/probe — verifikasi
            # instance-nya tetap dijalankan lewat jalur yang sama.
            try:
                meta = assemble_node(node_dir).meta
            except NodeValidationError as e:
                if not node_dir.name.startswith("_"):
                    failed += 1
                    print(f"[INVALID] {domain_dir.name}/{node_dir.name}: {e}")
                    continue
                meta = _fixture_meta(node_dir)
                if meta is None:
                    continue

            grader = get_grader(meta.grader_type.value)
            node_ext = ""
            for variant_dir in sorted(p for p in (node_dir / "instances").iterdir() if p.is_dir()):
                instance = _instance_for(node_dir, node_dir.name, meta, variant_dir)
                reference = reference_solution_path(instance)
                if not reference.exists():
                    print(f"[SKIP] {node_dir.name}/{variant_dir.name}: tanpa reference_solution")
                    continue

                total += 1
                node_ext = node_ext or reference.suffix
                label = f"{domain_dir.name}/{node_dir.name}/{variant_dir.name}"

                starter = find_instance_file(variant_dir, "starter_code")
                triad = run_triad(
                    grader,
                    instance,
                    reference=reference.read_text(encoding="utf-8"),
                    starter=starter.read_text(encoding="utf-8") if starter else None,
                    check_negatives=not args.skip_starter,
                )
                if not triad.ok:
                    failed += 1
                    bad = triad.failing
                    tag = _TAG.get(bad.name, "FAIL") if bad else "FAIL"
                    if bad and bad.timed_out:
                        tag = "TIMEOUT"
                    took = f"  ({bad.duration_seconds:.2f}s)" if bad else ""
                    print(f"[{tag}] {label}{took}")
                    print(f"    {triad.reason}")
                    if bad and bad.output:
                        for line in bad.output.splitlines()[-15:]:
                            print(f"    {line}")
                    continue

                print(f"[PASS] {label}  ({_timing(triad)})")

            # Probe node ini — jawabannya DIJALANKAN, bukan dipercaya (M7 langkah 2).
            if not args.skip_starter and node_ext:
                for probe in _probes_of(node_dir):
                    probes_total += 1
                    verdict = verify_probe(probe, file_ext=node_ext)
                    plabel = f"{domain_dir.name}/{node_dir.name}/{probe.id}"
                    if verdict.skipped:
                        probes_unverified += 1
                        print(f"[PROBE-?] {plabel}  {verdict.reason}")
                    elif verdict.ok:
                        print(f"[PROBE-OK] {plabel}  ({verdict.duration_seconds:.2f}s)")
                    else:
                        failed += 1
                        print(f"[PROBE-SALAH] {plabel}  ({verdict.duration_seconds:.2f}s)")
                        print(f"    {verdict.reason}")
                        for line in verdict.output.splitlines()[-10:]:
                            print(f"    {line}")

    checks = (
        "referensi hijau" if args.skip_starter else "referensi hijau + kosong merah + starter merah"
    )
    print(f"\n{total - failed}/{total} instance lolos ({checks}).")
    if probes_total:
        print(f"{probes_total - probes_unverified}/{probes_total} probe terverifikasi eksekusi.")
    if probes_unverified:
        print(
            f"CATATAN: {probes_unverified} probe belum punya `snippet`/`expression` — "
            "kunci jawabannya belum pernah dibuktikan mesin (migrasi M7 langkah 6)."
        )
    if args.skip_starter:
        print(
            "CATATAN: pemeriksaan negatif & verifikasi probe dilewati "
            "— jangan commit atas dasar run ini."
        )
    return 1 if failed else 0


def _fixture_meta(node_dir: Path):
    """Meta seadanya untuk node fixture `_example`.

    Fixture harness sengaja tak memenuhi aturan node kurikulum (≥2 varian, ≥1 probe,
    `scaffold_level`) — ia cuma membuktikan pipa eksekusinya hidup. Field yang tak ada
    diisi default supaya ia tetap ikut diverifikasi tanpa melonggarkan skema node asli.
    """
    from app.services.node_schema import NodeYaml

    node_yaml = node_dir / "node.yaml"
    if not node_yaml.exists():
        return None
    raw = yaml.safe_load(node_yaml.read_text(encoding="utf-8"))
    raw.setdefault("scaffold_level", "L2")
    return NodeYaml.model_validate(raw)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
