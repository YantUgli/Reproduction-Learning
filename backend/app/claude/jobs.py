"""Orkestrasi job Claude Code: trigger → jalankan → validasi → GERBANG MESIN → promosi.

Alur satu job (semuanya di latar, TAK PERNAH memblokir request UI):

    pending  --execute_job()-->  running  --runner-->  artifact di direktori job
                                              |
                       contracts.py (skema) --+--> tak lolos --> failed
                       grounding kutipan R3 --+--> tak lolos --> failed
                                              |
                       gerbang R4: TRIAD eksekusi + probe dijalankan
                                              |
                                     merah --+--> rejected (tak pernah masuk sistem)
                                              |
                                            ready --> PROMOSI OTOMATIS ke data/ + DB

Sampai M6 alurnya berhenti di `ready` dan menunggu klik Isyah. Sejak §7 2026-08-31
approve manusia bukan lagi gerbang blokir: artifact yang lolos SELURUH gerbang mesin
langsung masuk sistem, dan peninjauan manusia pindah ke belakang (meja audit +
tombol pensiun di `/authoring`). Alasan lengkap + batasnya ada di entri log itu;
ringkasnya: peran manusia di sini tak pernah gerbang *mastery* — verdict selalu
eksekusi kode (§1.2) — melainkan gerbang kualitas konten, dan node buruk memakan
waktu Bryant sedangkan verdict buruk menanam keyakinan palsu.

Matikan lewat `CLAUDE_AUTO_PROMOTE=0` → alurnya kembali berhenti di `ready`.

Beda `failed` vs `rejected` disengaja: `failed` = tak berhasil memproduksi artifact
(CLI mati, timeout, format salah); `rejected` = artifact ada tapi tak lolos mutu.
Keduanya sama-sama tak masuk sistem, tapi yang kedua layak dibaca sebagai sinyal
kualitas prompt/model, bukan sinyal infrastruktur.
"""

import json
import re
from pathlib import Path

from sqlmodel import Session, select

from app.claude import contracts
from app.claude.artifacts import Job, JobStatus, Role, new_job, read_job, save_job, set_status
from app.claude.prompts import render
from app.claude.runner import ClaudeRunner, CliClaudeRunner
from app.config import (
    CLAUDE_AUTO_PROMOTE,
    CLAUDE_MAX_RETRIES,
    CLAUDE_TIMEOUT_SECONDS,
    DATA_DIR,
    EXPLANATION_MAX_CHARS,
    REPO_ROOT,
)
from app.graders import get_grader
from app.graders.files import repo_pointer
from app.models import Attempt, ChallengeInstance, Node
from app.services import grounding, quality_gate
from app.services.node_loader import find_instance_file, load_sources
from app.services.probe_verifier import verify_probe
from app.services.quality_gate import run_triad


class JobError(ValueError):
    """Permintaan job tak bisa dibentuk (node tak ada, konteks kurang, dll)."""


# --------------------------------------------------------------------------- #
# Trigger — membentuk prompt & direktori job. TIDAK memanggil Claude Code.
# --------------------------------------------------------------------------- #
def trigger_r3(session: Session, *, node_id: str, attempt_id: int | None = None) -> Job:
    """Materi just-in-time untuk satu attempt yang GAGAL."""
    node = _node(session, node_id)
    attempt = _failed_attempt(session, node_id, attempt_id)
    instance = (
        session.get(ChallengeInstance, attempt.instance_id) if attempt.instance_id else None
    ) or _first_instance(session, node_id)

    sources = load_sources(DATA_DIR / "sources.yaml")
    known = "\n".join(f"- `{s.id}` — {s.citation}" for s in sources)

    prompt = render(
        "r3_explanation",
        {
            "node_id": node.id,
            "concept": node.concept,
            "signature_contract": instance.signature_contract if instance else "",
            "prompt_md": instance.prompt if instance else "",
            "submitted_code": attempt.submitted_code or "(kosong)",
            "test_output": attempt.test_output or "(tak ada output)",
            "known_sources": known,
            "max_chars": str(EXPLANATION_MAX_CHARS),
        },
    )
    job = new_job(
        Role.r3_explanation,
        request={"node_id": node.id, "attempt_id": attempt.id},
        prompt_version=prompt.version,
    )
    (job.dir / "prompt.md").write_text(prompt.text, encoding="utf-8")
    return job


def trigger_r4(session: Session, *, node_id: str, variant_label: str | None = None) -> Job:
    """Varian soal baru untuk satu node (menutup 'varian menipis', M4)."""
    node = _node(session, node_id)
    instances = _instances(session, node_id)
    if not instances:
        raise JobError(f"node {node_id!r} belum punya satu pun instance untuk dicontoh")
    example = instances[0]
    example_dir = (REPO_ROOT / example.hidden_test_path).parent

    label = variant_label or _next_variant_label([i.variant_label for i in instances])
    probe_id = _next_probe_id(session, node_id)

    prompt = render(
        "r4_challenge",
        {
            "node_id": node.id,
            "concept": node.concept,
            "signature_contract": example.signature_contract,
            "variant_label": label,
            "existing_variants": ", ".join(i.variant_label for i in instances),
            "example_prompt": example.prompt,
            "example_reference": _read_or_empty(example_dir / "reference_solution.py"),
            "example_test": _read_or_empty(example_dir / "hidden_test.py"),
            "probe_id": probe_id,
        },
    )
    job = new_job(
        Role.r4_challenge,
        request={"node_id": node.id, "variant_label": label, "probe_id": probe_id},
        prompt_version=prompt.version,
    )
    (job.dir / "prompt.md").write_text(prompt.text, encoding="utf-8")
    return job


def trigger_r2(session: Session, *, repo_path: str, node_ids: list[str] | None = None) -> Job:
    """Bukti codebase → hipotesis (tak pernah verdict)."""
    path = Path(repo_path)
    if not path.is_dir():
        raise JobError(f"repo_path bukan direktori yang ada: {repo_path}")

    nodes = session.exec(select(Node)).all()
    if node_ids:
        wanted = set(node_ids)
        nodes = [n for n in nodes if n.id in wanted]
    if not nodes:
        raise JobError("tak ada node untuk dianalisis")

    prompt = render(
        "r2_hypotheses",
        {
            "repo_path": str(path),
            "node_list": "\n".join(f"- `{n.id}` · {n.concept}" for n in sorted(nodes, key=_by_id)),
        },
    )
    job = new_job(
        Role.r2_hypotheses,
        request={"repo_path": str(path), "node_ids": [n.id for n in nodes]},
        prompt_version=prompt.version,
    )
    (job.dir / "prompt.md").write_text(prompt.text, encoding="utf-8")
    return job


# --------------------------------------------------------------------------- #
# Eksekusi — dipanggil di latar (BackgroundTasks / thread), bukan dari handler UI.
# --------------------------------------------------------------------------- #
def execute_job(
    job_id: str,
    session: Session,
    *,
    runner: ClaudeRunner | None = None,
) -> Job:
    job = read_job(job_id)
    if job.status not in (JobStatus.pending.value, JobStatus.failed.value):
        raise JobError(
            f"job {job_id} berstatus {job.status}, hanya pending/failed yang bisa dijalankan"
        )

    runner = runner or CliClaudeRunner(extra_dirs=_extra_dirs_for(job))
    prompt = (job.dir / "prompt.md").read_text(encoding="utf-8")

    last_error = ""
    for _ in range(1 + CLAUDE_MAX_RETRIES):
        job.attempts += 1
        set_status(job, JobStatus.running)

        result = runner.run(job.dir, prompt, CLAUDE_TIMEOUT_SECONDS)
        (job.dir / "stdout.log").write_text(result.stdout, encoding="utf-8")
        (job.dir / "stderr.log").write_text(result.stderr, encoding="utf-8")
        if not result.ok:
            last_error = result.error or "Claude Code gagal tanpa pesan"
            continue

        try:
            summary = _validate(job, session)
        except contracts.ArtifactError as e:
            last_error = str(e)
            continue

        if job.role == Role.r4_challenge.value:
            gate = _gate_r4(job, session)
            job.gate = gate
            if not gate["passed"]:
                last_error = gate["reason"]
                # Artifact ADA tapi tak lolos mutu → ditolak otomatis, tak ke Isyah.
                save_job(job)
                continue

        job.summary = summary
        job.error = ""
        ready = set_status(job, JobStatus.ready)

        # PROMOSI OTOMATIS (M7 langkah 9). Sampai M6 alurnya berhenti di sini dan
        # menunggu klik Isyah; sejak §7 2026-08-31 artifact yang lolos SELURUH gerbang
        # mesin langsung masuk sistem, dan peninjauan manusia pindah ke belakang
        # (meja audit + tombol pensiun di `/authoring`).
        #
        # Diimpor di dalam fungsi: `review_queue` mengimpor `contracts` & `node_loader`
        # seperti modul ini, dan impor tingkat-modul membuat keduanya saling menunggu.
        # Materi yang groundingnya belum bisa diperiksa DITAHAN di `ready`: ia boleh
        # ada, tapi tak boleh sampai ke Bryant tanpa ada yang memeriksanya — entah
        # mesin (snapshot sumbernya dibuat) atau manusia (approve manual).
        if summary.get("grounding_unverified"):
            job.error = (
                "ditahan: grounding belum bisa diperiksa — " + summary["grounding_unverified"]
            )
            save_job(job)
            return read_job(job.id)

        if CLAUDE_AUTO_PROMOTE:
            from app.claude import review_queue

            try:
                promotion = review_queue.promote(session, job.id)
                job = read_job(job.id)
                job.summary = {**job.summary, "auto_promoted": promotion.written_paths}
                save_job(job)
            except review_queue.PromotionError as e:
                # Gerbang lolos tapi promosi tetap gagal (mis. label varian bentrok).
                # Artifact tetap `ready` — bisa dipromosikan manual setelah dibereskan.
                job = read_job(job.id)
                job.error = f"lolos gerbang tapi promosi otomatis gagal: {e}"
                save_job(job)
            return read_job(job.id)
        return ready

    # Semua percobaan habis.
    gate_failed = job.gate is not None and not job.gate.get("passed", False)
    return set_status(
        job,
        JobStatus.rejected if gate_failed else JobStatus.failed,
        error=last_error,
    )


def _validate(job: Job, session: Session) -> dict:
    """Validasi artifact sesuai peran. Raise ArtifactError bila tak lolos."""
    node_id = job.request.get("node_id", "")

    if job.role == Role.r3_explanation.value:
        artifact = contracts.load_explanation(job.dir, node_id)
        known = {s.id for s in load_sources(DATA_DIR / "sources.yaml")}
        contracts.check_citations_known(artifact, known)
        # Sitasi menunjuk sumber yang ADA belum berarti klaimnya ditopang sumber itu.
        # Tanpa manusia di jalur (M7), kutipannya harus benar-benar dicocokkan.
        problems = grounding.check_quotes(artifact.citations)
        pesan = "; ".join(str(p) for p in problems)
        if problems and not grounding.only_missing_snapshots(problems):
            raise contracts.ArtifactError("sitasi tak lolos grounding verbatim: " + pesan)
        return {
            "explanation_chars": len(artifact.explanation_md),
            "citations": len(artifact.citations),
            "has_worked_example": bool(artifact.worked_example.strip()),
            # "Belum bisa diverifikasi" bukan "terverifikasi salah". Sumber yang belum
            # di-snapshot menahan PROMOSI (materi tak sampai ke Bryant sendirinya),
            # tapi tak menghukum artifact-nya sebagai cacat — kekurangannya di pihak
            # kita, dan menolaknya cuma menyuruh model mengulang kerja yang sudah benar.
            "grounding_unverified": pesan if problems else "",
        }

    if job.role == Role.r4_challenge.value:
        artifact = contracts.load_challenge(job.dir, node_id)
        expected = job.request.get("variant_label")
        if expected and artifact.variant_label != expected:
            raise contracts.ArtifactError(
                f"variant_label {artifact.variant_label!r} != yang diminta {expected!r}"
            )
        return {
            "variant_label": artifact.variant_label,
            "probe_id": artifact.probe.id,
            "probe_options": len(artifact.probe.options),
        }

    artifact = contracts.load_hypotheses(job.dir)
    known_nodes = {n.id for n in session.exec(select(Node)).all()}
    contracts.check_nodes_known(artifact, known_nodes)
    return {
        "hypotheses": len(artifact.hypotheses),
        "nodes": sorted({h.node_id for h in artifact.hypotheses}),
        # Daftar kosong itu sah (lihat contracts.HypothesesArtifact) — catatannya
        # dinaikkan ke ringkasan supaya Isyah tahu KENAPA tanpa membuka artifact.
        "note": artifact.note,
    }


def _gate_r4(job: Job, session: Session) -> dict:
    """GATE OTOMATIS (M5 langkah 5, dinaikkan jadi TRIAD di M7 langkah 1).

    Soal buatan AI diuji SEBELUM manusia melihatnya, dengan aturan yang sama persis
    dengan gerbang authoring tulisan tangan (`scripts/verify_nodes.py`) — keduanya
    memanggil `services/quality_gate.run_triad`. Aturan yang hidup di dua salinan
    cepat atau lambat akan berbeda, dan yang lebih longgar yang akan dipakai.

    Dinilai lewat grader NODE-nya (`get_grader(node.grader_type)`), bukan lewat
    `SubprocessExecutor` langsung. Versi M5 memanggil executor Python apa adanya dan
    membaca `reference_solution.py` secara literal — artinya gate ini diam-diam hanya
    bekerja untuk domain Python, dan node React/ML lolos tanpa pernah benar-benar
    tergerbang. Timeout pun sekarang milik grader (React butuh 120 detik, bukan 30).
    """
    node = _node(session, job.request.get("node_id", ""))
    grader = get_grader(node.grader_type)

    variant = job.dir / "variant"
    hidden = _find_variant_file(variant, "hidden_test")
    reference = _find_variant_file(variant, "reference_solution").read_text(encoding="utf-8")
    starter_file = find_instance_file(variant, "starter_code")

    instance = ChallengeInstance(
        id=f"{node.id}__gate_{job.id}",
        node_id=node.id,
        variant_label=job.request.get("variant_label", "gate"),
        prompt="",
        starter_code="",
        signature_contract="",
        hidden_test_path=repo_pointer(hidden),
        scaffold_level="L2",
    )

    triad = run_triad(
        grader,
        instance,
        reference=reference,
        starter=starter_file.read_text(encoding="utf-8") if starter_file else None,
    )

    def _passed(name: str) -> bool | None:
        check = triad.check(name)
        return None if check is None or check.skipped else check.test_passed

    failing = triad.failing
    gate = {
        "passed": triad.ok,
        "reason": triad.reason,
        "reference_passed": _passed(quality_gate.REFERENCE),
        "empty_passed": _passed(quality_gate.EMPTY),
        "starter_passed": _passed(quality_gate.STARTER),
        "output": failing.output if failing else (triad.check(quality_gate.REFERENCE).output),
    }
    if not triad.ok:
        return gate

    # Probe buatan AI: kunci jawabannya DIJALANKAN, tak cukup "ada di options".
    # Sejak M7 tak ada manusia yang wajib membacanya, jadi satu-satunya yang berdiri
    # antara probe berkunci salah dan Bryant adalah pemeriksaan ini.
    artifact = contracts.load_challenge(job.dir, node.id)
    probe = artifact.probe

    # Di sini gate MESIN sengaja lebih ketat daripada gerbang authoring manusia.
    # Probe tulisan tangan boleh berupa prosa dengan `expected_value` sebagai klaim
    # terukurnya — jembatan prosa->nilai ditulis manusia dan bisa dibaca ulang.
    # Probe buatan AI tak punya penulis yang bisa ditanya, jadi jawabannya WAJIB
    # berupa nilai yang persis keluar dari eksekusi: tak ada jembatan, tak ada celah.
    if not probe.snippet.strip():
        gate["passed"] = False
        gate["reason"] = (
            "probe tanpa `snippet`/`expression` — kunci jawabannya tak bisa dibuktikan "
            "mesin, dan tak ada manusia di jalur ini (§7 2026-08-31)"
        )
        return gate
    if probe.expected_value.strip():
        gate["passed"] = False
        gate["reason"] = (
            "probe buatan AI memakai `expected_value` (jawaban berupa prosa) — "
            "jawabannya harus berupa nilai yang persis dihasilkan eksekusi"
        )
        return gate

    verdict = verify_probe(probe, file_ext=artifact.file_ext)
    gate["probe_verified"] = verdict.ok and not verdict.skipped
    if not verdict.ok:
        gate["passed"] = False
        gate["reason"] = f"probe ditolak: {verdict.reason}"
        gate["output"] = verdict.output
    return gate


def _find_variant_file(variant_dir: Path, stem: str) -> Path:
    """Berkas instance dari NAMA DASAR — `.py` (FastAPI/ML) maupun `.jsx` (React)."""
    found = find_instance_file(variant_dir, stem)
    if found is None:
        raise JobError(f"artifact tak punya {stem}.* di variant/ (job {variant_dir.parent.name})")
    return found


# --------------------------------------------------------------------------- #
# Helper
# --------------------------------------------------------------------------- #
def _by_id(node: Node) -> str:
    return node.id


def _node(session: Session, node_id: str) -> Node:
    node = session.get(Node, node_id)
    if node is None:
        raise JobError(f"node tak ditemukan: {node_id!r}")
    return node


def _instances(session: Session, node_id: str) -> list[ChallengeInstance]:
    rows = session.exec(select(ChallengeInstance).where(ChallengeInstance.node_id == node_id)).all()
    return sorted(rows, key=lambda i: i.variant_label)


def _first_instance(session: Session, node_id: str) -> ChallengeInstance | None:
    rows = _instances(session, node_id)
    return rows[0] if rows else None


def _failed_attempt(session: Session, node_id: str, attempt_id: int | None) -> Attempt:
    """R3 hanya masuk akal untuk attempt yang GAGAL (§10: input = attempt gagal)."""
    if attempt_id is not None:
        attempt = session.get(Attempt, attempt_id)
        if attempt is None or attempt.node_id != node_id:
            raise JobError(f"attempt {attempt_id} bukan milik node {node_id!r}")
    else:
        attempt = session.exec(
            select(Attempt)
            .where(Attempt.node_id == node_id, Attempt.result == "fail")
            .order_by(Attempt.id.desc())
        ).first()
        if attempt is None:
            raise JobError(
                f"node {node_id!r} belum punya attempt yang gagal — materi just-in-time "
                "hanya dibuat untuk kegagalan nyata, bukan untuk dibaca lebih dulu"
            )
    if attempt.result != "fail":
        raise JobError(f"attempt {attempt.id} tidak gagal — R3 hanya untuk attempt gagal")
    return attempt


def _next_variant_label(existing: list[str]) -> str:
    used = set(existing)
    for letter in "abcdefghijklmnopqrstuvwxyz":
        label = f"variant_{letter}"
        if label not in used:
            return label
    return f"variant_{len(used) + 1}"


def _next_probe_id(session: Session, node_id: str) -> str:
    """Ikuti konvensi tulisan tangan: `n006_probe_02`, bukan nama node penuh."""
    from app.models import ComprehensionProbe

    count = len(
        session.exec(select(ComprehensionProbe).where(ComprehensionProbe.node_id == node_id)).all()
    )
    match = re.match(r"^(n\d+)", node_id)
    prefix = match.group(1) if match else node_id
    return f"{prefix}_probe_{count + 1:02d}"


def _read_or_empty(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _extra_dirs_for(job: Job) -> tuple[str, ...]:
    """R2 perlu MEMBACA repo Bryant; peran lain tak butuh akses di luar job dir."""
    repo_path = job.request.get("repo_path")
    return (repo_path,) if job.role == Role.r2_hypotheses.value and repo_path else ()


def _tail(text: str, lines: int = 20) -> str:
    return "\n".join(text.strip().splitlines()[-lines:])


def job_artifact_files(job: Job) -> dict[str, str]:
    """Isi artifact untuk ditampilkan di UI review (teks apa adanya)."""
    out: dict[str, str] = {}
    for path in sorted(job.dir.rglob("*")):
        if not path.is_file() or path.name in {
            "job.json",
            "stdout.log",
            "stderr.log",
            "command.log",
        }:
            continue
        rel = path.relative_to(job.dir).as_posix()
        try:
            out[rel] = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            out[rel] = "(berkas biner — tak ditampilkan)"
    return out


def write_artifact_files(job: Job, files: dict[str, str]) -> None:
    """Dipakai test & mode offline: menaruh artifact seolah Claude Code yang menulis."""
    for rel, content in files.items():
        target = job.dir / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")


def dump_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
