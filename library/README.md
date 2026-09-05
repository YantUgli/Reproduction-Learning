# `library/` — Lajur Library (Knowledge Management)

> **Status:** format beku sejak L0 (2026-09-04). Sumber kebenaran keputusan =
> [`../CLAUDE.md`](../CLAUDE.md) §7 entri 2026-09-04 + §1 invariant. Roadmap lajur =
> [`../docs/roadmap-library-lane.md`](../docs/roadmap-library-lane.md).
> Kalau ada konflik, **invariant menang**.

Folder ini adalah lajur **Library**: tempat menangkap & menyusun materi yang
*nyaman dikonsumsi*, mendampingi lajur **Forge** (`data/` + loop reproduksi) yang
*membuktikan*. Dibuka di **Obsidian** untuk graf; di-commit ke git & di-diff seperti
`data/`.

---

## Batas keras — apa yang boleh & TIDAK boleh mendarat di sini

Ini garis yang menjaga §8 ("content library/bab materi panjang" ditolak) tetap
berlaku untuk yang berbahaya. Lihat CLAUDE.md §7 2026-09-04.

**BOLEH di `library/`:**
- Catatan & transkripsi yang **ditulis Bryant sendiri** (`type: note|transcription`).
- Kerangka/indeks course & modul (`type: outline`).
- Roadmap belajar (`type: roadmap`).
- **Sitasi terkurasi** ke sumber otoritatif — `id` yang ADA di [`../data/sources.yaml`](../data/sources.yaml).
- `node_ids` — link ke node Forge yang dipetakan materi ini.

**TIDAK boleh di `library/`:**
- **Prosa penjelasan yang disintesis AI.** Itu hidup di `artifacts/` (git-ignored)
  dan sampai ke Bryant **hanya lewat gerbang 403** — muncul sesudah attempt gagal.
  Tanpa manusia yang membaca materi generate lebih dulu (§7 2026-08-31), 403 adalah
  satu-satunya penjaga tersisa; jangan bypass lewat pintu `library/`.

**Dua penjaga:**
1. **Grounding** — yang generate di sini cuma peta + sitasi, bukan sintesis. "Baca
   senyaman Dicoding" = baca **sumber asli** yang ditunjuk peta + catatanmu sendiri.
2. **"% direproduksi, bukan % dibaca"** — status reproduksi TIDAK ditulis di sini;
   dashboard (L5) menghitungnya dengan join `node_ids` → DB Forge. Sebuah course
   tampil *berlubang* sampai node-nya tertempa & terbukti tanpa AI.

---

## Bentuk folder

```
library/
  <course-slug>/
    _index.md                 # type: outline — silabus + daftar modul
    01-<module-slug>/
      _index.md               # type: outline — daftar materi modul
      <material-slug>.md      # type: note | transcription
    02-<module-slug>/
      ...
```

- Prefix modul `NN-` (dua digit) untuk urutan yang stabil saat di-diff & di-graph.
- `_index.md` tiap level = simpul yang menautkan anaknya (jadi graf Obsidian terhubung).
- Tautan antar-materi pakai `[[wikilink]]` (Obsidian merender graf dari ini).
- Node Forge **tidak** ikut ke graf (mereka YAML di `data/`); tautannya lewat
  `node_ids` di frontmatter, dipakai dashboard — bukan graf.

---

## Frontmatter (wajib di tiap `.md`)

```yaml
---
title: "GET route JSON dengan status 200"
course: fastapi-dasar          # slug folder course induk
module: 01-routing-dasar       # nama folder modul induk ("" untuk _index course)
type: note                     # note | transcription | outline | roadmap
source_refs: [fastapi_docs_first_steps]   # id di data/sources.yaml — WAJIB ada di sana
node_ids: [n002_get_json_route]           # node Forge yang dipetakan (boleh kosong)
status: captured               # outline (kerangka kosong) | captured (sudah berisi)
created: 2026-09-04
---
```

**Aturan field:**
- `source_refs` — tiap id **wajib ADA** di `data/sources.yaml` (satu namespace sitasi
  dengan Forge; jangan bikin registry sitasi kedua). Boleh `[]` untuk catatan mentah
  yang belum dikaitkan.
- `node_ids` — id node Forge nyata (folder di `data/domains/<domain>/nodes/`). Ini
  **satu-satunya** jembatan Library→Forge yang dibaca dashboard. Boleh `[]`.
- `status` — **status catatan, BUKAN reproduksi.** `outline` = kerangka kosong,
  `captured` = sudah ada isinya. Status reproduksi (`acquired/mastered/...`) hanya
  hidup di DB Forge dan datang dari eksekusi kode (§1.2). Jangan pernah menulis
  `forged`/`mastered` di sini.
- `type` — `note` (tulisanmu), `transcription` (transkrip course luar), `outline`
  (kerangka `_index`), `roadmap` (peta belajar dari `learn-intake`, L3).

---

## Aturan tambahan untuk `type: roadmap` (L3 · ditegakkan mesin)

File `roadmap` adalah satu-satunya tempat teks hasil riset AI mendarat di `library/`,
jadi ia dijaga `scripts/verify_library.py` dengan aturan yang **tidak** berlaku untuk
file `note`/`transcription`/`outline`:

| Aturan | Kenapa |
|---|---|
| **Dilarang blok kode** (code fence) | fence di peta adalah sinyal paling jujur bahwa ia berubah jadi materi (§8) |
| `source_refs` **wajib non-kosong** | peta tanpa sitasi = peta tanpa gigi |
| tiap `source_ref` wajib punya `data/sources/<id>.md` | tanpa snapshot, kutipan tak bisa dicocokkan dengan apa pun |
| tiap kutipan `> "…"` wajib **verbatim ada** di snapshot | inti gerbang L3 — mesin yang sama dengan gate R3 (`app/services/grounding.py`) |
| kutipan ≥ 25 karakter (`MIN_QUOTE_CHARS`) | potongan sependek itu cocok secara kebetulan |
| prosa non-kutipan ≤ 3000 karakter | peta, bukan bab (preseden `EXPLANATION_MAX_CHARS`) |

**Bentuk baris kutipan `> "…"` itu KONTRAK, bukan gaya** — validator mengenali kutipan
justru dari bentuk ini. Menulisnya dengan bentuk lain membuatnya lolos **tanpa**
diperiksa: persis kebalikan dari yang kita mau.

**Kutipan hanya hidup di file `roadmap`.** Sitasi di file `note` TIDAK diverifikasi
(itu tulisan Bryant, bukan klaim generate) — jadi jangan pernah menaruh sitasi generate
di stub materi.

**Snapshot tak pernah diketik tangan.** `data/sources/<id>.md` hanya lahir dari
`python scripts/fetch_source.py --id <id>` (unduhan, `provenance: fetch`) atau berkas
yang Bryant sediakan (`--from-file`, `provenance: manual`). Kalau isinya boleh dikarang,
pemeriksaan "kutipan ⊆ snapshot" jadi melingkar.

---

## Template siap-salin

**`_index.md` course:**
```markdown
---
title: "<Nama Course>"
course: <course-slug>
module: ""
type: outline
source_refs: []
node_ids: []
status: outline
created: <YYYY-MM-DD>
---

# <Nama Course>

Sumber: <link/nama course luar, atau "generate roadmap (L3)">

## Modul
- [[01-<slug>/_index|01 · <Nama Modul>]]
```

**Materi (`<slug>.md`):**
```markdown
---
title: "<Judul materi>"
course: <course-slug>
module: <NN-slug>
type: note
source_refs: [<id di sources.yaml>]
node_ids: [<id node Forge, bila sudah ditempa>]
status: captured
created: <YYYY-MM-DD>
---

# <Judul materi>

<catatan/transkripsi Bryant — konsep, bukan solusi yang di-Forge>

**Sumber:** <sitasi manusiawi>
**Tempa di Forge:** [[../../<link ke materi terkait>]] · node: `<node_id>`
```

---

## Contoh

Lihat [`fastapi-dasar/`](fastapi-dasar/_index.md) — course contoh yang ditulis tangan
di L0 sebagai acuan bentuk (2 modul, catatan bersitasi, `node_ids` menunjuk node
FastAPI nyata).
