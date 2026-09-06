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

import yaml
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


#: `n013_depends_shared_params` -> ("n", "013"). Dipakai untuk MEWARISI konvensi
#: penamaan domain, bukan menciptakan konvensi baru per node.
_NODE_ID_RE = re.compile(r"^([a-z])(\d+)_")


def _domain_nodes(session: Session, domain_id: str) -> list[Node]:
    nodes = session.exec(select(Node).where(Node.domain_id == domain_id)).all()
    return sorted(nodes, key=_by_id)


def _next_node_id(existing: list[Node], slug: str) -> str:
    """`[n013…]` + "get-route-json" -> `n014_get_route_json`.

    Prefix & lebar angka DIWARISI dari node yang sudah ada di domain itu, tidak
    di-hardcode: domain ML memakai `m…`, React `r…`, dan menebaknya di sini berarti
    L4 melahirkan node dengan konvensi penamaan yang bercabang diam-diam.
    """
    prefix, width, top = "n", 3, 0
    for node in existing:
        m = _NODE_ID_RE.match(node.id)
        if m:
            prefix, width = m.group(1), len(m.group(2))
            top = max(top, int(m.group(2)))
    return f"{prefix}{top + 1:0{width}d}_{slug.replace('-', '_')}"


def _probe_id_for(node_id: str, urutan: int) -> str:
    """Konvensi tulisan tangan: `n014_probe_01` / `m004_probe_01`, bukan nama node penuh."""
    m = _NODE_ID_RE.match(node_id)
    prefix = node_id[: m.end() - 1] if m else node_id
    return f"{prefix}_probe_{urutan:02d}"


def _library_material(library_file: str, source_ref_id: str) -> str:
    """Validasi berkas materi Library asal node. Kembalikan path POSIX relatif-repo.

    Tiga pemeriksaan, semuanya murah dan semuanya menutup kesalahan yang mahal:
    berkasnya benar-benar di `library/`, BELUM tertaut node lain, dan berdiri di
    sumber yang SAMA dengan node yang akan lahir (L4 KUNCI 6) — itu yang membuat
    jembatannya bukan sekadar nama berkas yang kebetulan mirip.
    """
    path = (REPO_ROOT / library_file).resolve()
    # Sengaja diturunkan dari REPO_ROOT modul ini, BUKAN `config.LIBRARY_DIR` (L5):
    # seluruh fungsi ini berjangkar di REPO_ROOT (lihat `relative_to` di bawah), dan
    # test L4 mem-patch `jobs.REPO_ROOT` ke tmp. Memakai LIBRARY_DIR di sini akan
    # membuat pemeriksaan containment mengabaikan root yang sedang di-patch.
    library_root = (REPO_ROOT / "library").resolve()
    if not path.is_file() or library_root not in path.parents:
        raise JobError(f"library_file {library_file!r} bukan berkas di dalam library/")
    text = path.read_text(encoding="utf-8")
    fm = yaml.safe_load(text.split("---", 2)[1]) if text.startswith("---") else None
    if not isinstance(fm, dict):
        raise JobError(f"{library_file}: frontmatter tak terbaca")
    if fm.get("node_ids"):
        raise JobError(f"{library_file}: sudah tertaut ke node {fm['node_ids']}")
    if source_ref_id not in (fm.get("source_refs") or []):
        raise JobError(
            f"{library_file}: source_refs-nya tak memuat {source_ref_id!r} — node dan "
            "materinya harus berdiri di sumber yang sama"
        )
    return path.relative_to(REPO_ROOT).as_posix()


def trigger_r4_node(
    session: Session,
    *,
    library_file: str,
    slug: str,
    domain_id: str,
    concept: str,
    source_ref_id: str,
    prereq_node_id: str | None = None,
) -> Job:
    """NODE BARU dari satu entri peta Library (L4).

    Identitas node — id, domain, grader, label varian, id probe, ekstensi berkas —
    dihitung DI SINI dari isi `data/`, lalu DIPAKSAKAN ke artifact
    (`contracts._require_identity`). Yang boleh dikarang model hanyalah ISI: prompt,
    kode, test, probe. Penamaan yang dikarang model adalah cara termurah membuat
    kurikulum berantakan tanpa satu pun gerbang berbunyi.

    `grader_type` diwarisi dari node contoh di domain yang sama, bukan dari tabel
    domain->grader baru: domain tanpa satu pun node tak bisa jadi target L4 — sekaligus
    alasan mengapa "domain baru" (= grader baru, pekerjaan gaya M6) di luar ruang lingkup.
    """
    if not re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", slug):
        raise JobError(f"slug harus kebab-case: {slug!r}")

    nodes = _domain_nodes(session, domain_id)
    if not nodes:
        raise JobError(
            f"domain {domain_id!r} belum punya satu pun node contoh — domain baru butuh "
            "grader baru (pekerjaan gaya M6), bukan L4"
        )
    exemplar = nodes[-1]
    example = _first_instance(session, exemplar.id)
    if example is None:
        raise JobError(f"node contoh {exemplar.id} tak punya instance untuk dicontoh")

    known = {s.id for s in load_sources(DATA_DIR / "sources.yaml")}
    if source_ref_id not in known:
        raise JobError(f"source_ref {source_ref_id!r} tak ada di sources.yaml")
    if not grounding.has_snapshot(source_ref_id):
        raise JobError(
            f"{source_ref_id} belum di-snapshot — jalankan "
            f"scripts/fetch_source.py --id {source_ref_id} (L3)"
        )

    material = _library_material(library_file, source_ref_id)
    node_id = _next_node_id(nodes, slug)
    if session.get(Node, node_id):
        raise JobError(f"node {node_id!r} sudah ada")
    if prereq_node_id:
        prereq = session.get(Node, prereq_node_id)
        if prereq is None or prereq.domain_id != domain_id:
            raise JobError(f"prereq {prereq_node_id!r} tak ada di domain {domain_id!r}")

    hidden_path = REPO_ROOT / example.hidden_test_path
    example_dir, ext = hidden_path.parent, hidden_path.suffix
    probe_id = _probe_id_for(node_id, 1)
    labels = ["variant_a", "variant_b"]

    prompt = render(
        "r4_node",
        {
            "node_id": node_id,
            "domain_id": domain_id,
            "concept": concept,
            "grader_type": str(exemplar.grader_type),
            "file_ext": ext,
            "source_ref_id": source_ref_id,
            "probe_id": probe_id,
            "variant_labels": ", ".join(labels),
            "example_node_id": exemplar.id,
            "example_node_yaml": _read_or_empty(
                DATA_DIR / "domains" / domain_id / "nodes" / exemplar.id / "node.yaml"
            ),
            "example_prompt": example.prompt,
            "example_reference": _read_or_empty(
                _find_variant_file(example_dir, "reference_solution")
            ),
            "example_test": _read_or_empty(hidden_path),
        },
    )
    job = new_job(
        Role.r4_challenge,
        request={
            "mode": "node",
            "node_id": node_id,
            "domain_id": domain_id,
            "grader_type": str(exemplar.grader_type),
            "file_ext": ext,
            "concept": concept,
            "source_ref_id": source_ref_id,
            "library_file": material,
            "prereq_node_id": prereq_node_id or "",
            "variant_labels": labels,
            "probe_id": probe_id,
        },
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
            gate = (
                _gate_r4_node(job, session)
                if job.request.get("mode") == "node"
                else _gate_r4(job, session)
            )
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
        if job.request.get("mode") == "node":
            artifact = contracts.load_node_genesis(job.dir, job.request)
            problems = grounding.check_quotes([artifact.citation])
            if problems:
                # Beda dari R3: di sini "belum di-snapshot" MUSTAHIL — trigger sudah
                # menolaknya di depan. Jadi setiap masalah berarti sitasinya cacat,
                # dan tak ada yang perlu ditahan-tahan.
                raise contracts.ArtifactError(
                    "sitasi node tak lolos grounding verbatim: "
                    + "; ".join(str(p) for p in problems)
                )
            return {
                "mode": "node",
                "node_id": artifact.node.id,
                "variants": [v.variant_label for v in artifact.variants],
                "probe_id": artifact.probe.id,
                "estimated_minutes": artifact.node.estimated_minutes,
                "quote": artifact.citation.quote[:120],
            }

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


def _gate_r4_node(job: Job, session: Session) -> dict:
    """GERBANG node baru (L4): TRIAD untuk SETIAP varian + probe DIJALANKAN.

    Node baru tak boleh masuk dengan standar lebih longgar daripada varian tambahan
    (M7 langkah 1) atau node tulisan tangan (`verify_nodes.py`) — ketiganya memanggil
    `quality_gate.run_triad`. Biayanya ~2x waktu gate varian; itu harga sebuah node
    yang tak memalsukan sinyal inti produk.

    Beda dari `_gate_r4`: node-nya BELUM ada di DB, jadi grader diambil dari `node.yaml`
    artifact. Itu aman HANYA karena `contracts._require_identity` sudah memaksa
    `grader_type` sama dengan yang ditetapkan trigger — jangan longgarkan salah satunya
    tanpa yang lain, kalau tidak model bisa memilih grader yang paling mudah dilewati.
    """
    artifact = contracts.load_node_genesis(job.dir, job.request)
    grader = get_grader(artifact.node.grader_type)
    gate: dict = {"passed": True, "reason": "", "variants": {}}

    for variant in artifact.variants:
        vdir = job.dir / "instances" / variant.variant_label
        hidden = _find_variant_file(vdir, "hidden_test")
        instance = ChallengeInstance(
            id=f"{artifact.node.id}__gate_{job.id}_{variant.variant_label}",
            node_id=artifact.node.id,
            variant_label=variant.variant_label,
            prompt="",
            starter_code="",
            signature_contract="",
            hidden_test_path=repo_pointer(hidden),
            scaffold_level="L2",
        )
        triad = run_triad(
            grader,
            instance,
            reference=variant.reference_solution,
            starter=variant.starter_code,
        )
        failing = triad.failing
        gate["variants"][variant.variant_label] = {
            "passed": triad.ok,
            "reason": triad.reason,
            "output": failing.output if failing else "",
        }
        if not triad.ok:
            gate["passed"] = False
            gate["reason"] = f"{variant.variant_label}: {triad.reason}"
            return gate  # berhenti di kegagalan pertama — sisanya tak menambah informasi

    # Probe buatan AI: kunci jawabannya DIJALANKAN, tak cukup "ada di options".
    # `snippet` wajib & `expected_value` terlarang sudah ditegakkan kontrak
    # (`NodeGenesisArtifact._shape`), jadi di sini tinggal membuktikannya lewat eksekusi.
    verdict = verify_probe(artifact.probe, file_ext=artifact.file_ext)
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
    # Dulu regex-nya `^(n\d+)` — hanya cocok untuk id domain FastAPI, dan buktinya
    # sudah ada di kurikulum: probe ML tulisan tangan bernama `m001_probe_01`, sedangkan
    # probe buatan AI di node yang sama jatuh ke fallback "nama node penuh" dan jadi
    # `m002_sigmoid_bce_probe_02`. `_probe_id_for` memakai `^([a-z]\d+)_`, jadi ketiga
    # domain mewarisi satu konvensi.
    return _probe_id_for(node_id, count + 1)


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
