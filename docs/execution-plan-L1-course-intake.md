# Plan Eksekusi L1 — Skill `course-intake` + `library_scaffold.py`

> **Status:** rencana eksekusi siap-kerja. Turunan dari
> [`roadmap-library-lane.md`](roadmap-library-lane.md) fase **L1** dan keputusan
> [`../CLAUDE.md`](../CLAUDE.md) §7 (2026-09-04). Format target dibekukan di
> [`../library/README.md`](../library/README.md) (L0).
>
> **Ditulis agar bisa dikerjakan developer pemula sekalipun** dan tetap menghasilkan
> kode berkualitas: tiap berkas punya spesifikasi lengkap, kode acuan yang bisa
> ditranskripsi, test yang eksplisit, urutan build, dan checklist selesai.
>
> **Bukan** pelonggaran invariant. Kalau ada konflik dengan §1 CLAUDE.md,
> **invariant menang**. — **Dicatat:** 2026-09-04

---

## 0. Peta cepat (baca ini dulu)

L1 membangun **satu skill + satu script + satu berkas test**:

| Berkas | Peran | Wajib? |
|---|---|---|
| `scripts/library_scaffold.py` | Scaffolder deterministik: spec YAML → pohon `library/`. **CREATE-ONLY.** | ✅ inti |
| `.claude/skills/course-intake/SKILL.md` | Pemandu alur: kumpulkan silabus → rakit spec → jalankan scaffolder. | ✅ inti |
| `scripts/test_library_scaffold.py` | Penjaga: create-only, bentuk frontmatter, validasi slug. | ✅ (house style) |

**Definisi selesai (ringkas):** dari satu silabus (mis. course Dicoding) → folder
`library/<course>/` terstruktur lahir dengan frontmatter persis format L0; **re-run
tidak menimpa** catatan yang sudah ada; test hijau; `ruff` bersih.

---

## 1. Tujuan & ruang lingkup

**Tujuan.** Mengotomasi **Penggunaan 2** (mirror course luar): dari silabus jadi
kerangka `library/` kosong-terstruktur yang siap diisi catatan. **Nol klaim mastery.**

**DI DALAM ruang lingkup L1:**
- Membuat pohon folder + `_index.md` per level + stub materi (opsional).
- Frontmatter persis format L0, di-generate mesin (bukan diketik model).
- Aman di-re-run (create-only).

**DI LUAR ruang lingkup L1 (jangan dikerjakan di sini):**
- Mengisi ISI catatan → itu `note-refine` (L2).
- Materi generate / grounding → `learn-intake` (L3).
- Membuat node Forge / mengisi `node_ids` → jembatan (L4).
- Dashboard "% direproduksi" → (L5).
- `scripts/verify_library.py` (validator frontmatter menyeluruh) → **boleh menyusul**,
  tidak memblok L1. Lihat §9.

---

## 2. Keputusan yang sudah dikunci (jangan ditawar ulang)

Dari diskusi + §7 CLAUDE.md 2026-09-04:

1. **Bentuk = script deterministik**, bukan pure-instruction. Alasan: frontmatter jadi
   sumber join dashboard L5; format layak penegak eksekutabel (analog `load_nodes.py`).
2. **AskUserQuestion tidak menelan silabus.** Silabus di-**paste** sebagai teks, Claude
   parse. AskUserQuestion hanya untuk fork nyata (granularitas + konfirmasi slug).
3. **Course luar = provenance teks-bebas** di `_index.md` (`Sumber: …`), **bukan** id
   `source_refs`. `source_refs` tetap `[]` saat intake; ia hanya untuk id yang ADA di
   `data/sources.yaml` (namespace sitasi otoritatif Forge — jangan dikotori).
4. **Granularitas = pertanyaan tiap run:** "sampai level materi" (bikin stub) vs "modul
   saja" (`_index` per modul).
5. **INVARIANT KESELAMATAN: create-only.** Scaffolder **tak pernah menimpa** file yang
   sudah ada — file existing di-skip + dilaporkan. Ini melindungi catatan Bryant.
6. **`status` bukan status reproduksi.** `_index` = `captured` (punya isi struktural);
   stub materi = `outline`. Tak pernah `forged`/`mastered` (§1.2 — reproduksi hanya dari
   eksekusi kode, hidup di DB Forge).

---

## 3. Kontrak `spec.yaml` (jembatan Claude → script)

Claude menulis berkas ini ke **scratchpad** dari silabus yang di-paste; script
membacanya. Bentuknya:

```yaml
course:
  slug: fastapi-dasar            # WAJIB, kebab-case: ^[a-z0-9]+(-[a-z0-9]+)*$
  title: "FastAPI Dasar"         # WAJIB, non-kosong
  source: "Dicoding — Belajar Membuat API (https://...)"   # opsional, provenance teks
modules:                         # WAJIB, list non-kosong
  - slug: routing-dasar          # WAJIB, kebab-case, unik antar-modul
    title: "Routing Dasar"       # WAJIB
    materials:                   # OPSIONAL — ada → bikin stub; kosong/absen → modul-saja
      - {slug: get-route-json, title: "GET route JSON status 200"}
      - {slug: path-param-404, title: "Path param + 404"}
  - slug: request-body
    title: "Request Body"
    # tanpa materials → hanya _index modul
```

**Aturan validasi (semua GAGAL-KERAS: tak ada file ditulis bila salah satu langgar):**
- `course.slug`, tiap `module.slug`, tiap `material.slug` **wajib** cocok
  `^[a-z0-9]+(-[a-z0-9]+)*$`. Ini sekaligus **penjaga keamanan**: menolak `../`, `/`,
  spasi, huruf besar → mustahil path traversal keluar dari `library/`.
- `course.title`, tiap `title` wajib string non-kosong.
- `modules` list non-kosong; slug modul unik; slug materi unik di dalam satu modul.

---

## 4. `scripts/library_scaffold.py` — spesifikasi lengkap

### 4.1 Perilaku
1. Baca `--spec <path>` → parse YAML → validasi jadi objek `Course` (gagal → exit 2).
2. Untuk course: hitung nomor modul `NN` (lihat 4.3), lalu pancarkan:
   - `library/<slug>/_index.md`
   - `library/<slug>/<NN>-<modul>/_index.md` per modul
   - `library/<slug>/<NN>-<modul>/<materi>.md` per materi (kalau ada)
3. Tiap tulis lewat `write_if_absent` (**create-only**).
4. Cetak ringkasan: `dibuat: N · skip: M (sudah ada)` + daftar path (relatif repo).
5. `--dry-run`: laporkan yang AKAN dibuat, jangan tulis apa pun.

**Exit code:** `0` sukses (termasuk saat semua di-skip); `2` spec tidak valid.

### 4.2 Path & dependency
- Ikuti pola `scripts/load_nodes.py`: `_REPO_ROOT = Path(__file__).resolve().parents[1]`,
  `_LIBRARY_ROOT = _REPO_ROOT / "library"`.
- Dependency: hanya `pyyaml` (sudah dep backend). Jalankan dengan interpreter yang
  punya pyyaml: `backend/.venv/bin/python scripts/library_scaffold.py ...`.
- **Tidak** mengimpor apa pun dari `app/` — scaffolder Library berdiri sendiri, tak
  menyentuh DB/Forge.

### 4.3 Penomoran modul `NN` (stabil lintas re-run)
Supaya re-run tak bikin folder ganda saat kamu menambah modul:
- Pindai folder `NN-<slug>` yang SUDAH ada di `library/<slug>/`.
- Modul yang slug-nya sudah punya folder → **pakai NN lama** (toleran terhadap urutan
  spec yang berubah).
- Modul baru → **NN berikutnya** setelah maksimum yang ada.

> **Batas yang diterima:** kalau kamu menyisipkan modul baru di TENGAH urutan konseptual,
> nomornya tetap ditambahkan di akhir (mis. jadi `03-`), bukan menyisip jadi `02-` lalu
> menggeser yang lain (menggeser = merename folder = melanggar create-only). Ini sadar:
> lebih baik nomor "meloncat" daripada catatan tergeser/hilang. Urutan bacaan diatur via
> tautan nav & daftar di `_index`, bukan cuma angka.

### 4.4 Kode acuan (boleh ditranskripsi utuh)

```python
#!/usr/bin/env python3
"""Scaffolder lajur Library (L1 · course-intake).

Baca spec course (YAML) → pancarkan pohon `library/<slug>/` kosong-terstruktur
mengikuti format beku `library/README.md` (L0). CREATE-ONLY: tak pernah menimpa
file yang sudah ada, jadi catatan Bryant aman saat re-run.

Pemakaian:
    python scripts/library_scaffold.py --spec <spec.yaml> [--dry-run]
Exit 0 = sukses (termasuk semua di-skip); 2 = spec tidak valid.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[1]
_LIBRARY_ROOT = _REPO_ROOT / "library"
_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_REQUIRED_FM = {"title", "course", "module", "type", "source_refs",
                "node_ids", "status", "created"}


class SpecError(ValueError):
    """Spec course tidak valid — tak ada file yang ditulis."""


@dataclass
class Material:
    slug: str
    title: str


@dataclass
class Module:
    slug: str
    title: str
    materials: list[Material] = field(default_factory=list)


@dataclass
class Course:
    slug: str
    title: str
    source: str
    modules: list[Module]


# ---------- parsing & validasi ----------

def _require(cond: bool, msg: str) -> None:
    if not cond:
        raise SpecError(msg)


def _valid_slug(s: object) -> bool:
    return isinstance(s, str) and bool(_SLUG_RE.match(s))


def parse_spec(raw: object) -> Course:
    _require(isinstance(raw, dict), "spec harus mapping YAML di level atas")
    c = raw.get("course")
    _require(isinstance(c, dict), "field `course` (mapping) wajib")
    slug, title = c.get("slug"), c.get("title")
    source = (c.get("source") or "")
    _require(_valid_slug(slug), f"course.slug harus kebab-case a-z0-9-: {slug!r}")
    _require(isinstance(title, str) and title.strip(), "course.title wajib non-kosong")
    _require(isinstance(source, str), "course.source harus teks")

    raw_mods = raw.get("modules")
    _require(isinstance(raw_mods, list) and raw_mods,
             "field `modules` (list non-kosong) wajib")
    modules: list[Module] = []
    seen_m: set[str] = set()
    for i, m in enumerate(raw_mods):
        _require(isinstance(m, dict), f"modules[{i}] harus mapping")
        ms, mt = m.get("slug"), m.get("title")
        _require(_valid_slug(ms), f"modules[{i}].slug tidak valid: {ms!r}")
        _require(ms not in seen_m, f"slug modul duplikat: {ms!r}")
        seen_m.add(ms)
        _require(isinstance(mt, str) and mt.strip(), f"modules[{i}].title wajib")
        mats: list[Material] = []
        seen_a: set[str] = set()
        for j, a in enumerate(m.get("materials") or []):
            _require(isinstance(a, dict), f"modules[{i}].materials[{j}] harus mapping")
            asg, att = a.get("slug"), a.get("title")
            _require(_valid_slug(asg), f"materi slug tidak valid: {asg!r}")
            _require(asg not in seen_a, f"slug materi duplikat di {ms}: {asg!r}")
            seen_a.add(asg)
            _require(isinstance(att, str) and att.strip(), "material.title wajib")
            mats.append(Material(asg, att.strip()))
        modules.append(Module(ms, mt.strip(), mats))
    return Course(slug, title.strip(), source.strip(), modules)


# ---------- penomoran modul ----------

def resolve_module_numbers(course_dir: Path, modules: list[Module]) -> dict[str, str]:
    existing: dict[str, int] = {}
    max_nn = 0
    if course_dir.exists():
        for child in course_dir.iterdir():
            mobj = re.match(r"^(\d{2})-(.+)$", child.name) if child.is_dir() else None
            if mobj:
                nn = int(mobj.group(1))
                existing[mobj.group(2)] = nn
                max_nn = max(max_nn, nn)
    out: dict[str, str] = {}
    for mod in modules:
        if mod.slug in existing:
            nn = existing[mod.slug]
        else:
            max_nn += 1
            nn = max_nn
        out[mod.slug] = f"{nn:02d}"
    return out


# ---------- template konten ----------

def _frontmatter(**fields: object) -> str:
    assert _REQUIRED_FM <= set(fields), "frontmatter kehilangan field wajib"
    body = yaml.safe_dump(fields, sort_keys=False, allow_unicode=True).strip()
    return f"---\n{body}\n---\n"


def course_index_md(course: Course, nn: dict[str, str], created: str) -> str:
    fm = _frontmatter(title=course.title, course=course.slug, module="",
                      type="outline", source_refs=[], node_ids=[],
                      status="captured", created=created)
    src = course.source or "(isi provenance sumber course)"
    lines = [f"- [[{nn[m.slug]}-{m.slug}/_index|{nn[m.slug]} · {m.title}]]"
             for m in course.modules]
    return (f"{fm}\n# {course.title}\n\n"
            f"Sumber: {src}\n\n"
            f"## Modul\n" + "\n".join(lines) + "\n")


def module_index_md(course: Course, mod: Module, nn: dict[str, str],
                    prev: Module | None, nxt: Module | None, created: str) -> str:
    my = nn[mod.slug]
    fm = _frontmatter(title=mod.title, course=course.slug, module=f"{my}-{mod.slug}",
                      type="outline", source_refs=[], node_ids=[],
                      status="captured", created=created)
    if mod.materials:
        mats = "\n".join(f"- [[{a.slug}|{a.title}]] · *stub, isi via note-refine*"
                         for a in mod.materials)
    else:
        mats = "- *(materi belum didaftarkan — tambah via note-refine / re-run intake)*"
    nav = []
    if prev:
        nav.append(f"Balik: [[../{nn[prev.slug]}-{prev.slug}/_index|"
                   f"{nn[prev.slug]} · {prev.title}]]")
    if nxt:
        nav.append(f"Lanjut: [[../{nn[nxt.slug]}-{nxt.slug}/_index|"
                   f"{nn[nxt.slug]} · {nxt.title}]]")
    nav_line = ("\n" + " · ".join(nav) + "\n") if nav else ""
    return f"{fm}\n# {my} · {mod.title}\n\n## Materi\n{mats}\n{nav_line}"


def material_md(course: Course, mod: Module, nn: dict[str, str],
                mat: Material, created: str) -> str:
    fm = _frontmatter(title=mat.title, course=course.slug,
                      module=f"{nn[mod.slug]}-{mod.slug}", type="note",
                      source_refs=[], node_ids=[], status="outline", created=created)
    return (f"{fm}\n# {mat.title}\n\n"
            "> `status: outline` — kerangka. Isi lewat note-refine (L2).\n\n"
            f"Balik: [[_index|{mod.title}]]\n")


# ---------- tulis (create-only) ----------

def write_if_absent(path: Path, content: str, dry_run: bool) -> bool:
    """True = dibuat; False = di-skip karena sudah ada. Tak pernah menimpa."""
    if path.exists():
        return False
    if not dry_run:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return True


def scaffold(course: Course, created: str,
             dry_run: bool = False) -> tuple[list[str], list[str]]:
    made: list[str] = []
    skipped: list[str] = []
    course_dir = _LIBRARY_ROOT / course.slug
    nn = resolve_module_numbers(course_dir, course.modules)

    def emit(path: Path, content: str) -> None:
        rel = path.relative_to(_REPO_ROOT).as_posix()
        (made if write_if_absent(path, content, dry_run) else skipped).append(rel)

    emit(course_dir / "_index.md", course_index_md(course, nn, created))
    for idx, mod in enumerate(course.modules):
        mod_dir = course_dir / f"{nn[mod.slug]}-{mod.slug}"
        prev = course.modules[idx - 1] if idx > 0 else None
        nxt = course.modules[idx + 1] if idx < len(course.modules) - 1 else None
        emit(mod_dir / "_index.md", module_index_md(course, mod, nn, prev, nxt, created))
        for mat in mod.materials:
            emit(mod_dir / f"{mat.slug}.md", material_md(course, mod, nn, mat, created))
    return made, skipped


# ---------- CLI ----------

def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Scaffolder lajur Library (L1).")
    ap.add_argument("--spec", required=True, type=Path, help="path spec.yaml")
    ap.add_argument("--dry-run", action="store_true", help="laporkan tanpa menulis")
    args = ap.parse_args(argv)

    try:
        raw = yaml.safe_load(args.spec.read_text(encoding="utf-8"))
        course = parse_spec(raw)
    except (SpecError, yaml.YAMLError, OSError) as exc:
        print(f"SPEC TIDAK VALID: {exc}", file=sys.stderr)
        return 2

    created = _dt.date.today().isoformat()
    made, skipped = scaffold(course, created, dry_run=args.dry_run)

    tag = "(dry-run) " if args.dry_run else ""
    print(f"{tag}dibuat: {len(made)} · skip: {len(skipped)} (sudah ada)")
    for p in made:
        print(f"  + {p}")
    for p in skipped:
        print(f"  = {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
```

---

## 5. `.claude/skills/course-intake/SKILL.md` — isi lengkap

Ikuti gaya `run-learning-engine/SKILL.md` (frontmatter `name`/`description`, prosa
Indonesia, imperatif, path relatif repo root). Isi yang dituju:

```markdown
---
name: course-intake
description: Scaffold sebuah course eksternal (mis. Dicoding, deeplearning.ai) menjadi kerangka folder library/ kosong-terstruktur untuk diisi catatan. Gunakan saat Bryant ingin "mirror"/menyalin struktur course luar ke dalam Library — BUKAN untuk mengisi materi (itu note-refine) atau menilai penguasaan.
---

# course-intake — mirror struktur course luar ke `library/`

Menghasilkan pohon `library/<course>/` kosong-terstruktur dari silabus yang
di-paste Bryant, lewat scaffolder deterministik `scripts/library_scaffold.py`.
**Nol klaim mastery.** Format & batas: [`../../../library/README.md`](../../../library/README.md).

## Kapan dipakai / TIDAK
- PAKAI: "bikinkan kerangka course X dari silabus ini", "mirror course Dicoding …".
- JANGAN: mengisi isi catatan (→ note-refine, L2), generate materi (→ learn-intake, L3),
  atau menyatakan Bryant sudah menguasai apa pun (dilarang §1.2).

## Alur
1. **Minta bahan.** Nama course + sumber (URL/platform) + **paste silabus** (daftar
   modul; boleh dengan judul materi per modul). Jangan mencoba menampung silabus lewat
   AskUserQuestion — silabus itu teks yang di-paste.
2. **AskUserQuestion untuk fork nyata saja:**
   - Granularitas: "sampai level materi (bikin stub per materi)" vs "modul saja".
   - Konfirmasi `slug` course (kebab-case) yang kamu turunkan dari nama.
3. **Rakit `spec.yaml` ke scratchpad** sesuai kontrak (docs/execution-plan-L1). Turunkan
   slug modul/materi dari judul (kebab-case; a-z0-9-). source_refs & node_ids DIKOSONGKAN
   oleh scaffolder — jangan isi manual.
4. **Jalankan scaffolder:**
   `backend/.venv/bin/python scripts/library_scaffold.py --spec "$CLAUDE_SCRATCHPAD/spec.yaml"`
   (opsional dulu `--dry-run` untuk pratinjau).
5. **Laporkan** daftar `dibuat`/`skip` apa adanya. Ingatkan: file yang sudah ada TIDAK
   ditimpa (create-only). Arahkan Bryant: buka `library/` di Obsidian; isi stub lewat
   `note-refine` (L2).

## Batas yang dijaga (jangan dilanggar)
- Provenance course luar → teks `Sumber:` di _index, BUKAN id source_refs (source_refs
  hanya untuk id yang ADA di data/sources.yaml).
- `status` tak pernah diisi "forged"/"mastered" — reproduksi hanya dari eksekusi kode.
- Jangan menulis prosa penjelasan materi ke library/ (itu artifacts/ + 403, §7 2026-09-04).
```

> Catatan `../../../`: SKILL.md ada di `.claude/skills/course-intake/`, jadi ke root
> repo naik 3 level. Sesuaikan bila memindah berkas.

---

## 6. `scripts/test_library_scaffold.py` — test eksplisit

Jalankan: `backend/.venv/bin/python -m pytest scripts/test_library_scaffold.py -q`.
Tiap test me-`monkeypatch` `_REPO_ROOT`/`_LIBRARY_ROOT` ke `tmp_path` supaya tak
menyentuh `library/` asli.

```python
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
import library_scaffold as ls  # noqa: E402

SPEC = {
    "course": {"slug": "fastapi-dasar", "title": "FastAPI Dasar",
               "source": "Dicoding — X (url)"},
    "modules": [
        {"slug": "routing-dasar", "title": "Routing Dasar",
         "materials": [{"slug": "get-route-json", "title": "GET route JSON"}]},
        {"slug": "request-body", "title": "Request Body"},   # tanpa materials
    ],
}


@pytest.fixture
def lib(tmp_path, monkeypatch):
    monkeypatch.setattr(ls, "_REPO_ROOT", tmp_path)
    monkeypatch.setattr(ls, "_LIBRARY_ROOT", tmp_path / "library")
    return tmp_path / "library"


def test_creates_expected_tree(lib):
    made, skipped = ls.scaffold(ls.parse_spec(SPEC), created="2026-09-04")
    assert (lib / "fastapi-dasar/_index.md").exists()
    assert (lib / "fastapi-dasar/01-routing-dasar/_index.md").exists()
    assert (lib / "fastapi-dasar/01-routing-dasar/get-route-json.md").exists()
    assert (lib / "fastapi-dasar/02-request-body/_index.md").exists()
    # modul tanpa materials: TIDAK ada file materi
    assert list((lib / "fastapi-dasar/02-request-body").glob("*.md")) == [
        lib / "fastapi-dasar/02-request-body/_index.md"]
    assert skipped == []


def test_frontmatter_shape_and_status_rule(lib):
    ls.scaffold(ls.parse_spec(SPEC), created="2026-09-04")
    stub = (lib / "fastapi-dasar/01-routing-dasar/get-route-json.md").read_text("utf-8")
    fm = yaml.safe_load(stub.split("---")[1])
    assert ls._REQUIRED_FM <= set(fm)
    assert fm["type"] == "note" and fm["status"] == "outline"     # stub materi
    assert fm["source_refs"] == [] and fm["node_ids"] == []
    idx = (lib / "fastapi-dasar/01-routing-dasar/_index.md").read_text("utf-8")
    assert yaml.safe_load(idx.split("---")[1])["status"] == "captured"  # _index


def test_create_only_never_overwrites(lib):
    course = ls.parse_spec(SPEC)
    ls.scaffold(course, created="2026-09-04")
    p = lib / "fastapi-dasar/01-routing-dasar/get-route-json.md"
    p.write_text("CATATAN BRYANT — jangan hilang", encoding="utf-8")
    made, skipped = ls.scaffold(course, created="2026-09-04")   # re-run
    assert p.read_text("utf-8") == "CATATAN BRYANT — jangan hilang"
    assert any("get-route-json" in s for s in skipped)
    assert not any("get-route-json" in s for s in made)


def test_nn_reuse_and_append(lib):
    ls.scaffold(ls.parse_spec(SPEC), created="d")
    spec2 = {**SPEC, "modules": SPEC["modules"] + [{"slug": "deps", "title": "Deps"}]}
    ls.scaffold(ls.parse_spec(spec2), created="d")
    assert (lib / "fastapi-dasar/01-routing-dasar").is_dir()
    assert (lib / "fastapi-dasar/02-request-body").is_dir()
    assert (lib / "fastapi-dasar/03-deps").is_dir()   # modul baru → NN berikutnya


@pytest.mark.parametrize("bad", ["../evil", "Routing", "a_b", "", "a/b", "a--"])
def test_rejects_bad_slug(bad):
    spec = {"course": {"slug": bad, "title": "X"},
            "modules": [{"slug": "m", "title": "M"}]}
    with pytest.raises(ls.SpecError):
        ls.parse_spec(spec)


def test_dry_run_writes_nothing(lib):
    made, skipped = ls.scaffold(ls.parse_spec(SPEC), created="d", dry_run=True)
    assert made and not lib.exists()
```

> Catatan: `"a--"` ditolak karena regex melarang tanda hubung ganda/di ujung — bukti
> validasi ketat. Kalau kamu ingin melonggarkannya, ubah regex + test bersamaan.

---

## 7. Urutan build (langkah demi langkah)

1. **Baca** [`../library/README.md`](../library/README.md) — pahami format target &
   batas keras.
2. Buat `scripts/library_scaffold.py` dari kode acuan §4.4. Pahami tiap fungsi
   (jangan tempel buta): `parse_spec` (validasi), `resolve_module_numbers` (NN stabil),
   `write_if_absent` (create-only), template `*_md`.
3. Buat `scripts/test_library_scaffold.py` dari §6. Jalankan:
   `backend/.venv/bin/python -m pytest scripts/test_library_scaffold.py -q` → **hijau**.
4. `backend/.venv/bin/ruff check scripts/library_scaffold.py scripts/test_library_scaffold.py`
   → bersih. Perbaiki temuan.
5. **Uji manual** end-to-end (§8). Pastikan re-run aman & Obsidian merender.
6. Buat `.claude/skills/course-intake/SKILL.md` dari §5.
7. (Opsional, disarankan) uji skill: minta Claude "mirror course contoh" → ia harus
   merakit spec → menjalankan scaffolder → melaporkan. Tak ada klaim mastery.

---

## 8. Verifikasi manual (smoke)

```bash
cd /home/kbuser/bryant_folder/machine_learning/Project_Learn_Bryant
# 1) tulis spec contoh ke scratchpad (atau file sementara)
cat > /tmp/spec-demo.yaml <<'YAML'
course: {slug: demo-course, title: "Demo Course", source: "Sumber X (url)"}
modules:
  - {slug: modul-satu, title: "Modul Satu",
     materials: [{slug: materi-a, title: "Materi A"}]}
  - {slug: modul-dua, title: "Modul Dua"}
YAML
# 2) pratinjau tanpa menulis
backend/.venv/bin/python scripts/library_scaffold.py --spec /tmp/spec-demo.yaml --dry-run
# 3) tulis beneran
backend/.venv/bin/python scripts/library_scaffold.py --spec /tmp/spec-demo.yaml
# 4) IDEMPOTEN: jalankan lagi → semua "skip", nol "dibuat"
backend/.venv/bin/python scripts/library_scaffold.py --spec /tmp/spec-demo.yaml
# 5) periksa hasil, lalu BERSIHKAN course demo (jangan commit)
find library/demo-course -type f
rm -rf library/demo-course
```

Lalu buka folder `library/` sebagai vault di Obsidian → graf harus tersambung
(`_index` course → `_index` modul → materi).

---

## 9. Definition of Done (checklist)

> **✅ TERVERIFIKASI 2026-09-04.** Semua item lulus. Perintah yang dijalankan:
> `pytest scripts/test_library_scaffold.py` → **11 passed**;
> `ruff check` → **All checks passed**; smoke §8 penuh (dry-run → tulis → re-run →
> spec buruk) → sesuai harapan. Satu deviasi positif dari kode acuan: `created`
> memakai `datetime.now(tz=utc).date()` (bukan `date.today()`) agar lolos aturan ruff
> `DTZ` — perilaku identik.

- [x] `scripts/library_scaffold.py` ada, jalan, exit code sesuai (0 sukses / 2 spec buruk).
      *(smoke: tulis→exit 0; spec `../evil`→exit 2 tanpa menulis)*
- [x] **Create-only terbukti** oleh test `test_create_only_never_overwrites` (hijau) +
      smoke re-run (`dibuat: 0 · skip: 4`).
- [x] Frontmatter hasil = 8 field wajib, `status` benar (`captured` _index / `outline` stub).
      *(test `test_frontmatter_shape_and_status_rule` + smoke 3e)*
- [x] `source_refs`/`node_ids` selalu `[]` saat intake; provenance course = teks `Sumber:`.
- [x] Slug tervalidasi (traversal & format ditolak) — `test_rejects_bad_slug` (6 kasus) +
      smoke `../evil` tak bocor keluar `library/`.
- [x] NN stabil lintas re-run (append dapat NN berikutnya) — `test_nn_reuse_and_append` hijau.
- [x] `ruff check` bersih untuk kedua berkas.
- [x] `.claude/skills/course-intake/SKILL.md` ada, mengarahkan alur & batas dengan benar.
- [x] Smoke manual §8 lulus; course demo dibersihkan (sisa `demo-course` = 0, tak ikut commit).
- [x] Tak ada invariant §1 tergores; tak ada prosa materi generate mendarat di `library/`
      (stub sengaja kosong; isi = L2).

---

## 10. Gotchas / jebakan yang harus dihindari

- **Jangan** membuat scaffolder menimpa file — satu bug di sini menghapus catatan Bryant.
  `write_if_absent` adalah jantung keselamatan; jangan "optimasi" jadi `write_text` polos.
- **Jangan** mengisi `source_refs` dengan nama course Dicoding — itu mengotori namespace
  sitasi otoritatif `data/sources.yaml` (§7 2026-09-04). Provenance = teks bebas.
- **Jangan** menaruh isi materi/penjelasan di stub — stub sengaja kosong; isi = L2.
- **Jangan** menambahkan field frontmatter baru "biar rapi" — format L0 beku; menambah
  field = ubah `library/README.md` + §7 dulu (format punya SATU sumber kebenaran).
- **Slug wajib divalidasi sebelum menyentuh disk** — regex `_SLUG_RE` juga penjaga
  keamanan path. Jangan pindahkan validasi ke setelah pembuatan folder.
- Jalankan dengan `backend/.venv/bin/python` (punya `pyyaml`), bukan `python` sistem
  yang mungkin tanpa pyyaml.

---

## 11. Setelah L1 (arah, bukan tugas sekarang)

- **`scripts/verify_library.py`** (opsional, analog `verify_nodes.py`): validasi SEMUA
  `library/**/*.md` — frontmatter lengkap, `source_refs` ⊆ id `sources.yaml`, `node_ids`
  ⊆ node di `data/`, `status` sah. Menjadi gerbang commit Library. Bagus dibangun sebelum
  L4 (saat `node_ids` mulai terisi).
- **L2 `note-refine`** mengisi stub `outline` → `captured`.
- Referensi berikutnya: [`roadmap-library-lane.md`](roadmap-library-lane.md) §3 (L2–L5).
