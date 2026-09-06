# Plan Eksekusi L4 — Jembatan Library→Forge (kelahiran node lewat R4 mode `node`)

> **Status:** ⏳ **DIEKSEKUSI 2026-09-06 — 11/12 DoD terbukti; 1 terblokir kuota CLI**
> (kelahiran node sungguhan; sebabnya `HTTP 429`, bukan gerbang — lihat §15).
> Turunan dari
> [`roadmap-library-lane.md`](roadmap-library-lane.md) fase **L4** dan keputusan
> [`../CLAUDE.md`](../CLAUDE.md) §7 (2026-08-31, 2026-09-01, 2026-09-04, 2026-09-05).
> Peta yang dijembatani lahir di [`execution-plan-L3-learn-intake.md`](execution-plan-L3-learn-intake.md);
> pipeline yang diperluas lahir di M5 dan digerbangi M7.
>
> **Ditulis agar bisa dikerjakan developer pemula sekalipun** dan tetap menghasilkan
> kode berkualitas: tiap berkas punya spesifikasi lengkap, kode acuan yang bisa
> ditranskripsi, test eksplisit, urutan build, dan checklist selesai.
>
> **Bukan** pelonggaran invariant. Kalau ada konflik dengan §1 CLAUDE.md,
> **invariant menang**. — **Dicatat:** 2026-09-06

---

## 0. Peta cepat (baca ini dulu)

L4 menutup lingkaran lajur Library: **satu entri peta → satu node Forge yang terbukti
hijau → `node_ids` terisi balik di materi Library**. Sesudah L4, "% direproduksi" (L5)
punya bahan untuk dihitung.

### Temuan yang membentuk plan ini

Roadmap L4 menulis "pakai pipeline authoring yang sudah ada (R4), jangan bikin jalur
baru". **Pipeline itu tidak bisa melahirkan node.** Diperiksa langsung di kode:

| Fakta | Bukti |
|---|---|
| `trigger_r4` menolak node tanpa instance (ia mencontoh `instances[0]`) | [`jobs.py:99`](../backend/app/claude/jobs.py#L99) |
| `_promote_r4` hanya menulis **varian** ke folder node yang sudah ada | [`review_queue.py:142`](../backend/app/claude/review_queue.py#L142) |
| R1 (pembuat node) tak pernah dibangun — `Role` cuma r2/r3/r4 | [`artifacts.py:34`](../backend/app/claude/artifacts.py#L34) |
| Node sah butuh **≥2 varian** + **≥1 probe** + `node.yaml` | `_MIN_INSTANCES`/`_MIN_PROBES` di [`node_loader.py:40`](../backend/app/services/node_loader.py#L40) |

Keputusan Isyah (2026-09-06): **perluas R4 dengan mode `node`**, bukan bikin peran R5.

### Yang dibangun

| Berkas | Peran | Wajib? |
|---|---|---|
| `backend/app/claude/prompts/r4_node.md` | Prompt peran R4 mode `node` (versi `r4node-v1`). | ✅ inti |
| `backend/app/claude/jobs.py` (perluasan) | `trigger_r4_node()` · cabang `_validate` · `_gate_r4_node()` (triad **2×** + probe dieksekusi). | ✅ inti |
| `backend/app/claude/contracts.py` (perluasan) | `NodeGenesisArtifact` + `load_node_genesis()`; ekstraksi aturan hidden-test jadi fungsi bersama. | ✅ inti |
| `backend/app/claude/review_queue.py` (perluasan) | `_promote_node_genesis()` — tulis folder node + edge **soft** + reload DB, rollback penuh bila gagal. | ✅ inti |
| `backend/app/routers/authoring.py` (perluasan) | `POST /authoring/node`. | ✅ inti |
| `scripts/verify_library.py` (perluasan) | `--link FILE --node ID` (isi `node_ids`, deterministik) & `--candidates` (laporan kandidat belum tertempa). | ✅ inti |
| `.claude/skills/forge-node/SKILL.md` | Alur: pilih kandidat → trigger → tunggu gerbang → tautkan balik. | ✅ inti |
| test di `backend/tests/` + `scripts/` | Penjaga. | ✅ (house style) |

**Definisi selesai (ringkas):** dari satu berkas materi di `library/` yang punya
`**Kandidat node:**`, lahir folder node baru di `data/domains/<domain>/nodes/` yang lolos
`verify_nodes.py`, terdaftar di DB, tertaut dua arah dengan materi Library-nya, dan
**tak satu pun langkahnya memutuskan mastery**.

---

## 1. Tujuan & ruang lingkup

**Tujuan.** Menutup jembatan: peta Library (L3) → node Forge nyata → tautan balik.

**DI DALAM ruang lingkup L4:**
- Melahirkan **node baru** di domain yang **sudah ada** (fastapi · react · ml) lewat R4
  mode `node`, dengan gerbang mesin yang sama ketatnya dengan node tulisan tangan.
- Menulis **edge `soft`** opsional dari node prasyarat yang disebut pemanggil.
- Mengisi `node_ids` di berkas materi Library lewat **script** (bukan tangan AI).
- Laporan "kandidat yang belum tertempa" sebagai pintu masuk alur.

**DI LUAR ruang lingkup L4 (jangan dikerjakan di sini):**
- **Domain baru** (mis. Docker/SQL): itu grader baru = pekerjaan gaya M6, dan node tanpa
  grader adalah node yang tak bisa dinilai. Trigger **menolak** domain tak dikenal.
- **Edge `hard`**: §7 2026-09-01 mengunci "edge usulan AI hanya boleh `soft`".
- Dashboard "% direproduksi" → L5.
- Halaman audit/tombol pensiun frontend (sisa M7) — bukan prasyarat L4.
- Menyentuh status/mastery apa pun (§1.2).

---

## 2. Keputusan yang sudah dikunci (jangan ditawar ulang)

1. **KUNCI 1 — Mode `node` di peran R4, bukan peran baru.** `Role` tetap r2/r3/r4;
   pembedanya `job.request["mode"] ∈ {variant, node}`. Alasan: gerbangnya sama
   (`run_triad` + `verify_probe`), promosinya sekeluarga, dan peran baru berarti
   endpoint+prompt+kontrak+gate+status baru yang harus dirawat selamanya. *Ditolak:*
   R5 node-genesis (permukaan kode terbesar untuk gerbang yang sama persis).

2. **KUNCI 2 — Node lahir LENGKAP atau tidak lahir sama sekali.** Satu artifact memuat
   `node.yaml` + **2 varian** + **1 probe**. Tak ada node "setengah jadi" yang menunggu
   dilengkapi: `assemble_node` menolak node dengan < 2 varian, jadi node setengah jadi
   akan memecahkan `load_nodes.py` untuk **seluruh** domain, bukan cuma dirinya.

3. **KUNCI 3 — Gerbang = triad DUA KALI + probe dieksekusi + skema.** Tiap varian
   dijalankan lewat `run_triad` (referensi HIJAU, kosong MERAH, starter MERAH). Node baru
   tak boleh masuk dengan standar lebih longgar daripada varian tambahan (M7 langkah 1)
   atau node tulisan tangan (`verify_nodes.py`). Biayanya ~2× waktu gate; itu harga node
   yang tak memalsukan sinyal inti produk.

4. **KUNCI 4 — Identitas node ditentukan MESIN, bukan AI.** `node_id`, label varian
   (`variant_a`/`variant_b`), `probe_id`, `domain_id`, dan `grader_type` dihitung
   `trigger_r4_node()` dari isi `data/` lalu **dipaksakan** ke artifact (artifact yang
   menyimpang ditolak kontrak). Yang boleh dikarang AI hanyalah isi: prompt, kode,
   test, probe. *Alasan:* penamaan yang dikarang model adalah cara termurah membuat
   kurikulum berantakan tanpa satu pun gerbang berbunyi.

5. **KUNCI 5 — `grader_type` diwarisi dari node contoh di domain yang sama.** Bukan dari
   tabel domain→grader yang baru (itu kolom/knowledge baru yang harus dijaga), melainkan
   dari node yang sudah terbukti hidup di domain itu. Domain tanpa satu pun node **tak
   bisa** jadi target L4 — sekaligus alasan mengapa "domain baru" di luar ruang lingkup.

6. **KUNCI 6 — Sumber node wajib TER-SNAPSHOT, dan satu sumber dengan materinya.**
   `source_ref_id` yang dipakai node baru wajib (a) ada di `sources.yaml`, (b) punya
   `data/sources/<id>.md` (L3), dan (c) **muncul di `source_refs` berkas materi Library**
   asalnya. Ini yang membuat jembatannya bukan sekadar nama file yang sama. Ditambah:
   artifact wajib membawa **kutipan verbatim** yang diperiksa `grounding.check_quotes`.

7. **KUNCI 7 — Kutipan diverifikasi lalu TIDAK disimpan ke `data/`.** `node.yaml` memakai
   `extra="forbid"` dan formatnya beku; menambah field `quote` berarti mengubah skema
   seluruh kurikulum demi satu jalur. Kutipannya hidup di `artifacts/<job>/citation.json`
   + ringkasan job (bisa diaudit), sementara `data/` cuma menyimpan `source_refs` seperti
   node tulisan tangan. Yang dijaga bukan arsipnya, melainkan **gerbangnya**.

8. **KUNCI 8 — Edge hasil L4 selalu `soft`, dan opsional.** §7 2026-09-01 sudah
   menghukum ini: edge `hard` yang salah mengunci Bryant keluar dari node yang sebenarnya
   siap ia kerjakan; edge `soft` yang salah cuma saran keliru. Konsekuensi yang diterima
   sadar: node hasil L4 **selalu langsung `available`** (`progress.py`: tanpa hard-prereq
   → available), jadi ia tak pernah mengunci apa pun dan tak pernah terkunci.

9. **KUNCI 9 — `edges.yaml` ditambahi dengan APPEND TEKS, bukan `yaml.dump` ulang.**
   Berkas itu penuh komentar kurasi ("difinalkan Isyah 2026-08-22 …"); menulis ulang lewat
   dumper akan menghapusnya diam-diam. Append + validasi `load_edges` + rollback dari
   salinan mentah.

10. **KUNCI 10 — Backend tak pernah menyentuh `library/`.** Promosi menulis `data/` +
    DB (seperti M5/M7); tautan balik `node_ids` ditulis `scripts/verify_library.py --link`.
    Dua lajur, dua penulis — dan lajur Library tetap bisa dipakai tanpa backend menyala.

11. **KUNCI 11 — Tautan balik ditulis SCRIPT, bukan AI.** Sama seperti flip status L2 dan
    snapshot L3: bagian yang menentukan dikeluarkan dari tangan AI. `--link` menolak node
    yang tak ada di `data/`, menolak duplikat, dan mempertahankan 8 field beku.

**Batas yang diterima sadar (WAJIB dicatat di §7 CLAUDE.md saat eksekusi):**
- **Relevansi entri peta terhadap tujuan tetap tanpa oracle.** Gerbang membuktikan node
  itu *bisa direproduksi & dinilai*, bukan bahwa ia *layak dipelajari*. Penjaganya sama
  seperti M7: telemetri menandai node curiga, pencabutan tetap satu klik manusia.
- **Kutipan membuktikan kutipannya nyata, bukan bahwa ia menopang konsep node.** Kalimat
  yang sama sudah tertulis di `grounding.py`; jangan mengklaim lebih.
- **n=1 tetap n=1.** L4 menambah laju pembuatan node; ia tak menambah bukti bahwa node
  itu baik. Karena itu L5 (penjaga metrik) naik prioritas begitu L4 hidup.

---

## 3. Daur hidup & kontrak

### 3.1 Alur end-to-end

```
library/<peta>/NN-modul/_index.md          ← L3: "**Kandidat node:** `get-route-json`"
   │
   ├─(SCRIPT) verify_library.py --candidates        daftar kandidat yang belum tertempa
   │
   ├─(HTTP)  POST /authoring/node {library_file, slug, domain_id, concept, source_ref_id}
   │            └→ trigger_r4_node(): hitung node_id/label/probe_id/grader_type,
   │               PAKSA identitas, render prompt r4_node.md              → job pending
   │
   ├─(latar) execute_job() → Claude Code menulis artifact ke artifacts/r4-<stamp>/
   │            ├─ contracts.load_node_genesis()   skema + identitas + bentuk hidden test
   │            ├─ grounding.check_quotes()        kutipan ⊆ snapshot sumber
   │            └─ _gate_r4_node()                 TRIAD ×2 varian + probe DIJALANKAN
   │                     merah → rejected (tak pernah masuk sistem)
   │
   ├─(otomatis) review_queue._promote_node_genesis()
   │            ├→ data/domains/<domain>/nodes/<node_id>/{node.yaml,instances/…,probes/…}
   │            ├→ edges.yaml  (+1 edge `soft`, bila prereq disebut)
   │            └→ assemble_node() + load_domain_into_db()   ← gagal = rollback total
   │
   └─(SCRIPT) verify_library.py --link <materi.md> --node <node_id>
                └→ node_ids: [<node_id>]     ← bahan hitung "% direproduksi" (L5)
```

### 3.2 Payload trigger (kontrak HTTP)

```json
{
  "library_file": "library/fastapi-produksi/01-routing-dasar/get-route-json.md",
  "slug": "get-route-json",
  "domain_id": "fastapi",
  "concept": "GET route sederhana mengembalikan dict JSON dengan status 200",
  "source_ref_id": "fastapi_docs_first_steps",
  "prereq_node_id": "n002_get_json_route"
}
```

| Field | Wajib | Aturan (ditegakkan `trigger_r4_node`, semua gagal → `JobError` 400) |
|---|---|---|
| `library_file` | ✅ | ada, di dalam `library/`, frontmatter terbaca, `node_ids` **masih kosong**, dan `source_refs` memuat `source_ref_id` |
| `slug` | ✅ | kebab-case; dipakai jadi bagian `node_id` (`-` → `_`) |
| `domain_id` | ✅ | folder `data/domains/<id>/` ada **dan** punya ≥1 node contoh |
| `concept` | ✅ | satu kalimat; masuk `node.yaml` lewat prompt |
| `source_ref_id` | ✅ | ada di `sources.yaml` **dan** `data/sources/<id>.md` ada |
| `prereq_node_id` | — | bila diisi: node itu ada, sedomain, dan **bukan** node yang sedang dibuat |

### 3.3 Bentuk artifact (ditulis Claude Code ke direktori job)

Sengaja **berbentuk sama dengan folder node M2** — itu prinsip yang sudah dipakai
`ChallengeArtifact` ("bentuknya SAMA dengan node folder M2"), dan ia membuat promosi jadi
penyalinan, bukan penerjemahan.

```
node.yaml                                   # skema NodeYaml (M2)
instances/variant_a/prompt.md
instances/variant_a/starter_code.py         # ekstensi mengikuti domain (.py / .jsx)
instances/variant_a/reference_solution.py
instances/variant_a/hidden_test.py
instances/variant_b/…                       # 4 berkas yang sama, DATA UJI berbeda
probe.yaml                                  # satu probe, `snippet` + `expression` WAJIB
citation.json                               # {"source_ref_id": …, "claim": …, "quote": "…verbatim…"}
```

**`expected.json`** (khusus grader `value_assert`/ML) ikut di dalam folder varian bila ada
— aturan M6 tak berubah: toleransi numerik hidup di `data/`, bukan di kolom DB.

### 3.4 Bentuk hasil di `data/` & `library/`

Setelah promosi, `data/domains/fastapi/nodes/n014_get_route_json/` berisi persis bentuk
node tulisan tangan (bandingkan `n002_get_json_route`). Dan berkas materi Library-nya:

```yaml
---
title: "GET route JSON 200"
course: fastapi-produksi
module: 01-routing-dasar
type: note
source_refs: [fastapi_docs_first_steps]
node_ids: [n014_get_route_json]     # ← DIISI SCRIPT setelah node hijau
status: outline                      # ← TIDAK berubah: status CATATAN, bukan reproduksi
created: 2026-09-06
---
```

`status` sengaja tak tersentuh: ia status catatan Bryant (L0), dan reproduksi hanya boleh
datang dari eksekusi kode (§1.2) lewat hitungan dashboard L5.
---

## 4. `jobs.py` — trigger mode `node`

### 4.1 Yang ditambahkan

| Simbol | Peran |
|---|---|
| `_NODE_ID_RE`, `_next_node_id()` | Turunkan `n014_<slug>` dari id node yang SUDAH ada di domain itu (prefix & lebar angka diwarisi, bukan di-hardcode). |
| `_probe_id_for()` | `n014` + urutan → `n014_probe_01`, konvensi tulisan tangan. |
| `_library_material()` | Validasi berkas materi Library asal-usul node. |
| `trigger_r4_node()` | Bentuk job `mode: node` + render `r4_node.md`. |
| `_gate_r4_node()` | §6. |
| cabang di `_validate()` & `execute_job()` | §6.3. |

Tambahkan `import yaml` di header `jobs.py` (modul ini belum mengimpornya; `review_queue`
sudah). `grounding` & `load_sources` sudah diimpor untuk R3 — dipakai ulang di sini.

### 4.2 Kode acuan

```python
#: `n013_depends_shared_params` → ("n", "013"). Dipakai untuk mewarisi konvensi
#: penamaan domain, bukan menciptakan konvensi baru per node.
_NODE_ID_RE = re.compile(r"^([a-z])(\d+)_")


def _domain_nodes(session: Session, domain_id: str) -> list[Node]:
    nodes = session.exec(select(Node).where(Node.domain_id == domain_id)).all()
    return sorted(nodes, key=lambda n: n.id)


def _next_node_id(existing: list[Node], slug: str) -> str:
    """`[n013…]` + "get-route-json" → `n014_get_route_json`."""
    prefix, width, top = "n", 3, 0
    for node in existing:
        m = _NODE_ID_RE.match(node.id)
        if m:
            prefix, width = m.group(1), len(m.group(2))
            top = max(top, int(m.group(2)))
    return f"{prefix}{top + 1:0{width}d}_{slug.replace('-', '_')}"


def _probe_id_for(node_id: str, urutan: int) -> str:
    m = _NODE_ID_RE.match(node_id)
    prefix = node_id[: m.end() - 1] if m else node_id
    return f"{prefix}_probe_{urutan:02d}"


def _library_material(library_file: str, source_ref_id: str) -> str:
    """Validasi berkas materi Library asal node. Kembalikan path POSIX relatif-repo.

    Tiga pemeriksaan, semuanya murah dan semuanya menutup kesalahan yang mahal:
    berkasnya benar-benar di `library/`, BELUM tertaut node lain, dan berdiri di
    sumber yang SAMA dengan node yang akan lahir (KUNCI 6).
    """
    path = (REPO_ROOT / library_file).resolve()
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
    dihitung DI SINI dari isi `data/`, lalu dipaksakan ke artifact (`contracts.
    _require_identity`). Yang boleh dikarang model hanyalah ISI: prompt, kode, test,
    probe. Penamaan yang dikarang model adalah cara termurah membuat kurikulum
    berantakan tanpa satu pun gerbang berbunyi.
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
            "grader_type": exemplar.grader_type,
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
```

### 4.3 Perbaikan kecil yang ikut dikerjakan (dengan bukti)

`_next_probe_id()` memakai regex `^(n\d+)` — hanya cocok untuk id domain FastAPI. Buktinya
sudah ada di kurikulum: probe tulisan tangan ML bernama `m001_probe_01`, sedangkan probe
buatan AI di node yang sama bernama **`m002_sigmoid_bce_probe_02`** (fallback "nama node
penuh"). L4 melahirkan node di ketiga domain, jadi ganti regex-nya jadi `^([a-z]\d+)` —
atau lebih baik, panggil `_probe_id_for()` yang baru. Satu baris, dan ia menghentikan
konvensi penamaan yang bercabang diam-diam.

---

## 5. `backend/app/claude/prompts/r4_node.md` (baru)

```markdown
---
version: r4node-v1
---
# Peran R4 (mode NODE) — bikin SATU node reproduksi baru, utuh

Kamu dipanggil headless oleh Reproduction Learning Engine. Tulis file ke direktori
kerja saat ini. **Jangan** menyentuh file lain di luar direktori ini.

## Identitas yang SUDAH DITETAPKAN (jangan diubah, jangan dikarang)

- node_id: `{{node_id}}`  · domain: `{{domain_id}}` · grader_type: `{{grader_type}}`
- ekstensi berkas kode: `{{file_ext}}`
- label varian yang WAJIB kamu tulis: {{variant_labels}}
- id probe: `{{probe_id}}` · sumber otoritatif: `{{source_ref_id}}`

Artifact yang menyimpang dari identitas di atas **ditolak otomatis**.

## Konsep yang harus jadi node

{{concept}}

## Contoh bentuk (node `{{example_node_id}}` — ikuti gayanya persis)

```yaml
{{example_node_yaml}}
```

```markdown
{{example_prompt}}
```

```text
{{example_reference}}
```

```text
{{example_test}}
```

## Yang harus kamu tulis

```
node.yaml                                   # metadata node (skema di bawah)
instances/variant_a/prompt.md               # spesifikasi tajam, bahasa Indonesia
instances/variant_a/starter_code{{file_ext}}       # kerangka L2: struktur ada, inti `# TODO:`
instances/variant_a/reference_solution{{file_ext}} # solusi benar
instances/variant_a/hidden_test{{file_ext}}        # test deterministik atas submisi
instances/variant_b/…                       # 4 berkas yang sama, DATA UJI berbeda
probe.yaml                                  # satu comprehension probe deterministik
citation.json                               # {"source_ref_id": "...", "claim": "...", "quote": "..."}
```

`node.yaml` wajib memuat: `id`, `domain_id`, `concept`, `description`, `grader_type`,
`estimated_minutes` (perkiraan jujur, > 0), `timebox_seconds` (> 0),
`status_default: locked`, `source_refs: [{{source_ref_id}}]`, `signature_contract`,
`scaffold_level: L2`. Tanpa field lain — skemanya menolak field asing.

`probe.yaml` wajib punya `snippet` **dan** `expression`: kunci jawabannya akan
**dijalankan**, bukan dipercaya. `expected_value` **dilarang** di jalur ini.

`citation.json`: `quote` harus potongan **verbatim** dari sumber `{{source_ref_id}}`
(minimal 25 karakter). Ia dicocokkan sebagai substring terhadap snapshot sumber; kutipan
karangan ditolak.

## Aturan mutu yang akan diuji mesin (tahu di depan lebih murah daripada ditolak)

1. **Tiap** varian: hidden test HIJAU di `reference_solution`, **MERAH** di berkas kosong,
   dan **MERAH** di `starter_code`. Kerangka yang sudah lolos = tantangan kosong.
2. Dua varian harus menguji konsep yang sama dengan **data uji berbeda** (transfer,
   bukan hafalan) — bukan dua penulisan ulang soal yang sama.
3. Hidden test wajib benar-benar memanggil submisi pengguna.
4. Probe: `correct_answer` harus persis nilai yang keluar dari menjalankan `expression`
   atas `snippet`; tiap distractor harus berbeda.
```

> **Catatan penulisan template:** blok contoh memakai pagar ``` di dalam template.
> Itu tak masalah — `prompts.render()` cuma mengganti `{{placeholder}}`, tak mem-parse
> markdown. Tapi **jangan** memakai `{{` di dalam contoh kode, karena placeholder yang
> tak punya nilai adalah error (lihat `prompts.render`).

---

## 6. `contracts.py` — `NodeGenesisArtifact`

### 6.1 Refactor kecil lebih dulu (aturan yang dipakai bersama)

`ChallengeArtifact._test_references_solution` memuat aturan bentuk hidden test. L4 butuh
aturan yang **sama persis** — jadi ekstrak jadi fungsi modul, lalu panggil dari keduanya.
(Preseden yang sudah dipegang proyek ini: gate R4 & `verify_nodes.py` sama-sama memanggil
`quality_gate.run_triad` justru supaya tak ada dua salinan aturan.)

```python
def check_test_references_solution(hidden_test: str, file_ext: str) -> None:
    """Hidden test wajib benar-benar memanggil submisi user. Dipakai R4 varian & node."""
    rule = _TEST_RULES.get(file_ext)
    if rule is None:
        raise ValueError(
            f"ekstensi berkas {file_ext!r} belum didukung kontrak R4 "
            f"(terdaftar: {sorted(_TEST_RULES)})"
        )
    imports_re, test_re, expectation = rule
    if not imports_re.search(hidden_test) or not test_re.search(hidden_test):
        raise ValueError(f"hidden_test{file_ext} harus {expectation}")
```

lalu di `ChallengeArtifact`:

```python
    @model_validator(mode="after")
    def _test_references_solution(self):
        check_test_references_solution(self.hidden_test, self.file_ext)
        return self
```

### 6.2 Model baru

```python
#: Node sah butuh >= 2 varian (`node_loader._MIN_INSTANCES`). Angkanya diulang di sini
#: dengan sadar: kontrak menolak SEBELUM eksekusi mahal dijalankan, loader menolak
#: sesudahnya. Kalau salah satu berubah, test `test_min_variants_sejalan` berteriak.
_MIN_VARIANTS = 2


class NodeVariant(BaseModel):
    """Satu folder `instances/<label>/` — bentuknya sama dengan node folder M2."""

    model_config = ConfigDict(extra="forbid")

    variant_label: str
    prompt_md: str
    starter_code: str
    reference_solution: str
    hidden_test: str
    file_ext: str = _DEFAULT_TEST_EXT
    expected_json: str = ""

    @field_validator("variant_label")
    @classmethod
    def _label_shape(cls, v: str) -> str:
        if not _VARIANT_RE.match(v):
            raise ValueError(f"variant_label harus 'variant_<slug>', dapat {v!r}")
        return v

    @field_validator("prompt_md", "reference_solution")
    @classmethod
    def _nonempty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("field wajib ini kosong")
        return v

    @model_validator(mode="after")
    def _test_shape(self):
        check_test_references_solution(self.hidden_test, self.file_ext)
        return self


class NodeGenesisArtifact(BaseModel):
    """NODE BARU utuh (L4): `node.yaml` + >=2 varian + 1 probe + sitasi terverifikasi.

    Bentuknya sengaja mengikuti folder node M2 supaya promosi jadi PENYALINAN, bukan
    penerjemahan — penerjemah adalah tempat lahir kebocoran (M6/M7 sudah membayar tiga
    kali: ekstensi `.py` yang di-hardcode di gate, di kontrak, dan di promosi).
    """

    model_config = ConfigDict(extra="forbid")

    node: NodeYaml
    variants: list[NodeVariant]
    probe: ProbeYaml
    citation: Citation

    @property
    def file_ext(self) -> str:
        return self.variants[0].file_ext

    @model_validator(mode="after")
    def _shape(self):
        if len(self.variants) < _MIN_VARIANTS:
            raise ValueError(
                f"node baru butuh >= {_MIN_VARIANTS} varian (transfer, bukan hafalan), "
                f"dapat {len(self.variants)}"
            )
        labels = [v.variant_label for v in self.variants]
        if len(set(labels)) != len(labels):
            raise ValueError(f"label varian duplikat: {labels}")
        exts = {v.file_ext for v in self.variants}
        if len(exts) != 1:
            raise ValueError(f"varian bercampur ekstensi {sorted(exts)} — satu node satu bahasa")
        if self.probe.node_id != self.node.id:
            raise ValueError(
                f"probe.node_id {self.probe.node_id!r} != node {self.node.id!r}"
            )
        # Sama seperti gate R4 varian (§7 2026-09-01): di jalur AI tak ada penulis yang
        # bisa ditanya, jadi jawabannya wajib nilai yang persis keluar dari eksekusi.
        if not self.probe.snippet.strip():
            raise ValueError("probe tanpa `snippet` — kunci jawabannya tak bisa dibuktikan mesin")
        if self.probe.expected_value.strip():
            raise ValueError("probe buatan AI dilarang memakai `expected_value`")
        if self.citation.source_ref_id not in self.node.source_refs:
            raise ValueError(
                f"citation.source_ref_id {self.citation.source_ref_id!r} tak ada di "
                f"node.source_refs {self.node.source_refs}"
            )
        return self
```

`NodeYaml` & `ProbeYaml` di-import dari `app.services.node_schema` — **jangan** menulis
ulang skema node di `contracts.py`; yang dipakai loader dan yang dipakai gate harus benda
yang sama.

### 6.3 Loader + penegak identitas

```python
def load_node_genesis(job_dir: Path, request: dict) -> NodeGenesisArtifact:
    """Baca artifact R4 mode `node`, lalu TEGAKKAN identitas yang diminta trigger."""

    def build() -> NodeGenesisArtifact:
        variants = []
        for label in request["variant_labels"]:
            vdir = job_dir / "instances" / label
            hidden = _find(vdir, "hidden_test")
            variants.append(
                NodeVariant(
                    variant_label=label,
                    prompt_md=_read(vdir / "prompt.md"),
                    starter_code=_read_found(vdir, "starter_code"),
                    reference_solution=_read_found(vdir, "reference_solution"),
                    hidden_test=_read(hidden),
                    file_ext=hidden.suffix,
                    expected_json=_read_found(vdir, "expected", required=False),
                )
            )
        artifact = NodeGenesisArtifact(
            node=yaml.safe_load(_read(job_dir / "node.yaml")),
            variants=variants,
            probe=yaml.safe_load(_read(job_dir / "probe.yaml")),
            citation=json.loads(_read(job_dir / "citation.json")),
        )
        _require_identity(artifact, request)
        return artifact

    return _wrap(build, "artifact R4 (node) tak valid")


def _require_identity(artifact: NodeGenesisArtifact, request: dict) -> None:
    """Identitas ditetapkan mesin (KUNCI 4). Model yang menggantinya = artifact ditolak."""
    diffs = []
    for field, want in (
        ("id", request["node_id"]),
        ("domain_id", request["domain_id"]),
        ("grader_type", request["grader_type"]),
    ):
        got = str(getattr(artifact.node, field))
        if got != str(want):
            diffs.append(f"node.{field}={got!r} != {want!r}")
    if artifact.probe.id != request["probe_id"]:
        diffs.append(f"probe.id={artifact.probe.id!r} != {request['probe_id']!r}")
    if artifact.file_ext != request["file_ext"]:
        diffs.append(f"ekstensi {artifact.file_ext!r} != {request['file_ext']!r}")
    if artifact.citation.source_ref_id != request["source_ref_id"]:
        diffs.append(
            f"citation.source_ref_id={artifact.citation.source_ref_id!r} != "
            f"{request['source_ref_id']!r}"
        )
    if diffs:
        raise ValueError("identitas node tak boleh dikarang model: " + "; ".join(diffs))
```

---

## 7. Gerbang mesin `_gate_r4_node` + sambungannya

### 7.1 Kode acuan

```python
def _gate_r4_node(job: Job, session: Session) -> dict:
    """GERBANG node baru (L4): TRIAD untuk SETIAP varian + probe DIJALANKAN.

    Node baru tak boleh masuk dengan standar lebih longgar daripada varian tambahan
    (M7 langkah 1) atau node tulisan tangan (`verify_nodes.py`) — ketiganya memanggil
    `quality_gate.run_triad`. Biayanya ~2x waktu gate varian; itu harga sebuah node
    yang tak memalsukan sinyal inti produk.

    Beda dari `_gate_r4`: node-nya belum ada di DB, jadi grader diambil dari
    `node.yaml` artifact — yang identitasnya sudah dipaksa sama dengan yang diminta
    trigger, jadi model tak bisa memilih grader yang paling mudah dilewati.
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

    verdict = verify_probe(artifact.probe, file_ext=artifact.file_ext)
    gate["probe_verified"] = verdict.ok and not verdict.skipped
    if not verdict.ok:
        gate["passed"] = False
        gate["reason"] = f"probe ditolak: {verdict.reason}"
        gate["output"] = verdict.output
    return gate
```

### 7.2 Cabang di `_validate()`

Di awal cabang R4 (`if job.role == Role.r4_challenge.value:`), sisipkan:

```python
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
```

### 7.3 Cabang di `execute_job()`

```python
        if job.role == Role.r4_challenge.value:
            gate = (
                _gate_r4_node(job, session)
                if job.request.get("mode") == "node"
                else _gate_r4(job, session)
            )
```

Sisa alurnya **tidak disentuh**: `rejected` saat gate merah, `ready` lalu promosi otomatis
saat hijau, `CLAUDE_AUTO_PROMOTE=0` tetap mengembalikan alur berhenti-di-`ready`.

---

## 8. `review_queue.py` — promosi node baru

### 8.1 Dispatch

```python
    elif job.role == Role.r4_challenge.value:
        promotion = (
            _promote_node_genesis(session, job)
            if job.request.get("mode") == "node"
            else _promote_r4(session, job)
        )
```

### 8.2 Kode acuan

```python
def _promote_node_genesis(session: Session, job: Job) -> Promotion:
    """Tulis NODE BARU ke `data/` + DB (L4). Semua-atau-tak-ada.

    Node setengah jadi bukan cuma jelek: `assemble_node` menolak node dengan < 2 varian,
    dan `load_nodes.py` memuat per-DOMAIN — jadi satu folder cacat mematikan seluruh
    domain, bukan cuma dirinya. Karena itu rollback di sini menghapus folder node DAN
    mengembalikan `edges.yaml` ke isi persisnya semula.
    """
    artifact = contracts.load_node_genesis(job.dir, job.request)
    node_id = artifact.node.id
    domain_dir = DATA_DIR / "domains" / artifact.node.domain_id
    target = domain_dir / "nodes" / node_id
    edges_path = domain_dir / "edges.yaml"

    if target.exists():
        raise PromotionError(f"folder node {node_id!r} sudah ada — ganti slug atau hapus dulu")
    if session.get(Node, node_id):
        raise PromotionError(f"node {node_id!r} sudah terdaftar di DB")

    edges_backup = edges_path.read_text(encoding="utf-8") if edges_path.exists() else None
    written: list[str] = []
    try:
        (target / "probes").mkdir(parents=True)
        _dump_yaml(target / "node.yaml", artifact.node.model_dump(mode="json"))
        written.append(_rel(target / "node.yaml"))

        for variant in artifact.variants:
            vdir = target / "instances" / variant.variant_label
            vdir.mkdir(parents=True)
            isi = {
                _PROMPT_FILE: variant.prompt_md,
                f"starter_code{variant.file_ext}": variant.starter_code,
                f"reference_solution{variant.file_ext}": variant.reference_solution,
                f"hidden_test{variant.file_ext}": variant.hidden_test,
            }
            if variant.expected_json.strip():
                isi["expected.json"] = variant.expected_json
            for nama, teks in isi.items():
                (vdir / nama).write_text(teks, encoding="utf-8")
                written.append(_rel(vdir / nama))

        probe_path = target / "probes" / f"{artifact.probe.id}.yaml"
        _dump_yaml(probe_path, artifact.probe.model_dump(mode="json"))
        written.append(_rel(probe_path))

        prereq = job.request.get("prereq_node_id") or ""
        if prereq:
            _append_soft_edge(
                edges_path,
                from_id=prereq,
                to_id=node_id,
                source_ref_id=job.request["source_ref_id"],
                library_file=job.request["library_file"],
            )
            written.append(_rel(edges_path))

        # Validasi M2 berlaku PENUH untuk output AI (sama seperti _promote_r4).
        assemble_node(target)
        load_domain_into_db(session, domain_dir, data_dir=DATA_DIR)
    except Exception as e:  # noqa: BLE001 — rollback file, lalu laporkan apa adanya
        shutil.rmtree(target, ignore_errors=True)
        if edges_backup is not None:
            edges_path.write_text(edges_backup, encoding="utf-8")
        raise PromotionError(f"promosi dibatalkan, node akan menjadi tak sah: {e}") from e

    return Promotion(
        job_id=job.id,
        role=job.role,
        node_id=node_id,
        written_paths=written,
        db_effect={
            "variants": [v.variant_label for v in artifact.variants],
            "probe_id": artifact.probe.id,
            "soft_edge_from": job.request.get("prereq_node_id", ""),
            "library_file": job.request["library_file"],
        },
    )


def _dump_yaml(path: Path, data: dict) -> None:
    """Satu gaya dump untuk seluruh berkas hasil promosi — supaya node buatan AI
    ter-diff sama bentuknya dengan node tulisan tangan."""
    path.write_text(
        yaml.dump(data, Dumper=_IndentedDumper, allow_unicode=True,
                  sort_keys=False, width=200),
        encoding="utf-8",
    )


def _append_soft_edge(edges_path: Path, *, from_id: str, to_id: str,
                      source_ref_id: str, library_file: str) -> None:
    """Tambah SATU edge `soft` lewat APPEND TEKS, lalu buktikan berkasnya masih parse.

    Ditulis sebagai teks, bukan `yaml.dump` ulang: `edges.yaml` penuh komentar kurasi
    ("difinalkan Isyah 2026-08-22 …") dan dumper akan menghapusnya diam-diam.

    Selalu `soft` (§7 2026-09-01): edge `hard` yang salah mengunci Bryant KELUAR dari
    node yang sebenarnya siap ia kerjakan; edge `soft` yang salah cuma saran keliru.
    """
    blok = (
        f"\n  # Usul L4 (AI) dari peta Library: {library_file}\n"
        f"  - from: {from_id}\n"
        f"    to: {to_id}\n"
        f"    type: soft\n"
        f"    source_ref_id: {source_ref_id}\n"
        f'    note: "Usulan L4 — menyarankan urutan, tidak mengunci."\n'
    )
    if edges_path.exists():
        edges_path.write_text(
            edges_path.read_text(encoding="utf-8").rstrip("\n") + "\n" + blok,
            encoding="utf-8",
        )
    else:
        edges_path.write_text("edges:\n" + blok, encoding="utf-8")
    load_edges(edges_path)  # gagal parse → exception → rollback di pemanggil
```

Tambahkan `load_edges` ke import `node_loader` di `review_queue.py`.

---

## 9. `routers/authoring.py` — endpoint

```python
class TriggerNodeIn(BaseModel):
    library_file: str
    slug: str
    domain_id: str
    concept: str
    source_ref_id: str
    prereq_node_id: str | None = None


@router.post("/node", response_model=JobOut, status_code=202)
def trigger_node(
    body: TriggerNodeIn, tasks: BackgroundTasks, session: Session = Depends(get_session)
) -> JobOut:
    """L4 — lahirkan node baru dari satu entri peta Library."""
    _require_enabled()
    try:
        job = jobs.trigger_r4_node(
            session,
            library_file=body.library_file,
            slug=body.slug,
            domain_id=body.domain_id,
            concept=body.concept,
            source_ref_id=body.source_ref_id,
            prereq_node_id=body.prereq_node_id,
        )
    except jobs.JobError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    tasks.add_task(_run_job_in_background, job.id)
    return JobOut.of(job)
```

Kill switch `CLAUDE_INTEGRATION_ENABLED=0` otomatis ikut berlaku (lewat `_require_enabled`),
jadi L4 mati bersama integrasi lainnya — sesuai PRD §10 (akselerator, bukan fondasi).
---

## 10. Sisi Library — `scripts/verify_library.py` diperluas

Dua mode baru. Keduanya **tak menyentuh `status`**: status itu status catatan (L0), dan
status reproduksi hanya boleh datang dari eksekusi kode (§1.2) lewat hitungan L5.

### 10.1 `--candidates` (laporan, bukan gerbang)

Memindai file `type: roadmap`, memungut penanda kandidat yang dipancarkan L3
(`**Kandidat node:** \`slug\``), lalu melaporkan mana yang **belum** punya `node_ids`.
Selalu exit 0 — ini pintu masuk alur, bukan gerbang. (Preseden: `edge_evidence`
melaporkan tanpa memblokir, §7 2026-09-01.)

```python
#: Penanda yang dipancarkan `library_scaffold.module_index_roadmap_md` (L3).
_CANDIDATE_RE = re.compile(r"^\*\*Kandidat node:\*\*\s*`([a-z0-9-]+)`")
#: Judul entri peta: `### [[<slug materi>|Judul]]`
_ENTRY_RE = re.compile(r"^###\s*\[\[([a-z0-9-]+)\|")


def candidates() -> list[dict]:
    """Kandidat node dari seluruh peta + status tautannya ke Forge.

    Pasangan (entri peta → berkas materi) diambil dari struktur yang DIPANCARKAN
    scaffolder, bukan ditebak: entri `### [[slug|…]]` diikuti barisnya sendiri.
    """
    out: list[dict] = []
    for path in _iter_library_files():
        fm, body = split_frontmatter(path.read_text("utf-8"))
        if not isinstance(fm, dict) or fm.get("type") != "roadmap":
            continue
        materi = ""
        for raw in body.splitlines():
            line = raw.strip()
            entry = _ENTRY_RE.match(line)
            if entry:
                materi = entry.group(1)
                continue
            cand = _CANDIDATE_RE.match(line)
            if cand and materi:
                target = path.parent / f"{materi}.md"
                t_fm, _ = split_frontmatter(target.read_text("utf-8")) if target.is_file() else (None, "")
                out.append({
                    "peta": path.relative_to(_REPO_ROOT).as_posix(),
                    "materi": target.relative_to(_REPO_ROOT).as_posix(),
                    "kandidat": cand.group(1),
                    "source_refs": list((t_fm or {}).get("source_refs") or []),
                    "node_ids": list((t_fm or {}).get("node_ids") or []),
                    "ada": target.is_file(),
                })
    return out
```

Cetakannya (dipakai skill sebagai langkah 1):

```
kandidat belum tertempa: 2
  - library/fastapi-produksi/01-routing-dasar/get-route-json.md
      kandidat: get-route-json · sumber: fastapi_docs_first_steps
sudah tertaut: 1
```

### 10.2 `--link FILE --node NODE_ID`

```python
def link_node(path: Path, source_ids: set[str], node_ids: set[str],
              node_id: str) -> list[str]:
    """Isi `node_ids` satu berkas materi. Kembalikan alasan tolak ([] = sukses).

    Ditulis SCRIPT, bukan AI — pola yang sama dengan flip status L2 dan snapshot L3:
    bagian yang menentukan dikeluarkan dari tangan AI. Di sini yang menentukan adalah
    klaim "materi ini sudah punya node": kalau AI boleh mengetiknya, dashboard L5
    ("% direproduksi") bisa digerakkan tanpa satu baris kode pun dieksekusi.
    """
    if not path.is_file():
        return ["file tak ditemukan"]
    fm, body = split_frontmatter(path.read_text("utf-8"))
    if fm is None:
        return ["frontmatter tak terbaca"]
    if node_id not in node_ids:
        return [f"node {node_id!r} tak ada di data/ — hanya node yang benar-benar "
                "lahir & termuat boleh ditautkan"]
    current = fm.get("node_ids")
    if not isinstance(current, list):
        return ["node_ids harus list"]
    if node_id in current:
        return []  # idempoten: menjalankan ulang bukan error
    fm["node_ids"] = [*current, node_id]
    errs = _field_errors(fm, path, source_ids, node_ids)
    if errs:
        return errs
    dumped = yaml.safe_dump(fm, sort_keys=False, allow_unicode=True).strip()
    path.write_text(f"---\n{dumped}\n---{body}", encoding="utf-8")
    return []
```

CLI (`main`): `--link FILE` wajib berpasangan dengan `--node ID` (kalau tidak → exit 2);
`--candidates` berdiri sendiri. Keduanya memakai `load_source_ids()` / `load_node_ids()`
yang sudah ada.

---

## 11. `.claude/skills/forge-node/SKILL.md` — isi lengkap

```markdown
---
name: forge-node
description: Tempa satu entri peta Library menjadi node reproduksi Forge lewat pipeline authoring (R4 mode node) dan tautkan balik node_ids-nya. Gunakan saat Bryant ingin mengubah kandidat node di library/ menjadi node yang benar-benar bisa direproduksi. BUKAN untuk menulis materi (artifacts/ + 403), merapikan catatan (note-refine), atau menilai penguasaan.
---

# forge-node — dari kandidat di peta Library ke node Forge (L4)

Menempa **satu** kandidat per panggilan. Semua keputusan mutu dipegang **gerbang mesin**;
kamu cuma menyiapkan permintaan dan melaporkan hasilnya apa adanya. **Nol klaim mastery.**

## Kapan dipakai / TIDAK
- PAKAI: "tempa kandidat X jadi node", "bikin node dari materi peta ini".
- JANGAN:
  - menulis berkas ke `data/` sendiri (promosi hanya lewat pipeline yang digerbangi).
  - mengetik `node_ids` dengan tangan (hanya `verify_library.py --link`).
  - membuat domain baru (butuh grader baru — pekerjaan gaya M6, bukan L4).
  - menyatakan Bryant menguasai sesuatu (dilarang §1.2).

## Alur
1. **Pilih kandidat:**
   `backend/.venv/Scripts/python.exe scripts/verify_library.py --candidates`
   Bila ada beberapa, tanyakan mana yang mau ditempa (AskUserQuestion). Ambil dari
   laporan: path materi, slug kandidat, `source_refs`.
2. **Pastikan backend hidup** (skill `run-learning-engine`) dan integrasi menyala
   (`CLAUDE_INTEGRATION_ENABLED` tidak 0). Cek: `GET /authoring/status`.
3. **Kirim permintaan:**
   `POST /authoring/node` dengan `{library_file, slug, domain_id, concept,
   source_ref_id, prereq_node_id?}`. `domain_id` HARUS domain yang sudah ada
   (`fastapi`/`react`/`ml`); `source_ref_id` harus id yang ada di `source_refs`
   materinya dan sudah ter-snapshot (L3). Balasan `202` + `job_id`.
4. **Tunggu gerbang:** poll `GET /authoring/jobs/{job_id}` sampai statusnya
   `approved` (lolos + dipromosikan otomatis), `ready` (lolos, promosi manual),
   `rejected` (gagal gerbang mutu), atau `failed` (gagal memproduksi artifact).
   Gerbang menjalankan test SUNGGUHAN dua kali (satu per varian) — sabar, jangan
   mengulang trigger karena terasa lama.
5. **Kalau `rejected`/`failed`:** laporkan `gate.reason` + potongan output APA ADANYA.
   **Jangan** mengakali gerbang (mengubah test, melonggarkan probe, memakai
   `expected_value`). Yang boleh: perbaiki konsep/sumber lalu ulangi.
6. **Kalau lolos:** verifikasi & tautkan.
   `backend/.venv/Scripts/python.exe scripts/verify_nodes.py <domain>`
   `backend/.venv/Scripts/python.exe scripts/verify_library.py --link "<materi.md>" --node <node_id>`
   `backend/.venv/Scripts/python.exe scripts/verify_library.py`
7. **Lapor:** node_id, path yang ditulis, edge soft (bila ada), dan hasil verifikasi.
   Arahkan Bryant membuka node-nya di frontend (`/node/<id>`) untuk mencobanya.

## Batas yang dijaga (jangan dilanggar)
- **Gerbang mesin yang memutuskan**, bukan kamu: triad per varian + probe dieksekusi.
- **Identitas node ditetapkan server** (id, label, probe id, grader). Jangan menyarankan
  model menamainya sendiri.
- **Edge selalu `soft`** — usul AI tak pernah mengunci urutan (§7 2026-09-01).
- **`status` materi tak berubah** saat ditautkan; "% direproduksi" dihitung dari DB (L5).
```

---

## 12. Test eksplisit

### 12.1 `backend/tests/test_node_genesis.py` (baru)

Gaya mengikuti `test_claude_contracts.py` (berkas + skema) dan `test_gate_triad.py`
(`FakeGrader`). Fixture `session` dari `conftest.py` sudah memuat domain fastapi nyata —
jadi `n013_depends_shared_params` ada dan node berikutnya harus `n014_…`.

```python
"""Test kelahiran node dari peta Library (L4).

Tiga lapis yang diuji terpisah, karena tiga-tiganya bisa gagal sendiri-sendiri:
  1. trigger  — menolak permintaan yang tak layak SEBELUM model dipanggil (hemat menit).
  2. kontrak  — menolak artifact yang identitas/bentuknya menyimpang.
  3. gerbang  — menolak soal yang tak lolos triad DUA varian / probe.
Promosi diuji di test terpisah karena ia menulis ke disk.
"""

import json

import pytest
import yaml

from app.claude import contracts, jobs
from app.claude.artifacts import Role
from app.graders.base import GradeResult
from app.models import ChallengeInstance

MATERIAL = """---
title: "GET route JSON"
course: fastapi-produksi
module: 01-routing-dasar
type: note
source_refs: [fastapi_docs_first_steps]
node_ids: []
status: outline
created: 2026-09-06
---

# GET route JSON
"""


@pytest.fixture
def materi(tmp_path, monkeypatch):
    """Berkas materi Library palsu, di bawah `library/` versi tmp."""
    monkeypatch.setattr(jobs, "REPO_ROOT", tmp_path)
    path = tmp_path / "library" / "fastapi-produksi" / "01-routing-dasar" / "get-route.md"
    path.parent.mkdir(parents=True)
    path.write_text(MATERIAL, encoding="utf-8")
    return "library/fastapi-produksi/01-routing-dasar/get-route.md"


def test_next_node_id_mewarisi_konvensi_domain():
    class N:
        def __init__(self, i): self.id = i
    assert jobs._next_node_id([N("n012_x"), N("n013_y")], "get-route") == "n014_get_route"
    assert jobs._next_node_id([N("m003_mse")], "adam-step") == "m004_adam_step"
    assert jobs._next_node_id([N("r003_list")], "use-effect") == "r004_use_effect"


def test_probe_id_ikut_konvensi_tulisan_tangan():
    assert jobs._probe_id_for("n014_get_route", 1) == "n014_probe_01"
    assert jobs._probe_id_for("m004_adam_step", 1) == "m004_probe_01"


def test_trigger_menolak_domain_tanpa_node(session, materi):
    with pytest.raises(jobs.JobError, match="belum punya satu pun node"):
        jobs.trigger_r4_node(session, library_file=materi, slug="x", domain_id="docker",
                             concept="c", source_ref_id="fastapi_docs_first_steps")


def test_trigger_menolak_sumber_tanpa_snapshot(session, materi, monkeypatch):
    monkeypatch.setattr(jobs.grounding, "has_snapshot", lambda sid, **kw: False)
    with pytest.raises(jobs.JobError, match="belum di-snapshot"):
        jobs.trigger_r4_node(session, library_file=materi, slug="get-route",
                             domain_id="fastapi", concept="c",
                             source_ref_id="fastapi_docs_first_steps")


def test_trigger_menolak_materi_yang_sudah_tertaut(session, materi, tmp_path, monkeypatch):
    path = tmp_path / materi
    path.write_text(MATERIAL.replace("node_ids: []", "node_ids: [n002_get_json_route]"),
                    encoding="utf-8")
    monkeypatch.setattr(jobs.grounding, "has_snapshot", lambda sid, **kw: True)
    with pytest.raises(jobs.JobError, match="sudah tertaut"):
        jobs.trigger_r4_node(session, library_file=materi, slug="get-route",
                             domain_id="fastapi", concept="c",
                             source_ref_id="fastapi_docs_first_steps")


def test_trigger_menolak_sumber_yang_tak_dipakai_materinya(session, materi, monkeypatch):
    monkeypatch.setattr(jobs.grounding, "has_snapshot", lambda sid, **kw: True)
    with pytest.raises(jobs.JobError, match="tak memuat"):
        jobs.trigger_r4_node(session, library_file=materi, slug="get-route",
                             domain_id="fastapi", concept="c",
                             source_ref_id="fastapi_docs_path_params")


def test_trigger_membentuk_job_dengan_identitas_terkunci(session, materi, monkeypatch):
    monkeypatch.setattr(jobs.grounding, "has_snapshot", lambda sid, **kw: True)
    job = jobs.trigger_r4_node(session, library_file=materi, slug="get-route",
                               domain_id="fastapi", concept="GET route JSON",
                               source_ref_id="fastapi_docs_first_steps")
    assert job.role == Role.r4_challenge.value
    assert job.request["mode"] == "node"
    assert job.request["node_id"].startswith("n014_")
    assert job.request["variant_labels"] == ["variant_a", "variant_b"]
    assert (job.dir / "prompt.md").exists()
```

Bagian kontrak (lanjutan berkas yang sama):

```python
def _genesis_files(**over) -> dict[str, str]:
    node_yaml = {
        "id": "n014_get_route", "domain_id": "fastapi",
        "concept": "GET route JSON 200", "description": "d",
        "grader_type": "unit_test", "estimated_minutes": 12, "timebox_seconds": 900,
        "status_default": "locked", "source_refs": ["fastapi_docs_first_steps"],
        "signature_contract": "@app.get('<path>') -> dict", "scaffold_level": "L2",
    }
    probe = {"id": "n014_probe_01", "node_id": "n014_get_route",
             "type": "predict_output", "question": "Status?",
             "options": ["200", "404"], "correct_answer": "200",
             "snippet": "x = 200\n", "expression": "x"}
    files = {
        "node.yaml": yaml.safe_dump(node_yaml),
        "probe.yaml": json.dumps(probe),
        "citation.json": json.dumps({"source_ref_id": "fastapi_docs_first_steps",
                                     "claim": "route dideklarasikan lewat dekorator",
                                     "quote": "The simplest FastAPI file could look like this"}),
    }
    for label in ("variant_a", "variant_b"):
        files[f"instances/{label}/prompt.md"] = f"# {label}\n"
        files[f"instances/{label}/starter_code.py"] = "# TODO:\n"
        files[f"instances/{label}/reference_solution.py"] = VALID_REFERENCE
        files[f"instances/{label}/hidden_test.py"] = VALID_TEST
    files.update(over)
    return files


REQUEST = {"mode": "node", "node_id": "n014_get_route", "domain_id": "fastapi",
           "grader_type": "unit_test", "file_ext": ".py",
           "source_ref_id": "fastapi_docs_first_steps",
           "variant_labels": ["variant_a", "variant_b"], "probe_id": "n014_probe_01"}


def test_kontrak_menerima_artifact_lengkap(tmp_path):
    _write(tmp_path, _genesis_files())
    artifact = contracts.load_node_genesis(tmp_path, REQUEST)
    assert len(artifact.variants) == 2 and artifact.file_ext == ".py"


def test_kontrak_menolak_id_karangan(tmp_path):
    files = _genesis_files()
    files["node.yaml"] = files["node.yaml"].replace("n014_get_route", "n999_keren")
    _write(tmp_path, files)
    with pytest.raises(contracts.ArtifactError, match="identitas node"):
        contracts.load_node_genesis(tmp_path, REQUEST)


def test_kontrak_menolak_satu_varian(tmp_path):
    _write(tmp_path, _genesis_files())
    req = {**REQUEST, "variant_labels": ["variant_a"]}
    with pytest.raises(contracts.ArtifactError, match=">= 2 varian"):
        contracts.load_node_genesis(tmp_path, req)


def test_kontrak_menolak_probe_expected_value(tmp_path):
    files = _genesis_files()
    probe = json.loads(files["probe.yaml"])
    probe["expected_value"] = "200"
    files["probe.yaml"] = json.dumps(probe)
    _write(tmp_path, files)
    with pytest.raises(contracts.ArtifactError, match="expected_value"):
        contracts.load_node_genesis(tmp_path, REQUEST)


def test_kontrak_menolak_sitasi_di_luar_source_refs(tmp_path):
    files = _genesis_files()
    files["citation.json"] = json.dumps({"source_ref_id": "fastapi_docs_body",
                                         "claim": "c", "quote": "q" * 30})
    _write(tmp_path, files)
    with pytest.raises(contracts.ArtifactError):
        contracts.load_node_genesis(tmp_path, REQUEST)
```

Bagian gerbang (memakai `FakeGrader` gaya `test_gate_triad.py`):

```python
def test_gate_menolak_saat_varian_kedua_merah(tmp_path, session, monkeypatch):
    """Varian pertama hijau TIDAK cukup — tiap varian diuji sendiri."""
    files = _genesis_files()
    files["instances/variant_b/reference_solution.py"] = "# solusi salah\n"
    _write(tmp_path, files)
    ...  # job palsu berisi request REQUEST + job.dir = tmp_path
    monkeypatch.setattr(jobs, "get_grader", lambda t: FakeGrader({VALID_REFERENCE}))
    gate = jobs._gate_r4_node(job, session)
    assert gate["passed"] is False and "variant_b" in gate["reason"]
    assert gate["variants"]["variant_a"]["passed"] is True
```

### 12.2 `backend/tests/test_promote_node.py` (baru)

**Ini test promosi PERTAMA di repo** — M5/M7 tak punya. Ia wajib mem-`monkeypatch`
`review_queue.DATA_DIR` ke `tmp_path`, kalau tidak ia akan menulis ke kurikulum sungguhan.

```python
def test_promosi_menulis_node_dan_edge_soft(tmp_path, session, monkeypatch): ...
def test_promosi_rollback_saat_node_tak_sah(tmp_path, session, monkeypatch):
    """node.yaml sah tapi varian dirusak → folder node HILANG lagi & edges.yaml pulih."""
def test_promosi_menolak_node_yang_sudah_ada(tmp_path, session, monkeypatch): ...
def test_edge_yang_ditulis_selalu_soft(tmp_path): ...
def test_append_edge_mempertahankan_komentar(tmp_path):
    """Komentar kurasi di edges.yaml masih ada setelah append (KUNCI 9)."""
```

### 12.3 Tambahan di `scripts/test_verify_library.py`

```python
def test_link_mengisi_node_ids(lib): ...
def test_link_menolak_node_yang_tak_ada(lib): ...
def test_link_idempoten(lib): ...
def test_link_tidak_mengubah_status(lib):
    """Menautkan node BUKAN klaim reproduksi — `status` harus tetap seperti semula."""
def test_candidates_menemukan_kandidat_belum_tertaut(lib, snaps): ...
def test_candidates_melewati_yang_sudah_tertaut(lib, snaps): ...
```

---

## 13. Urutan build (langkah demi langkah)

Prinsip yang sama dengan L3: **gerbang lebih dulu, penulis belakangan.**

1. **Kontrak** (`contracts.py`): ekstrak `check_test_references_solution`, tambah
   `NodeVariant`/`NodeGenesisArtifact`/`load_node_genesis`/`_require_identity` + test
   §12.1 bagian kontrak. Test lama `test_claude_contracts.py` harus tetap hijau — itu
   buktinya refactor tak menggores R4 varian.
2. **Gerbang** (`jobs._gate_r4_node`) + test §12.1 bagian gerbang.
3. **Trigger** (`jobs.trigger_r4_node` + helper + perbaikan `_next_probe_id`) + test.
4. **Prompt** `r4_node.md` (§5). Test `test_prompt_templates_are_versioned` sudah ada —
   pastikan template baru ikut ter-parametrize di sana.
5. **Promosi** (`review_queue._promote_node_genesis` + `_append_soft_edge`) + test §12.2.
6. **Router** (`POST /authoring/node`).
7. **Sisi Library** (`verify_library.py --link/--candidates`) + test §12.3.
8. **Skill** `forge-node`.
9. **Smoke end-to-end sungguhan** (§14) — dengan CLI Claude Code nyata, satu node.
10. **Catat:** entri §7 CLAUDE.md (KUNCI 1–11 + batas), tandai L4 ✅ di roadmap, tambahkan
    `POST /authoring/node` & perintah `--link/--candidates` ke §6 CLAUDE.md.

---

## 14. Verifikasi manual (smoke)

Prasyarat: peta L3 sudah ada di `library/` dengan minimal satu `**Kandidat node:**`,
sumbernya ter-snapshot, backend jalan, `CLAUDE_INTEGRATION_ENABLED` tidak 0.

```bash
# 1) Pintu masuk
backend/.venv/Scripts/python.exe scripts/verify_library.py --candidates

# 2) Tempa satu kandidat
curl -X POST localhost:8000/authoring/node -H "content-type: application/json" -d '{
  "library_file": "library/fastapi-produksi/01-routing-dasar/get-route-json.md",
  "slug": "get-route-json", "domain_id": "fastapi",
  "concept": "GET route sederhana mengembalikan dict JSON dengan status 200",
  "source_ref_id": "fastapi_docs_first_steps",
  "prereq_node_id": "n002_get_json_route"}'

# 3) Tunggu gerbang (triad 2x + probe)
curl localhost:8000/authoring/jobs/<job_id>

# 4) Verifikasi node baru lewat gerbang authoring tulisan tangan
backend/.venv/Scripts/python.exe scripts/verify_nodes.py fastapi

# 5) Tautkan balik + validasi Library
backend/.venv/Scripts/python.exe scripts/verify_library.py --link "library/.../get-route-json.md" --node n014_get_route_json
backend/.venv/Scripts/python.exe scripts/verify_library.py
```

**Yang WAJIB kamu lihat:**

| Uji | Harapan |
|---|---|
| trigger dengan `domain_id: docker` | `400`, "domain … belum punya satu pun node contoh" |
| trigger dengan sumber yang belum di-snapshot | `400`, menyebut `fetch_source.py --id …` |
| trigger materi yang `node_ids`-nya sudah terisi | `400`, "sudah tertaut" |
| job sukses | status `approved`, `summary.promotion` memuat `node.yaml` + 8 berkas varian + 1 probe |
| folder node baru | `data/domains/fastapi/nodes/n014_*/` berisi 2 varian + 1 probe |
| `edges.yaml` | bertambah satu blok `type: soft`, **komentar lama utuh** |
| `verify_nodes.py fastapi` | HIJAU termasuk node baru (triad + probe dieksekusi) |
| `--link` | `node_ids` terisi, **`status` tak berubah** |
| `--link` diulang | exit 0, berkas tak berubah (idempoten) |
| node baru di frontend `/node/<id>` | tampil `available` (tak ada hard-prereq — KUNCI 8) |
| **uji penolakan:** jalankan lagi trigger dengan slug yang sama | ditolak (`node … sudah ada` / folder ada) |

---

## 15. Definition of Done (checklist) — 11/12 TERBUKTI 2026-09-06 · 1 TERBLOKIR KUOTA

> Dieksekusi 2026-09-06. Kolom bukti diisi dari run nyata, bukan dari niat.
> **Satu item belum bisa dibuktikan** dan sebabnya di luar kode — lihat catatan di bawah.

- [x] `NodeGenesisArtifact` + `load_node_genesis` + `_require_identity` ada; aturan hidden
      test **satu salinan** (dipakai R4 varian & node).
      → `contracts.check_test_references_solution` diekstrak; `test_claude_contracts` &
      `test_gate_triad` lama tetap hijau = refactor tak menggores R4 varian.
- [x] `trigger_r4_node`, `_gate_r4_node`, cabang `_validate`/`execute_job` ada.
- [x] `r4_node.md` ber-`version:` (`r4node-v1`) dan ikut test versi prompt.
- [x] `_promote_node_genesis` + `_append_soft_edge` ada, **dengan rollback yang diuji**.
      → `test_promote_node.py`, 9 test — **test promosi PERTAMA di repo**. Rollback
      dibuktikan: folder node hilang lagi DAN `edges.yaml` byte-identik dengan semula.
- [x] `POST /authoring/node` ada dan tunduk pada kill switch.
      → `CLAUDE_INTEGRATION_ENABLED=0` ⇒ **503**, sementara `GET /stats` tetap **200**
      (loop inti tak punya ketergantungan pada L4).
- [x] `verify_library.py --link` & `--candidates` ada; `--link` tak menyentuh `status`.
- [x] `.claude/skills/forge-node/SKILL.md` ada.
- [x] Test hijau: **185 backend** (naik dari 151: +24 `test_node_genesis`, +9
      `test_promote_node`, +1 versi prompt) dan **62 scripts** (+9 untuk `--link`/
      `--candidates`).
- [x] `ruff` bersih — persis 3 temuan lama (1×UP017 + 2×E402), nol temuan baru.
      **Catatan invokasi:** jalankan dari `backend/`; dari repo root tak ada
      `pyproject.toml` sehingga ruff memakai aturan default (lihat plan L3 §12).
- [~] Smoke §14 — **sebagian**: seluruh uji PENOLAKAN terbukti live (empat, satu lebih
      banyak dari rencana), jalur L3→L4 terbukti, kill switch terbukti. Yang belum:
      baris-baris yang menuntut job SUKSES (folder node, `edges.yaml`, `verify_nodes.py`,
      `--link`, tampil `available`) — semuanya hilir dari item berikut.
- [ ] **TERBLOKIR:** satu node sungguhan lahir dari peta Library dan lolos
      `verify_nodes.py`. Sebabnya **bukan gerbang dan bukan kode**: panggilan CLI ketiga
      dibalas `HTTP 429 — "You've hit your session limit"`. Lihat catatan di bawah.
- [x] Entri §7 CLAUDE.md ditulis; roadmap & §6 CLAUDE.md diperbarui.
- [x] **Invariant utuh:** tak ada verdict mastery dari AI; edge baru semuanya `soft`;
      `status` materi Library tak tersentuh; `data/` hanya berubah lewat promosi yang
      digerbangi — dan selama seluruh smoke, `git status data/` **tetap bersih**.

### Catatan eksekusi — apa yang sebenarnya terjadi di smoke

Tiga job R4 mode `node` dijalankan dengan CLI sungguhan, dari peta Library nyata
(`library/fastapi-produksi/01-parameter-request/cookie-param.md`, sumber
`fastapi_docs_cookie_params` yang di-snapshot L3):

| Job | Hasil | Sebab |
|---|---|---|
| `r4-20260906T022656` (2 percobaan) | `failed` | **Celah prompt**, bukan celah gerbang — lihat di bawah |
| `r4-20260906T023250` (2 percobaan) | `failed` | `HTTP 429` kuota sesi CLI habis |

**Celah prompt yang ditemukan smoke (dan itu gunanya smoke).** `r4_node.md` versi rencana
hanya menulis "`probe.yaml` wajib punya `snippet` dan `expression`" — ia **tak pernah
mendaftar skema `ProbeYaml` utuh**, padahal prompt R4 varian (`r4_challenge.md`) sudah
mendaftarnya sejak M5. Dua panggilan berturut-turut menghasilkan probe tanpa `node_id`
dan `type`; log hasil model menyebut sendiri bahwa ia mengikuti nama field "dari instruksi
peran, tanpa bisa mengecek `contracts.py`". **Kontrak menolak keduanya dan nol berkas
menyentuh `data/`.** Skema probe kini didaftar lengkap di `r4_node.md`.

**Ikut terlihat:** retry `execute_job` memakai prompt yang IDENTIK, jadi celah prompt yang
sistematis memakan dua panggilan CLI penuh sebelum menyerah. Itu perilaku M5 yang sudah
ada, bukan bawaan L4 — tak diubah di sini, tapi biayanya sekarang terukur.

**Cara menuntaskan item yang terblokir** (sesudah kuota pulih, tak perlu perubahan kode):

```bash
cd backend && .venv/Scripts/python.exe -m uvicorn app.main:app --port 8000   # jendela lain
curl -X POST localhost:8000/authoring/node -H "content-type: application/json" -d '{
  "library_file": "library/fastapi-produksi/01-parameter-request/cookie-param.md",
  "slug": "cookie-param", "domain_id": "fastapi",
  "concept": "Membaca satu cookie dari request sebagai parameter fungsi lewat Cookie(), lalu mengembalikannya sebagai JSON",
  "source_ref_id": "fastapi_docs_cookie_params",
  "prereq_node_id": "n004_query_param_default"}'
# lalu poll GET /authoring/jobs/<id> sampai approved/rejected, dan bila approved:
backend/.venv/Scripts/python.exe scripts/verify_nodes.py fastapi
backend/.venv/Scripts/python.exe scripts/verify_library.py --link "library/fastapi-produksi/01-parameter-request/cookie-param.md" --node n014_cookie_param
backend/.venv/Scripts/python.exe scripts/verify_library.py
```

---

## 16. Gotchas / jebakan yang harus dihindari

1. **Test promosi WAJIB mem-`monkeypatch` `review_queue.DATA_DIR`.** Ia konstanta yang
   di-import ke namespace modul; lupa satu kali = test menulis node palsu ke kurikulum
   sungguhan, dan kamu baru sadar saat `git status` penuh.
2. **`edges.yaml` jangan pernah ditulis ulang lewat `yaml.dump`** — komentar kurasinya
   hilang diam-diam (KUNCI 9). Append teks + `load_edges()` sebagai bukti masih parse.
3. **Gate node memakai grader dari `node.yaml` artifact, bukan dari DB** (node-nya belum
   ada di DB saat gate jalan). Itu aman **hanya karena** `_require_identity` sudah
   memaksa `grader_type` sama dengan yang ditetapkan trigger — jangan longgarkan salah
   satunya tanpa yang lain.
4. **Biaya gate berlipat.** Triad = 3 eksekusi/varian → 6 untuk node baru. Di React
   (`REACT_EXECUTION_TIMEOUT_SECONDS = 120`) satu job bisa memakan menit. Jangan
   menurunkan timeout untuk "mempercepat" — submisi benar yang ter-grade FAIL adalah
   kegagalan terburuk sistem ini (§7 2026-08-22).
5. **`_next_probe_id` yang lama hanya cocok untuk id `n…`** — buktinya
   `m002_sigmoid_bce_probe_02` di kurikulum. Perbaiki bersamaan (§4.3), kalau tidak node
   ML/React baru mewarisi penamaan yang bercabang.
6. **Jangan menambah field ke `node.yaml`** untuk menyimpan kutipan. `extra="forbid"` dan
   format node dipakai seluruh kurikulum; kutipan hidup di `artifacts/` + ringkasan job
   (KUNCI 7).
7. **`prompts.render` menolak placeholder tanpa nilai.** Kalau menaruh contoh kode di
   template, pastikan tak ada `{{` di dalamnya.
8. **Jangan biarkan skill mengisi `node_ids`.** Hanya `--link`. Kalau AI boleh
   mengetiknya, angka "% direproduksi" (L5) bisa naik tanpa satu baris kode dieksekusi —
   dan itu persis illusion of competence yang produk ini dibangun untuk melawan.
9. **Materi yang belum ada berkas stub-nya** (`### [[slug|…]]` menunjuk berkas yang tak
   ada) harus dilaporkan `--candidates` apa adanya, bukan dilewati diam-diam.
10. **Kill switch harus benar-benar mematikan L4.** Endpoint baru wajib lewat
    `_require_enabled()`; loop inti M3/M4 tak boleh punya ketergantungan padanya.

---

## 17. Setelah L4 (arah, bukan tugas sekarang)

- **L5 (penjaga metrik) naik prioritas, bukan turun.** L4 mempercepat lahirnya node; ia
  tak menambah bukti bahwa node itu baik, dan ia membuat Library terasa makin seperti
  kurikulum. Roadmap §4 sudah memperingatkan: tiap minggu lajur ini hidup tanpa L5,
  Bryant berlatih mengukur "dibaca". Bahan hitungnya kini lengkap: `node_ids` di
  `library/` + status/attempt di DB Forge.
- **Telemetri M7 mulai berguna untuk node buatan L4:** pass rate, waktu-vs-`estimated_minutes`,
  lapse rate. Node L4 adalah pelanggan pertama meja audit — yang halaman frontend-nya
  masih sisa pekerjaan M7.
- **Edge `hard`** untuk node baru tetap urusan manusia (atau bukti prediktif dari
  `Attempt`, §7 2026-09-01). L4 sengaja tak menyentuhnya.
