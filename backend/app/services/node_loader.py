"""Muat node dari `data/` → validasi → upsert ke DB (§9 tables).

Kontrak (M2):
- File test **tetap di `data/`** (git), tidak masuk DB — DB hanya menyimpan
  *pointer* (`hidden_test_path`, relatif ke repo root). Memudahkan audit/diff Isyah.
- **Idempoten**: jalan ulang tak menggandakan (upsert by primary key; edge di-reset).
- Node dengan nama diawali `_` (mis. `_example`) di-skip: itu fixture harness,
  bukan node kurikulum.

Discovery folder (bentuk beku M2):
    nodes/<node_id>/node.yaml
    nodes/<node_id>/instances/<variant>/{prompt.md,starter_code.py,
                                         reference_solution.py,hidden_test.py}
    nodes/<node_id>/probes/<probe>.yaml
"""

from dataclasses import dataclass, field
from pathlib import Path

import yaml
from sqlmodel import Session, delete, select

from app.config import DATA_DIR, REPO_ROOT
from app.models import (
    ChallengeInstance,
    ComprehensionProbe,
    Domain,
    Edge,
    Node,
    ScheduleItem,
    SourceRef,
)
from app.services.node_schema import EdgeYaml, NodeYaml, ProbeYaml, SourceRefYaml

_REQUIRED_INSTANCE_FILES = (
    "prompt.md",
    "starter_code.py",
    "reference_solution.py",
    "hidden_test.py",
)
_MIN_INSTANCES = 2
_MIN_PROBES = 1


@dataclass
class InstanceBundle:
    variant_label: str
    dir: Path
    prompt: str
    starter_code: str
    hidden_test_path: str  # relatif ke repo root


@dataclass
class NodeBundle:
    meta: NodeYaml
    dir: Path
    instances: list[InstanceBundle] = field(default_factory=list)
    probes: list[ProbeYaml] = field(default_factory=list)


class NodeValidationError(ValueError):
    """Node/instance/probe cacat — pesan wajib bisa ditindaklanjuti."""


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _rel_to_repo(path: Path) -> str:
    """Path relatif ke repo root untuk disimpan sebagai pointer. Fallback ke absolut
    jika di luar repo (mis. folder tmp saat test)."""
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise NodeValidationError(f"{path}: YAML harus berupa mapping, dapat {type(data).__name__}")
    return data


# --------------------------------------------------------------------------- #
# Discovery + validasi (tanpa DB) — dipakai verify_nodes & loader.
# --------------------------------------------------------------------------- #
def assemble_node(node_dir: Path) -> NodeBundle:
    """Baca satu folder node, validasi struktur & skema. Raise NodeValidationError."""
    node_yaml = node_dir / "node.yaml"
    if not node_yaml.exists():
        raise NodeValidationError(f"{node_dir}: node.yaml tidak ada")
    try:
        meta = NodeYaml.model_validate(_load_yaml(node_yaml))
    except Exception as e:  # noqa: BLE001 — bungkus jadi pesan yang bisa ditindaklanjuti
        raise NodeValidationError(f"{node_yaml}: {e}") from e

    if meta.id != node_dir.name:
        raise NodeValidationError(
            f"{node_yaml}: id {meta.id!r} tidak cocok dengan nama folder {node_dir.name!r}"
        )

    # Instances
    instances_dir = node_dir / "instances"
    instances: list[InstanceBundle] = []
    if instances_dir.is_dir():
        for variant_dir in sorted(p for p in instances_dir.iterdir() if p.is_dir()):
            missing = [f for f in _REQUIRED_INSTANCE_FILES if not (variant_dir / f).exists()]
            if missing:
                raise NodeValidationError(
                    f"{variant_dir}: file instance kurang: {', '.join(missing)}"
                )
            hidden_test = variant_dir / "hidden_test.py"
            instances.append(
                InstanceBundle(
                    variant_label=variant_dir.name,
                    dir=variant_dir,
                    prompt=_read(variant_dir / "prompt.md"),
                    starter_code=_read(variant_dir / "starter_code.py"),
                    hidden_test_path=_rel_to_repo(hidden_test),
                )
            )
    if len(instances) < _MIN_INSTANCES:
        raise NodeValidationError(
            f"{node_dir}: butuh >= {_MIN_INSTANCES} varian instance (transfer, bukan hafalan), "
            f"dapat {len(instances)}"
        )

    # Probes
    probes_dir = node_dir / "probes"
    probes: list[ProbeYaml] = []
    if probes_dir.is_dir():
        for probe_file in sorted(probes_dir.glob("*.yaml")):
            try:
                probe = ProbeYaml.model_validate(_load_yaml(probe_file))
            except Exception as e:  # noqa: BLE001
                raise NodeValidationError(f"{probe_file}: {e}") from e
            if probe.node_id != meta.id:
                raise NodeValidationError(
                    f"{probe_file}: node_id {probe.node_id!r} != node {meta.id!r}"
                )
            probes.append(probe)
    if len(probes) < _MIN_PROBES:
        raise NodeValidationError(
            f"{node_dir}: butuh >= {_MIN_PROBES} comprehension probe deterministik, "
            f"dapat {len(probes)}"
        )

    return NodeBundle(meta=meta, dir=node_dir, instances=instances, probes=probes)


def discover_node_dirs(domain_dir: Path) -> list[Path]:
    """Folder node kurikulum (skip nama diawali `_`)."""
    nodes_root = domain_dir / "nodes"
    if not nodes_root.is_dir():
        return []
    return sorted(
        p for p in nodes_root.iterdir() if p.is_dir() and not p.name.startswith("_")
    )


def load_sources(sources_path: Path) -> list[SourceRefYaml]:
    raw = _load_yaml(sources_path).get("sources", [])
    return [SourceRefYaml.model_validate(s) for s in raw]


def load_edges(edges_path: Path) -> list[EdgeYaml]:
    if not edges_path.exists():
        return []
    raw = _load_yaml(edges_path).get("edges") or []
    return [EdgeYaml.model_validate(e) for e in raw]


# --------------------------------------------------------------------------- #
# Upsert ke DB
# --------------------------------------------------------------------------- #
@dataclass
class LoadReport:
    domains: int = 0
    sources: int = 0
    nodes: int = 0
    instances: int = 0
    probes: int = 0
    edges: int = 0


def load_domain_into_db(
    session: Session,
    domain_dir: Path,
    data_dir: Path = DATA_DIR,
) -> LoadReport:
    """Muat satu domain (mis. `data/domains/fastapi`) ke DB secara idempoten."""
    report = LoadReport()

    # Domain
    domain_meta = _load_yaml(domain_dir / "domain.yaml")
    session.merge(
        Domain(
            id=domain_meta["id"],
            name=domain_meta["name"],
            status=domain_meta.get("status", "draft"),
        )
    )
    report.domains += 1

    # SourceRef (global untuk semua domain)
    for src in load_sources(data_dir / "sources.yaml"):
        session.merge(
            SourceRef(
                id=src.id,
                type=src.type.value,
                citation=src.citation,
                url_or_locator=src.url_or_locator,
            )
        )
        report.sources += 1

    known_source_ids = {s.id for s in load_sources(data_dir / "sources.yaml")}

    # Nodes + instances + probes
    node_ids: set[str] = set()
    for node_dir in discover_node_dirs(domain_dir):
        bundle = assemble_node(node_dir)
        meta = bundle.meta

        for ref in meta.source_refs:
            if ref not in known_source_ids:
                raise NodeValidationError(
                    f"{node_dir}: source_ref {ref!r} tidak ada di sources.yaml"
                )

        session.merge(
            Node(
                id=meta.id,
                domain_id=meta.domain_id,
                concept=meta.concept,
                description=meta.description,
                grader_type=meta.grader_type.value,
                source_refs=meta.source_refs,
                estimated_minutes=meta.estimated_minutes,
                timebox_seconds=meta.timebox_seconds,
                status_default=meta.status_default.value,
            )
        )
        node_ids.add(meta.id)
        report.nodes += 1

        # Seed ScheduleItem HANYA jika belum ada — reload node tak boleh menghapus
        # progres (status acquired) yang sudah diperoleh Bryant.
        if session.get(ScheduleItem, meta.id) is None:
            session.add(ScheduleItem(node_id=meta.id, status=meta.status_default.value))

        for inst in bundle.instances:
            session.merge(
                ChallengeInstance(
                    id=f"{meta.id}__{inst.variant_label}",
                    node_id=meta.id,
                    variant_label=inst.variant_label,
                    prompt=inst.prompt,
                    starter_code=inst.starter_code,
                    signature_contract=meta.signature_contract,
                    hidden_test_path=inst.hidden_test_path,
                    scaffold_level=meta.scaffold_level,
                )
            )
            report.instances += 1

        for probe in bundle.probes:
            session.merge(
                ComprehensionProbe(
                    id=probe.id,
                    node_id=probe.node_id,
                    type=probe.type.value,
                    question=probe.question,
                    options=probe.options,
                    correct_answer=probe.correct_answer,
                )
            )
            report.probes += 1

    # Edges: reset lalu insert (idempoten; PK autoincrement tak bisa merge by pasangan).
    edges = load_edges(domain_dir / "edges.yaml")
    session.exec(delete(Edge))
    for e in edges:
        for endpoint in (e.from_, e.to):
            if endpoint not in node_ids:
                raise NodeValidationError(
                    f"edges.yaml: node {endpoint!r} tidak dikenal (edge {e.from_} -> {e.to})"
                )
        if e.source_ref_id and e.source_ref_id not in known_source_ids:
            raise NodeValidationError(
                f"edges.yaml: source_ref_id {e.source_ref_id!r} tidak ada di sources.yaml"
            )
        session.add(
            Edge(
                from_node_id=e.from_,
                to_node_id=e.to,
                type=e.type.value,
                source_ref_id=e.source_ref_id,
                note=e.note,
            )
        )
        report.edges += 1

    session.commit()
    return report


def existing_node_count(session: Session) -> int:
    return len(session.exec(select(Node)).all())
