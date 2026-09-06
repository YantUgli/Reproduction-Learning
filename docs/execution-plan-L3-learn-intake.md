# Plan Eksekusi L3 — Skill `learn-intake` + gerbang grounding (snapshot + kutipan verbatim)

> **Status:** ✅ **DIEKSEKUSI & TERVERIFIKASI 2026-09-05** — seluruh DoD §12 terbukti
> (commit `7a258e0` + `4e1e91f`, branch `m7-machine-gates`). Dokumen ini kini jadi
> catatan rancangan + bukti, bukan daftar tugas. Turunan dari
> [`roadmap-library-lane.md`](roadmap-library-lane.md) fase **L3** dan keputusan
> [`../CLAUDE.md`](../CLAUDE.md) §7 (2026-08-31, 2026-09-01, 2026-09-04). Format target
> dibekukan di [`../library/README.md`](../library/README.md) (L0); scaffolder yang
> diperluas lahir di [`execution-plan-L1-course-intake.md`](execution-plan-L1-course-intake.md);
> validator yang diperluas lahir di [`execution-plan-L2-note-refine.md`](execution-plan-L2-note-refine.md).
>
> **Ditulis agar bisa dikerjakan developer pemula sekalipun** dan tetap menghasilkan
> kode berkualitas: tiap berkas punya spesifikasi lengkap, kode acuan yang bisa
> ditranskripsi, test eksplisit, urutan build, dan checklist selesai.
>
> **Bukan** pelonggaran invariant. Kalau ada konflik dengan §1 CLAUDE.md,
> **invariant menang**. — **Dicatat:** 2026-09-05

---

## 0. Peta cepat (baca ini dulu)

L3 adalah **fase risiko** lajur Library: fase pertama yang menaruh teks hasil riset AI
ke `library/`. Yang dibangun bukan "generator materi" — melainkan **peta belajar
bersitasi** yang menunjuk **sumber asli**, dijaga gerbang mesin.

| Berkas | Peran | Wajib? |
|---|---|---|
| `scripts/fetch_source.py` | **Penulis snapshot**: unduh teks sumber otoritatif → `data/sources/<id>.md`. Isinya tak pernah diketik AI. | ✅ inti |
| `scripts/verify_library.py` (perluasan) | **Gerbang baca**: file `type: roadmap` wajib bersitasi, tiap kutipan wajib verbatim ada di snapshot, tanpa blok kode, prosa dibatasi. | ✅ inti |
| `scripts/library_scaffold.py` (perluasan) | **Gerbang tulis**: `kind: roadmap` di spec; kutipan dicek terhadap snapshot **sebelum** satu berkas pun ditulis. | ✅ inti |
| `.claude/skills/learn-intake/SKILL.md` | Pemandu alur: 5 keputusan → riset → snapshot → spec → scaffold → validasi. | ✅ inti |
| `data/sources/*.md` | Snapshot teks sumber (di-commit, di-diff seperti kode). **Belum ada sama sekali hari ini.** | ✅ inti |
| `scripts/test_fetch_source.py` + tambahan di 2 test lama | Penjaga. | ✅ (house style) |

**Efek samping yang disengaja:** `data/sources/` adalah bahan yang sama yang ditunggu
gate R3 (§7 2026-08-31: "Yang BELUM: … snapshot `data/sources/<id>.md` (tanpa snapshot,
job R3 ditolak)"). Mengerjakan L3 **menghidupkan lajur 403** yang sudah terbangun tapi
mati sejak M7. Satu kerja, dua lajur.

**Definisi selesai (ringkas):** dari 5 keputusan Bryant lahir `library/<goal>/` berisi
peta bersitasi yang **tiap kutipannya terbukti ada di snapshot sumber**; nol prosa
penjelasan sintesis; nol blok kode di peta; validator hijau; test hijau; `ruff` bersih.

---

## 1. Tujuan & ruang lingkup

**Tujuan.** Mengotomasi **Penggunaan 1** (belajar sesuatu dari nol): dari tujuan Bryant
menjadi **roadmap + kerangka + sitasi terkurasi + usul node**, yang mendarat di
`library/` sebagai **peta**, bukan bab materi.

**DI DALAM ruang lingkup L3:**
- Riset sumber otoritatif, mendaftarkannya ke `data/sources.yaml`, **meng-snapshot**
  teksnya lewat script.
- Merakit spec roadmap menjadi pohon `library/<goal-slug>/` (create-only, lewat scaffolder).
- Tiap entri peta memuat: judul · **apa yang harus bisa direproduksi** (satu kalimat) ·
  sitasi + **kutipan verbatim** · **kandidat node** Forge.
- Gerbang mesin dua lapis: saat **menulis** (scaffolder) dan saat **membaca** (validator).

**DI LUAR ruang lingkup L3 (jangan dikerjakan di sini):**
- **Menulis penjelasan/prosa materi ke `library/`** — dilarang keras (§7 2026-09-04).
  Sintesis just-in-time hidup di `artifacts/` dan sampai ke Bryant **hanya lewat
  gerbang 403**.
- **Membuat node Forge** dari kandidat → itu L4 (lewat pipeline R4 + gerbang M7).
- Dashboard "% direproduksi" → L5.
- Menyentuh status/DB Forge, edge prasyarat, atau apa pun yang berbau mastery (§1.2).
- Mengisi isi catatan materi → itu `note-refine` (L2).

---

## 2. Keputusan yang sudah dikunci (jangan ditawar ulang)

Dari diskusi 2026-09-05 (pendekatan **A**, dipilih dari 5 alternatif) + §7 CLAUDE.md:

1. **KUNCI 1 — Gerbang sitasi = snapshot + kutipan verbatim, bukan "id terdaftar".**
   Gerbang lama ("`source_ref` ADA di `sources.yaml`") *self-satisfying* begitu AI boleh
   menulis ke registry: karang sitasi, daftarkan id, lolos. Ini persis celah yang diakui
   entri M5 2026-08-22 dan sudah ditutup M7 untuk R3. L3 memakai mesin yang **sama**:
   [`backend/app/services/grounding.py`](../backend/app/services/grounding.py).

2. **KUNCI 2 — Isi snapshot TIDAK PERNAH diketik AI.** Kalau AI boleh mengarang isi
   `data/sources/<id>.md`, pemeriksaan "kutipan ⊆ snapshot" jadi melingkar. Maka snapshot
   hanya lahir dari `scripts/fetch_source.py`: unduhan HTTP (`provenance: fetch`) atau
   berkas yang **Bryant** sediakan (`provenance: manual`). Pola yang sama dengan L1
   (scaffolder yang menulis) dan L2 (script yang flip status): **bagian yang menentukan
   dikeluarkan dari tangan AI.**

3. **KUNCI 3 — AI boleh menambah entri ke `sources.yaml` tanpa menunggu manusia.**
   Sejalan tujuan otonomi §7 2026-08-31 (Bryant belajar tanpa Isyah di jalur). Aman
   karena pendaftaran id **bukan** gerbangnya: URL karangan gagal diunduh → tak ada
   snapshot → tak ada kutipan yang bisa lolos. Wajib: `type` ∈ `{cs2023_ku, textbook_toc,
   official_docs}`, tanpa field asing — `SourceRefYaml` memakai `extra="forbid"`, jadi
   pelanggaran memecahkan `load_nodes.py`, bukan cuma jelek.

4. **KUNCI 4 — Penulis berkas tetap scaffolder deterministik, bukan AI.** AI merakit
   `spec.yaml`; `library_scaffold.py` yang menyentuh disk, create-only. L1 aman *by
   construction* karena ini; melepasnya di fase paling berisiko berarti melepas penjaga
   terkuat justru saat paling dibutuhkan.

5. **KUNCI 5 — Kutipan hidup di file peta (`type: roadmap`); catatan hidup di file
   materi (`type: note`).** `_index.md` modul = peta modul (entri + sitasi + kutipan +
   kandidat node). Stub materi = halaman kosong milik Bryant, diisi lewat L2. Akibatnya
   aturan gerbang bisa dikunci ke **`type`**, bukan ke tebakan isi. **Konsekuensi yang
   harus disadari: kutipan di file `type: note` TIDAK diverifikasi** — jadi jangan pernah
   menaruh sitasi generate di sana.

6. **KUNCI 6 — Kandidat node = teks di body peta, bukan field baru & bukan pipa baru.**
   `node_ids` divalidasi ⊆ node yang **sudah ada**, dan format 8-field L0 beku (validator
   menolak field asing). `nodes.proposed.yaml` tidak dibangun di L3: belum ada konsumennya
   sampai L4, dan preseden M6 (`structural`) + M7 langkah 5 sudah menghukum "pipa tanpa
   konsumen" sebagai kode yang tak pernah dijalankan.

7. **KUNCI 7 — "Tinjau kemampuan" hanya menetapkan LANTAI, tak pernah mastery.**
   `baseline` boleh tercatat sebagai teks di peta (alasan cut-list). Lantai sungguhan
   tetap ditentukan `/placement` yang sudah ada (§1.2 utuh). Skill wajib mengarahkan ke
   sana dan dilarang menulis status apa pun.

8. **KUNCI 8 — Batas "peta vs bab" dibuat MEKANIS, bukan disiplin prompt.** Tiga aturan
   yang bisa dijalankan mesin: (a) **dilarang blok kode** di file roadmap — code fence di
   peta adalah sinyal paling jujur bahwa ia berubah jadi materi; (b) **prosa non-kutipan
   dibatasi** `MAX_ROADMAP_PROSE_CHARS = 3000` (preseden `EXPLANATION_MAX_CHARS = 2500`
   di `config.py` — guardrail §8 yang bisa DIUJI); (c) tiap file roadmap wajib punya
   `source_refs` non-kosong yang sudah ter-snapshot.

9. **KUNCI 9 — Gerbang dibangun SEBELUM penulisnya** (urutan build §9). Roadmap lajur ini
   berdiri di atas prinsip "tiap fase memasang penjaga sebelum fase berikutnya menambah
   risiko"; prinsip yang sama berlaku di dalam L3.

**Batas yang diterima sadar (WAJIB dicatat di §7 CLAUDE.md saat eksekusi):**
- Kutipan verbatim membuktikan **kutipannya nyata**, bukan bahwa kutipan itu **menopang**
  entri petanya — itu penalaran, dan tak ada mesin di sini yang melakukannya. Kalimat ini
  sudah tertulis apa adanya di `grounding.py`; jangan mengklaim lebih.
- `--from-file` (`provenance: manual`) adalah lubang yang disisakan sengaja: ia ada untuk
  sumber non-URL (buku, PDF, transkrip). Penjaganya bukan mesin melainkan (a) label
  `provenance: manual` yang tampak di diff dan (b) larangan keras di SKILL: AI tak pernah
  memasok berkasnya sendiri.
- Halaman yang dirender JavaScript menghasilkan snapshot pendek/kosong; script menolaknya
  (< 500 karakter) alih-alih menyimpan snapshot palsu yang bisa dikutip sembarangan.

---

## 3. Daur hidup & kontrak

### 3.1 Alur data end-to-end

```
5 keputusan Bryant (tujuan · baseline · cut-list · milestone · waktu)
   │
   ├─(AI riset)→ entri baru di data/sources.yaml           [id · type · citation · url]
   │
   ├─(SCRIPT)→ scripts/fetch_source.py --id <id>
   │              └→ data/sources/<id>.md                  [provenance: fetch|manual]
   │
   ├─(AI baca SNAPSHOT, bukan web/ingatan)→ ambil kutipan verbatim per entri
   │
   ├─(AI rakit)→ scratchpad/spec.yaml   (kind: roadmap)
   │
   ├─(SCRIPT)→ scripts/library_scaffold.py --spec …
   │              ├─ tolak bila kutipan ⊄ snapshot  (gerbang TULIS)
   │              └→ library/<goal>/…                       create-only
   │
   └─(SCRIPT)→ scripts/verify_library.py                    (gerbang BACA)
```

Dua gerbang sengaja memeriksa hal yang sama di dua waktu berbeda: gerbang tulis mencegah
berkas cacat lahir, gerbang baca menangkap suntingan tangan sesudahnya (dan snapshot yang
berubah karena `--force`).

### 3.2 Bentuk hasil di `library/`

Sama persis dengan pohon L1 — yang berbeda hanya `type` di `_index` dan isi peta:

```
library/<goal-slug>/
  _index.md                 # type: roadmap   — tujuan, baseline, cut-list, daftar modul
  01-<modul>/
    _index.md               # type: roadmap   — PETA: entri + sitasi + kutipan + kandidat node
    <materi>.md             # type: note, status: outline — stub kosong milik Bryant
```

**`_index.md` course (roadmap):**

```markdown
---
title: "FastAPI sampai bisa deploy"
course: fastapi-produksi
module: ""
type: roadmap
source_refs: [fastapi_docs_first_steps, fastapi_docs_path_params]
node_ids: []
status: captured
created: 2026-09-05
---

# FastAPI sampai bisa deploy

**Tujuan:** bisa menulis & men-deploy API CRUD kecil sendiri.
**Baseline (lantai awal, BUKAN mastery):** sudah paham Python dasar, belum pernah
memakai framework web — lantai sungguhan ditentukan `/placement`, bukan berkas ini.
**Sengaja TIDAK dipelajari dulu:** async database · websockets · auth OAuth.

## Modul
- [[01-routing-dasar/_index|01 · Routing dasar]]
- [[02-request-body/_index|02 · Request body]]

> Peta ini menunjuk sumber asli; penjelasan tidak ditulis di sini (§8). Materi
> just-in-time muncul di Forge sesudah attempt gagal (gerbang 403).
```

**`_index.md` modul (roadmap) — di sinilah kutipan hidup:**

```markdown
---
title: "Routing dasar"
course: fastapi-produksi
module: 01-routing-dasar
type: roadmap
source_refs: [fastapi_docs_first_steps]
node_ids: []
status: captured
created: 2026-09-05
---

# 01 · Routing dasar

## Peta materi

### [[get-route-json|GET route JSON 200]]
**Reproduksi:** tulis route GET `/` yang mengembalikan JSON dengan status 200.
**Sumber:** `fastapi_docs_first_steps`
> "The simplest FastAPI file could look like this"
**Kandidat node:** `get-route-json` — belum ditempa (L4).

Lanjut: [[../02-request-body/_index|02 · Request body]]
```

**Stub materi (`type: note`, `status: outline`) — tak berubah dari L1 selain `source_refs`:**

```markdown
---
title: "GET route JSON 200"
course: fastapi-produksi
module: 01-routing-dasar
type: note
source_refs: [fastapi_docs_first_steps]
node_ids: []
status: outline
created: 2026-09-05
---

# GET route JSON 200

> `status: outline` — kerangka. Isi lewat note-refine (L2).

**Yang harus bisa kamu reproduksi:** tulis route GET `/` yang mengembalikan JSON
dengan status 200.
**Baca sumber aslinya:** `fastapi_docs_first_steps`

Balik: [[_index|Routing dasar]]
```

Sentinel stub L1 sengaja **dipertahankan**: selama ia ada, `verify_library.py --capture`
menolak flip ke `captured`. Peta yang lengkap tak pernah membuat catatan Bryant terlihat
sudah terisi.

### 3.3 Kontrak `spec.yaml` (jembatan Claude → script)

Perluasan kontrak L1. Field lama tetap; yang baru ditandai **(L3)**.

```yaml
course:
  slug: fastapi-produksi          # kebab-case, a-z0-9-
  title: "FastAPI sampai bisa deploy"
  source: "roadmap generate (learn-intake L3)"
  kind: roadmap                   # (L3) "course" (default, = L1) | "roadmap"
  goal: "Bisa menulis & men-deploy API CRUD kecil sendiri."      # (L3) wajib bila roadmap
  baseline: "Python dasar oke; belum pernah pakai framework web." # (L3) opsional
  cut_list:                       # (L3) opsional — yang sengaja ditunda
    - "async database"
    - "websockets"
modules:
  - slug: routing-dasar
    title: "Routing dasar"
    materials:
      - slug: get-route-json
        title: "GET route JSON 200"
        source_ref: fastapi_docs_first_steps     # (L3) wajib bila roadmap
        quote: "The simplest FastAPI file could look like this"   # (L3) wajib bila roadmap
        reproduce: "tulis route GET / yang mengembalikan JSON dengan status 200"  # (L3) wajib
        candidate_node: get-route-json           # (L3) opsional
```

**Aturan kontrak (ditegakkan `parse_spec`, semua pelanggaran → `SpecError`, nol berkas ditulis):**

| Aturan | Kenapa |
|---|---|
| `kind` ∈ `{course, roadmap}`; default `course` | jalur L1 tak boleh berubah perilaku |
| `kind: roadmap` → `goal` wajib non-kosong | peta tanpa tujuan bukan peta |
| `kind: roadmap` → tiap materi wajib `source_ref`, `quote`, `reproduce` | tiap entri peta bersitasi (gate keras roadmap L3) |
| `quote` ≥ 25 karakter setelah normalisasi spasi | potongan pendek cocok secara kebetulan (`MIN_QUOTE_CHARS`) |
| `reproduce` ≤ 200 karakter | satu kalimat "apa yang harus bisa kamu tulis ulang", bukan penjelasan |
| tak ada ``` di teks bebas mana pun | code fence = peta berubah jadi materi (KUNCI 8) |
| `source_ref` ada di `sources.yaml` **dan** snapshot-nya ada **dan** `quote` ⊆ snapshot | gerbang tulis (KUNCI 1) |
| `candidate_node` kebab-case bila diisi | dipakai L4 sebagai usulan slug node |
---

## 4. `scripts/_console.py` — helper bersama (12 baris, tapi wajib)

### 4.1 Kenapa ada
Konsol Windows default **cp1252**. Teks dokumentasi penuh `–`, `—`, `"`, `"`, `❯`.
M7 sudah membayar bug ini sekali: `verify_nodes.py` **mati** `UnicodeEncodeError` persis
saat sedang mencetak kegagalan — pesan yang paling dibutuhkan justru yang hilang
(§7 2026-09-01). Tiga script L3 mencetak potongan teks sumber, jadi ketiganya rawan.

### 4.2 Kode acuan (utuh)

```python
"""Helper konsol bersama untuk script di `scripts/`.

Dipisah karena tiga script L3 mencetak potongan TEKS SUMBER (dokumentasi resmi penuh
en-dash & kutip melengkung) ke konsol Windows cp1252. M7 sudah membayar bug ini sekali:
`verify_nodes.py` mati UnicodeEncodeError tepat ketika sedang melaporkan kegagalan.
"""
from __future__ import annotations

import sys


def force_utf8_stdio() -> None:
    """Paksa stdout/stderr ke UTF-8 (errors=replace). Aman dipanggil berkali-kali."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass  # stream diganti test (StringIO) — tak apa, tak ada yang perlu dipaksa
```

---

## 5. `scripts/fetch_source.py` — spesifikasi lengkap

### 5.1 Perilaku

| Mode | Perintah | Hasil |
|---|---|---|
| satu sumber | `--id <source_id>` | unduh `url_or_locator` → `data/sources/<id>.md` |
| semua | `--all` | semua entri `sources.yaml` ber-URL yang **belum** punya snapshot |
| non-URL | `--id <id> --from-file <berkas>` | salin teks berkas (buku/PDF/transkrip) |
| perbarui | `--force` | timpa snapshot lama (default: **skip** kalau sudah ada) |
| pratinjau | `--dry-run` | laporkan tanpa menulis |

**Exit code:** `0` sukses atau semua di-skip · `1` ada yang gagal unduh / hasilnya tak
layak · `2` argumen atau registry tidak valid.

**Default create-only** (skip bila sudah ada) konsisten dengan L1: snapshot adalah bahan
pembanding kutipan yang sudah dipakai, jadi memperbaruinya adalah tindakan sadar
(`--force`), bukan efek samping menjalankan ulang perintah.

### 5.2 Bentuk snapshot `data/sources/<id>.md`

```markdown
---
source_ref_id: fastapi_docs_first_steps
url_or_locator: https://fastapi.tiangolo.com/tutorial/first-steps/
provenance: fetch
fetched_at: 2026-09-05T10:12:33+00:00
char_count: 18422
---

First Steps
The simplest FastAPI file could look like this:
...
```

Gerbang kutipan mencocokkan **seluruh berkas** sebagai teks; frontmatter ikut terbaca dan
itu tak masalah — kutipan sah panjangnya ≥ 25 karakter prosa dan takkan cocok dengan
baris metadata.

### 5.3 Path & dependency
- `_REPO_ROOT = Path(__file__).resolve().parents[1]` (pola L1/L2).
- Dependency: **stdlib + `pyyaml` saja**. `urllib.request` + `html.parser` sudah cukup;
  `requests`/`beautifulsoup4` **tidak** ditambahkan (§4 CLAUDE.md: jangan menambah
  dependency tanpa alasan tercatat, dan di sini tak ada alasannya).
- Tidak mengimpor `app/` — script ini hanya menulis bahan, tak menegakkan gerbang.

### 5.4 Kode acuan (boleh ditranskripsi utuh)

```python
#!/usr/bin/env python3
"""Snapshot sumber otoritatif (L3 · grounding).

Menulis `data/sources/<id>.md` dari `url_or_locator` di `data/sources.yaml`. Snapshot
inilah bahan pembanding gerbang kutipan verbatim (`backend/app/services/grounding.py`)
yang dipakai gate R3 (M7) dan peta Library (L3).

ATURAN PALING PENTING: isi snapshot TIDAK PERNAH diketik manusia/AI dari ingatan. Ia
hasil unduhan script ini (`provenance: fetch`) atau salinan berkas yang Bryant sediakan
(`provenance: manual`). Kalau AI boleh mengarang snapshot, gerbang "kutipan ⊆ snapshot"
jadi melingkar: karang sumbernya, karang kutipannya, lolos.

Pemakaian:
    python scripts/fetch_source.py --id fastapi_docs_first_steps
    python scripts/fetch_source.py --all
    python scripts/fetch_source.py --id buku_bab3 --from-file bab3.txt
    python scripts/fetch_source.py --id … --force

Exit 0 sukses/skip · 1 gagal unduh atau hasil tak layak · 2 argumen/registry tidak valid.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import re
import sys
import urllib.error
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

import yaml
from _console import force_utf8_stdio

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SOURCES_YAML = _REPO_ROOT / "data" / "sources.yaml"
_SNAPSHOT_DIR = _REPO_ROOT / "data" / "sources"

_UA = "Mozilla/5.0 (compatible; ReproductionLearningEngine/1.0)"
_TIMEOUT_SECONDS = 20

#: Snapshot sependek ini hampir pasti bukan halamannya (dinding JS, halaman error,
#: layar consent). Menyimpannya justru berbahaya: ia menjadi "sumber" yang tak memuat
#: apa pun, sehingga SETIAP kutipan atasnya gagal — dan gagalnya membingungkan.
_MIN_SNAPSHOT_CHARS = 500

_SKIP_TAGS = {"script", "style", "noscript", "svg", "head", "template"}
_BLOCK_TAGS = {"p", "div", "section", "article", "br", "li", "ul", "ol", "tr", "table",
               "h1", "h2", "h3", "h4", "h5", "h6", "pre", "blockquote", "header",
               "footer", "nav", "aside", "main"}


class _HtmlToText(HTMLParser):
    """Pengupas tag seadanya — cukup untuk pencocokan substring, bukan renderer.

    Yang dikejar bukan tampilan cantik melainkan teks yang STABIL untuk dicocokkan.
    `convert_charrefs=True` sudah menerjemahkan entity; JANGAN `html.unescape()` lagi
    sesudahnya — halaman dokumentasi penuh contoh kode, dan unescape ganda mengubahnya.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._chunks: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag in _SKIP_TAGS:
            self._skip_depth += 1
        elif tag in _BLOCK_TAGS:
            self._chunks.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in _SKIP_TAGS:
            self._skip_depth = max(0, self._skip_depth - 1)
        elif tag in _BLOCK_TAGS:
            self._chunks.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth == 0:
            self._chunks.append(data)

    def text(self) -> str:
        return "".join(self._chunks)


def html_to_text(raw: str) -> str:
    parser = _HtmlToText()
    parser.feed(raw)
    parser.close()
    text = re.sub(r"[ \t\u00a0]+", " ", parser.text())  # spasi, tab, nbsp
    text = "\n".join(line.strip() for line in text.splitlines())
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def fetch_url(url: str) -> str:
    """Teks polos satu URL. Melempar urllib.error.* / OSError bila gagal."""
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    with urllib.request.urlopen(req, timeout=_TIMEOUT_SECONDS) as resp:
        ctype = (resp.headers.get_content_type() or "").lower()
        charset = resp.headers.get_content_charset() or "utf-8"
        raw = resp.read().decode(charset, errors="replace")
    return html_to_text(raw) if "html" in ctype else raw.strip()


def load_registry() -> dict[str, dict]:
    data = yaml.safe_load(_SOURCES_YAML.read_text("utf-8")) or {}
    return {s["id"]: s for s in data.get("sources", [])
            if isinstance(s, dict) and "id" in s}


def snapshot_text(entry: dict, body: str, provenance: str, fetched_at: str) -> str:
    fm = {"source_ref_id": entry["id"],
          "url_or_locator": entry.get("url_or_locator", ""),
          "provenance": provenance,
          "fetched_at": fetched_at,
          "char_count": len(body)}
    dumped = yaml.safe_dump(fm, sort_keys=False, allow_unicode=True).strip()
    return f"---\n{dumped}\n---\n\n{body}\n"


def snapshot_one(sid: str, entry: dict, args: argparse.Namespace,
                 fetched_at: str) -> tuple[str, str]:
    """(status, pesan) dengan status ∈ {created, skipped, failed}. Tak melempar."""
    path = _SNAPSHOT_DIR / f"{sid}.md"
    if path.exists() and not args.force:
        return "skipped", "sudah ada (pakai --force untuk memperbarui)"

    if args.from_file:
        try:
            body = args.from_file.read_text("utf-8").strip()
        except OSError as exc:
            return "failed", f"gagal membaca --from-file: {exc}"
        provenance = "manual"
    else:
        locator = str(entry.get("url_or_locator", ""))
        if not locator.startswith(("http://", "https://")):
            return "failed", (f"locator bukan URL ({locator!r}) — sumber seperti ini "
                              "harus disalin MANUSIA lewat --from-file")
        try:
            body = fetch_url(locator)
        except (urllib.error.URLError, OSError, ValueError) as exc:
            return "failed", f"gagal mengunduh {locator}: {exc}"
        provenance = "fetch"

    if len(body) < _MIN_SNAPSHOT_CHARS:
        return "failed", (f"hasil cuma {len(body)} karakter (< {_MIN_SNAPSHOT_CHARS}) — "
                          "halaman mungkin butuh JavaScript; salin manual via --from-file")

    if not args.dry_run:
        _SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
        path.write_text(snapshot_text(entry, body, provenance, fetched_at),
                        encoding="utf-8")
    return "created", f"{len(body)} karakter · provenance={provenance}"


def resolve_targets(args: argparse.Namespace, registry: dict[str, dict]) -> list[str]:
    if not args.all:
        return [args.id]
    return [sid for sid, e in registry.items()
            if str(e.get("url_or_locator", "")).startswith(("http://", "https://"))]


def main(argv: list[str]) -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="Snapshot sumber otoritatif (L3).")
    grp = ap.add_mutually_exclusive_group(required=True)
    grp.add_argument("--id", help="id SourceRef di data/sources.yaml")
    grp.add_argument("--all", action="store_true",
                     help="semua sumber ber-URL di registry")
    ap.add_argument("--from-file", type=Path,
                    help="ambil teks dari berkas (untuk sumber non-URL)")
    ap.add_argument("--force", action="store_true", help="timpa snapshot yang ada")
    ap.add_argument("--dry-run", action="store_true", help="laporkan tanpa menulis")
    args = ap.parse_args(argv)

    if args.from_file and args.all:
        print("--from-file hanya untuk satu --id", file=sys.stderr)
        return 2
    try:
        registry = load_registry()
    except (OSError, yaml.YAMLError) as exc:
        print(f"REGISTRY TIDAK TERBACA: {exc}", file=sys.stderr)
        return 2
    if args.id and args.id not in registry:
        print(f"id {args.id!r} tak ada di data/sources.yaml — daftarkan dulu di sana",
              file=sys.stderr)
        return 2

    fetched_at = _dt.datetime.now(tz=_dt.UTC).isoformat(timespec="seconds")
    targets = resolve_targets(args, registry)
    failed = 0
    tag = "(dry-run) " if args.dry_run else ""
    print(f"{tag}snapshot: {len(targets)} sumber")
    for sid in targets:
        status, msg = snapshot_one(sid, registry[sid], args, fetched_at)
        marker = {"created": "+", "skipped": "=", "failed": "x"}[status]
        print(f"  {marker} {sid}: {msg}")
        if status == "failed":
            failed += 1
    if failed:
        print(f"\n{failed} sumber gagal di-snapshot.", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
```

> **Catatan transkripsi:** baris penanda status di `main()` sengaja ditulis panjang di
> atas; kalau kamu mau lebih bersih, ganti dengan
> `marker = {"created": "+", "skipped": "=", "failed": "x"}[status]` lalu
> `print(f"  {marker} {sid}: {msg}")`. Hasilnya sama; pilih yang paling kamu paham.

---

## 6. `scripts/library_scaffold.py` — perluasan `kind: roadmap`

**Jalur L1 tak boleh berubah perilaku.** Semua yang di bawah ini aktif hanya bila
`course.kind == "roadmap"`; tanpa field itu, script berperilaku persis seperti L1
(dijaga test regresi §8.3).

### 6.1 Tambahan konstanta & import

```python
# --- L3: gerbang grounding DIPINJAM dari backend, bukan ditulis ulang ------------
# Aturan kutipan verbatim sudah hidup di `app/services/grounding.py` (gate R3/M7).
# Dua implementasi atas gerbang yang SAMA akan menyimpang diam-diam — dan yang
# menyimpang adalah gerbang inti L3. Karena itu di-import, bukan disalin.
sys.path.insert(0, str(_REPO_ROOT / "backend"))
from app.services.grounding import MIN_QUOTE_CHARS, normalize  # noqa: E402

_SOURCES_YAML = _REPO_ROOT / "data" / "sources.yaml"
_SNAPSHOT_DIR = _REPO_ROOT / "data" / "sources"
_VALID_KIND = {"course", "roadmap"}
#: Satu kalimat "apa yang harus bisa kamu tulis ulang". Lebih panjang dari ini berarti
#: ia sudah menjelaskan, dan peta tidak menjelaskan (KUNCI 8).
_MAX_REPRODUCE_CHARS = 200
```

### 6.2 Dataclass yang diperluas

```python
@dataclass
class Material:
    slug: str
    title: str
    source_ref: str = ""      # (L3) id di data/sources.yaml
    quote: str = ""           # (L3) kutipan verbatim dari snapshot sumber
    reproduce: str = ""       # (L3) satu kalimat tujuan reproduksi
    candidate_node: str = ""  # (L3) usulan node Forge — LABEL, bukan node id


@dataclass
class Course:
    slug: str
    title: str
    source: str
    modules: list[Module]
    kind: str = "course"                              # (L3)
    goal: str = ""                                    # (L3)
    baseline: str = ""                                # (L3)
    cut_list: list[str] = field(default_factory=list) # (L3)
```

> `candidate_node` sengaja **kebab-case**, bukan berbentuk node id Forge
> (`n002_get_json_route`). Ia usulan, bukan pointer — bentuk yang berbeda mencegahnya
> salah dibaca sebagai node yang sudah ada.

### 6.3 Tambahan validasi di `parse_spec`

```python
def _no_fence(text: str, where: str) -> None:
    _require("```" not in text, f"{where}: dilarang blok kode di peta (peta menunjuk "
                                "sumber, tidak mengajarkan)")
```

Di dalam `parse_spec`, setelah `source` dibaca:

```python
    kind = c.get("kind", "course")
    _require(kind in _VALID_KIND, f"course.kind harus course|roadmap: {kind!r}")
    goal = str(c.get("goal") or "").strip()
    baseline = str(c.get("baseline") or "").strip()
    raw_cut = c.get("cut_list") or []
    _require(isinstance(raw_cut, list), "course.cut_list harus list")
    cut_list = [str(x).strip() for x in raw_cut if str(x).strip()]
    if kind == "roadmap":
        _require(bool(goal), "course.goal wajib diisi untuk kind: roadmap")
    for text, where in ((title, "course.title"), (source, "course.source"),
                        (goal, "course.goal"), (baseline, "course.baseline")):
        _no_fence(text, where)
```

Di dalam loop materi, setelah `att` divalidasi:

```python
            src_ref = str(a.get("source_ref") or "").strip()
            quote = str(a.get("quote") or "").strip()
            reproduce = str(a.get("reproduce") or "").strip()
            cand = str(a.get("candidate_node") or "").strip()
            if kind == "roadmap":
                _require(bool(src_ref), f"{asg}: source_ref wajib untuk kind: roadmap")
                _require("\n" not in quote, f"{asg}: quote harus SATU baris")
                _require(len(normalize(quote)) >= MIN_QUOTE_CHARS,
                         f"{asg}: quote minimal {MIN_QUOTE_CHARS} karakter — potongan "
                         "sependek itu cocok secara kebetulan")
                _require(bool(reproduce), f"{asg}: reproduce wajib (satu kalimat)")
                _require(len(reproduce) <= _MAX_REPRODUCE_CHARS,
                         f"{asg}: reproduce > {_MAX_REPRODUCE_CHARS} karakter — itu "
                         "penjelasan, bukan tujuan reproduksi")
            _require(not cand or _valid_slug(cand),
                     f"{asg}: candidate_node harus kebab-case: {cand!r}")
            _no_fence(quote, f"{asg}.quote")
            _no_fence(reproduce, f"{asg}.reproduce")
            mats.append(Material(asg, att.strip(), src_ref, quote, reproduce, cand))
```

dan `return Course(slug, title.strip(), source.strip(), modules, kind, goal, baseline, cut_list)`.

### 6.4 Gerbang TULIS: `check_grounding`

```python
def load_source_ids() -> set[str]:
    data = yaml.safe_load(_SOURCES_YAML.read_text("utf-8")) or {}
    return {s["id"] for s in data.get("sources", [])
            if isinstance(s, dict) and "id" in s}


def check_grounding(course: Course, *, snapshot_dir: Path | None = None) -> list[str]:
    """Gerbang TULIS L3: tiap kutipan wajib benar-benar ADA di snapshot sumbernya.

    Dijalankan SEBELUM satu berkas pun ditulis, jadi peta cacat tak pernah lahir.
    Yang dibuktikan: kutipannya nyata. Yang TIDAK dibuktikan: bahwa kutipan itu
    menopang entri petanya — itu penalaran, dan tak ada mesin di sini yang melakukannya.
    """
    if course.kind != "roadmap":
        return []
    snap_dir = snapshot_dir or _SNAPSHOT_DIR
    known = load_source_ids()
    cache: dict[str, str | None] = {}
    problems: list[str] = []
    for mod in course.modules:
        for mat in mod.materials:
            sid = mat.source_ref
            where = f"{mod.slug}/{mat.slug}"
            if sid not in known:
                problems.append(f"{where}: source_ref {sid!r} tak ada di sources.yaml")
                continue
            if sid not in cache:
                p = snap_dir / f"{sid}.md"
                cache[sid] = p.read_text("utf-8") if p.is_file() else None
            snap = cache[sid]
            if snap is None:
                problems.append(f"{where}: {sid} belum di-snapshot — jalankan "
                                f"scripts/fetch_source.py --id {sid}")
            elif normalize(mat.quote) not in normalize(snap):
                problems.append(f"{where}: kutipan TIDAK ada di snapshot {sid}: "
                                f"{mat.quote[:60]!r}")
    return problems
```

### 6.5 Template roadmap

```python
def course_index_roadmap_md(course: Course, nn: dict[str, str], created: str) -> str:
    refs = sorted({m.source_ref for mod in course.modules
                   for m in mod.materials if m.source_ref})
    fm = _frontmatter(title=course.title, course=course.slug, module="",
                      type="roadmap", source_refs=refs, node_ids=[],
                      status="captured", created=created)
    mods = "\n".join(f"- [[{nn[m.slug]}-{m.slug}/_index|{nn[m.slug]} · {m.title}]]"
                     for m in course.modules)
    head = [f"{fm}\n# {course.title}\n", f"**Tujuan:** {course.goal}\n"]
    if course.baseline:
        head.append(f"**Baseline (lantai awal, BUKAN mastery):** {course.baseline} — "
                    "lantai sungguhan ditentukan `/placement`, bukan berkas ini.\n")
    if course.cut_list:
        head.append("**Sengaja TIDAK dipelajari dulu:** "
                    + " · ".join(course.cut_list) + "\n")
    tail = ("\n> Peta ini menunjuk sumber asli; penjelasan tidak ditulis di sini.\n"
            "> Materi just-in-time muncul di Forge sesudah attempt gagal (gerbang 403).\n")
    return "\n".join(head) + f"\n## Modul\n{mods}\n" + tail


def module_index_roadmap_md(course: Course, mod: Module, nn: dict[str, str],
                            prev: Module | None, nxt: Module | None,
                            created: str) -> str:
    my = nn[mod.slug]
    refs = sorted({m.source_ref for m in mod.materials if m.source_ref})
    fm = _frontmatter(title=mod.title, course=course.slug,
                      module=f"{my}-{mod.slug}", type="roadmap", source_refs=refs,
                      node_ids=[], status="captured", created=created)
    entries = []
    for mat in mod.materials:
        block = [f"### [[{mat.slug}|{mat.title}]]",
                 f"**Reproduksi:** {mat.reproduce}",
                 f"**Sumber:** `{mat.source_ref}`",
                 f'> "{mat.quote}"']
        if mat.candidate_node:
            block.append(f"**Kandidat node:** `{mat.candidate_node}` — "
                         "belum ditempa (L4).")
        entries.append("\n".join(block))
    body = ("\n\n".join(entries) if entries
            else "*(peta modul kosong — tambahkan materi di spec)*")
    nav = []
    if prev:
        nav.append(f"Balik: [[../{nn[prev.slug]}-{prev.slug}/_index|"
                   f"{nn[prev.slug]} · {prev.title}]]")
    if nxt:
        nav.append(f"Lanjut: [[../{nn[nxt.slug]}-{nxt.slug}/_index|"
                   f"{nn[nxt.slug]} · {nxt.title}]]")
    nav_line = ("\n" + " · ".join(nav) + "\n") if nav else ""
    return f"{fm}\n# {my} · {mod.title}\n\n## Peta materi\n\n{body}\n{nav_line}"
```

**Bentuk baris kutipan `> "…"` itu KONTRAK**, bukan gaya: `verify_library.py` mengenali
kutipan justru dari bentuk ini (§7.2). Mengubahnya membuat kutipan lolos tanpa diperiksa.

### 6.6 `material_md` diperluas (satu template, dua kelakuan)

```python
def material_md(course: Course, mod: Module, nn: dict[str, str],
                mat: Material, created: str) -> str:
    """Stub materi. Untuk kind: roadmap ia membawa POINTER (tujuan reproduksi + id
    sumber) tapi TAK PERNAH kutipan: kutipan hidup di file peta yang diverifikasi.
    Sentinel stub dipertahankan supaya `--capture` (L2) tetap menolak flip status
    sampai Bryant benar-benar menulis catatannya.
    """
    fm = _frontmatter(title=mat.title, course=course.slug,
                      module=f"{nn[mod.slug]}-{mod.slug}", type="note",
                      source_refs=[mat.source_ref] if mat.source_ref else [],
                      node_ids=[], status="outline", created=created)
    extra = ""
    if mat.reproduce:
        extra += f"**Yang harus bisa kamu reproduksi:** {mat.reproduce}\n"
    if mat.source_ref:
        extra += f"**Baca sumber aslinya:** `{mat.source_ref}`\n"
    if extra:
        extra += "\n"
    return (f"{fm}\n# {mat.title}\n\n"
            "> `status: outline` — kerangka. Isi lewat note-refine (L2).\n\n"
            f"{extra}Balik: [[_index|{mod.title}]]\n")
```

### 6.7 `scaffold()` & `main()`

Di `scaffold()`, pilih template sekali di atas (tak ada `if` per berkas):

```python
    course_tpl = (course_index_roadmap_md if course.kind == "roadmap"
                  else course_index_md)
    module_tpl = (module_index_roadmap_md if course.kind == "roadmap"
                  else module_index_md)
```

Di `main()`, **sebelum** `scaffold(...)`:

```python
    problems = check_grounding(course)
    if problems:
        print("GROUNDING GAGAL — tak ada berkas yang ditulis:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 2
```

dan `force_utf8_stdio()` sebagai baris pertama `main()`.

---

## 7. `scripts/verify_library.py` — aturan L3 (gerbang BACA)

### 7.1 Aturan baru (hanya untuk file `type: roadmap`)

| # | Aturan | Pesan gagal menyebut | Kenapa |
|---|---|---|---|
| R1 | tak boleh ada code fence (```` ``` ````) | "peta memuat blok kode" | code fence = peta berubah jadi materi (§8) |
| R2 | `source_refs` wajib non-kosong | "wajib minimal satu source_refs" | peta tanpa sitasi = peta tanpa gigi |
| R3 | tiap `source_ref` wajib punya `data/sources/<id>.md` | perintah `fetch_source.py --id …` | tanpa snapshot, kutipan tak bisa dicocokkan |
| R4 | tiap kutipan `> "…"` wajib verbatim ada di salah satu snapshot `source_refs` | 60 karakter pertama kutipan | inti gerbang L3 |
| R5 | kutipan ≥ `MIN_QUOTE_CHARS` (25) | panjang aktual | potongan pendek cocok kebetulan |
| R6 | prosa non-kutipan ≤ 3000 karakter | jumlah aktual | peta, bukan bab (preseden `EXPLANATION_MAX_CHARS`) |

Aturan L2 yang sudah ada **tidak berubah**, dan sengaja **tidak** diperluas ke file
`note`: kutipan di catatan Bryant adalah tulisannya sendiri, bukan klaim generate.

### 7.2 Tambahan kode acuan

```python
import re  # (bila belum ada)

from _console import force_utf8_stdio

# --- L3: gerbang kutipan DIPINJAM dari backend (satu sumber kebenaran) -----------
sys.path.insert(0, str(_REPO_ROOT / "backend"))
from app.services.grounding import MIN_QUOTE_CHARS, normalize  # noqa: E402

_SNAPSHOT_DIR = _REPO_ROOT / "data" / "sources"
#: Peta = pointer + sitasi, bukan bab. Preseden: EXPLANATION_MAX_CHARS = 2500 di
#: config.py — guardrail §8 yang bisa DIUJI. Baris kutipan TIDAK ikut dihitung: yang
#: dibatasi adalah prosa yang ditulis AI, bukan teks sumber yang dikutip.
MAX_ROADMAP_PROSE_CHARS = 3000
#: Kutipan = baris blockquote yang SELURUHNYA berada di dalam tanda kutip ganda.
#: Blockquote lain (catatan, sentinel stub, nav) sengaja tidak dianggap kutipan —
#: kalau tidak, tiap catatan pinggir jadi kewajiban sitasi palsu.
_QUOTE_RE = re.compile(r'^>\s*"(.+)"\s*$')
_FENCE_RE = re.compile(r"^\s*```")


def extract_quotes(body: str) -> list[str]:
    out = []
    for line in body.splitlines():
        m = _QUOTE_RE.match(line.strip())
        if m:
            out.append(m.group(1).strip())
    return out


def _prose_chars(body: str) -> int:
    return sum(len(line.strip()) for line in body.splitlines()
               if not line.lstrip().startswith(">"))


def roadmap_errors(fm: dict, body: str, *, snapshot_dir: Path | None = None) -> list[str]:
    """Aturan L3 untuk file `type: roadmap`. Kumpulkan SEMUA pelanggaran."""
    snap_dir = snapshot_dir or _SNAPSHOT_DIR
    errs: list[str] = []

    if any(_FENCE_RE.match(line) for line in body.splitlines()):
        errs.append("peta memuat blok kode — peta menunjuk sumber, tidak mengajarkan")

    refs = fm.get("source_refs")
    refs = refs if isinstance(refs, list) else []
    if not refs:
        errs.append("file roadmap wajib punya minimal satu source_refs")

    haystacks: list[str] = []
    for sid in refs:
        path = snap_dir / f"{sid}.md"
        if path.is_file():
            haystacks.append(normalize(path.read_text("utf-8")))
        else:
            errs.append(f"{sid} belum di-snapshot — jalankan "
                        f"scripts/fetch_source.py --id {sid}")

    for quote in extract_quotes(body):
        norm = normalize(quote)
        if len(norm) < MIN_QUOTE_CHARS:
            errs.append(f"kutipan terlalu pendek ({len(norm)} < {MIN_QUOTE_CHARS}): "
                        f"{quote[:40]!r}")
        elif not any(norm in hay for hay in haystacks):
            errs.append(f"kutipan TIDAK ada di snapshot sumbernya: {quote[:60]!r}")

    prose = _prose_chars(body)
    if prose > MAX_ROADMAP_PROSE_CHARS:
        errs.append(f"prosa peta {prose} karakter > {MAX_ROADMAP_PROSE_CHARS} — "
                    "ini sudah jadi bab, bukan peta")
    return errs
```

Sambungkan di `validate_file`, tepat sebelum `return errs`:

```python
    if fm.get("type") == "roadmap":
        errs += roadmap_errors(fm, body)
```

dan `force_utf8_stdio()` sebagai baris pertama `main()`.

> **Kenapa `capture()` tidak ikut diubah:** file roadmap lahir dengan
> `status: captured` dari scaffolder dan bukan milik alur L2 (`--capture` hanya untuk
> `note`/`transcription`). Menambah cabang di sana berarti menulis kode yang tak pernah
> dijalankan.
---

## 8. Test eksplisit

Gaya rumah: test berdiri di `scripts/`, mem-`monkeypatch` konstanta path supaya **tak
pernah** menyentuh `library/` atau `data/` sungguhan. Jalankan dari repo root:

```
backend/.venv/Scripts/python.exe -m pytest scripts/ -q
```

### 8.1 `scripts/test_fetch_source.py` (baru)

```python
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
import fetch_source as fs  # noqa: E402

ENTRY = {"id": "demo_docs", "type": "official_docs", "citation": "Demo",
         "url_or_locator": "https://example.test/demo"}
BOOK = {"id": "demo_buku", "type": "textbook_toc", "citation": "Buku",
        "url_or_locator": "textbook:demo/toc"}
LONG = "Kalimat sumber yang cukup panjang untuk lolos ambang minimum. " * 20


class Args:
    """Pengganti argparse.Namespace supaya test tak perlu mem-parse CLI."""

    def __init__(self, **over):
        self.id, self.all, self.from_file = "demo_docs", False, None
        self.force = self.dry_run = False
        self.__dict__.update(over)


@pytest.fixture
def snap(tmp_path, monkeypatch):
    d = tmp_path / "data" / "sources"
    monkeypatch.setattr(fs, "_SNAPSHOT_DIR", d)
    monkeypatch.setattr(fs, "load_registry", lambda: {"demo_docs": ENTRY,
                                                      "demo_buku": BOOK})
    return d


def test_html_to_text_buang_script_style_dan_rapikan(snap):
    html = ("<html><head><style>p{color:red}</style></head>"
            "<body><p>Halo dunia</p><script>x=1</script><p>Baris dua</p></body></html>")
    out = fs.html_to_text(html)
    assert "Halo dunia" in out and "Baris dua" in out
    assert "color:red" not in out and "x=1" not in out


def test_fetch_menulis_snapshot_dengan_provenance_fetch(snap, monkeypatch):
    monkeypatch.setattr(fs, "fetch_url", lambda url: LONG)
    status, _ = fs.snapshot_one("demo_docs", ENTRY, Args(), "2026-09-05T00:00:00+00:00")
    assert status == "created"
    text = (snap / "demo_docs.md").read_text("utf-8")
    assert "provenance: fetch" in text and "source_ref_id: demo_docs" in text
    assert LONG.strip()[:40] in text


def test_skip_bila_snapshot_sudah_ada(snap, monkeypatch):
    monkeypatch.setattr(fs, "fetch_url", lambda url: LONG)
    fs.snapshot_one("demo_docs", ENTRY, Args(), "t")
    status, msg = fs.snapshot_one("demo_docs", ENTRY, Args(), "t")
    assert status == "skipped" and "--force" in msg


def test_force_menimpa(snap, monkeypatch):
    monkeypatch.setattr(fs, "fetch_url", lambda url: LONG)
    fs.snapshot_one("demo_docs", ENTRY, Args(), "t")
    monkeypatch.setattr(fs, "fetch_url", lambda url: LONG + "TAMBAHAN")
    status, _ = fs.snapshot_one("demo_docs", ENTRY, Args(force=True), "t")
    assert status == "created"
    assert "TAMBAHAN" in (snap / "demo_docs.md").read_text("utf-8")


def test_hasil_terlalu_pendek_ditolak(snap, monkeypatch):
    monkeypatch.setattr(fs, "fetch_url", lambda url: "dinding JS")
    status, msg = fs.snapshot_one("demo_docs", ENTRY, Args(), "t")
    assert status == "failed" and "JavaScript" in msg
    assert not (snap / "demo_docs.md").exists()


def test_locator_bukan_url_minta_from_file(snap):
    status, msg = fs.snapshot_one("demo_buku", BOOK, Args(id="demo_buku"), "t")
    assert status == "failed" and "--from-file" in msg


def test_from_file_ditandai_provenance_manual(snap, tmp_path):
    src = tmp_path / "bab3.txt"
    src.write_text(LONG, encoding="utf-8")
    status, _ = fs.snapshot_one("demo_buku", BOOK,
                                Args(id="demo_buku", from_file=src), "t")
    assert status == "created"
    assert "provenance: manual" in (snap / "demo_buku.md").read_text("utf-8")


def test_id_tak_dikenal_exit_2(snap):
    assert fs.main(["--id", "tak_ada"]) == 2


def test_dry_run_tak_menulis(snap, monkeypatch):
    monkeypatch.setattr(fs, "fetch_url", lambda url: LONG)
    status, _ = fs.snapshot_one("demo_docs", ENTRY, Args(dry_run=True), "t")
    assert status == "created" and not (snap / "demo_docs.md").exists()
```

### 8.2 Tambahan di `scripts/test_verify_library.py`

```python
SNAPSHOT = ("---\nsource_ref_id: fastapi_docs_first_steps\n---\n\n"
            "The simplest FastAPI file could look like this, with one decorator.\n")
QUOTE = "The simplest FastAPI file could look like this"


@pytest.fixture
def snaps(lib, tmp_path, monkeypatch):
    d = tmp_path / "data" / "sources"
    d.mkdir(parents=True)
    (d / "fastapi_docs_first_steps.md").write_text(SNAPSHOT, encoding="utf-8")
    monkeypatch.setattr(vl, "_SNAPSHOT_DIR", d)
    return d


def _roadmap_fm(**over):
    base = _fm(type="roadmap", source_refs=["fastapi_docs_first_steps"])
    base.update(over)
    return base


def _peta_body(quote=QUOTE, extra=""):
    return (f"\n# Routing dasar\n\n## Peta materi\n\n### [[get|GET route]]\n"
            f"**Reproduksi:** tulis route GET /.\n"
            f"**Sumber:** `fastapi_docs_first_steps`\n> \"{quote}\"\n{extra}")


def test_roadmap_kutipan_cocok_lolos(lib, snaps):
    p = _write(lib, "fastapi-dasar/01-routing-dasar/_index.md",
               _roadmap_fm(), _peta_body())
    assert vl.validate_file(p, SRC_IDS, NODE_IDS) == []


def test_roadmap_kutipan_karangan_ditolak(lib, snaps):
    p = _write(lib, "fastapi-dasar/01-routing-dasar/_index.md", _roadmap_fm(),
               _peta_body(quote="FastAPI otomatis membuat migrasi database untukmu"))
    assert any("TIDAK ada di snapshot" in e
               for e in vl.validate_file(p, SRC_IDS, NODE_IDS))


def test_roadmap_sumber_belum_di_snapshot_ditolak(lib, snaps):
    p = _write(lib, "fastapi-dasar/01-routing-dasar/_index.md",
               _roadmap_fm(source_refs=["fastapi_official_docs"]), _peta_body())
    errs = vl.validate_file(p, SRC_IDS, NODE_IDS)
    assert any("belum di-snapshot" in e for e in errs)


def test_roadmap_blok_kode_ditolak(lib, snaps):
    p = _write(lib, "fastapi-dasar/01-routing-dasar/_index.md", _roadmap_fm(),
               _peta_body(extra="\n```python\napp = FastAPI()\n```\n"))
    assert any("blok kode" in e for e in vl.validate_file(p, SRC_IDS, NODE_IDS))


def test_roadmap_tanpa_source_refs_ditolak(lib, snaps):
    p = _write(lib, "fastapi-dasar/01-routing-dasar/_index.md",
               _roadmap_fm(source_refs=[]), "\n# Peta kosong\n\nsatu baris.\n")
    assert any("minimal satu source_refs" in e
               for e in vl.validate_file(p, SRC_IDS, NODE_IDS))


def test_roadmap_kutipan_terlalu_pendek_ditolak(lib, snaps):
    p = _write(lib, "fastapi-dasar/01-routing-dasar/_index.md", _roadmap_fm(),
               _peta_body(quote="FastAPI file"))
    assert any("terlalu pendek" in e for e in vl.validate_file(p, SRC_IDS, NODE_IDS))


def test_roadmap_prosa_kepanjangan_ditolak(lib, snaps):
    p = _write(lib, "fastapi-dasar/01-routing-dasar/_index.md", _roadmap_fm(),
               _peta_body(extra="\n" + ("penjelasan panjang. " * 200)))
    assert any("sudah jadi bab" in e for e in vl.validate_file(p, SRC_IDS, NODE_IDS))


def test_aturan_roadmap_tak_menyentuh_file_note(lib, snaps):
    """Kutipan di catatan Bryant adalah tulisannya sendiri — bukan klaim generate."""
    p = _write(lib, "fastapi-dasar/01-routing-dasar/get.md", _fm(),
               '\n# GET\n\ncatatanku.\n\n> "kutipan bebas yang tak ada di snapshot"\n')
    assert vl.validate_file(p, SRC_IDS, NODE_IDS) == []
```

### 8.3 Tambahan di `scripts/test_library_scaffold.py`

```python
SNAPSHOT = ("---\nsource_ref_id: demo_docs\n---\n\n"
            "The simplest FastAPI file could look like this, with one decorator.\n")
QUOTE = "The simplest FastAPI file could look like this"


def _roadmap_spec(**mat_over):
    mat = {"slug": "get-route", "title": "GET route JSON",
           "source_ref": "demo_docs", "quote": QUOTE,
           "reproduce": "tulis route GET / yang mengembalikan JSON 200",
           "candidate_node": "get-route-json"}
    mat.update(mat_over)
    return {"course": {"slug": "fastapi-produksi", "title": "FastAPI Produksi",
                       "source": "roadmap generate (L3)", "kind": "roadmap",
                       "goal": "bisa men-deploy API CRUD kecil",
                       "baseline": "Python dasar oke", "cut_list": ["websockets"]},
            "modules": [{"slug": "routing-dasar", "title": "Routing dasar",
                         "materials": [mat]}]}


@pytest.fixture
def snaps(tmp_path, monkeypatch):
    d = tmp_path / "data" / "sources"
    d.mkdir(parents=True)
    (d / "demo_docs.md").write_text(SNAPSHOT, encoding="utf-8")
    monkeypatch.setattr(ls, "_SNAPSHOT_DIR", d)
    monkeypatch.setattr(ls, "load_source_ids", lambda: {"demo_docs"})
    return d


def test_roadmap_menghasilkan_peta_bersitasi(lib, snaps):
    course = ls.parse_spec(_roadmap_spec())
    assert ls.check_grounding(course) == []
    ls.scaffold(course, "2026-09-05")
    peta = (lib / "fastapi-produksi/01-routing-dasar/_index.md").read_text("utf-8")
    assert "type: roadmap" in peta
    assert f'> "{QUOTE}"' in peta
    assert "Kandidat node:" in peta
    stub = (lib / "fastapi-produksi/01-routing-dasar/get-route.md").read_text("utf-8")
    assert "type: note" in stub and "status: outline" in stub
    assert "demo_docs" in stub and "kerangka" in stub      # sentinel L1 dipertahankan
    assert QUOTE not in stub                                # kutipan hanya di peta


def test_roadmap_tanpa_quote_ditolak(lib, snaps):
    with pytest.raises(ls.SpecError):
        ls.parse_spec(_roadmap_spec(quote=""))


def test_roadmap_quote_terlalu_pendek_ditolak(lib, snaps):
    with pytest.raises(ls.SpecError):
        ls.parse_spec(_roadmap_spec(quote="FastAPI file"))


def test_roadmap_blok_kode_di_spec_ditolak(lib, snaps):
    with pytest.raises(ls.SpecError):
        ls.parse_spec(_roadmap_spec(reproduce="tulis ```python app=FastAPI()```"))


def test_grounding_menolak_kutipan_yang_tak_ada_di_snapshot(lib, snaps):
    course = ls.parse_spec(_roadmap_spec(
        quote="FastAPI otomatis membuat migrasi database untukmu"))
    assert any("TIDAK ada di snapshot" in p for p in ls.check_grounding(course))


def test_grounding_menolak_sumber_tanpa_snapshot(lib, snaps, monkeypatch):
    monkeypatch.setattr(ls, "load_source_ids", lambda: {"demo_docs", "lain"})
    course = ls.parse_spec(_roadmap_spec(source_ref="lain"))
    assert any("belum di-snapshot" in p for p in ls.check_grounding(course))


def test_jalur_L1_tak_berubah(lib):
    """Regresi: spec tanpa `kind` tetap menghasilkan course biasa (type: outline)."""
    spec = {"course": {"slug": "c", "title": "C", "source": "x"},
            "modules": [{"slug": "m", "title": "M",
                         "materials": [{"slug": "a", "title": "A"}]}]}
    course = ls.parse_spec(spec)
    assert course.kind == "course" and ls.check_grounding(course) == []
    ls.scaffold(course, "2026-09-05")
    assert "type: outline" in (lib / "c/01-m/_index.md").read_text("utf-8")
```

> Sesuaikan nama fixture `lib` dengan yang sudah ada di berkas test masing-masing
> (`test_library_scaffold.py` sudah punya fixture yang mem-`monkeypatch`
> `_LIBRARY_ROOT`; jangan bikin yang kedua).

---

## 9. `.claude/skills/learn-intake/SKILL.md` — isi lengkap

```markdown
---
name: learn-intake
description: Ubah tujuan belajar Bryant menjadi PETA belajar bersitasi di library/ — roadmap, kerangka modul, sitasi ke sumber otoritatif dengan kutipan terverifikasi, dan usul kandidat node Forge. Gunakan saat Bryant ingin belajar sesuatu dari nol dan butuh arah. BUKAN untuk menulis materi/penjelasan (itu artifacts/ + gerbang 403), mengisi catatan (note-refine), atau menilai penguasaan.
---

# learn-intake — peta belajar bersitasi ke `library/`

Mengubah tujuan Bryant menjadi **peta**: roadmap + modul + sitasi + kutipan verbatim +
kandidat node. **Bukan** bab materi. **Nol klaim mastery.**
Format & batas: [`../../../library/README.md`](../../../library/README.md).

## Kapan dipakai / TIDAK
- PAKAI: "aku mau bisa X, bikinkan peta belajarnya", "susun roadmap FastAPI sampai deploy".
- JANGAN:
  - **menulis penjelasan/materi** — dilarang di `library/` (§7 2026-09-04). Sintesis
    hidup di `artifacts/` dan sampai ke Bryant hanya lewat gerbang 403 (sesudah gagal).
  - mengisi isi catatan → `note-refine` (L2). Mirror course luar → `course-intake` (L1).
  - membuat node Forge → L4. Menyatakan Bryant menguasai sesuatu → dilarang §1.2.

## Alur
1. **Kumpulkan 5 keputusan** (AskUserQuestion untuk fork nyata; teks panjang di-paste):
   tujuan konkret · baseline (apa yang sudah bisa) · cut-list (yang sengaja ditunda) ·
   milestone · waktu per minggu. **Baseline = lantai awal, BUKAN mastery** — akhiri
   dengan mengarahkan Bryant ke `/placement` untuk lantai sungguhnya.
2. **Riset sumber otoritatif** (docs resmi, spesifikasi, buku). Untuk tiap sumber yang
   BELUM ada di `data/sources.yaml`, tambahkan entri:
   `id` (snake_case) · `type` ∈ `{cs2023_ku, textbook_toc, official_docs}` ·
   `citation` · `url_or_locator`. **Tanpa field lain** — skema `extra="forbid"`.
3. **Snapshot tiap sumber (WAJIB, lewat script):**
   `backend/.venv/Scripts/python.exe scripts/fetch_source.py --id <id>`
   Gagal unduh → sumber itu **tidak boleh dipakai**. JANGAN pernah menulis/menambal
   `data/sources/*.md` sendiri: isinya adalah bahan pembanding kutipan, dan kalau kamu
   yang mengarangnya, seluruh gerbang jadi melingkar.
4. **Ambil kutipan DARI BERKAS SNAPSHOT**, bukan dari ingatan atau halaman web. Baca
   `data/sources/<id>.md`, salin potongan **verbatim** ≥ 25 karakter, satu baris.
5. **Rakit `spec.yaml` ke scratchpad** (`kind: roadmap`) sesuai kontrak
   [`docs/execution-plan-L3-learn-intake.md`](../../../docs/execution-plan-L3-learn-intake.md) §3.3.
   Tiap materi: `source_ref` · `quote` · `reproduce` (satu kalimat, ≤200 karakter) ·
   `candidate_node` (kebab-case). Dilarang blok kode di teks mana pun.
6. **Jalankan scaffolder** (dia yang menulis berkas, bukan kamu):
   `backend/.venv/Scripts/python.exe scripts/library_scaffold.py --spec "$CLAUDE_SCRATCHPAD/spec.yaml"`
   Ditolak karena grounding → perbaiki kutipannya, jangan akali gerbangnya.
7. **Validasi & lapor:**
   `backend/.venv/Scripts/python.exe scripts/verify_library.py`
   Laporkan `dibuat`/`skip` apa adanya. Arahkan: buka `library/` di Obsidian; isi stub
   lewat `note-refine`; jalankan `/placement` untuk menemukan lantai.

## Batas yang dijaga (jangan dilanggar)
- **Peta, bukan bab.** Tanpa blok kode; prosa peta dibatasi mesin (3000 karakter
  non-kutipan). Kalau terasa perlu menjelaskan — itu tanda materinya milik 403, bukan peta.
- **Kutipan verbatim dari snapshot.** Mengarang kutipan = gerbang menolak; mengarang
  snapshot = dilarang keras (dan tak akan terlihat di diff sebagai apa pun selain itu).
- **Kutipan hanya di file `type: roadmap`.** Jangan menaruh sitasi generate di stub
  materi — di sana tak ada yang memeriksanya.
- **`node_ids` tetap kosong.** Kandidat node ditulis sebagai teks; node lahir di L4
  lewat pipeline R4 + gerbang mesin M7.
- **Tak pernah menulis `status`, mastery, atau apa pun ke DB Forge** (§1.2).
```

---

## 10. Urutan build (langkah demi langkah)

**Prinsipnya: gerbang lebih dulu, penulis belakangan** (KUNCI 9) — supaya tak pernah ada
jendela waktu ketika peta bisa ditulis tanpa diperiksa.

1. **`scripts/_console.py`** (§4). Selesai dalam 2 menit; dipakai tiga script.
2. **`scripts/fetch_source.py`** (§5) + `scripts/test_fetch_source.py` (§8.1).
   Lalu snapshot **sumber nyata** minimal dua:
   ```
   backend/.venv/Scripts/python.exe scripts/fetch_source.py --id fastapi_docs_first_steps
   backend/.venv/Scripts/python.exe scripts/fetch_source.py --id fastapi_docs_path_params
   ```
   Periksa isinya sekilas (bukan halaman error), lalu **commit `data/sources/`**.
3. **Aturan L3 di `verify_library.py`** (§7) + test (§8.2). Jalankan validator atas
   `library/` yang ada — harus tetap hijau (belum ada file `type: roadmap`).
4. **`kind: roadmap` di `library_scaffold.py`** (§6) + test (§8.3), termasuk test regresi
   jalur L1.
5. **`.claude/skills/learn-intake/SKILL.md`** (§9).
6. **Smoke end-to-end** (§11) dengan sumber & kutipan sungguhan.
7. **`ruff` + seluruh test** (§12).
8. **Catat keputusan:** entri baru §7 `CLAUDE.md` (ringkas KUNCI 1–9 + batas yang
   diterima), tandai L3 ✅ di [`roadmap-library-lane.md`](roadmap-library-lane.md), dan
   tambahkan perintah `fetch_source.py` ke §6 CLAUDE.md.

---

## 11. Verifikasi manual (smoke)

Semua perintah dari **repo root**. Python: `backend/.venv/Scripts/python.exe` (Windows).

```bash
# 1) Snapshot dua sumber nyata (idempoten: jalankan dua kali, yang kedua "skip")
backend/.venv/Scripts/python.exe scripts/fetch_source.py --id fastapi_docs_first_steps
backend/.venv/Scripts/python.exe scripts/fetch_source.py --id fastapi_docs_first_steps

# 2) Lihat kepala snapshot & AMBIL kutipan dari sini (bukan dari web)
head -n 30 data/sources/fastapi_docs_first_steps.md

# 3) Rakit spec roadmap di scratchpad (kutipan disalin dari langkah 2), lalu:
backend/.venv/Scripts/python.exe scripts/library_scaffold.py --spec "$SPEC" --dry-run
backend/.venv/Scripts/python.exe scripts/library_scaffold.py --spec "$SPEC"

# 4) Gerbang baca
backend/.venv/Scripts/python.exe scripts/verify_library.py
```

**Yang WAJIB kamu lihat:**

| Uji | Harapan |
|---|---|
| `fetch_source` kedua kali | `= <id>: sudah ada (pakai --force …)`, exit 0 |
| `fetch_source --id yang_tak_ada` | exit 2, pesan "daftarkan dulu di sources.yaml" |
| spec dengan kutipan **diubah satu huruf** | scaffolder **exit 2**, "kutipan TIDAK ada di snapshot", **nol berkas ditulis** |
| spec dengan ```` ``` ```` di `reproduce` | `SPEC TIDAK VALID`, exit 2 |
| scaffold sukses | `library/<slug>/_index.md` `type: roadmap`; `01-*/index` memuat baris `> "…"`; stub materi `status: outline` + sentinel kerangka |
| jalankan scaffold lagi | semua `= skip` (create-only), tak ada yang ditimpa |
| sunting tangan: tambah blok kode ke peta | `verify_library.py` exit 1, "peta memuat blok kode" |
| `--capture` stub materi hasil L3 | **DITOLAK** ("body masih stub") — peta tak membuat catatan terlihat terisi |

---

## 12. Definition of Done (checklist) — ✅ SEMUA TERBUKTI 2026-09-05

> Dieksekusi 2026-09-05 pada commit `7a258e0` (L3) + `4e1e91f` (gotcha #1, terpisah),
> branch `m7-machine-gates`. Kolom bukti diisi dari run nyata, bukan dari niat.

- [x] `scripts/_console.py`, `scripts/fetch_source.py` ada; `library_scaffold.py` &
      `verify_library.py` diperluas sesuai §6–§7.
      → gerbang TULIS `check_grounding()`, gerbang BACA `roadmap_errors()`;
      `MIN_QUOTE_CHARS`/`normalize` **di-import** dari `app/services/grounding.py`
      (bukan disalin — gotcha #7).
- [x] `data/sources/` berisi ≥ 2 snapshot sumber nyata, **ter-commit** (bukan di-ignore).
      → `fastapi_docs_first_steps.md` (17.714 karakter) &
      `fastapi_docs_path_params.md` (15.441 karakter), keduanya `provenance: fetch`.
- [x] `.claude/skills/learn-intake/SKILL.md` ada, isinya sesuai §9.
- [x] Test hijau seluruhnya: `backend/.venv/Scripts/python.exe -m pytest scripts/ -q`
      (24 test lama tetap hijau + tambahan L3).
      → **53 passed** = 24 lama + 9 `test_fetch_source` + 9 validator L3 + 11
      scaffolder L3 (termasuk regresi `test_jalur_L1_tak_berubah`).
- [x] Test backend tak tersentuh: `cd backend && .venv/Scripts/python.exe -m pytest -q`.
      → **151 passed, 1 warning in 429.85s**, exit 0.
- [x] `ruff` bersih untuk berkas L3:
      `cd backend && .venv/Scripts/python.exe -m ruff check ../scripts` — tak ada temuan
      **baru** (3 temuan lama: 1×UP017 + 2×E402 di test lama; jangan campur perbaikannya
      ke commit L3).
      → persis 3 temuan, ketiganya yang lama; berkas L3 baru nol temuan.
      **Catatan invokasi:** `ruff` harus dijalankan **dari `backend/`** — dari repo root
      tak ada `pyproject.toml`, jadi ruff memakai aturan default (RUF/I) dan melaporkan
      13 "temuan" yang bukan pelanggaran konfigurasi proyek.
- [x] Validator hijau atas seluruh `library/`.
- [x] Semua baris tabel smoke §11 terbukti, termasuk **dua uji penolakan**
      (kutipan diubah satu huruf, dan blok kode di peta).
      → `simplest`→`simplect` ⇒ `GROUNDING GAGAL`, exit 2, **nol berkas ditulis**;
      code fence disunting ke peta ⇒ gerbang baca exit 1 `"peta memuat blok kode"`;
      `--capture` stub L3 ⇒ **DITOLAK** (`body masih stub`).
- [x] Entri §7 `CLAUDE.md` ditulis; L3 ✅ di roadmap; §6 CLAUDE.md dapat perintah baru.
      → plus satu bagian baru di `library/README.md` yang mendaftar enam aturan mesin
      `type: roadmap` (tak ada di rencana; tanpa itu penulis file roadmap tangan
      ditolak tanpa tahu sebabnya).
- [x] **Invariant utuh:** nol prosa penjelasan sintesis di `library/`; nol tulisan ke DB
      Forge; `node_ids` tetap kosong; tak ada field frontmatter ke-9.

**Tiga penyimpangan kecil dari rencana — semuanya dicatat, bukan didiamkan:**

1. **Course smoke `library/fastapi-l3-smoke/` DIHAPUS setelah diverifikasi.** §11 adalah
   prosedur verifikasi, bukan daftar deliverable; `library/` adalah vault Obsidian Bryant,
   dan course bernama "smoke" di sana adalah derau yang bukan tujuan belajarnya. Buktinya
   hidup di test + laporan ini, dan skill bisa meregenerasinya kapan saja.
2. **`library/README.md` dapat bagian "Aturan tambahan untuk `type: roadmap`".** Ia dokumen
   format-beku L0; L3 menambah enam aturan yang ditegakkan mesin ke salah satu nilai
   `type`-nya, jadi membiarkannya tak tercatat berarti gerbang yang menolak tanpa
   menjelaskan.
3. **Docstring modul `library_scaffold.py` & `verify_library.py` diperbarui** supaya tak lagi
   mengklaim dirinya murni L1/L2 — keduanya kini memikul separuh gerbang L3.

**Yang SENGAJA tidak dikerjakan:** `.claude/skills/run-learning-engine/SKILL.md` masih
memakai path venv POSIX di 6 tempat. Gotcha #1 menyebut "dua skill lama" (lajur Library);
skill itu di luar lingkup L3 dan pantas dapat commit sendiri.

---

## 13. Gotchas / jebakan yang harus dihindari

1. **Path venv di mesin ini Windows:** `backend/.venv/Scripts/python.exe`. SKILL L1/L2
   lama menulis `backend/.venv/bin/python` (POSIX) — itu tidak ada di sini. Tulis jalur
   Windows di SKILL L3; perbaiki dua skill lama kalau sempat (commit terpisah).
2. **Jangan `--force` refetch sembarangan.** Snapshot berubah → kutipan yang sudah
   dipakai peta bisa mati. Setelah `--force`, **selalu** jalankan `verify_library.py`.
3. **`data/sources/` harus ikut git.** Ia `data/`, bukan `artifacts/`. Kalau ia tak
   ter-commit, gerbang jadi tak bisa direproduksi di mesin lain (dan R3 mati lagi).
4. **Jangan menaruh kutipan di stub materi.** File `type: note` tak diperiksa aturan
   roadmap (KUNCI 5) — sitasi di sana adalah klaim tanpa pengawas.
5. **Bentuk `> "…"` adalah kontrak**, bukan gaya. Kutipan yang ditulis dengan bentuk lain
   lolos tanpa diperiksa — persis kebalikan dari yang kita mau.
6. **`MIN_QUOTE_CHARS` dihitung SETELAH normalisasi spasi**; kutipan berbaris-lipat di
   sumber tetap cocok, tapi jangan pernah menormalisasi huruf besar-kecil (`grounding.py`
   sengaja tidak) — `Query` dan `query` beda hal.
7. **Jangan menulis ulang aturan kutipan di `scripts/`.** Import dari
   `app/services/grounding.py`. Dua salinan gerbang = satu gerbang yang menyimpang diam-diam.
8. **`yaml.safe_dump` memancarkan list sebagai blok** (`source_refs:\n- id`), bukan
   inline seperti contoh di `library/README.md`. Itu perilaku L1 yang sudah ada dan
   valid — jangan "memperbaikinya" dengan menulis YAML manual.
9. **Konsol cp1252**: jangan mencetak isi snapshot mentah; cetak potongan pendek, dan
   pastikan `force_utf8_stdio()` dipanggil di awal `main()` ketiga script.
10. **Halaman dokumentasi ber-JS** (mis. yang butuh render) menghasilkan snapshot pendek
    → script menolak. Itu fitur; jalan keluarnya `--from-file` dengan teks yang **Bryant**
    salin, bukan menurunkan ambang.

---

## 14. Setelah L3 (arah, bukan tugas sekarang)

- **R3 hidup lagi.** Dengan `data/sources/` terisi, job R3 yang selama ini ditolak
  (`NO_SNAPSHOT`) bisa lolos. Verifikasi terpisah dengan satu job R3 sungguhan — ini
  bonus L3, bukan bagian DoD-nya.
- **L4 (jembatan)** memungut `candidate_node` dari peta → pipeline R4 + gerbang mesin M7
  → node nyata, lalu mengisi `node_ids` di stub materi (link dua arah).
- **L5 (penjaga metrik)** menghitung "% direproduksi" dengan join `node_ids` → DB Forge.
  Roadmap §4 memperingatkan: tiap minggu L1–L4 hidup tanpa L5, Bryant berlatih mengukur
  "dibaca". L3 menambah **daya tarik** lajur Library (peta terasa seperti kurikulum), jadi
  tekanan untuk menyegerakan L5 naik justru setelah fase ini.
