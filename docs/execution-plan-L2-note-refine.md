# Plan Eksekusi L2 — Skill `note-refine` + `verify_library.py`

> **Status:** rencana eksekusi siap-kerja. Turunan dari
> [`roadmap-library-lane.md`](roadmap-library-lane.md) fase **L2** dan keputusan
> [`../CLAUDE.md`](../CLAUDE.md) §7 (2026-08-31 & 2026-09-04). Format target dibekukan
> di [`../library/README.md`](../library/README.md) (L0); stub yang diisi lahir dari
> [`execution-plan-L1-course-intake.md`](execution-plan-L1-course-intake.md) (L1).
>
> **Ditulis agar bisa dikerjakan developer pemula sekalipun** dan tetap menghasilkan
> kode berkualitas: tiap berkas punya spesifikasi lengkap, kode acuan yang bisa
> ditranskripsi, test eksplisit, urutan build, dan checklist selesai.
>
> **Bukan** pelonggaran invariant. Kalau ada konflik dengan §1 CLAUDE.md,
> **invariant menang**. — **Dicatat:** 2026-09-04

---

## 0. Peta cepat (baca ini dulu)

L2 mengubah **stub `outline` (kosong) → `captured` (berisi catatan Bryant)**. Ia
membangun **satu skill + satu script + satu berkas test**:

| Berkas | Peran | Wajib? |
|---|---|---|
| `.claude/skills/note-refine/SKILL.md` | Pemandu alur: paste catatan mentah → Claude **rapikan** (editor, bukan penulis) → tulis ke satu stub → flip status via script. | ✅ inti |
| `scripts/verify_library.py` | **Gerbang mesin** deterministik: (default) validasi SEMUA `library/**/*.md`; (`--capture <file>`) flip `outline→captured` **hanya bila body sudah berisi**. | ✅ inti |
| `scripts/test_verify_library.py` | Penjaga: field lengkap, `source_refs`/`node_ids` ⊆ registry, aturan "captured wajib berisi", capture menolak stub. | ✅ (house style) |

**Definisi selesai (ringkas):** catatan mentah Bryant → satu stub jadi markdown rapi
tertaut ke modul yang benar; **status di-flip oleh SCRIPT** (bukan AI) hanya setelah
body benar-benar berisi; validator hijau untuk seluruh `library/`; `ruff` bersih; test
hijau. **Nol klaim mastery.**

---

## 1. Tujuan & ruang lingkup

**Tujuan.** Mengotomasi **Penggunaan 3** (rapikan catatan mentah jadi arsip): dari
paste/dikte catatan kasar → markdown rapi di stub yang benar. **AI = editor + peneliti,
bukan penilai, bukan penulis materi.**

**DI DALAM ruang lingkup L2:**
- Merapikan teks yang **Bryant produksi** (paste/dikte) ke satu stub target eksplisit.
- Flip `status: outline → captured` lewat **script deterministik** (cek body berisi dulu).
- Validator menyeluruh `library/`: frontmatter lengkap, `source_refs` ⊆ `sources.yaml`,
  `node_ids` ⊆ node `data/`, `type`/`status` sah, `captured` wajib berisi.
- Boleh mengisi `source_refs`/`node_ids` **bila** Bryant menyebut & id-nya valid.

**DI LUAR ruang lingkup L2 (jangan dikerjakan di sini):**
- **Mensintesis materi/penjelasan yang Bryant tak tulis** → itu `learn-intake` (L3), dan
  hasilnya ke `artifacts/` + gerbang 403, **tak pernah** ke `library/` (§7 2026-08-31).
- Membuat node Forge / mengusulkan node baru → jembatan (L4).
- Dashboard "% direproduksi" → (L5).
- Mengubah edge prasyarat Forge (domain Isyah, §1.4).

---

## 2. Keputusan yang sudah dikunci (jangan ditawar ulang)

Dari diskusi 2026-09-04 (5 crux) + §7 CLAUDE.md:

1. **CRUX 1 — gigi penjaga = TODO-marker.** AI merapikan HANYA teks Bryant. Celah/kekurangan
   ditandai `> TODO: …`, **tak pernah ditambal** dengan prosa. "Catatan berlubang itu jujur"
   — sejalan filosofi "% direproduksi, bukan % dibaca". Guard-nya **disiplin skill +
   Bryant baca diff**, bukan mesin (lihat batas yang diterima di bawah).
2. **CRUX 2 — Skill + `verify_library.py`.** Inti (merapikan teks) inheren pekerjaan AI.
   Tapi dua bagian mekanis **keluar dari tangan AI**: (a) **flip status** hanya oleh script
   setelah cek "body berisi"; (b) **validasi** refs ⊆ registry. Analog `verify_nodes.py`.
3. **CRUX 3 — overwrite (bukan create-only).** L1 create-only pecah di sini karena L2
   memang menulis ke stub yang ada. **Pengganti create-only = git + diff review**:
   `library/` di-commit (beda `artifacts/`), jadi git = undo. Skill wajib menunjukkan diff.
4. **CRUX 4 — satu stub target eksplisit per panggilan.** Bryant menyebut file targetnya;
   AI boleh **mengusulkan** modul tapi Bryant konfirmasi. Tak ada distribusi brain-dump
   otomatis (itu = AI menghakimi penempatan → salah-file).
5. **CRUX 5 — `source_refs`/`node_ids` boleh, opsional, tervalidasi.** L2 boleh mengisi
   bila Bryant menyebut id yang **ADA** di registry; validator menolak id menggantung.
   Tak ada kerja jembatan (usul node baru = L4).

**Batas yang diterima sadar (WAJIB dicatat di §7 saat eksekusi):** L2 **lebih lemah**
dari L1 — L1 aman *by construction* (scaffolder deterministik, nol prosa AI), L2 sengaja
menaruh teks sentuhan-AI ke `library/`. Ini bisa diterima karena **(a)** input milik
Bryant (bukan sintesis), **(b)** penjaga metrik bikin catatan rapi **tak pernah**
menggerakkan mastery %, **(c)** Bryant reviewer atas tulisannya sendiri, **(d)** gerbang
403 tetap satu-satunya jalan prosa generate — dan L2 dilarang mensintesis. *Alternatif
ditolak:* citation-teeth gaya R3 (melebur L2→L3, terlalu berat), raw-preserved verbatim
(dobel konten), refuse-on-dirty-tree (friksi commit tiap sesi), formatter nol-AI (turun
jadi linter, tak merestruktur dikte).

---

## 3. Daur hidup file & kontrak L2

Satu stub materi hasil L1 (`status: outline`):

```markdown
---
title: GET route JSON status 200
course: fastapi-dasar
module: 01-routing-dasar
type: note
source_refs: []
node_ids: []
status: outline
created: 2026-09-04
---

# GET route JSON status 200

> `status: outline` — kerangka. Isi lewat note-refine (L2).

Balik: [[_index|Routing Dasar]]
```

Setelah L2 (`status: captured`, body diisi catatan rapi Bryant + TODO untuk celah):

```markdown
---
title: GET route JSON status 200
course: fastapi-dasar
module: 01-routing-dasar
type: note
source_refs: [fastapi_docs_first_steps]   # opsional; hanya id yang ADA di sources.yaml
node_ids: [n002_get_json_route]           # opsional; hanya node yang ADA di data/
status: captured                          # DI-FLIP OLEH SCRIPT, bukan diketik AI
created: 2026-09-04
---

# GET route JSON status 200

Route GET paling dasar: `@app.get("/")` mengembalikan dict, FastAPI serialize
jadi JSON, status default 200.

> TODO: cek apakah return `list` juga otomatis jadi JSON array — belum kutulis.

Balik: [[_index|Routing Dasar]]
```

**Yang berubah di L2:** BODY (teks Bryant, rapi) + opsional `source_refs`/`node_ids` +
opsional `type` (`note`↔`transcription`). **Status di-flip terpisah oleh script.**
**Yang TIDAK boleh berubah:** `title`/`course`/`module`/`created` (identitas file);
himpunan 8 field frontmatter (format L0 beku); dan **status tak pernah diketik AI**.

**Aturan gerbang "captured wajib berisi":** file `status: captured` bertipe
`note`/`transcription` **dilarang** masih memuat sentinel stub L1
(`` `status: outline` — kerangka ``) atau tanpa satu pun baris prosa. Ini yang bikin
"captured" **bukan** klaim kosong: script menolak flip bila body masih stub.

---

## 4. `scripts/verify_library.py` — spesifikasi lengkap

### 4.1 Perilaku (dua mode)
- **Default (validasi):** pindai `library/**/*.md` (hanya file di dalam folder course;
  lewati `README.md` & apa pun langsung di `library/`), validasi tiap file, cetak
  pelanggaran. **Exit 0** bersih / **1** ada pelanggaran. Ini gerbang commit Library.
- **`--capture <file>`:** validasi SATU file; bila field valid **dan** body sudah berisi
  (bukan stub) → flip `status` jadi `captured`, tulis balik (pertahankan urutan field).
  **Exit 0** sukses / **1** ditolak (masih stub / field invalid) — file tak disentuh saat ditolak.

### 4.2 Registry yang dibaca (sumber kebenaran ⊆)
- **source ids** ← `data/sources.yaml` → `sources[].id`. `source_refs` ⊆ himpunan ini.
- **node ids** ← `data/domains/*/nodes/*/node.yaml` → field `id` (lewati folder `_example`).
  `node_ids` ⊆ himpunan ini. *(Node id = nama folder, mis. `n002_get_json_route`,
  `m001_softmax_stable`, `r001_state_counter`.)*

### 4.3 Aturan validasi per file (semua pelanggaran dikumpulkan, bukan berhenti di pertama)
1. Awali frontmatter `---\n…\n---\n` yang parse jadi mapping.
2. **Himpunan field = persis 8** (`_REQUIRED_FM`): laporkan yang hilang **dan** yang asing
   (format L0 beku — tak boleh nambah/kurang).
3. `type` ∈ `{note, transcription, outline, roadmap}`; `status` ∈ `{outline, captured}`.
4. `title`/`course` string non-kosong; `created` non-kosong.
5. `course` **cocok** nama folder course (`library/<course>/…`) — cegah salah-tempel.
6. `source_refs` list, tiap elemen ∈ source ids. `node_ids` list, tiap elemen ∈ node ids.
7. **captured wajib berisi:** bila `status == captured` **dan** `type ∈ {note, transcription}`
   **dan** body masih stub → pelanggaran. (`_index` bertipe `outline`/`roadmap` dikecualikan —
   body-nya memang daftar struktural, bukan stub isi.)

### 4.4 Path & dependency
- Ikuti pola `scripts/library_scaffold.py`: `_REPO_ROOT = Path(__file__).resolve().parents[1]`,
  `_LIBRARY_ROOT = _REPO_ROOT / "library"`.
- Dependency: hanya `pyyaml`. Jalankan dengan `backend/.venv/bin/python`.
- **Tidak** mengimpor apa pun dari `app/` — berdiri sendiri, tak menyentuh DB/Forge.

### 4.5 Kode acuan (boleh ditranskripsi utuh)

```python
#!/usr/bin/env python3
"""Validator + capture lajur Library (L2 · note-refine).

Dua mode:
  (default)         validasi SEMUA library/**/*.md → gerbang commit.
                    exit 0 bersih / 1 ada pelanggaran.
  --capture <file>  validasi SATU file lalu flip status outline→captured BILA body
                    sudah berisi (bukan stub). exit 0 sukses / 1 ditolak.

Registry (sumber kebenaran untuk ⊆):
  - source ids ← data/sources.yaml  (source_refs ⊆ ini)
  - node ids   ← data/domains/*/nodes/*/node.yaml `id` (node_ids ⊆ ini)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[1]
_LIBRARY_ROOT = _REPO_ROOT / "library"
_SOURCES_YAML = _REPO_ROOT / "data" / "sources.yaml"

_REQUIRED_FM = {"title", "course", "module", "type", "source_refs",
                "node_ids", "status", "created"}
_VALID_TYPE = {"note", "transcription", "outline", "roadmap"}
_VALID_STATUS = {"outline", "captured"}
# Sentinel stub dari library_scaffold.material_md (L1). Kehadirannya = belum diisi.
_STUB_SENTINEL = "`status: outline` — kerangka"


# ---------- registry ----------

def load_source_ids() -> set[str]:
    data = yaml.safe_load(_SOURCES_YAML.read_text("utf-8"))
    return {s["id"] for s in (data or {}).get("sources", [])
            if isinstance(s, dict) and "id" in s}


def load_node_ids() -> set[str]:
    ids: set[str] = set()
    for p in _REPO_ROOT.glob("data/domains/*/nodes/*/node.yaml"):
        if p.parent.name == "_example":
            continue
        try:
            data = yaml.safe_load(p.read_text("utf-8"))
            nid = data.get("id") if isinstance(data, dict) else None
        except (yaml.YAMLError, OSError):
            nid = None
        ids.add(nid or p.parent.name)
    return ids


# ---------- parsing ----------

def split_frontmatter(text: str) -> tuple[dict | None, str]:
    """(mapping_frontmatter, body). Kembalikan (None, text) bila bentuk salah."""
    if not text.startswith("---"):
        return None, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None, text
    try:
        fm = yaml.safe_load(parts[1])
    except yaml.YAMLError:
        return None, text
    if not isinstance(fm, dict):
        return None, text
    return fm, parts[2]


def is_stub_body(body: str) -> bool:
    """True bila body belum berisi catatan (masih kerangka L1)."""
    if _STUB_SENTINEL in body:
        return True
    for raw in body.splitlines():
        line = raw.strip()
        if not line or len(line) < 3:
            continue
        if line.startswith(("#", ">", "Balik:", "Lanjut:", "Sumber:",
                            "- [[", "- *")):
            continue  # heading/blockquote/nav/bullet wikilink — bukan prosa
        return False   # ada baris prosa nyata → bukan stub
    return True


# ---------- validasi ----------

def _field_errors(fm: dict, path: Path, source_ids: set[str],
                  node_ids: set[str]) -> list[str]:
    errs: list[str] = []
    keys = set(fm)
    for miss in sorted(_REQUIRED_FM - keys):
        errs.append(f"field wajib hilang: {miss}")
    for extra in sorted(keys - _REQUIRED_FM):
        errs.append(f"field asing (format L0 beku): {extra}")

    if fm.get("type") not in _VALID_TYPE:
        errs.append(f"type tak sah: {fm.get('type')!r}")
    if fm.get("status") not in _VALID_STATUS:
        errs.append(f"status tak sah: {fm.get('status')!r}")
    for key in ("title", "course"):
        val = fm.get(key)
        if not (isinstance(val, str) and val.strip()):
            errs.append(f"{key} wajib string non-kosong")
    if not str(fm.get("created") or "").strip():
        errs.append("created wajib non-kosong")

    # course cocok folder course: library/<course>/...
    try:
        top = path.relative_to(_LIBRARY_ROOT).parts[0]
        if fm.get("course") != top:
            errs.append(f"course={fm.get('course')!r} != folder {top!r}")
    except ValueError:
        errs.append("file di luar library/")

    for key, registry, label in (("source_refs", source_ids, "sources.yaml"),
                                 ("node_ids", node_ids, "data/ nodes")):
        val = fm.get(key)
        if not isinstance(val, list):
            errs.append(f"{key} harus list")
            continue
        for item in val:
            if item not in registry:
                errs.append(f"{key}: {item!r} tak ada di {label}")
    return errs


def validate_file(path: Path, source_ids: set[str],
                  node_ids: set[str]) -> list[str]:
    text = path.read_text("utf-8")
    fm, body = split_frontmatter(text)
    if fm is None:
        return ["frontmatter tak terbaca (harus diawali blok --- … ---)"]
    errs = _field_errors(fm, path, source_ids, node_ids)
    if (fm.get("status") == "captured"
            and fm.get("type") in {"note", "transcription"}
            and is_stub_body(body)):
        errs.append("status=captured tapi body masih stub (belum ada catatan)")
    return errs


# ---------- capture (flip outline→captured) ----------

def capture(path: Path, source_ids: set[str], node_ids: set[str]) -> list[str]:
    """Flip status→captured bila valid & berisi. Kembalikan daftar alasan tolak
    ([] = sukses & file ditulis ulang)."""
    if not path.is_file():
        return ["file tak ditemukan"]
    text = path.read_text("utf-8")
    fm, body = split_frontmatter(text)
    if fm is None:
        return ["frontmatter tak terbaca"]
    errs = _field_errors(fm, path, source_ids, node_ids)
    if errs:
        return errs
    if fm.get("type") in {"note", "transcription"} and is_stub_body(body):
        return ["body masih stub — isi catatan dulu sebelum capture"]
    if fm.get("status") == "captured":
        return []  # sudah captured; idempoten, tak menulis ulang
    fm["status"] = "captured"
    dumped = yaml.safe_dump(fm, sort_keys=False, allow_unicode=True).strip()
    path.write_text(f"---\n{dumped}\n---{body}", encoding="utf-8")
    return []


# ---------- CLI ----------

def _iter_library_files() -> list[Path]:
    # hanya file di DALAM folder course (rel parts >= 2); lewati README & top-level.
    out = []
    for p in sorted(_LIBRARY_ROOT.glob("**/*.md")):
        rel = p.relative_to(_LIBRARY_ROOT)
        if len(rel.parts) >= 2:
            out.append(p)
    return out


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Validator + capture lajur Library (L2).")
    ap.add_argument("--capture", type=Path, metavar="FILE",
                    help="flip satu file outline→captured bila body berisi")
    args = ap.parse_args(argv)

    source_ids = load_source_ids()
    node_ids = load_node_ids()

    if args.capture is not None:
        path = args.capture.resolve()
        reasons = capture(path, source_ids, node_ids)
        try:
            rel = path.relative_to(_REPO_ROOT).as_posix()
        except ValueError:
            rel = str(path)
        if reasons:
            print(f"CAPTURE DITOLAK: {rel}", file=sys.stderr)
            for r in reasons:
                print(f"  - {r}", file=sys.stderr)
            return 1
        print(f"captured: {rel}")
        return 0

    problems = 0
    for path in _iter_library_files():
        errs = validate_file(path, source_ids, node_ids)
        if errs:
            problems += 1
            rel = path.relative_to(_REPO_ROOT).as_posix()
            print(f"✗ {rel}")
            for e in errs:
                print(f"    - {e}")
    if problems:
        print(f"\n{problems} file bermasalah.", file=sys.stderr)
        return 1
    print("library/ bersih — semua frontmatter valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
```

> **Catatan `created`:** validator hanya cek non-kosong (bukan format tanggal), supaya
> tak menolak file L1 lama. Kalau nanti mau ketat ISO-8601, ubah di satu tempat + test.

---

## 5. `.claude/skills/note-refine/SKILL.md` — isi lengkap

Ikuti gaya `course-intake/SKILL.md` (frontmatter `name`/`description`, prosa Indonesia,
imperatif, path relatif repo root). Isi yang dituju:

```markdown
---
name: note-refine
description: Rapikan catatan mentah/dikte Bryant menjadi markdown bersih di SATU stub library/ yang ia tunjuk, lalu flip status outline→captured lewat verify_library.py. AI = editor (perbaiki bahasa/struktur/format), BUKAN penulis materi: celah ditandai TODO, tak pernah ditambal. Gunakan saat mengisi stub hasil course-intake — BUKAN untuk generate materi baru (itu learn-intake) atau menilai penguasaan.
---

# note-refine — rapikan catatan Bryant ke `library/`

Mengubah catatan mentah yang **Bryant tulis/dikte** menjadi markdown rapi di **satu
stub target**, lalu status di-flip oleh script deterministik. **Nol klaim mastery.**
Format & batas: [`../../../library/README.md`](../../../library/README.md).

## Kapan dipakai / TIDAK
- PAKAI: "rapikan catatan ini ke materi X", "transkripsi dikte ini ke stub Y".
- JANGAN:
  - **generate materi/penjelasan yang Bryant tak sediakan** → itu learn-intake (L3);
    hasil sintesis ke `artifacts/` + gerbang 403, TAK PERNAH ke `library/` (§7 2026-08-31).
  - membuat node Forge / mengisi node dari nol (→ L4).
  - menyatakan Bryant menguasai apa pun (dilarang §1.2 — mastery hanya dari eksekusi kode).

## Alur (satu file per panggilan)
1. **Minta target + bahan.** Path stub eksplisit di `library/…/<materi>.md` + **paste/dikte
   catatan mentah**. Kalau Bryant tak menyebut file, USULKAN modul yang cocok tapi minta
   konfirmasi — jangan menyebar sendiri ke banyak file (bisa salah-tempat).
   **Kalau Bryant tak menyediakan bahan mentah: TOLAK.** Tak ada bahan = tak ada yang
   dirapikan; jangan mengarang isi.
2. **Baca isi file sekarang.** Kalau `status` sudah `captured`, INGATKAN ini akan
   menimpa (overwrite) — git adalah undo-nya; tunjukkan apa yang akan berubah.
3. **Rapikan HANYA teks Bryant.** Boleh: perbaiki ejaan/tata bahasa, restruktur kalimatnya
   sendiri, tambah heading, format blok kode, buang duplikat, padatkan. **DILARANG**:
   menambah fakta/penjelasan/contoh yang tak ada di input, "mengembangkan" catatan pendek
   jadi bab. **Celah → tandai `> TODO: …`, JANGAN tambal dengan prosa.**
4. **GANTI seluruh body dengan versi rapi** (pertahankan 8 field frontmatter; JANGAN
   ketik `status` sendiri). **Buang baris sentinel kerangka L1**
   (`` > `status: outline` — kerangka … ``) — selama ia ada, `--capture` menolak (guard
   stub). Boleh set `type` `note`↔`transcription`. Boleh isi `source_refs`/`node_ids`
   HANYA bila Bryant menyebut & id-nya ADA di registry (sources.yaml / data node) — kalau
   ragu, biarkan `[]`.
5. **Flip status (deterministik):**
   `backend/.venv/bin/python scripts/verify_library.py --capture "<path stub>"`
   Script menolak bila body masih stub / field invalid — perbaiki lalu ulangi.
6. **Validasi menyeluruh & lapor:**
   `backend/.venv/bin/python scripts/verify_library.py`
   Tunjukkan diff/ringkasan perubahan ke Bryant. Arahkan: buka `library/` di Obsidian.

## Batas yang dijaga (jangan dilanggar)
- **Editor, bukan penulis.** Tak menambah pengetahuan; celah jadi TODO, bukan tambalan.
- **Status hanya dari `--capture`** (script), tak pernah diketik AI (§1.2).
- **`source_refs` ⊆ sources.yaml, `node_ids` ⊆ node data/** — validator menolak id menggantung.
- **Tak ada prosa sintesis di `library/`.** Materi generate = artifacts/ + 403 (§7 2026-09-04).
```

> Catatan `../../../`: SKILL.md ada di `.claude/skills/note-refine/`, naik 3 level ke root.

---

## 6. `scripts/test_verify_library.py` — test eksplisit

Jalankan: `backend/.venv/bin/python -m pytest scripts/test_verify_library.py -q`.
Registry (source/node ids) di-**monkeypatch** ke himpunan tetap supaya test tak
tergantung isi `data/` yang berubah; `_LIBRARY_ROOT` → `tmp_path`.

```python
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
import verify_library as vl

SRC_IDS = {"fastapi_docs_first_steps", "fastapi_official_docs"}
NODE_IDS = {"n002_get_json_route", "m001_softmax_stable"}


def _write(root: Path, rel: str, fm: dict, body: str) -> Path:
    import yaml
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    dumped = yaml.safe_dump(fm, sort_keys=False, allow_unicode=True).strip()
    p.write_text(f"---\n{dumped}\n---\n{body}", encoding="utf-8")
    return p


def _fm(**over) -> dict:
    base = {"title": "GET route", "course": "fastapi-dasar",
            "module": "01-routing-dasar", "type": "note",
            "source_refs": [], "node_ids": [], "status": "captured",
            "created": "2026-09-04"}
    base.update(over)
    return base


@pytest.fixture
def lib(tmp_path, monkeypatch):
    monkeypatch.setattr(vl, "_REPO_ROOT", tmp_path)
    monkeypatch.setattr(vl, "_LIBRARY_ROOT", tmp_path / "library")
    monkeypatch.setattr(vl, "load_source_ids", lambda: set(SRC_IDS))
    monkeypatch.setattr(vl, "load_node_ids", lambda: set(NODE_IDS))
    return tmp_path / "library"


def test_valid_captured_note_passes(lib):
    p = _write(lib, "fastapi-dasar/01-routing-dasar/get.md",
               _fm(source_refs=["fastapi_docs_first_steps"],
                   node_ids=["n002_get_json_route"]),
               "\n# GET route\n\nRoute GET dasar mengembalikan dict jadi JSON.\n")
    assert vl.validate_file(p, SRC_IDS, NODE_IDS) == []


def test_missing_field_fails(lib):
    fm = _fm()
    del fm["created"]
    p = _write(lib, "fastapi-dasar/01-routing-dasar/get.md", fm, "\nisi nyata.\n")
    errs = vl.validate_file(p, SRC_IDS, NODE_IDS)
    assert any("created" in e for e in errs)


def test_extra_field_fails(lib):
    p = _write(lib, "fastapi-dasar/01-routing-dasar/get.md",
               _fm(extra="x"), "\nisi nyata.\n")
    assert any("field asing" in e for e in vl.validate_file(p, SRC_IDS, NODE_IDS))


def test_bad_source_ref_fails(lib):
    p = _write(lib, "fastapi-dasar/01-routing-dasar/get.md",
               _fm(source_refs=["tidak_ada"]), "\nisi nyata.\n")
    assert any("source_refs" in e for e in vl.validate_file(p, SRC_IDS, NODE_IDS))


def test_bad_node_id_fails(lib):
    p = _write(lib, "fastapi-dasar/01-routing-dasar/get.md",
               _fm(node_ids=["n999_bogus"]), "\nisi nyata.\n")
    assert any("node_ids" in e for e in vl.validate_file(p, SRC_IDS, NODE_IDS))


def test_bad_type_and_status_fail(lib):
    p = _write(lib, "fastapi-dasar/01-routing-dasar/get.md",
               _fm(type="forged", status="mastered"), "\nisi nyata.\n")
    errs = vl.validate_file(p, SRC_IDS, NODE_IDS)
    assert any("type" in e for e in errs) and any("status" in e for e in errs)


def test_course_mismatch_fails(lib):
    p = _write(lib, "fastapi-dasar/01-routing-dasar/get.md",
               _fm(course="salah-course"), "\nisi nyata.\n")
    assert any("course" in e for e in vl.validate_file(p, SRC_IDS, NODE_IDS))


def test_captured_but_stub_fails(lib):
    body = "\n# GET route\n\n> `status: outline` — kerangka. Isi lewat note-refine.\n"
    p = _write(lib, "fastapi-dasar/01-routing-dasar/get.md", _fm(), body)
    assert any("stub" in e for e in vl.validate_file(p, SRC_IDS, NODE_IDS))


def test_capture_flips_when_body_present(lib):
    p = _write(lib, "fastapi-dasar/01-routing-dasar/get.md",
               _fm(status="outline"), "\n# GET route\n\nCatatan nyata Bryant.\n")
    assert vl.capture(p, SRC_IDS, NODE_IDS) == []
    import yaml
    fm = yaml.safe_load(p.read_text("utf-8").split("---")[1])
    assert fm["status"] == "captured"


def test_capture_refuses_stub(lib):
    body = "\n# GET route\n\n> `status: outline` — kerangka. Isi lewat note-refine.\n"
    p = _write(lib, "fastapi-dasar/01-routing-dasar/get.md", _fm(status="outline"), body)
    reasons = vl.capture(p, SRC_IDS, NODE_IDS)
    assert reasons and any("stub" in r for r in reasons)
    import yaml
    fm = yaml.safe_load(p.read_text("utf-8").split("---")[1])
    assert fm["status"] == "outline"          # tak berubah


def test_capture_refuses_bad_ref_without_flipping(lib):
    p = _write(lib, "fastapi-dasar/01-routing-dasar/get.md",
               _fm(status="outline", node_ids=["n999_bogus"]),
               "\nCatatan nyata.\n")
    assert vl.capture(p, SRC_IDS, NODE_IDS)   # ditolak
    import yaml
    fm = yaml.safe_load(p.read_text("utf-8").split("---")[1])
    assert fm["status"] == "outline"


def test_capture_missing_file_is_clean_error(lib):
    reasons = vl.capture(lib / "tak-ada.md", SRC_IDS, NODE_IDS)
    assert reasons == ["file tak ditemukan"]


def test_index_captured_is_not_stub(lib):
    # _index bertipe outline/roadmap dikecualikan dari aturan captured-wajib-berisi
    p = _write(lib, "fastapi-dasar/_index.md",
               _fm(module="", type="outline", status="captured"),
               "\n# FastAPI Dasar\n\n## Modul\n- [[01-routing-dasar/_index|01 · Routing]]\n")
    assert vl.validate_file(p, SRC_IDS, NODE_IDS) == []
```

---

## 7. Urutan build (langkah demi langkah)

1. **Baca** [`../library/README.md`](../library/README.md) + stub L1 nyata di
   [`../library/fastapi-dasar/`](../library/fastapi-dasar/_index.md) — pahami bentuk target.
2. Buat `scripts/verify_library.py` dari kode acuan §4.5, lalu `chmod +x
   scripts/verify_library.py` (ada shebang; tanpa exec-bit ruff `EXE001` merah). Pahami
   tiap fungsi (jangan tempel buta): `split_frontmatter`, `is_stub_body` (definisi
   "berisi"), `_field_errors` (⊆ registry + himpunan field beku), `capture` (flip tergerbang).
3. Buat `scripts/test_verify_library.py` dari §6. Jalankan:
   `backend/.venv/bin/python -m pytest scripts/test_verify_library.py -q` → **hijau**.
4. `backend/.venv/bin/ruff check scripts/verify_library.py scripts/test_verify_library.py`
   → bersih.
5. **Jalankan validator atas `library/` nyata:**
   `backend/.venv/bin/python scripts/verify_library.py` → **harus hijau** (file L0/L1
   yang ada sudah valid). Kalau merah, itu temuan nyata — perbaiki file atau aturan,
   catat bila format berubah.
6. **Uji manual** end-to-end (§8): isi satu stub → `--capture` → validator.
7. Buat `.claude/skills/note-refine/SKILL.md` dari §5.
8. (Opsional, disarankan) uji skill sungguhan: minta Claude "rapikan catatan ini ke
   stub Z" dengan bahan mentah → ia harus merapikan (TODO untuk celah), flip via script,
   lapor diff. Tanpa bahan → ia harus MENOLAK.

---

## 8. Verifikasi manual (smoke)

```bash
cd /home/kbuser/bryant_folder/machine_learning/Project_Learn_Bryant
# 0) validator atas library/ nyata harus hijau lebih dulu
backend/.venv/bin/python scripts/verify_library.py

# 1) siapkan course + stub demo lewat scaffolder L1
cat > /tmp/spec-l2.yaml <<'YAML'
course: {slug: demo-l2, title: "Demo L2", source: "Sumber (url)"}
modules:
  - {slug: modul-satu, title: "Modul Satu",
     materials: [{slug: materi-a, title: "Materi A"}]}
YAML
backend/.venv/bin/python scripts/library_scaffold.py --spec /tmp/spec-l2.yaml

STUB=library/demo-l2/01-modul-satu/materi-a.md
# 2) capture SEBELUM diisi → HARUS DITOLAK (masih stub), status tetap outline
backend/.venv/bin/python scripts/verify_library.py --capture "$STUB"; echo "exit=$?"

# 3) isi body — note-refine MENGGANTI body (buang baris sentinel L1), pertahankan
#    frontmatter. (Append di bawah sentinel TIDAK cukup: sentinel = penanda stub,
#    capture akan tetap menolak selama ia masih ada — itu guard yang benar.)
python3 - "$STUB" <<'PY'
import sys, pathlib
p = pathlib.Path(sys.argv[1]); fm = p.read_text("utf-8").split("---", 2)[1]
body = ('\n# Materi A\n\nCatatan nyata: `@app.get("/")` balikan dict jadi JSON, '
        'status 200.\n\n> TODO: cek perilaku return list.\n\n'
        'Balik: [[_index|Modul Satu]]\n')
p.write_text(f"---{fm}---{body}", encoding="utf-8")
PY
# 4) capture SESUDAH diisi → sukses, status jadi captured
backend/.venv/bin/python scripts/verify_library.py --capture "$STUB"; echo "exit=$?"
grep -m1 "^status:" "$STUB"        # → status: captured

# 5) validator menyeluruh tetap hijau
backend/.venv/bin/python scripts/verify_library.py

# 6) BERSIHKAN demo (jangan commit)
rm -rf library/demo-l2
```

Harapan: langkah 2 exit 1 (ditolak, stub), langkah 4 exit 0 (captured), langkah 5 hijau.

---

## 9. Definition of Done (checklist)

> **✅ TERVERIFIKASI 2026-09-04.** Semua item lulus. Perintah yang dijalankan:
> `pytest scripts/test_verify_library.py scripts/test_library_scaffold.py` → **24 passed**
> (13 L2 + 11 L1, nol regresi); `ruff check` → **All checks passed**; validator atas
> `library/` nyata → **hijau tanpa mengubah file**; smoke §8 penuh → sesuai harapan.
> **Satu pengerasan di luar rencana awal:** `--capture` pada path tak-ada/luar-repo dulu
> melempar `FileNotFoundError` mentah; ditambah guard `if not path.is_file()` + tampilan
> path tahan-ValueError, plus test `test_capture_missing_file_is_clean_error`. Kode acuan
> §4.5/§6 sudah disamakan dengan disk (diff = kosong).

- [x] `scripts/verify_library.py` ada; mode default & `--capture` jalan; exit code sesuai
      (0 bersih/sukses, 1 pelanggaran/ditolak). *(smoke: capture stub→exit 1; terisi→exit 0)*
- [x] **Validasi ⊆ registry terbukti:** `source_refs` bukan-id-sources ditolak; `node_ids`
      bukan-node ditolak (`test_bad_source_ref_fails` / `test_bad_node_id_fails` hijau).
- [x] **Format L0 beku ditegakkan:** field hilang & field asing ditolak; `type`/`status`
      di luar himpunan ditolak (`test_missing_field_fails`/`test_extra_field_fails`/
      `test_bad_type_and_status_fail` hijau).
- [x] **Aturan "captured wajib berisi":** captured+stub ditolak; `_index` dikecualikan
      (`test_captured_but_stub_fails`, `test_index_captured_is_not_stub`).
- [x] **Capture tergerbang:** `--capture` menolak stub, ref menggantung & file tak-ada
      **tanpa** mengubah status; flip hanya saat body berisi & valid (`test_capture_*` +
      smoke [1][2][3]).
- [x] `.claude/skills/note-refine/SKILL.md` ada; menegaskan editor-bukan-penulis,
      TODO-bukan-tambal, status-dari-script, tolak-tanpa-bahan.
- [x] Validator atas `library/` nyata **hijau** (file L0/L1 lolos tanpa diubah).
- [x] `ruff check` bersih untuk kedua berkas.
- [x] Smoke §8 lulus (capture-stub ditolak → isi → capture sukses → idempoten → validator
      hijau); demo dibersihkan (sisa `demo-l2` = 0).
- [x] **§7 CLAUDE.md** memuat entri L2 (baris 619–635): overwrite menggantikan create-only
      (git=undo), guard editor lunak + batas yang diterima, semua alternatif ditolak.
- [x] Tak ada invariant §1 tergores; tak ada prosa sintesis AI mendarat di `library/`
      (validator menolak captured-stub; SKILL.md melarang sintesis).

---

## 10. Gotchas / jebakan yang harus dihindari

- **Jangan biarkan AI mengetik `status: captured`.** Itu status-by-assertion — persis
  yang `--capture` ada untuk cegah. Status hanya berubah lewat script yang mengecek body.
- **Jangan menambah prosa yang Bryant tak tulis.** Godaan "melengkapi biar rapi" =
  menyelundup content-library lewat pintu refine (§7 2026-08-31). Celah = `> TODO:`.
- **Jangan mengisi `source_refs` dengan nama course/URL bebas** — hanya id yang ADA di
  `sources.yaml`. Provenance course tetap teks `Sumber:` di `_index` (aturan L1).
- **Jangan menambah/kurangi field frontmatter** — himpunan 8 field beku (L0). Ubah format =
  ubah `library/README.md` + §7 dulu.
- **`is_stub_body` itu heuristik**, bukan pembuktian. Ia menangkap kasus umum (sentinel
  ada / tanpa prosa). Kalau nanti bikin stub baru dengan sentinel berbeda, perbarui
  `_STUB_SENTINEL` + test bersamaan.
- **note-refine harus MENGGANTI body, bukan menempel di bawah sentinel.** Selama baris
  `` > `status: outline` — kerangka `` masih ada, `--capture` menolak (dianggap stub).
  Ini disengaja: memaksa penulisan bersih, bukan tumpuk-di-atas-kerangka.
- **Overwrite = andalkan git.** Sebelum re-refine file `captured`, pastikan kerja lama
  sudah ter-commit; skill wajib menunjukkan diff. Tak ada create-only lagi di L2.
- Jalankan dengan `backend/.venv/bin/python` (punya `pyyaml`), bukan `python` sistem.

---

## 11. Setelah L2 (arah, bukan tugas sekarang)

- **L3 `learn-intake` + grounding** (fase risiko §8): roadmap + sitasi + usul node ke
  `library/`; sintesis penjelasan → `artifacts/` + 403. `verify_library.py` jadi gerbang
  yang sudah siap dipakai ulang.
- **L4 jembatan Library→Forge:** `node_ids` mulai terisi dari usulan node; validator ini
  yang menjaga id-nya nyata.
- **L5 dashboard "% direproduksi":** join `node_ids` → DB Forge. Membaca materi **tidak**
  menggerakkan progres.
- Referensi: [`roadmap-library-lane.md`](roadmap-library-lane.md) §3 (L3–L5).
```
