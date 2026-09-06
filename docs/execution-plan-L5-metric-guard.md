# Plan Eksekusi L5 — Penjaga metrik: "% direproduksi", bukan "% dibaca"

> **Status:** rencana eksekusi siap-kerja. Turunan dari
> [`roadmap-library-lane.md`](roadmap-library-lane.md) fase **L5** — fase terakhir lajur
> Library, dan satu-satunya yang roadmap sebut **wajib ada sebelum sistem boleh disebut
> selesai**. Bahan join lahir di L0/L4 (`node_ids`), oracle-nya milik Forge (DB attempt).
>
> **Ditulis agar bisa dikerjakan developer pemula sekalipun** dan tetap menghasilkan
> kode berkualitas: tiap berkas punya spesifikasi lengkap, kode acuan yang bisa
> ditranskripsi, test eksplisit, urutan build, dan checklist selesai.
>
> **Bukan** pelonggaran invariant. Kalau ada konflik dengan §1 CLAUDE.md,
> **invariant menang**. — **Dicatat:** 2026-09-06

---

## 0. Peta cepat (baca ini dulu)

L5 bukan fitur pelaporan. Ia **penjaga**. Brainstorm lajur ini menyebut bahayanya apa
adanya: bukan satu invariant jebol, melainkan Bryant menghabiskan waktunya di **Library
yang nyaman** sementara **Forge yang tak nyaman** terbengkalai. Penjaganya satu kalimat:

> Progres materi diukur dari **% yang sudah direproduksi**, bukan % yang sudah dibaca.

L5 membuat kalimat itu jadi kode yang berjalan — dan diuji.

### Yang dibangun

| Berkas | Peran | Wajib? |
|---|---|---|
| `backend/app/config.py` (+1 konstanta) | `LIBRARY_DIR` — satu-satunya alamat `library/` di backend. | ✅ inti |
| `backend/app/services/library_progress.py` | Pembaca `library/` (READ-ONLY) + join ke DB Forge + definisi metrik. | ✅ inti |
| `backend/app/routers/library.py` | `GET /library/progress`. | ✅ inti |
| `frontend/lib/api.ts` (+tipe & 1 fungsi) | Klien tipis. | ✅ inti |
| `frontend/app/library/page.tsx` | Halaman course → modul → materi, **dengan lubangnya terlihat**. | ✅ inti |
| `frontend/app/page.tsx` (+1 kartu KPI) | Satu angka di dashboard + tautan ke `/library`. | ✅ inti |
| `backend/tests/test_library_progress.py` | Penjaga dari penjaga — termasuk uji anti-gaming. | ✅ inti |

**Definisi selesai (ringkas):** `/library` menampilkan tiap course dengan tiga keadaan
per materi (belum tertempa · tertempa belum dibuktikan · direproduksi); angkanya **hanya**
bergerak oleh attempt mode dingin di DB; mengisi seluruh catatan (`status: captured`)
**tidak** menggerakkan satu angka pun, dan itu **diuji**.

### Kondisi awal yang sudah terverifikasi

| Fakta | Bukti |
|---|---|
| Definisi "reproduce-without-AI" sudah ada & sempit | `kpi.REPRODUCE_MODES = ("verification", "review", "placement")` |
| Bahan join sudah nyata | `library/fastapi-dasar/` — 4 materi ber-`node_ids` (n002–n005) |
| Peta generate masih berlubang | `library/fastapi-produksi/` — `node_ids: []` (L4 belum melahirkan node) |
| Backend belum tahu `library/` | nol pembaca `library/` di `backend/app/` |
| Frontend punya primitif UI | `app/components/ui/{Card,Container,PageHeader,EmptyState,Badge,Icon}` |

> **Catatan sequencing yang jujur:** acceptance L4 belum tuntas (belum ada node yang
> benar-benar lahir dari peta generate — CLI kena `HTTP 429`). L5 **tidak** menunggu itu:
> ia justru yang membuat kekurangannya terlihat sebagai **0% berlubang** di
> `fastapi-produksi`, bukan sebagai course yang tampak baik-baik saja.

---

## 1. Tujuan & ruang lingkup

**Tujuan.** Menutup lajur Library dengan penjaga yang membuat kenyamanan tak bisa
menyamar jadi kemajuan.

**DI DALAM ruang lingkup L5:**
- Membaca `library/**/*.md` (frontmatter saja) — **read-only**.
- Join `node_ids` → DB Forge, menghitung tiga keadaan per materi + agregat per course.
- Endpoint `GET /library/progress` + halaman `/library` + satu kartu KPI di dashboard.
- Test yang menegakkan aturan anti-gaming.

**DI LUAR ruang lingkup L5 (jangan dikerjakan di sini):**
- **Menulis apa pun ke `library/`** — penulisnya `scripts/` (L1–L3) dan `--link` (L4).
- **Menambah field frontmatter** (mis. `forged`) — ditolak §7 2026-09-04: dua sumber
  kebenaran, dan status reproduksi hanya boleh datang dari eksekusi kode (§1.2).
- Halaman audit / tombol pensiun / `destination` per domain — sisa **M7**, bukan L5
  (lihat §14).
- Mengubah KPI Forge yang sudah ada (`/stats`) — L5 menambah, tak mengutak-atik.
- Grafik/visualisasi tren — §8 menolak kenyamanan visual sebagai pengganti bukti.

---

## 2. Keputusan yang sudah dikunci (jangan ditawar ulang)

Dari diskusi 2026-09-06 (5 crux, semuanya disetujui apa adanya):

1. **KUNCI 1 — "Direproduksi" = pernah lolos attempt mode DINGIN.** Yaitu ada `Attempt`
   dengan `mode ∈ REPRODUCE_MODES` dan `result == "pass"`. Definisi ini **di-import** dari
   `services/kpi.py`, tidak disalin: dua definisi "reproduce-without-AI" akan menyimpang,
   dan yang lebih longgar yang akan dipakai. Mode `acquisition` (L3–L1, scaffold masih di
   layar) tak pernah dihitung — memasukkannya menggelembungkan angka dengan latihan
   bersontekan, persis illusion of competence yang produk ini lawan.

2. **KUNCI 2 — Tiga keadaan per materi, bukan satu angka.** `unmapped` (belum punya
   `node_ids`) · `mapped_unproven` (node ada, belum pernah dibuktikan dingin) ·
   `reproduced`. Ditambah dua penanda: `mastered` (semua node-nya `mastered`) dan
   `decayed` (ada node `lapsed` — pernah dibuktikan, memorinya meluruh). Satu angka
   tunggal akan menyembunyikan beda yang paling penting: "belum ditempa" dan "sudah
   ditempa tapi belum kamu buktikan" adalah dua utang yang berbeda.

3. **KUNCI 3 — `lapsed` tetap dihitung "direproduksi", tapi ditandai meluruh.** Sejalan
   §7 2026-08-21 (Q3): yang meluruh adalah memorinya, **bukan buktinya** — Bryant memang
   pernah memproduksinya. Menghapus buktinya dari angka akan membuat satu review buruk
   terlihat seperti kemunduran kurikulum.

4. **KUNCI 4 — Materi tanpa `node_ids` tetap masuk PENYEBUT.** Inilah properti
   "berlubang" yang diminta roadmap: course tampil belum selesai sampai node-nya tertempa
   **dan** terbukti. Mengeluarkannya dari penyebut akan membuat course dengan satu materi
   tertempa tampil 100%.

5. **KUNCI 5 — Penyebut hanya `type ∈ {note, transcription}`.** `outline` & `roadmap`
   adalah berkas **struktural** (indeks & peta); memasukkannya menghukum course hanya
   karena ia punya banyak modul, dan peta memang tak untuk direproduksi.

6. **KUNCI 6 — Materi dengan banyak `node_ids` butuh SEMUANYA terbukti.** "Materi ini
   selesai" berarti seluruh yang ia tunjuk sudah bisa diproduksi ulang. Ambang yang lebih
   longgar (salah satu saja) akan memberi hadiah untuk memetakan banyak node lalu
   membuktikan yang termudah.

7. **KUNCI 7 — Backend MEMBACA `library/`, tak pernah menulis.** L4 KUNCI 10 melarang
   backend *menyentuh* (menulis) `library/`; L5 memperjelas batasnya: membaca boleh,
   menulis tidak. Alternatif "script menghasilkan berkas indeks yang di-commit" ditolak —
   ia menciptakan sumber kebenaran kedua yang bisa basi, pola yang sudah dua kali ditolak
   proyek ini (job state di file vs DB; toleransi ML di `data/` vs kolom DB).

8. **KUNCI 8 — `status` frontmatter (`outline`/`captured`) TIDAK PERNAH masuk hitungan.**
   Ia boleh tampil sebagai label netral per materi, tak pernah sebagai persentase,
   progress bar, atau apa pun yang berakumulasi. **Diuji**: mengubah seluruh materi jadi
   `captured` harus menghasilkan angka yang identik. Penjaga yang tak diuji adalah penjaga
   yang akan luntur.

9. **KUNCI 9 — `node_ids` menggantung dilaporkan, dan dihitung BELUM terbukti.** Node yang
   tak ada di DB tak bisa dibuktikan; menyembunyikannya akan membuat kesalahan tautan
   tampak seperti kemajuan.

10. **KUNCI 10 — Halaman `/library` terpisah dari dashboard.** Dashboard cuma mendapat
    **satu** kartu + tautan. Menjejalkan course ke dashboard membuat lajur Library terasa
    jadi lajur utama — padahal Forge yang harus terasa utama.

**Batas yang diterima sadar (WAJIB dicatat di §7 CLAUDE.md saat eksekusi):**
- **Metrik ini mengukur cakupan pembuktian, bukan kualitas kurikulum.** Course bisa 100%
  direproduksi dan tetap mengajarkan hal yang salah; yang menjaga itu telemetri M7 +
  pencabutan manual, bukan L5.
- **Pemetaan materi→node ditulis manusia/script** (`--link`). L5 mempercayai tautan itu;
  ia hanya memeriksa bahwa node-nya ada dan terbukti.
- **n=1 tetap n=1.** Persentase dari satu pelajar adalah catatan perjalanan, bukan
  statistik.

---

## 3. Kontrak & bentuk data

### 3.1 Alur

```
library/<course>/<NN-modul>/<materi>.md          ← frontmatter: type, status, node_ids
        │  (READ-ONLY: frontmatter saja)
        ▼
services/library_progress.read_materials()        murni baca berkas, tanpa DB
        │
        ├── join ──►  DB Forge:
        │              • Attempt(mode ∈ verification|review|placement, result=pass)  → terbukti
        │              • progress.all_statuses()  → mastered / lapsed
        │              • Node                     → node yang dikenal (deteksi menggantung)
        ▼
   LibraryProgress ──► GET /library/progress ──► /library (halaman) + 1 kartu dashboard
```

Yang **tidak** ada di alur ini, dan itu disengaja: `status` frontmatter tak pernah masuk
cabang perhitungan mana pun.

### 3.2 Keadaan per materi (aturan tunggal)

| Keadaan | Syarat | Tampil sebagai |
|---|---|---|
| `unmapped` | `node_ids` kosong | **lubang** — "belum tertempa" |
| `mapped_unproven` | punya `node_ids`, tapi ada yang belum pernah lolos dingin (termasuk node menggantung) | "tertempa, belum dibuktikan" |
| `reproduced` | **semua** `node_ids` pernah lolos attempt mode dingin | "direproduksi" |

Penanda tambahan (bukan keadaan, boleh menumpuk di atas `reproduced`):
`mastered` = semua node-nya berstatus `mastered` · `decayed` = ada node `lapsed`.

### 3.3 Bentuk respons `GET /library/progress`

```json
{
  "total": 5,
  "reproduced": 2,
  "reproduced_pct": 0.4,
  "courses": [
    {
      "course": "fastapi-dasar",
      "title": "FastAPI Dasar",
      "total": 4, "unmapped": 0, "mapped_unproven": 2,
      "reproduced": 2, "mastered": 1, "decayed": 0,
      "reproduced_pct": 0.5,
      "modules": [
        {
          "module": "01-routing-dasar",
          "title": "Routing Dasar",
          "materials": [
            {
              "path": "library/fastapi-dasar/01-routing-dasar/get-route-json.md",
              "title": "GET route JSON dengan status 200",
              "type": "note",
              "note_status": "captured",
              "node_ids": ["n002_get_json_route"],
              "missing_node_ids": [],
              "state": "reproduced",
              "mastered": false,
              "decayed": false
            }
          ]
        }
      ]
    }
  ]
}
```

`note_status` sengaja **dinamai ulang** (bukan `status`) supaya di sisi frontend tak ada
yang tergoda memperlakukannya sebagai status kemajuan — ia status CATATAN (L0).
---

## 4. `backend/app/config.py` — satu konstanta

```python
# --------------------------------------------------------------------------- #
# Lajur Library (L0–L5). Backend MEMBACA folder ini untuk menghitung
# "% direproduksi" (L5) dan TAK PERNAH menulisnya: penulisnya `scripts/` (L1–L3)
# dan promosi L4. Satu alamat, supaya tak ada modul yang menyusun path-nya sendiri.
# --------------------------------------------------------------------------- #
LIBRARY_DIR = REPO_ROOT / "library"
```

---

## 5. `backend/app/services/library_progress.py` (baru)

### 5.1 Perilaku

| Fungsi | Tugas | Butuh DB? |
|---|---|---|
| `read_materials(library_dir=None)` | Baca frontmatter seluruh `library/**/*.md`. Berkas cacat **dilewati**. | tidak |
| `_forge_state(session)` | `(terbukti dingin, mastered, lapsed, node dikenal)` dari DB. | ya |
| `compute(session, library_dir=None)` | Join keduanya → `LibraryProgress`. | ya |

Pemisahan itu disengaja: bagian yang membaca berkas bisa diuji **tanpa DB**, dan ia jadi
tempat yang jelas untuk menegakkan "modul ini tak pernah menulis".

**Berkas cacat dilewati, bukan bikin 500.** Yang bertugas meneriakkan frontmatter rusak
adalah `scripts/verify_library.py` (gerbang commit). Dashboard yang mati total gara-gara
satu berkas setengah tersunting adalah kegagalan yang tak sepadan.

### 5.2 Kode acuan (boleh ditranskripsi utuh)

```python
"""Join lajur Library → Forge: "% direproduksi", bukan "% dibaca" (L5).

Ini PENJAGA, bukan fitur pelaporan. Brainstorm lajur Library menyebut bahayanya apa
adanya: bukan satu invariant jebol, melainkan Bryant menghabiskan waktunya di Library
yang nyaman sementara Forge yang tak nyaman terbengkalai. Begitu progres Library bisa
naik karena MEMBACA, seluruh lajur ini berubah jadi consumption comfort yang §8 tolak.

Tiga aturan yang membuat angkanya jujur — ketiganya diuji di
`backend/tests/test_library_progress.py`:

1. Yang menggerakkan angka HANYA eksekusi kode: attempt mode dingin
   (`kpi.REPRODUCE_MODES`), di-IMPORT bukan disalin. Dua definisi
   "reproduce-without-AI" akan menyimpang, dan yang longgar yang akan dipakai.
2. `status` frontmatter (`outline`/`captured` = status CATATAN, L0) tak pernah masuk
   cabang perhitungan mana pun. Mengisi seluruh catatan = angka identik.
3. Materi tanpa `node_ids` tetap masuk PENYEBUT — course tampil berlubang sampai
   node-nya tertempa DAN terbukti. Itu tampilan yang benar, bukan bug.

Modul ini READ-ONLY terhadap `library/`. Penulisnya `scripts/` (L1–L3) & promosi L4.
"""

from dataclasses import dataclass
from pathlib import Path

import yaml
from sqlmodel import Session, select

from app.config import LIBRARY_DIR
from app.models import Attempt, AttemptResult, Node, ScheduleStatus
from app.services.kpi import REPRODUCE_MODES
from app.services.progress import all_statuses

#: Materi yang bisa "direproduksi". `outline`/`roadmap` adalah berkas STRUKTURAL
#: (indeks & peta): memasukkannya ke penyebut menghukum course hanya karena ia punya
#: banyak modul, dan peta memang bukan unit yang direproduksi.
LEARNABLE_TYPES = ("note", "transcription")

#: Keadaan materi. Tiga, bukan satu angka — "belum ditempa" dan "sudah ditempa tapi
#: belum kamu buktikan" adalah dua utang yang berbeda dan butuh tindakan berbeda.
UNMAPPED = "unmapped"
MAPPED_UNPROVEN = "mapped_unproven"
REPRODUCED = "reproduced"


@dataclass
class MaterialProgress:
    rel_path: str  # relatif terhadap library/ (POSIX)
    title: str
    type: str
    note_status: str  # LABEL saja — tak pernah masuk hitungan (aturan 2)
    node_ids: list[str]
    missing_node_ids: list[str]
    state: str
    mastered: bool
    decayed: bool


@dataclass
class ModuleProgress:
    module: str
    title: str
    materials: list[MaterialProgress]


@dataclass
class CourseProgress:
    course: str
    title: str
    modules: list[ModuleProgress]
    total: int
    unmapped: int
    mapped_unproven: int
    reproduced: int
    mastered: int
    decayed: int
    reproduced_pct: float | None


@dataclass
class LibraryProgress:
    courses: list[CourseProgress]
    total: int
    reproduced: int
    reproduced_pct: float | None


@dataclass
class RawMaterial:
    rel_path: str
    course: str
    module: str
    fm: dict


# --------------------------------------------------------------------------- #
# Baca berkas (tanpa DB)
# --------------------------------------------------------------------------- #
def _frontmatter(text: str) -> dict | None:
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    try:
        fm = yaml.safe_load(parts[1])
    except yaml.YAMLError:
        return None
    return fm if isinstance(fm, dict) else None


def read_materials(library_dir: Path | None = None) -> list[RawMaterial]:
    """Frontmatter seluruh berkas `library/`. MURNI BACA — tak ada Session di sini.

    Berkas cacat DILEWATI: yang bertugas meneriakkannya `scripts/verify_library.py`
    (gerbang commit). Dashboard mati total gara-gara satu berkas setengah tersunting
    adalah kegagalan yang tak sepadan.
    """
    root = library_dir or LIBRARY_DIR
    out: list[RawMaterial] = []
    if not root.is_dir():
        return out
    for path in sorted(root.glob("**/*.md")):
        rel = path.relative_to(root)
        if len(rel.parts) < 2:  # README.md & apa pun di akar library/
            continue
        fm = _frontmatter(path.read_text(encoding="utf-8"))
        if fm is None:
            continue
        out.append(
            RawMaterial(
                rel_path=rel.as_posix(),
                course=rel.parts[0],
                module=rel.parts[1] if len(rel.parts) > 2 else "",
                fm=fm,
            )
        )
    return out


# --------------------------------------------------------------------------- #
# Sisi Forge (DB)
# --------------------------------------------------------------------------- #
def _forge_state(session: Session) -> tuple[set[str], set[str], set[str], set[str]]:
    """(terbukti dingin, mastered, lapsed, node yang dikenal DB).

    "Terbukti" dihitung dari ATTEMPT, bukan dari status: status bisa berubah karena
    peluruhan jadwal, sedangkan bukti bahwa Bryant pernah memproduksinya tidak hilang
    (§7 2026-08-21 Q3).
    """
    known = {n.id for n in session.exec(select(Node)).all()}
    proven = {
        a.node_id
        for a in session.exec(
            select(Attempt).where(
                Attempt.mode.in_(REPRODUCE_MODES),
                Attempt.result == AttemptResult.passed.value,
            )
        ).all()
    }
    statuses = all_statuses(session)
    mastered = {nid for nid, s in statuses.items() if s == ScheduleStatus.mastered.value}
    lapsed = {nid for nid, s in statuses.items() if s == ScheduleStatus.lapsed.value}
    return proven, mastered, lapsed, known


# --------------------------------------------------------------------------- #
# Join
# --------------------------------------------------------------------------- #
def compute(session: Session, *, library_dir: Path | None = None) -> LibraryProgress:
    proven, mastered_ids, lapsed_ids, known = _forge_state(session)
    materials = read_materials(library_dir)

    # Judul course & modul diambil dari `_index.md`-nya (berkas struktural itu tak
    # ikut dihitung, tapi ia yang menyimpan namanya).
    titles: dict[tuple[str, str], str] = {}
    for raw in materials:
        if Path(raw.rel_path).name == "_index.md":
            titles[(raw.course, raw.module)] = str(raw.fm.get("title") or "")

    grouped: dict[str, dict[str, list[MaterialProgress]]] = {}
    for raw in materials:
        if str(raw.fm.get("type") or "") not in LEARNABLE_TYPES:
            continue  # _index (outline/roadmap) = struktural, bukan unit belajar
        node_ids = [str(x) for x in (raw.fm.get("node_ids") or [])]
        missing = [n for n in node_ids if n not in known]
        # Node menggantung tak ada di `proven`, jadi materinya otomatis BELUM terbukti —
        # tautan salah tak boleh tampak seperti kemajuan (KUNCI 9).
        reproduced = bool(node_ids) and all(n in proven for n in node_ids)
        state = REPRODUCED if reproduced else (UNMAPPED if not node_ids else MAPPED_UNPROVEN)
        grouped.setdefault(raw.course, {}).setdefault(raw.module, []).append(
            MaterialProgress(
                rel_path=raw.rel_path,
                title=str(raw.fm.get("title") or Path(raw.rel_path).stem),
                type=str(raw.fm.get("type") or ""),
                note_status=str(raw.fm.get("status") or ""),
                node_ids=node_ids,
                missing_node_ids=missing,
                state=state,
                mastered=bool(node_ids) and all(n in mastered_ids for n in node_ids),
                decayed=any(n in lapsed_ids for n in node_ids),
            )
        )

    courses: list[CourseProgress] = []
    for course in sorted(grouped):
        modules = [
            ModuleProgress(
                module=module,
                title=titles.get((course, module)) or module,
                materials=sorted(mats, key=lambda m: m.rel_path),
            )
            for module, mats in sorted(grouped[course].items())
        ]
        semua = [m for mod in modules for m in mod.materials]
        n = len(semua)
        rep = sum(1 for m in semua if m.state == REPRODUCED)
        courses.append(
            CourseProgress(
                course=course,
                title=titles.get((course, "")) or course,
                modules=modules,
                total=n,
                unmapped=sum(1 for m in semua if m.state == UNMAPPED),
                mapped_unproven=sum(1 for m in semua if m.state == MAPPED_UNPROVEN),
                reproduced=rep,
                mastered=sum(1 for m in semua if m.mastered),
                decayed=sum(1 for m in semua if m.decayed),
                reproduced_pct=(rep / n) if n else None,
            )
        )

    total = sum(c.total for c in courses)
    reproduced = sum(c.reproduced for c in courses)
    return LibraryProgress(
        courses=courses,
        total=total,
        reproduced=reproduced,
        reproduced_pct=(reproduced / total) if total else None,
    )
```

---

## 6. `backend/app/routers/library.py` (baru)

```python
"""Router lajur Library (L5) — "% direproduksi", bukan "% dibaca".

Router tipis di atas `services/library_progress.py`; definisi metriknya ada di sana
(pola yang sama dengan `stats.py` di atas `kpi.py`).

READ-ONLY: tak ada satu pun endpoint di sini yang menulis ke `library/`. Penulisnya
`scripts/` (L1–L3) dan promosi L4 — dan batas itu yang menjaga lajur Library tetap
bisa dipakai (Obsidian, git) tanpa backend menyala.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import Session

from app.db import get_session
from app.services import library_progress

router = APIRouter(prefix="/library", tags=["library"])


class MaterialOut(BaseModel):
    path: str  # relatif repo, mis. "library/fastapi-dasar/01-routing/get.md"
    title: str
    type: str
    #: Status CATATAN (outline/captured). Sengaja TIDAK bernama `status` supaya tak ada
    #: yang memperlakukannya sebagai status kemajuan — status reproduksi hanya datang
    #: dari eksekusi kode (§1.2), dan yang ini cuma label (§7 2026-09-04).
    note_status: str
    node_ids: list[str]
    missing_node_ids: list[str]
    state: str  # unmapped | mapped_unproven | reproduced
    mastered: bool
    decayed: bool


class ModuleOut(BaseModel):
    module: str
    title: str
    materials: list[MaterialOut]


class CourseOut(BaseModel):
    course: str
    title: str
    total: int
    unmapped: int
    mapped_unproven: int
    reproduced: int
    mastered: int
    decayed: int
    reproduced_pct: float | None
    modules: list[ModuleOut]


class LibraryProgressOut(BaseModel):
    total: int
    reproduced: int
    reproduced_pct: float | None
    courses: list[CourseOut]


@router.get("/progress", response_model=LibraryProgressOut)
def get_library_progress(session: Session = Depends(get_session)) -> LibraryProgressOut:
    data = library_progress.compute(session)
    return LibraryProgressOut(
        total=data.total,
        reproduced=data.reproduced,
        reproduced_pct=data.reproduced_pct,
        courses=[
            CourseOut(
                course=c.course,
                title=c.title,
                total=c.total,
                unmapped=c.unmapped,
                mapped_unproven=c.mapped_unproven,
                reproduced=c.reproduced,
                mastered=c.mastered,
                decayed=c.decayed,
                reproduced_pct=c.reproduced_pct,
                modules=[
                    ModuleOut(
                        module=m.module,
                        title=m.title,
                        materials=[
                            MaterialOut(
                                path=f"library/{mat.rel_path}",
                                title=mat.title,
                                type=mat.type,
                                note_status=mat.note_status,
                                node_ids=mat.node_ids,
                                missing_node_ids=mat.missing_node_ids,
                                state=mat.state,
                                mastered=mat.mastered,
                                decayed=mat.decayed,
                            )
                            for mat in m.materials
                        ],
                    )
                    for m in c.modules
                ],
            )
            for c in data.courses
        ],
    )
```

Daftarkan di `backend/app/main.py`, **sebelum** blok M5 (router Library bagian dari loop
inti, bukan integrasi yang boleh mati):

```python
app.include_router(stats.router)
app.include_router(library.router)
```

---

## 7. Frontend

### 7.1 `frontend/lib/api.ts` — tipe + satu fungsi

```typescript
// --- L5: lajur Library ("% direproduksi", bukan "% dibaca") ---
export type MaterialState = "unmapped" | "mapped_unproven" | "reproduced";

export interface LibraryMaterial {
  path: string;
  title: string;
  type: string;
  /** Status CATATAN (outline/captured) — label, BUKAN kemajuan. Jangan diakumulasi. */
  note_status: string;
  node_ids: string[];
  missing_node_ids: string[];
  state: MaterialState;
  mastered: boolean;
  decayed: boolean;
}

export interface LibraryModule {
  module: string;
  title: string;
  materials: LibraryMaterial[];
}

export interface LibraryCourse {
  course: string;
  title: string;
  total: number;
  unmapped: number;
  mapped_unproven: number;
  reproduced: number;
  mastered: number;
  decayed: number;
  reproduced_pct: number | null;
  modules: LibraryModule[];
}

export interface LibraryProgress {
  total: number;
  reproduced: number;
  reproduced_pct: number | null;
  courses: LibraryCourse[];
}
```

di objek `api`:

```typescript
  // --- L5 ---
  getLibraryProgress: () =>
    fetch(`${BACKEND_URL}/library/progress`).then(j<LibraryProgress>),
```

### 7.2 `frontend/app/library/page.tsx` (baru)

Batas gaya yang berlaku (§7 2026-08-23): Tailwind + token CSS var, **tanpa emoji**,
ikon garis SVG dari `components/ui/Icon`, angka `tabular-nums`, kontras AA.

```tsx
"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, type LibraryCourse, type LibraryMaterial, type LibraryProgress } from "../../lib/api";
import Badge, { type BadgeTone } from "../components/ui/Badge";
import Card from "../components/ui/Card";
import Container from "../components/ui/Container";
import EmptyState from "../components/ui/EmptyState";
import ErrorState from "../components/ui/ErrorState";
import PageHeader from "../components/ui/PageHeader";
import { IconArrowRight, IconInbox } from "../components/ui/Icon";

/**
 * Halaman lajur Library (L5) — PENJAGA metrik, bukan katalog bacaan.
 *
 * Yang ditampilkan: berapa banyak materi yang sudah kamu PRODUKSI ULANG tanpa AI.
 * Yang sengaja TIDAK ditampilkan: persentase catatan yang sudah diisi. `note_status`
 * muncul hanya sebagai label netral per materi — tak pernah diakumulasi, tak pernah
 * jadi progress bar. Begitu "sudah dibaca" bisa naik jadi angka, lajur ini berubah
 * jadi consumption comfort yang §8 tolak.
 */
export default function LibraryPage() {
  const [data, setData] = useState<LibraryProgress | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = () => {
    setError(null);
    api.getLibraryProgress().then(setData).catch((e) => setError(String(e)));
  };
  useEffect(load, []);

  return (
    <Container>
      <PageHeader
        title="Library"
        subtitle={
          <>
            Diukur dari <strong className="font-semibold text-fg">yang sudah kamu produksi
            ulang tanpa AI</strong> — bukan dari yang sudah dibaca atau dicatat. Course
            tampil berlubang sampai node-nya tertempa dan terbukti.
          </>
        }
      />

      {error && <ErrorState error={error} onRetry={load} />}

      {data && data.courses.length === 0 && (
        <EmptyState
          icon={<IconInbox />}
          title="Belum ada course di library/"
          description="Mulai dari skill course-intake (mirror course luar) atau learn-intake (peta belajar)."
        />
      )}

      {data && data.courses.length > 0 && (
        <>
          <Card className="p-4">
            <div className="text-xs font-medium uppercase tracking-wide text-muted">
              materi direproduksi
            </div>
            <div className="mt-0.5 text-3xl font-bold leading-tight tabular-nums">
              {pct(data.reproduced_pct)}
            </div>
            <div className="mt-0.5 text-xs text-muted">
              {data.reproduced}/{data.total} materi terbukti tanpa AI
            </div>
          </Card>

          <div className="mt-6 space-y-6">
            {data.courses.map((c) => (
              <CourseSection key={c.course} course={c} />
            ))}
          </div>
        </>
      )}
    </Container>
  );
}

function pct(v: number | null): string {
  return v === null ? "—" : `${Math.round(v * 100)}%`;
}

function CourseSection({ course }: { course: LibraryCourse }) {
  return (
    <section>
      <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
        <h2 className="text-lg font-semibold">{course.title}</h2>
        <span className="text-sm text-muted tabular-nums">
          {course.reproduced}/{course.total} direproduksi · {course.unmapped} belum tertempa
        </span>
      </div>

      {/* Bar = proporsi materi yang TERBUKTI. Materi tanpa node ikut penyebut, jadi
          lubangnya terlihat sebagai ruang kosong — itu memang maksudnya. */}
      <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-neutral-bg">
        <div
          className="h-full bg-success"
          style={{ width: `${Math.round((course.reproduced_pct ?? 0) * 100)}%` }}
        />
      </div>

      <div className="mt-3 space-y-4">
        {course.modules.map((m) => (
          <div key={m.module}>
            <h3 className="text-sm font-semibold text-muted">{m.title}</h3>
            <ul className="mt-2 space-y-2">
              {m.materials.map((mat) => (
                <li key={mat.path}>
                  <MaterialRow material={mat} />
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </section>
  );
}

const STATE_LABEL: Record<LibraryMaterial["state"], { text: string; tone: BadgeTone }> = {
  unmapped: { text: "belum tertempa", tone: "neutral" },
  mapped_unproven: { text: "tertempa, belum dibuktikan", tone: "warning" },
  reproduced: { text: "direproduksi", tone: "success" },
};

function MaterialRow({ material }: { material: LibraryMaterial }) {
  const label = STATE_LABEL[material.state];
  return (
    <Card className="flex flex-wrap items-center justify-between gap-2 p-3">
      <div className="min-w-0">
        <div className="truncate font-medium">{material.title}</div>
        <div className="mt-0.5 truncate font-mono text-xs text-subtle">
          {material.node_ids.length > 0 ? material.node_ids.join(" · ") : "belum ada node"}
          {material.missing_node_ids.length > 0 && (
            <span className="text-danger"> · node hilang: {material.missing_node_ids.join(", ")}</span>
          )}
        </div>
      </div>
      <div className="flex flex-wrap items-center gap-2">
        {/* Label catatan — netral, tak pernah diakumulasi (KUNCI 8). */}
        <span className="text-xs text-subtle">catatan: {material.note_status || "—"}</span>
        {material.decayed && <Badge tone="warning">meluruh</Badge>}
        {material.mastered && <Badge tone="info">dikuasai</Badge>}
        <Badge tone={label.tone}>{label.text}</Badge>
        {material.node_ids.length > 0 && (
          <Link
            href={`/node/${material.node_ids[0]}`}
            className="inline-flex items-center gap-1 text-sm text-accent hover:underline"
          >
            Buka node <IconArrowRight size={14} />
          </Link>
        )}
      </div>
    </Card>
  );
}
```

### 7.3 `frontend/app/page.tsx` — satu kartu + tautan

Dashboard **tidak** menampilkan daftar course (KUNCI 10). Yang ditambahkan hanya:

- state baru: `const [lib, setLib] = useState<LibraryProgress | null>(null);` dan
  `api.getLibraryProgress()` masuk ke `Promise.all` yang sudah ada (kegagalannya tak boleh
  merobohkan dashboard — bungkus dengan `.catch(() => null)`);
- satu `<Kpi>` di `KpiRow` (grid `sm:grid-cols-3` → `sm:grid-cols-4`):

```tsx
      <Kpi
        label="materi direproduksi"
        value={lib ? pct(lib.reproduced_pct) : "—"}
        hint={lib ? `${lib.reproduced}/${lib.total} materi Library terbukti` : "library/ kosong"}
      />
```

- satu tautan di baris aksi `DueSection`:

```tsx
          <Link href="/library" className="inline-flex items-center gap-1 text-accent hover:underline">
            Library <IconArrowRight size={14} />
          </Link>
```
---

## 8. `backend/tests/test_library_progress.py` (baru)

Fixture `session` dari `conftest.py` sudah memuat domain fastapi nyata (n001–n013), jadi
node yang ditautkan test benar-benar ada. Library-nya **selalu tmp** — test tak pernah
menyentuh `library/` sungguhan.

```python
"""Test penjaga metrik lajur Library (L5).

Yang dibuktikan di sini semuanya adalah aturan yang membuat angkanya JUJUR:

- Mengisi seluruh catatan (`status: captured`) TIDAK menggerakkan satu angka pun.
  Ini test terpenting di berkas ini: begitu ia merah, lajur Library sudah berubah
  jadi metrik "% dibaca" dan penjaganya bocor.
- Attempt BERSCAFFOLD (`acquisition`) bukan bukti reproduksi.
- Materi tanpa `node_ids` tetap masuk penyebut (course tampil berlubang).
- Materi dengan banyak node butuh SEMUANYA terbukti.
- `node_ids` menggantung dilaporkan, dan dihitung BELUM terbukti.
- Berkas struktural (`_index`) tak ikut dihitung.
- Modul ini tak pernah menulis ke `library/`.
"""

from pathlib import Path

import pytest
import yaml

from app.models import Attempt, AttemptMode, AttemptResult, ScheduleItem, ScheduleStatus
from app.services import library_progress as lp

NODE_A = "n002_get_json_route"
NODE_B = "n003_path_param_404"


def _write(lib: Path, rel: str, **over) -> Path:
    parts = rel.split("/")
    fm = {
        "title": parts[-1].removesuffix(".md"),
        "course": parts[0],
        "module": parts[1] if len(parts) > 2 else "",
        "type": "note",
        "source_refs": [],
        "node_ids": [],
        "status": "outline",
        "created": "2026-09-06",
    }
    fm.update(over)
    path = lib / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    dumped = yaml.safe_dump(fm, sort_keys=False, allow_unicode=True).strip()
    path.write_text(f"---\n{dumped}\n---\n\n# {fm['title']}\n", encoding="utf-8")
    return path


@pytest.fixture
def lib(tmp_path):
    """Course kecil: 1 _index struktural + 3 materi (satu ditautkan ke NODE_A)."""
    root = tmp_path / "library"
    _write(root, "kursus/_index.md", type="outline", status="captured", title="Kursus")
    _write(root, "kursus/01-modul/_index.md", type="outline", status="captured", title="Modul 1")
    _write(root, "kursus/01-modul/a.md", node_ids=[NODE_A])
    _write(root, "kursus/01-modul/b.md")
    _write(root, "kursus/01-modul/c.md")
    return root


def _attempt(session, node_id, *, mode=AttemptMode.verification.value, result="pass"):
    session.add(Attempt(node_id=node_id, mode=mode, result=result))
    session.commit()


def _schedule(session, node_id, status):
    """UPDATE, bukan INSERT — `load_domain_into_db` (conftest) sudah membuat satu
    `ScheduleItem` per node, dan `node_id` adalah primary key. Menambah baris baru
    akan gagal `UNIQUE constraint failed: scheduleitem.node_id`."""
    item = session.get(ScheduleItem, node_id) or ScheduleItem(node_id=node_id)
    item.status = status
    session.add(item)
    session.commit()


# --------------------------------------------------------------------------- #
# Penyebut & keadaan
# --------------------------------------------------------------------------- #
def test_materi_tanpa_node_ids_tetap_masuk_penyebut(session, lib):
    data = lp.compute(session, library_dir=lib)
    course = data.courses[0]
    assert course.total == 3            # _index TIDAK dihitung
    assert course.unmapped == 2
    assert course.reproduced == 0
    assert course.reproduced_pct == 0.0


def test_index_struktural_tak_masuk_penyebut(session, lib):
    data = lp.compute(session, library_dir=lib)
    paths = [m.rel_path for c in data.courses for mo in c.modules for m in mo.materials]
    assert not any(p.endswith("_index.md") for p in paths)


def test_attempt_dingin_membuktikan_materi(session, lib):
    _attempt(session, NODE_A)
    data = lp.compute(session, library_dir=lib)
    materi = _by_name(data, "a.md")
    assert materi.state == lp.REPRODUCED
    assert data.courses[0].reproduced == 1


def test_attempt_berscaffold_tidak_dihitung(session, lib):
    """Latihan dengan scaffold di layar bukan bukti reproduksi (kpi.REPRODUCE_MODES)."""
    _attempt(session, NODE_A, mode=AttemptMode.acquisition.value)
    data = lp.compute(session, library_dir=lib)
    assert _by_name(data, "a.md").state == lp.MAPPED_UNPROVEN


def test_attempt_gagal_tidak_dihitung(session, lib):
    _attempt(session, NODE_A, result=AttemptResult.failed.value)
    data = lp.compute(session, library_dir=lib)
    assert _by_name(data, "a.md").state == lp.MAPPED_UNPROVEN


def test_materi_dengan_dua_node_butuh_keduanya(session, lib):
    _write(lib, "kursus/01-modul/a.md", node_ids=[NODE_A, NODE_B])
    _attempt(session, NODE_A)
    assert _by_name(lp.compute(session, library_dir=lib), "a.md").state == lp.MAPPED_UNPROVEN
    _attempt(session, NODE_B)
    assert _by_name(lp.compute(session, library_dir=lib), "a.md").state == lp.REPRODUCED


def test_node_menggantung_dilaporkan_dan_belum_terbukti(session, lib):
    _write(lib, "kursus/01-modul/a.md", node_ids=["n999_tak_ada"])
    materi = _by_name(lp.compute(session, library_dir=lib), "a.md")
    assert materi.missing_node_ids == ["n999_tak_ada"]
    assert materi.state == lp.MAPPED_UNPROVEN


# --------------------------------------------------------------------------- #
# Penanda
# --------------------------------------------------------------------------- #
def test_lapsed_tetap_terbukti_tapi_ditandai_meluruh(session, lib):
    """Yang meluruh memorinya, BUKAN buktinya (§7 2026-08-21 Q3)."""
    _attempt(session, NODE_A)
    _schedule(session, NODE_A, ScheduleStatus.lapsed.value)
    materi = _by_name(lp.compute(session, library_dir=lib), "a.md")
    assert materi.state == lp.REPRODUCED and materi.decayed is True


def test_mastered_ditandai(session, lib):
    _attempt(session, NODE_A)
    _schedule(session, NODE_A, ScheduleStatus.mastered.value)
    assert _by_name(lp.compute(session, library_dir=lib), "a.md").mastered is True


# --------------------------------------------------------------------------- #
# ANTI-GAMING — test terpenting di berkas ini
# --------------------------------------------------------------------------- #
def test_status_captured_tidak_menggerakkan_angka(session, lib):
    _attempt(session, NODE_A)
    sebelum = lp.compute(session, library_dir=lib)

    for path in lib.glob("**/*.md"):
        teks = path.read_text(encoding="utf-8")
        path.write_text(teks.replace("status: outline", "status: captured"), encoding="utf-8")

    sesudah = lp.compute(session, library_dir=lib)
    assert (sesudah.total, sesudah.reproduced, sesudah.reproduced_pct) == (
        sebelum.total, sebelum.reproduced, sebelum.reproduced_pct
    )
    # Labelnya BOLEH berubah — yang tak boleh adalah angkanya.
    assert _by_name(sesudah, "b.md").note_status == "captured"
    assert _by_name(sesudah, "b.md").state == lp.UNMAPPED


def test_membaca_tidak_pernah_menulis(session, lib):
    jejak = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in sorted(lib.glob("**/*.md"))}
    lp.compute(session, library_dir=lib)
    assert {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in sorted(lib.glob("**/*.md"))} == jejak


def test_berkas_cacat_dilewati_bukan_meledak(session, lib):
    (lib / "kursus/01-modul/rusak.md").write_text("bukan frontmatter", encoding="utf-8")
    data = lp.compute(session, library_dir=lib)
    assert data.courses[0].total == 3  # tetap 3, tanpa exception


def test_library_kosong_tidak_error(session, tmp_path):
    data = lp.compute(session, library_dir=tmp_path / "tak-ada")
    assert data.courses == [] and data.total == 0 and data.reproduced_pct is None


def _by_name(data: lp.LibraryProgress, nama: str) -> lp.MaterialProgress:
    for course in data.courses:
        for module in course.modules:
            for materi in module.materials:
                if materi.rel_path.endswith(nama):
                    return materi
    raise AssertionError(f"materi {nama} tak ada di hasil")
```

Tambahan satu test HTTP tipis (gaya `test_health.py`) — ia membaca `library/` **nyata**,
jadi jangan menegakkan angka, cukup bentuknya:

```python
def test_endpoint_progress_membalas_bentuk_yang_benar():
    from fastapi.testclient import TestClient
    from app.main import app

    with TestClient(app) as client:
        resp = client.get("/library/progress")
    assert resp.status_code == 200
    body = resp.json()
    assert {"total", "reproduced", "reproduced_pct", "courses"} <= set(body)
    assert body["reproduced"] <= body["total"]
```

---

## 9. Dokumen yang ikut diperbarui

1. **`library/README.md`** — tambah bagian pendek "Bagaimana progres dihitung (L5)":
   tiga keadaan, apa yang masuk penyebut, dan kalimat tegas bahwa `status` frontmatter
   **tak pernah** masuk hitungan. README ini yang dibaca saat menulis materi baru; kalau
   aturannya cuma hidup di kode, ia akan dilanggar oleh niat baik.
2. **`CLAUDE.md` §6** — tambahkan halaman `/library` ke daftar halaman frontend dan
   endpoint `GET /library/progress`.
3. **`CLAUDE.md` §7** — entri keputusan baru (KUNCI 1–10 + batas yang diterima).
4. **`docs/roadmap-library-lane.md`** — tandai L5 ✅ dan catat bukti (test + smoke).

---

## 10. Urutan build (langkah demi langkah)

Prinsip yang sama dengan L3/L4: **penjaga dulu, tampilan belakangan.** Di L5 itu berarti
metrik + test anti-gaming harus hijau sebelum satu piksel dibuat — kalau tidak, yang
selesai duluan adalah halaman yang enak dilihat, dan angkanya menyusul mengikuti tampilan.

1. **`config.LIBRARY_DIR`** (§4).
2. **`services/library_progress.py`** (§5) — tulis `read_materials` lebih dulu, lalu
   `_forge_state`, lalu `compute`.
3. **`backend/tests/test_library_progress.py`** (§8) — jalankan sampai hijau, terutama
   `test_status_captured_tidak_menggerakkan_angka` dan `test_membaca_tidak_pernah_menulis`.
4. **`routers/library.py`** + registrasi di `main.py` + test HTTP tipis.
5. **`frontend/lib/api.ts`** (tipe + `getLibraryProgress`).
6. **`frontend/app/library/page.tsx`**.
7. **Kartu KPI + tautan di dashboard** (`app/page.tsx`).
8. **Smoke** (§11).
9. **Dokumen** (§9) + entri §7 CLAUDE.md.

---

## 11. Verifikasi manual (smoke)

> **Catatan mesin ini (RAM ±3.4 GB):** jangan menyalakan `npm run build`, dev server, dan
> browser sekaligus — mudah OOM. Pakai skill `run-learning-engine`, ambil screenshot
> per-halaman, dan **backup `backend/app.db` dulu** sebelum menyentuh data.

```bash
# 0) Aman dulu
cp backend/app.db backend/app.db.bak-$(date +%Y%m%d-%H%M%S)

# 1) Backend
cd backend && .venv/Scripts/python.exe -m uvicorn app.main:app --reload

# 2) Endpoint
curl -s localhost:8000/library/progress | head -40

# 3) Frontend
cd frontend && npm run dev      # buka /library dan /
```

**Yang WAJIB kamu lihat:**

| Uji | Harapan |
|---|---|
| `GET /library/progress` | `200`; `fastapi-dasar` muncul dengan `total: 4` (4 materi, `_index` tak ikut) |
| Course `fastapi-produksi` (peta generate L3) | hari ini: `total: 1`, `unmapped: 1`, `reproduced_pct: 0.0` — **berlubang, bukan hilang** |
| **Uji anti-gaming manual:** ubah satu materi jadi `status: captured`, panggil ulang endpoint | `reproduced`/`reproduced_pct` **identik**; hanya `note_status` berubah. Lalu `git checkout` berkasnya |
| Materi yang node-nya sudah pernah kamu lolosi dingin | `state: "reproduced"` |
| Materi ber-`node_ids` yang belum pernah dicoba dingin | `state: "mapped_unproven"` |
| Halaman `/library` | tiga label keadaan terlihat, bar course = proporsi terbukti, catatan tampil sebagai label netral (bukan bar) |
| Dashboard `/` | satu kartu "materi direproduksi" + tautan ke `/library`; sisa dashboard tak berubah |
| Backend dimatikan lalu buka `/library` | `ErrorState` (bukan halaman putih) |
| `library/` di-rename sementara → panggil endpoint | `200` dengan `courses: []`, bukan `500` |

---

## 12. Definition of Done (checklist)

> **Dieksekusi & diverifikasi 2026-09-06.** Semua kotak di bawah dicentang dari hasil
> jalan sungguhan, bukan dari pembacaan kode. Bukti ringkasnya di tabel §12.1.

- [x] `LIBRARY_DIR` di `config.py`; **tak ada** modul lain yang menyusun path `library/`
      untuk metrik. (Satu pengecualian yang disengaja & kini berkomentar:
      `claude/jobs.py::_library_material` tetap menurunkan root-nya dari `jobs.REPO_ROOT`
      — seluruh fungsi itu berjangkar di sana dan test L4 mem-patch-nya; memakai
      `LIBRARY_DIR` justru membuat pemeriksaan containment mengabaikan root yang di-patch.)
- [x] `services/library_progress.py` ada: `read_materials` (tanpa DB) + `compute` (join).
- [x] `GET /library/progress` terdaftar di `main.py` (sebelum blok M5) dan membalas
      bentuk §3.3 persis.
- [x] Halaman `/library` + satu kartu KPI di dashboard + tipe & fungsi di `lib/api.ts`.
- [x] Test hijau: `cd backend && .venv/Scripts/python.exe -m pytest -q` -> **201 passed**
      (185 lama + 16 L5, 0 regresi) dan `pytest scripts/ -q` -> **62 passed**.
- [x] **Dua test penjaga hijau & benar-benar dibaca:**
      `test_status_captured_tidak_menggerakkan_angka` (angka identik sesudah SELURUH
      materi jadi `captured`) dan `test_membaca_tidak_pernah_menulis` (byte + mtime tiap
      berkas tak berubah sesudah `compute`).
- [x] `ruff check .` dari `backend/` -> **All checks passed**; `ruff format --check` ->
      5 berkas sudah terformat.
- [x] Frontend tanpa error TypeScript BARU: `tsc --noEmit` hanya menyisakan **2 error
      lama** di `app/components/SandboxEditor.tsx` (typing monaco `javascriptDefaults`/
      `typescriptDefaults`) yang sudah ada sebelum L5 dan tak disentuh L5. `next dev`
      meng-compile `/library` & `/` tanpa error (200 keduanya).
- [x] Seluruh baris tabel smoke §11 terbukti — termasuk **uji anti-gaming manual** dan
      **library/ hilang -> 200 kosong**. Rincian di §12.1.
- [x] `library/README.md` (bagian "Bagaimana progres dihitung (L5)"), `CLAUDE.md` §6
      (halaman `/library` + perintah) & §7 (entri keputusan 2026-09-06 L5), dan
      `docs/roadmap-library-lane.md` (L5 ditandai selesai + bukti) diperbarui.
- [x] **Invariant utuh:** `git status library/` sesudah seluruh smoke hanya menampilkan
      suntingan dokumen yang memang disengaja — backend tak menulis apa pun; tak ada
      field frontmatter baru; `status` catatan tak pernah diakumulasi (dibuktikan dua
      kali: unit test + smoke HTTP); angka hanya bergerak oleh attempt mode dingin.

### 12.1 Bukti smoke (dijalankan 2026-09-06, backend `:8000` + `next dev` `:3000`)

| Uji §11 | Hasil nyata |
|---|---|
| `GET /library/progress` | `200`; `total: 5`, `reproduced: 0`, `reproduced_pct: 0.0`; `fastapi-dasar` `total: 4` (`_index` tak ikut, judul course/modul terbaca dari `_index`) |
| Course `fastapi-produksi` (peta generate L3) | `total: 1`, `unmapped: 1`, `reproduced_pct: 0.0` — **berlubang, bukan hilang** (acceptance L4 yang belum tuntas jadi terlihat) |
| **Uji anti-gaming manual** | `post-pydantic-body.md` diubah `outline` -> `captured`, endpoint dipanggil ulang: `(total, reproduced, pct)` **identik** `5 0 0.0`; hanya `note_status` berubah jadi `captured`, `state` tetap `mapped_unproven`. Berkas dipulihkan `git checkout` |
| Materi yang node-nya sudah lolos dingin | Satu `Attempt(n002, verification, pass)` disisipkan -> `get-route-json.md` jadi `reproduced`, global `1/5 = 0.2`. Baris smoke itu **dihapus lagi** (verifikasi isi dulu), angka kembali `5 0 0.0` |
| Materi ber-`node_ids` yang belum dicoba dingin | 4 materi `fastapi-dasar` semuanya `mapped_unproven` (DB Bryant memang belum punya satu pun attempt) |
| Halaman `/library` | Tiga label keadaan terlihat ("belum tertempa" netral · "tertempa, belum dibuktikan" warning · "direproduksi" success), bar course = proporsi terbukti, catatan tampil sebagai **label netral** ("catatan: captured/outline"), bukan bar |
| Dashboard `/` | Kartu keempat "MATERI DIREPRODUKSI 0% · 0/5 materi Library terbukti" + tautan "Library ->" di baris aksi; KPI Forge & peta progres tak berubah (`KpiRowSkeleton` ikut dinaikkan ke 4 kolom) |
| Backend dimatikan lalu buka `/library` | `ErrorState` "Tidak bisa menghubungi backend" + tombol **Coba lagi** — bukan halaman putih |
| `library/` di-rename sementara -> panggil endpoint | `200` dengan `{"total":0,"reproduced":0,"reproduced_pct":null,"courses":[]}`, bukan `500`. Folder dipulihkan, `total` kembali 5 |

**Satu baris yang TIDAK di-smoke (dan alasannya):** guard `.catch(() => null)` pada
`getLibraryProgress()` di dashboard hanya bermakna bila `/library/progress` gagal
sementara `/stats` sehat — keadaan yang tak bisa dibuat tanpa mengubah kode. Dengan
backend mati **seluruhnya**, dashboard memang menampilkan `ErrorState` (perilaku lama,
tak berubah). Guard-nya benar secara konstruksi, tapi jujurnya: ia belum pernah dilihat
bekerja.

---

## 13. Gotchas / jebakan yang harus dihindari

1. **Jangan pernah menambahkan `status` catatan ke perhitungan** — termasuk "kecil-kecilan"
   seperti mengurutkan course berdasarkan berapa banyak yang sudah `captured`. Urutan pun
   adalah pesan tentang apa yang dihargai.
2. **Pembulatan bisa berbohong.** `Math.round(0.996)` = 100% padahal masih ada materi yang
   belum terbukti. Aturan: kalau `reproduced < total`, jangan pernah menampilkan `100%`
   (batasi di 99%), dan **selalu** tampilkan `x/y` di sebelahnya.
3. **Definisi reproduksi harus di-IMPORT dari `kpi.py`**, tak boleh ditulis ulang. Dua
   definisi "reproduce-without-AI" akan menyimpang, dan yang longgar yang akan dipakai.
4. **`rel.as_posix()`, bukan `str(rel)`** — di Windows path akan berisi `\` dan pointer di
   respons berubah bentuk tergantung OS penulisnya (kebocoran yang sama sudah diperbaiki
   di `node_loader` pada M4).
5. **Berkas cacat dilewati, bukan melempar.** Endpoint dashboard yang 500 gara-gara satu
   berkas setengah tersunting akan membuat Bryant berhenti memakainya.
6. **Kegagalan `getLibraryProgress()` tak boleh merobohkan dashboard.** Bungkus dengan
   `.catch(() => null)` di `Promise.all` — KPI Library boleh kosong, KPI Forge tidak boleh
   ikut hilang.
7. **Test HTTP membaca `library/` & DB SUNGGUHAN** (`TestClient(app)`), jadi jangan
   menegakkan angka di sana — hanya bentuk. Angka diuji lewat `library_dir=tmp`.
8. **Materi dengan `node_ids` lintas domain** (mis. satu materi menunjuk node fastapi &
   react) sah dan harus tetap bekerja: `known` diambil dari seluruh tabel `Node`, bukan
   per domain.
9. **Jangan bikin endpoint tulis apa pun di router ini.** Kalau nanti butuh menautkan node
   dari UI, jalurnya tetap `scripts/verify_library.py --link` (L4 KUNCI 11) — bukan
   `POST /library/...`.
10. **Mesin RAM kecil:** jangan menjalankan build frontend bersamaan dengan browser
    screenshot; backup `app.db` sebelum smoke apa pun yang menyentuh attempt.
11. **`ScheduleItem` sudah ada untuk tiap node.** `load_domain_into_db` membuatnya saat
    memuat domain, dan `node_id` adalah primary key — di test, **update** barisnya
    (`session.get(...)`), jangan `session.add(ScheduleItem(...))` baru. Terbukti saat
    prototipe plan ini dijalankan: `UNIQUE constraint failed: scheduleitem.node_id`.

---

## 14. Setelah L5 (arah, bukan tugas sekarang)

Roadmap menyebut L5 sebagai syarat sebelum sistem boleh disebut **selesai**. Sesudah ia
hijau, yang tersisa tinggal dua, dan keduanya sudah tercatat sebagai utang — bukan ide baru:

- **Acceptance L4 yang belum tuntas:** satu node sungguhan lahir dari peta generate
  (tertahan `HTTP 429`, bukan gerbang). L5 justru membuat kekurangan ini terlihat sebagai
  `fastapi-produksi` 0% berlubang — jadi menutupnya sekarang punya efek yang bisa dilihat.
- **Sisa M7:** halaman meja audit + tombol pensiun + `destination` per domain. Itu alat
  **kurasi** (menjawab "node ini layak tidak?"), sementara L5 alat **kejujuran** (menjawab
  "sudah kamu buktikan belum?"). Keduanya sengaja tak digabung.

Yang **tidak** boleh menyusul: grafik tren, streak, atau lencana. Semuanya membuat angka
terasa enak tanpa menambah satu pun bukti reproduksi — dan itu definisi persis dari yang
lajur ini dibangun untuk melawan.
