#!/usr/bin/env python3
"""GERBANG MUTU AUTHORING (M2 langkah 2, diperluas M6).

Untuk SETIAP instance node di SETIAP domain, DUA pemeriksaan — keduanya eksekusi kode,
lewat grader yang sama dengan yang dipakai aplikasi (`grader_type` node → registry):

1. **Hidden test HIJAU di `reference_solution`.** Penegak aturan PRD §10 R4. Test yang
   belum pernah dibuktikan hijau bukan test, cuma niat.
2. **Hidden test MERAH di `starter_code`.** Kalau kerangka L2 sudah lolos apa adanya,
   tantangannya kosong: Bryant bisa menekan "Jalankan" tanpa memproduksi apa pun dan
   sistem akan mencatatnya sebagai `reproduce-without-AI` yang berhasil. Node seperti
   itu tak cuma tak berguna — ia MEMALSUKAN sinyal inti produk ini.

Node yang gagal salah satunya TIDAK BOLEH di-commit.

Kenapa lewat grader, bukan memanggil Executor langsung (seperti versi M2): sejak ada
domain kedua, "cara menjalankan test" berbeda per grader (pytest vs vitest, file
tambahan seperti `expected.json`). Kalau skrip ini punya salinan aturannya sendiri,
ia akan memverifikasi sesuatu yang bukan persis yang dinilai saat Bryant submit.

Pemakaian:
    python scripts/verify_nodes.py [domain ...] [--skip-starter]
Exit 0 = semua hijau; 1 = ada yang merah/timeout/starter-lolos.
"""

import argparse
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "backend"))

from app.config import DATA_DIR  # noqa: E402
from app.graders import get_grader  # noqa: E402
from app.graders.files import reference_solution_path  # noqa: E402
from app.models import ChallengeInstance  # noqa: E402
from app.services.node_loader import (  # noqa: E402
    NodeValidationError,
    assemble_node,
    find_instance_file,
)


def _pointer(path: Path) -> str:
    """Pointer hidden test seperti yang disimpan loader: relatif ke repo bila bisa,
    absolut bila `data/` sedang ditunjuk ke luar repo (mis. salinan untuk uji coba)."""
    try:
        return path.relative_to(_REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


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
        hidden_test_path=_pointer(hidden),
        scaffold_level=meta.scaffold_level,
    )


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
            "lewati pemeriksaan 'starter harus gagal' (kira-kira 2x lebih cepat). "
            "Untuk iterasi cepat saat mengarang — JANGAN dipakai sebelum commit."
        ),
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = _parse_args(argv)
    total = 0
    failed = 0

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
            for variant_dir in sorted(p for p in (node_dir / "instances").iterdir() if p.is_dir()):
                instance = _instance_for(node_dir, node_dir.name, meta, variant_dir)
                reference = reference_solution_path(instance)
                if not reference.exists():
                    print(f"[SKIP] {node_dir.name}/{variant_dir.name}: tanpa reference_solution")
                    continue

                total += 1
                label = f"{domain_dir.name}/{node_dir.name}/{variant_dir.name}"

                # 1. Solusi referensi WAJIB hijau.
                result = grader.grade(instance, reference.read_text(encoding="utf-8"))
                if not result.passed:
                    failed += 1
                    verdict = "TIMEOUT" if result.timed_out else "FAIL"
                    print(f"[{verdict}] {label}  ({result.duration_seconds:.2f}s)")
                    for line in result.test_output.strip().splitlines()[-15:]:
                        print(f"    {line}")
                    continue

                # 2. Kerangka WAJIB merah. Dilewati kalau tak ada starter_code —
                #    node fixture boleh tak punya, node kurikulum ditolak loader.
                starter = find_instance_file(variant_dir, "starter_code")
                if args.skip_starter or starter is None:
                    note = "" if starter is not None else "  (tanpa starter_code)"
                    print(f"[PASS] {label}  ({result.duration_seconds:.2f}s){note}")
                    continue

                starter_run = grader.grade(instance, starter.read_text(encoding="utf-8"))
                if starter_run.passed:
                    failed += 1
                    print(
                        f"[STARTER-LOLOS] {label}  ({starter_run.duration_seconds:.2f}s)\n"
                        "    starter_code sudah melewati hidden test — tantangannya kosong.\n"
                        "    Kosongkan bagian inti kerangka, atau perketat hidden test."
                    )
                    continue

                print(
                    f"[PASS] {label}  "
                    f"(referensi {result.duration_seconds:.2f}s | "
                    f"starter gagal {starter_run.duration_seconds:.2f}s)"
                )

    checks = "referensi hijau" if args.skip_starter else "referensi hijau + starter merah"
    print(f"\n{total - failed}/{total} instance lolos ({checks}).")
    if args.skip_starter:
        print("CATATAN: pemeriksaan starter dilewati — jangan commit atas dasar run ini.")
    return 1 if failed else 0


def _fixture_meta(node_dir: Path):
    """Meta seadanya untuk node fixture `_example`.

    Fixture harness sengaja tak memenuhi aturan node kurikulum (≥2 varian, ≥1 probe,
    `scaffold_level`) — ia cuma membuktikan pipa eksekusinya hidup. Field yang tak ada
    diisi default supaya ia tetap ikut diverifikasi tanpa melonggarkan skema node asli.
    """
    import yaml

    from app.services.node_schema import NodeYaml

    node_yaml = node_dir / "node.yaml"
    if not node_yaml.exists():
        return None
    raw = yaml.safe_load(node_yaml.read_text(encoding="utf-8"))
    raw.setdefault("scaffold_level", "L2")
    return NodeYaml.model_validate(raw)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
