# Rencana Uji Workflow End-to-End (manual, dikerjakan Bryant)

> **Tujuan:** membuktikan bahwa seluruh rantai yang sudah dibangun benar-benar bekerja
> **di tanganmu**, bukan cuma hijau di test: loop Forge (M3/M4) → lajur Library (L1–L3) →
> jembatan Library→Forge (L4) → penjaga metrik (L5).
>
> Sisi kode sudah diverifikasi (201 test backend + 62 test scripts hijau, ruff bersih).
> Yang **belum pernah** dibuktikan justru bagian yang cuma bisa kamu lakukan: memakainya.
> — **Dicatat:** 2026-09-07

---

## 0. Cara memakai dokumen ini

- Tiap uji punya bentuk yang sama: **Tujuan · Langkah · Harapan · Artinya kalau merah**.
- Centang di §12 sambil jalan. **Uji yang gagal lebih berharga daripada yang lolos** —
  catat apa adanya, jangan dirapikan.
- Total ±60–90 menit, **bisa dicicil**. Tiap uji berdiri sendiri, kecuali:
  **B butuh A**, dan **E butuh A**.
- Kalau ragu apakah sesuatu "salah" — catat saja. Perasaan "ini kok aneh" adalah data.

**Prioritas kalau waktumu sedikit:** A → B → C. Ketiganya (±25 menit) sudah membuktikan
inti produk: reproduksi dinilai eksekusi, dan angka Library hanya bergerak karenanya.

---

## 1. Prasyarat & pengamanan

### 1.1 Amankan dulu (2 menit)

```bash
# Cadangkan DB (semua sinyal belajarmu ada di sini)
cp backend/app.db backend/app.db.bak-uji-$(date +%Y%m%d-%H%M%S)

# Pastikan pekerjaan tersimpan — git adalah undo-mu saat menguji
git status --short
```

> Kalau L4/L5 belum di-commit, commit dulu. Uji ini menyentuh DB dan (di UJI C & G)
> berkas `library/`; tanpa commit, membedakan "perubahan hasil uji" dari "pekerjaan yang
> belum tersimpan" jadi sulit.

### 1.2 Cek lingkungan (1 menit)

| Perintah | Harapan |
|---|---|
| `node --version` | v24.x |
| `ls frontend/node_modules \| head -1` | ada isinya |
| `backend/.venv/Scripts/python.exe scripts/verify_library.py` | `library/ bersih` · exit 0 |
| `backend/.venv/Scripts/python.exe scripts/verify_library.py --candidates` | `kandidat belum tertempa: 1` (`cookie-param`) |

Kurikulum di DB saat ini: **19 node** (13 fastapi · 3 ml · 3 react), **0 attempt**.
Angka nol itu benar — kamu memang belum pernah mengerjakan apa pun di DB ini.

### 1.3 Catatan mesin ini

RAM ±3.4 GB. **Jangan** menjalankan `npm run build`, `next dev`, dan browser berat
sekaligus. Urutan aman: nyalakan backend → nyalakan `next dev` → buka satu tab browser.
Kalau layar putih/terasa berat: matikan `next dev`, pakai jalur `curl` yang disediakan
tiap uji (semua uji punya alternatif tanpa browser).

---

## 2. Menyalakan aplikasi

**Dua terminal.** Terminal 1 (backend):

```bash
cd backend
.venv/Scripts/python.exe -m uvicorn app.main:app --reload
```

Terminal 2 (frontend):

```bash
cd frontend
npm run dev
```

Cek sehat sebelum lanjut:

```bash
curl -s localhost:8000/health          # {"status":"ok"}
curl -s localhost:8000/stats | head -c 200
```

> **Catatan:** skill `run-learning-engine` ditulis untuk container Linux
> (`.venv/bin/python`, `google-chrome`, `driver.sh`). Di mesin Windows ini jalankan
> manual seperti di atas — path venv-nya `\.venv\Scripts\python.exe`.

---

## 3. UJI A — Loop Forge inti (WAJIB · ±20 menit)

**Tujuan.** Membuktikan rantai yang menjadi alasan produk ini ada: scaffold memudar
L3→L0, verifikasi dingin di **varian berbeda**, dan verdict datang dari **eksekusi kode**.

### Langkah
1. Buka `http://localhost:3000` → dashboard.
2. Di peta progres, buka node **`n002_get_json_route`** (`/node/n002_get_json_route`).
3. Jalani level berurutan:
   - **L3 · Contoh dikerjakan** — baca solusi beranotasi.
   - **L2 · Reproduksi dengan kerangka** — isi bagian `# TODO:`, jalankan.
   - **L1 · Hanya signature + spesifikasi** — tulis dari kontrak.
   - **L0 · Verifikasi (tanpa AI, timebox jalan)** — editor kosong, tulis dari nol.
4. Setelah L0 **PASS**, jawab **probe** yang muncul.

### Harapan

| # | Yang diperiksa | Harapan |
|---|---|---|
| A1 | Editor | Monaco muncul, **tak ada** saran AI/autocomplete cerdas (invariant §1.2) |
| A2 | L0 vs L3 | **Prompt/data uji L0 BERBEDA** dari L3 (transfer, bukan hafalan) |
| A3 | Timebox | Hanya muncul di L0, berjalan mundur dari 15:00 (`timebox_seconds: 900`) |
| A4 | Submit salah | Output test gagal ditampilkan apa adanya (bukan disembunyikan) |
| A5 | Submit benar | Verdict PASS datang dari hasil test, bukan dari komentar AI |
| A6 | Probe | Muncul **setelah** PASS; pilihan ganda deterministik |
| A7 | Status node | Berubah jadi **`acquired`** setelah PASS + probe |
| A8 | Dashboard | KPI `reproduce-without-AI` berubah dari `—` jadi angka; `jatuh tempo` mungkin 0 (interval FSRS berhari-hari) |

Alternatif tanpa browser (verifikasi angka saja):

```bash
curl -s localhost:8000/stats | python -m json.tool | head -20
```

### Artinya kalau merah
- **A2 merah** (L0 sama dengan L3) → node itu cuma punya 1 varian, atau `scaffold.py`
  salah memilih instance. Ini serius: kelulusan jadi hafalan, bukan transfer.
- **A5 merah** → jangan lanjut; seluruh kepercayaan sistem bersandar pada sinyal ini.
- **A7 merah** → cek `probes/answer` di Network tab; status hanya berubah lewat jalur itu.

---

## 4. UJI B — Penjaga metrik L5 bergerak (WAJIB · ±5 menit)

**Tujuan.** Ini pembuktian utama L5: angka Library **hanya** bergerak oleh eksekusi kode.
Kamu sudah menanam buktinya di UJI A; sekarang lihat apakah lajur Library mengakuinya.

### Langkah
1. **Sebelum** UJI A (atau pakai catatan awal): `/library` → `fastapi-dasar` **0/4 (0%)**.
2. **Sesudah** UJI A: refresh `/library`.

### Harapan

| # | Yang diperiksa | Harapan |
|---|---|---|
| B1 | `fastapi-dasar` | **1/4 · 25%**, bar terisi seperempat |
| B2 | Baris "GET route JSON dengan status 200" | label **direproduksi** (hijau) |
| B3 | Tiga baris lain | label **tertempa, belum dibuktikan** (kuning) |
| B4 | `fastapi-produksi` | **0/1**, satu baris **belum tertempa** (abu-abu) — lubang L4 yang belum ditutup |
| B5 | Dashboard | kartu **materi direproduksi** = `20%` (1/5 total materi) |
| B6 | Kolom "catatan" | menampilkan `outline`/`captured` sebagai teks netral — **bukan** bar/persentase |

Alternatif tanpa browser:

```bash
curl -s localhost:8000/library/progress | python -m json.tool | head -40
```

### Artinya kalau merah
- **B1 tak bergerak** → join `node_ids`→DB putus. Cek `node_ids` di
  `library/fastapi-dasar/01-routing-dasar/get-route-json.md` benar-benar `n002_get_json_route`.
- **B4 hilang** (course tak muncul) → materi tanpa node dikeluarkan dari penyebut; itu
  bug yang menghapus properti "berlubang" — inti L5.

---

## 5. UJI C — Anti-gaming: membaca tak boleh menggerakkan apa pun (WAJIB · ±3 menit)

**Tujuan.** Membuktikan sendiri bahwa "% dibaca" tak punya jalan masuk.

### Langkah
```bash
# 1) Catat angka sekarang
curl -s localhost:8000/library/progress | python -c "import json,sys; d=json.load(sys.stdin); print(d['reproduced'], d['total'], d['reproduced_pct'])"

# 2) Tandai SEMUA catatan sebagai sudah diisi (simulasi "aku sudah baca semuanya")
backend/.venv/Scripts/python.exe -c "
from pathlib import Path
n=0
for p in Path('library').glob('**/*.md'):
    t=p.read_text('utf-8')
    if 'status: outline' in t:
        p.write_text(t.replace('status: outline','status: captured'), encoding='utf-8'); n+=1
print('diubah:', n)"

# 3) Angka HARUS identik
curl -s localhost:8000/library/progress | python -c "import json,sys; d=json.load(sys.stdin); print(d['reproduced'], d['total'], d['reproduced_pct'])"

# 4) Kembalikan
git checkout library/
```

| # | Harapan |
|---|---|
| C1 | Angka langkah 1 dan 3 **persis sama** |
| C2 | Di `/library`, kolom catatan berubah jadi `captured`, tapi bar & persentase tidak |
| C3 | `git checkout library/` mengembalikan semuanya |

**Artinya kalau merah:** lajur Library sudah berubah jadi metrik konsumsi — hentikan
pemakaian sampai diperbaiki. Ini satu-satunya uji di dokumen ini yang berstatus
"berhenti kalau merah".

---

## 6. UJI D — Gerbang 403 materi just-in-time (±10 menit)

**Tujuan.** Materi hanya muncul **setelah** kegagalan nyata — penjaga terakhir terhadap
"content library" (§8) sejak approve manusia dicabut.

### Langkah & harapan

```bash
# D1: node yang belum pernah kamu gagalkan
curl -i -s localhost:8000/nodes/n004_query_param_default/explanation | head -3
```
→ **403** `"materi just-in-time baru terbuka setelah attempt yang gagal"`.

```bash
# D2: sekarang GAGALKAN sengaja node itu lewat UI (submit kode ngawur di level mana pun),
#     lalu ulangi perintah di atas
```
→ **404** `"node ini belum punya materi just-in-time"`.

> **404 di D2 itu BENAR, bukan bug.** Gerbangnya lolos (kamu sudah gagal), tapi memang
> belum ada satu pun node yang punya `explanation.md` — R3 belum pernah dipromosikan.

```bash
# D3 (opsional tapi berharga): picu R3 sekarang — sejak L3 ada snapshot sumber,
# job R3 seharusnya TIDAK lagi ditolak `NO_SNAPSHOT`.
curl -s -X POST localhost:8000/authoring/r3 -H "content-type: application/json" \
  -d '{"node_id":"n004_query_param_default"}'
# tunggu ±1-3 menit, lalu:
curl -s localhost:8000/authoring/jobs | python -m json.tool | head -30
```

| # | Yang diperiksa | Harapan |
|---|---|---|
| D1 | Sebelum gagal | `403` |
| D2 | Sesudah gagal | `404` (gerbang lolos, materi belum ada) |
| D3 | Job R3 | status `approved` (lolos gerbang kutipan verbatim + dipromosikan) **atau** `rejected` dengan alasan yang jelas. **Yang TIDAK boleh:** ditahan dengan `NO_SNAPSHOT` untuk sumber yang sudah punya `data/sources/<id>.md` |
| D4 | Sesudah D3 sukses | `GET .../explanation` balas `200` + `explanation.md` muncul di `data/domains/fastapi/nodes/n004_*/` |

**Artinya kalau merah:** D1 balas 200 → gerbang bocor, materi bisa dilahap sebelum
mencoba (langsung laporkan). D3 ditolak `NO_SNAPSHOT` → jembatan L3→R3 belum benar-benar
hidup.

---

## 7. UJI E — Review jatuh tempo (±10 menit · butuh UJI A)

**Tujuan.** Membuktikan FSRS menjadwalkan reproduksi ulang, dan review memakai
**instance berbeda**.

Interval pertama FSRS berskala hari, jadi untuk menguji hari ini majukan jatuh temponya
(**ini manipulasi khusus uji**, DB sudah kamu cadangkan di §1.1):

```bash
backend/.venv/Scripts/python.exe -c "
import sys; sys.path.insert(0,'backend')
from datetime import datetime, timedelta, timezone
from app.db import get_session
from app.models import ScheduleItem
g=get_session(); s=next(g)
it=s.get(ScheduleItem,'n002_get_json_route')
print('due lama:', it.due_at, '| status:', it.status)
it.due_at = datetime.now(timezone.utc) - timedelta(days=1)
s.add(it); s.commit(); print('due dimajukan ke kemarin')
g.close()"
```

| # | Yang diperiksa | Harapan |
|---|---|---|
| E1 | Dashboard | kartu **jatuh tempo** jadi ≥ 1; node muncul di daftar review |
| E2 | `/review` | tantangan muncul **tanpa** scaffold, timebox jalan |
| E3 | Varian | instance-nya **berbeda** dari yang kamu pakai di L0 (rotasi varian) |
| E4 | Lolos review | `review_count` naik, `due_at` mundur lebih jauh (interval membesar) |
| E5 | Gagal review | status jadi **`lapsed`**, dan di `/library` materinya tetap **direproduksi** + ditandai **meluruh** |

> E5 sekaligus menguji keputusan §7 2026-08-21: yang meluruh memorinya, bukan buktinya.
> Kalau ingin mengujinya, lakukan **setelah** E4, lalu pulihkan DB dari cadangan.

---

## 8. UJI F — Placement (±10 menit)

**Tujuan.** Menemukan lantai tanpa memaraton seluruh kurikulum.

### Langkah
`/placement` → mulai sesi → kerjakan yang disodorkan sampai sesi berhenti sendiri.

| # | Yang diperiksa | Harapan |
|---|---|---|
| F1 | Urutan | menurun linear (node sulit → mudah), **bukan** acak |
| F2 | Berhenti | di batas **fail→pass pertama**, maksimal **7 node** (`PLACEMENT_MAX_NODES`) |
| F3 | Node lantai | jadi **`acquired`** |
| F4 | Prasyarat transitifnya | **hanya** dibuka jadi `available` — bukan `acquired` |
| F5 | Gagal semua | sesi `exhausted`, **tak ada** status yang diberikan ke node mana pun |
| F6 | Dashboard | `placement_floor_node_id` terisi |

**Artinya kalau merah:** F4 memberi `acquired` ke prasyarat → sistem mengklaim penguasaan
yang tak pernah dieksekusi (menggores §1.2). Laporkan segera.

---

## 9. UJI G — Jembatan L4: melahirkan node dari peta Library (±15 menit)

**Tujuan.** Menutup acceptance L4 yang belum tuntas — belum ada node yang benar-benar
lahir dari peta generate (percobaan terakhir kena `HTTP 429`, kuota, bukan gerbang).

### Langkah
Cara termudah: panggil skill.

```
/forge-node
```
lalu pilih kandidat `cookie-param` saat ditanya. Atau manual:

```bash
curl -s -X POST localhost:8000/authoring/node -H "content-type: application/json" -d '{
  "library_file": "library/fastapi-produksi/01-parameter-request/cookie-param.md",
  "slug": "cookie-param",
  "domain_id": "fastapi",
  "concept": "Membaca cookie dari request lewat Cookie parameter",
  "source_ref_id": "fastapi_docs_cookie_params",
  "prereq_node_id": "n012_header_param"}'

# pantau (gerbang menjalankan test SUNGGUHAN 2x — sabar, jangan trigger ulang)
curl -s localhost:8000/authoring/jobs | python -m json.tool | head -40
```

| # | Yang diperiksa | Harapan |
|---|---|---|
| G1 | Balasan trigger | `202` + `job_id` |
| G2 | Selama job jalan | `git status data/` **tetap bersih** — tak ada yang masuk sebelum lolos gerbang |
| G3 | Job sukses | status `approved`; `summary.promotion` memuat `node.yaml` + 8 berkas varian + 1 probe |
| G4 | Folder baru | `data/domains/fastapi/nodes/n014_cookie_param/` berisi **2 varian** + **1 probe** |
| G5 | `edges.yaml` | bertambah satu blok `type: soft`, **komentar kurasi lama utuh** |
| G6 | Gerbang authoring | `backend/.venv/Scripts/python.exe scripts/verify_nodes.py fastapi` → **HIJAU** (±5 menit) |
| G7 | Tautan balik | `... verify_library.py --link "library/fastapi-produksi/01-parameter-request/cookie-param.md" --node n014_cookie_param` → exit 0, `status` materi **tak berubah** |
| G8 | `/library` | `fastapi-produksi` jadi `0/1` **tertempa belum dibuktikan** (kuning), bukan lagi lubang abu-abu |
| G9 | Node baru di UI | `/node/n014_cookie_param` tampil `available` (edge soft tak mengunci) |
| G10 | Job gagal | kalau `rejected`: alasannya **spesifik** (triad merah / probe ditolak). Kalau `failed` karena `429`: itu kuota CLI, **bukan** kegagalan gerbang — ulangi lain waktu |

**Artinya kalau merah:** G2 kotor → ada yang menulis ke `data/` sebelum gerbang; itu
pelanggaran paling serius di jalur ini. G5 kehilangan komentar → `edges.yaml` ditulis
ulang lewat dumper, bukan append.

---

## 10. UJI H — Kill switch integrasi (±3 menit)

**Tujuan.** Integrasi Claude Code adalah **akselerator, bukan fondasi** (PRD §10).

Matikan backend, nyalakan ulang dengan integrasi mati:

```bash
# Git Bash
cd backend
CLAUDE_INTEGRATION_ENABLED=0 .venv/Scripts/python.exe -m uvicorn app.main:app --reload
```

```powershell
# PowerShell (sintaks env var berbeda — bukan prefix)
cd backend
$env:CLAUDE_INTEGRATION_ENABLED = "0"
.venv\Scripts\python.exe -m uvicorn app.main:app --reload
# jangan lupa: Remove-Item Env:CLAUDE_INTEGRATION_ENABLED  setelah uji selesai
```

| # | Yang diperiksa | Harapan |
|---|---|---|
| H1 | `POST /authoring/node` | **503** dengan pesan yang menjelaskan |
| H2 | `GET /stats`, `/library/progress` | tetap `200` |
| H3 | UI: buka node, kerjakan, submit | **jalan penuh** — loop inti tak tersentuh |

---

## 11. UJI I — Skill lajur Library (opsional · ±20 menit)

Uji ini menyentuh berkas `library/`; jalankan saat working tree bersih agar diff-nya
mudah dibaca.

| # | Skill | Cara | Harapan |
|---|---|---|---|
| I1 | `/course-intake` | paste silabus course luar (mis. satu modul Dicoding) | folder stub kosong-terstruktur; **re-run tak menimpa** apa pun |
| I2 | `/note-refine` | tunjuk satu stub + paste catatan mentahmu | body rapi berisi **tulisanmu**; celah ditandai `> TODO:`, bukan ditambal prosa; `status` di-flip **script** |
| I3 | `/learn-intake` | beri satu tujuan belajar baru | peta bersitasi + kutipan verbatim; **tanpa blok kode**; snapshot sumber terunduh script |
| I4 | Sesudah I1–I3 | `verify_library.py` | hijau |
| I5 | Uji tolak | ubah satu kutipan di file `type: roadmap` satu huruf → `verify_library.py` | **exit 1**, menyebut kutipan tak ada di snapshot |

---

## 12. Rekap hasil

| Uji | Status | Catatan |
|---|---|---|
| A. Loop Forge inti (A1–A8) | [ ] lolos / [ ] merah | |
| B. Metrik L5 bergerak (B1–B6) | [ ] lolos / [ ] merah | |
| C. Anti-gaming (C1–C3) | [ ] lolos / [ ] merah | |
| D. Gerbang 403 + R3 (D1–D4) | [ ] lolos / [ ] merah | |
| E. Review & lapsed (E1–E5) | [ ] lolos / [ ] merah | |
| F. Placement (F1–F6) | [ ] lolos / [ ] merah | |
| G. Jembatan L4 (G1–G10) | [ ] lolos / [ ] merah | |
| H. Kill switch (H1–H3) | [ ] lolos / [ ] merah | |
| I. Skill Library (I1–I5) | [ ] lolos / [ ] merah | |

**Kesan UI (tulis bebas — belum pernah dilihat siapa pun selain kamu):**
apa yang terasa membingungkan · apa yang perlu diklik dua kali padahal harusnya sekali ·
di mana kamu berhenti sejenak karena tak tahu harus apa.

---

## 13. Kalau ada yang merah — kumpulkan ini

Supaya bisa langsung ditindaklanjuti tanpa menebak:

1. **Uji & nomor barisnya** (mis. "B1 merah").
2. **Terminal backend**: 20 baris terakhir.
3. **Untuk kegagalan job (D3/G)**: isi `artifacts/<role>/<stamp>/job.json` +
   `command.log` — di situ ada argv lengkap dan alasan gerbangnya.
4. **Untuk kegagalan UI**: screenshot + tab Network (status code endpoint yang gagal).
5. **Untuk kegagalan angka (B/C)**: keluaran `curl -s localhost:8000/library/progress`.

---

## 14. Mengembalikan keadaan semula

```bash
# DB (mis. sesudah UJI E yang memajukan due_at, atau kalau ingin mulai bersih)
cp backend/app.db.bak-uji-<stamp> backend/app.db

# Berkas library/ yang tersentuh uji
git checkout library/

# Node hasil UJI G (hanya kalau ingin membatalkannya)
rm -rf data/domains/fastapi/nodes/n014_cookie_param
git checkout data/domains/fastapi/edges.yaml
backend/.venv/Scripts/python.exe scripts/load_nodes.py     # muat ulang DB dari data/
```

> Attempt yang kamu hasilkan selama uji **tidak** perlu dihapus kalau kamu memang
> mengerjakannya sungguhan — itu sinyal belajar yang sah, dan justru yang membuat angka
> `/library` mulai bergerak.
