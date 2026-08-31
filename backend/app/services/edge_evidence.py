"""Bukti untuk edge prerequisite (M7 langkah 4) — dan batas jujurnya.

Sampai M6, otoritas edge ada di §1.4: "sumber otoritatif + Isyah". Begitu Isyah
dicabut dari jalur (§7 2026-08-31), yang tersisa kalau tak ditambal adalah asersi
LLM — persis yang §1.4 tolak.

## Yang DICOBA lebih dulu, dan kenapa gagal

Rencana M7 menuntut "bukti statis" sebagai GERBANG: konstruk khas node hulu wajib
muncul di `reference_solution` hilir; kalau tidak, edge `hard` ditolak. Diuji atas
kurikulum nyata (14 edge hard, 19 node), aturan itu menandai **6-7 edge**, dan
hampir semuanya salah tuduh.

Sebabnya struktural, bukan penyetelan ambang. Sidik jari dibangun dari token yang
JARANG (kalau tidak, `def`/`app`/`return` membuat semua edge "terbukti"). Tapi
konstruk yang benar-benar diwariskan node fondasi justru yang PALING SERING muncul
— `@app.get` ada di hampir tiap node FastAPI, `useState` di hampir tiap node React.
Filter kejarangan membuang persis bukti yang dicari, dan menyisakan nama-nama
insidental (`read_status`, `orders`, `version`) yang memang tak akan pernah muncul
di node lain. Arah kesimpulannya jadi terbalik: makin fondasional sebuah node, makin
pasti ia dituduh tak mendukung apa pun.

Kesimpulan yang dipegang: **kesamaan konstruk bisa MENGUKUHKAN sebuah edge, tapi
ketiadaannya tidak membuktikan edge itu salah.** Karena itu modul ini melaporkan,
tidak memblokir.

## Yang dipakai sebagai gantinya

1. **Korroborasi (di sini).** Konstruk jarang yang DIPAKAI BERSAMA hulu & hilir =
   bukti positif. Ketiadaannya = "tak terkukuhkan", bukan "salah".
2. **Bukti prediktif (di sini).** Kalau X prasyarat Y, kegagalan di X mestinya
   memprediksi kegagalan di Y. Ini bisa difalsifikasi data `Attempt` — dan tak satu
   pun sistem rujukan bisa melakukannya, karena mereka tak punya oracle yang
   menghasilkan datanya. Batas jujurnya: dengan satu pelajar, datanya berisik, jadi
   ia MENANDAI dan diam sampai ambang minimum terlampaui. Diamnya benar, bukan bug.
3. **Pembatasan akibat (aturan, bukan kode di sini).** Karena edge tak bisa
   digerbangi mesin, yang dibatasi adalah AKIBAT kesalahannya: **edge usulan AI
   hanya boleh `soft`.** Hanya `hard` yang mengunci urutan (§1.4), jadi edge soft
   yang salah cuma jadi saran keliru — sementara edge hard yang salah mengunci
   Bryant keluar dari node yang sebenarnya siap ia kerjakan. `hard` tetap menuntut
   keputusan manusia.
"""

import re
from dataclasses import dataclass

from sqlmodel import Session, select

from app.graders.files import reference_solution_path
from app.models import Attempt, AttemptResult, ChallengeInstance, Edge, EdgeType, Node

#: Token dianggap JARANG bila muncul di <= proporsi ini dari node satu domain.
DISTINCTIVE_MAX_SHARE = 0.3

#: Kata yang tak pernah dihitung sebagai konstruk: kata kunci bahasa & nama generik.
_STOPWORDS = {
    "def",
    "return",
    "class",
    "import",
    "from",
    "int",
    "str",
    "float",
    "bool",
    "dict",
    "list",
    "none",
    "self",
    "function",
    "const",
    "export",
    "default",
    "app",
    "true",
    "false",
    "if",
    "in",
    "not",
    "for",
    "raise",
}

_TOKEN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")

#: Attempt minimum di KEDUA sisi sebelum bukti prediktif berani bersuara.
MIN_ATTEMPTS_FOR_PREDICTION = 5


@dataclass
class EdgeFinding:
    from_node_id: str
    to_node_id: str
    kind: str  # "corroborated" | "uncorroborated" | "predictive"
    reason: str
    #: SELALU False di modul ini. Field-nya tetap ada supaya pemanggil (meja audit)
    #: tak perlu tahu bedanya — dan supaya kalau suatu saat ada bukti edge yang
    #: benar-benar layak memblokir, tempatnya sudah jelas.
    blocking: bool = False

    def __str__(self) -> str:
        return f"[{self.kind}] {self.from_node_id} -> {self.to_node_id}: {self.reason}"


def _tokens(text: str) -> set[str]:
    return {t for t in _TOKEN.findall(text or "") if t.lower() not in _STOPWORDS}


def rare_tokens(text: str, peers: list[str]) -> set[str]:
    """Token `text` yang jarang muncul di teks pembanding."""
    own = _tokens(text)
    if not own or not peers:
        return own
    limit = max(1, int(len(peers) * DISTINCTIVE_MAX_SHARE))
    counts = dict.fromkeys(own, 0)
    for peer in peers:
        peer_tokens = _tokens(peer)
        for t in own:
            if t in peer_tokens:
                counts[t] += 1
    return {t for t, c in counts.items() if c <= limit}


def code_by_node(session: Session) -> dict[str, str]:
    """node_id -> gabungan seluruh `reference_solution` milik node itu.

    Sumber sidik jari sengaja KODE, bukan `signature_contract`: diuji atas kurikulum
    nyata, kontrak menghasilkan token seperti `status` — nama path di contoh node,
    bukan konstruk yang diajarkannya.
    """
    out: dict[str, list[str]] = {}
    for instance in session.exec(select(ChallengeInstance)).all():
        path = reference_solution_path(instance)
        if path.exists():
            out.setdefault(instance.node_id, []).append(path.read_text(encoding="utf-8"))
    return {node_id: "\n".join(v) for node_id, v in out.items()}


def corroboration(session: Session) -> list[EdgeFinding]:
    """Apakah hulu & hilir berbagi konstruk jarang? Melaporkan, tidak memblokir.

    Hanya edge `hard` yang dinilai: `soft` mengklaim sesuatu yang lebih lemah
    ("membantu, bukan prasyarat") dan sering benar tanpa berbagi satu pun konstruk.
    """
    nodes = {n.id: n for n in session.exec(select(Node)).all()}
    code = code_by_node(session)
    by_domain: dict[str, list[str]] = {}
    for node in nodes.values():
        by_domain.setdefault(node.domain_id, []).append(node.id)

    findings: list[EdgeFinding] = []
    for edge in session.exec(select(Edge)).all():
        if edge.type != EdgeType.hard.value:
            continue
        upstream, downstream = nodes.get(edge.from_node_id), nodes.get(edge.to_node_id)
        if upstream is None or downstream is None:
            continue

        hulu_code, hilir_code = code.get(upstream.id, ""), code.get(downstream.id, "")
        if not hulu_code or not hilir_code:
            continue

        peers = [
            code.get(nid, "")
            for nid in by_domain.get(upstream.domain_id, [])
            if nid not in (upstream.id, downstream.id)
        ]
        # Bukti = konstruk jarang yang dipakai KEDUANYA.
        bersama = rare_tokens(hulu_code, peers) & _tokens(hilir_code)

        if bersama:
            findings.append(
                EdgeFinding(
                    from_node_id=edge.from_node_id,
                    to_node_id=edge.to_node_id,
                    kind="corroborated",
                    reason=f"berbagi konstruk jarang: {', '.join(sorted(bersama)[:6])}",
                )
            )
        else:
            findings.append(
                EdgeFinding(
                    from_node_id=edge.from_node_id,
                    to_node_id=edge.to_node_id,
                    kind="uncorroborated",
                    reason=(
                        "tak berbagi konstruk jarang — belum terkukuhkan. BUKAN berarti "
                        "salah: konstruk node fondasi justru terlalu umum untuk jadi bukti"
                    ),
                )
            )
    return findings


def predictive_evidence(session: Session) -> list[EdgeFinding]:
    """Edge yang DIBANTAH data attempt: gagal di hulu tak memprediksi apa pun.

    Menandai, tak pernah memblokir (n=1 — lihat §7 2026-08-31).
    """
    findings: list[EdgeFinding] = []
    for edge in session.exec(select(Edge)).all():
        hulu = fail_rate(session, edge.from_node_id)
        hilir = fail_rate(session, edge.to_node_id)
        if hulu is None or hilir is None:
            continue  # datanya belum cukup — diam adalah jawaban yang benar
        if hulu == 0.0 and hilir > 0.5:
            findings.append(
                EdgeFinding(
                    from_node_id=edge.from_node_id,
                    to_node_id=edge.to_node_id,
                    kind="predictive",
                    reason=(
                        f"hulu tak pernah gagal ({hulu:.0%}) padahal hilir sering gagal "
                        f"({hilir:.0%}) — urutannya mungkin terbalik atau prasyaratnya lain"
                    ),
                )
            )
    return findings


def fail_rate(session: Session, node_id: str) -> float | None:
    """Proporsi attempt GAGAL di node ini. None bila attempt-nya belum cukup."""
    dinilai = (AttemptResult.passed.value, AttemptResult.failed.value)
    attempts = session.exec(select(Attempt).where(Attempt.node_id == node_id)).all()
    scored = [a for a in attempts if a.result in dinilai]
    if len(scored) < MIN_ATTEMPTS_FOR_PREDICTION:
        return None
    return sum(1 for a in scored if a.result == AttemptResult.failed.value) / len(scored)
