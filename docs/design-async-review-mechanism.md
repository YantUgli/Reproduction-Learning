# Rancangan mekanisme review ASYNC (Amandemen C)

> **Status:** rancangan, bukan keputusan teknis final. Amandemen C (§7 CLAUDE.md
> 2026-09-16) memerintahkan mekanisme ini **didokumentasikan lebih dulu, sebelum satu
> baris kode implementasi pun ditulis.** Dokumen ini menjawab lima pertanyaan desain
> berdasarkan kode yang ADA per 2026-09-18, memilih satu keputusan per pertanyaan,
> dan menandai batas yang diterima sadar. Ia belum menggantikan sebuah execution-plan.

## 0. Kenapa mekanisme ini perlu ada

Amandemen B (§7 CLAUDE.md 2026-09-16) mengizinkan AI **mengusulkan `hard` edge** sebagai
keputusan awal, bukan hanya `soft`. Tapi B ditulis **tidak aktif secara praktis** sampai
mekanisme C dibangun: sampai saat itu `_append_soft_edge` tetap satu-satunya jalur
penulisan edge dari AI, dan **selalu `soft`**. Asimetri yang jadi alasan seluruh
rancangan ini: **edge `hard` yang salah mengunci Bryant KELUAR** dari node yang siap ia
kerjakan (korosif, tak terlihat); edge `soft` yang salah cuma saran keliru. Karena itu
`hard` dari AI tak boleh langsung mendarat — ia butuh jendela veto manusia.

Yang butuh review async **hanya edge `hard`.** Node itu sendiri sudah lahir lewat gerbang
mesin dan langsung `available` (L4 KUNCI g) — itu invariant-safe dan tidak berubah di sini.

## 1. Apa yang kode LAKUKAN hari ini (fakta, bukan asumsi)

- **State job hidup di FILE**, `artifacts/<role>/<stamp>/job.json`, bukan tabel DB
  (`artifacts.py` docstring + `Job`/`save_job`/`read_job`). Alasan tercatat: artifact =
  sumber kebenaran, kill-switch bersih, loop inti tak punya ketergantungan skema.
  **`artifacts/` git-ignored & fana.**
- **`JobStatus`** = `pending → running → ready → {approved|rejected|failed}`
  (`artifacts.py:42`). `REVIEWABLE = (ready,)`. `promote()` menuntut `status == ready`.
- **Dua mode promosi** yang ADA (`config.CLAUDE_AUTO_PROMOTE`, default `True`):
  - `=1`: lolos gerbang → `ready` → **langsung** `review_queue.promote()` → `approved`,
    tanpa manusia (`jobs.execute_job:399-414`).
  - `=0`: berhenti di `ready`, menunggu klik manual `POST /authoring/jobs/{id}/approve`
    (`/authoring/queue`).
  - **Tak ada mode ketiga.** Keduanya mengasumsikan keputusan diambil *sekarang*
    (in-sesi atau otomatis), bukan "selesai lalu tidur 7 hari" — persis yang ditolak di
    entri Amandemen C ("memperluas `CLAUDE_AUTO_PROMOTE=0` apa adanya" ditolak).
- **Edge ditulis backend ke `edges.yaml`** lewat `_append_soft_edge` (append TEKS, bukan
  `yaml.dump`, supaya komentar kurasi tak hilang), di dalam promosi atomik
  `_promote_node_genesis`, **selalu `type: soft`** (`review_queue.py:304`).
- **`edges.yaml` git-committed & di-diff seperti kode.** `node_loader.load_edges`
  **hanya membaca `edges.yaml`** (`node_loader.py:181`) — file lain tak tersentuh loop.
- **Preseden file usulan sudah ada:** `data/domains/fastapi/edges.proposed.yaml`
  (edges A2 "difinalkan Isyah dengan menerima kandidat dari `edges.proposed.yaml` apa
  adanya" — komentar di `edges.yaml`).
- **Tak ada scheduler di aplikasi.** Yang ada: `BackgroundTasks` FastAPI (hidup hanya
  selama proses) dan `py-fsrs` (murni algoritma SR, bukan job runner). Tak ada
  APScheduler/celery/cron in-app.
- **`/authoring` = meja AUDIT** yang SUDAH merender edge findings
  (`AuditOut.edge_findings`, `authoring.py:333-372`) dan **sudah** merender kontrol
  `retire`/`set-destination` sebagai **kontrol pending tanpa endpoint** — repo nyaman
  menampilkan aksi read-only yang tindakannya di luar backend.
- **Pola "dua lajur, dua penulis":** backend menulis `data/` (termasuk edges via
  promosi), tapi tautan `node_ids` & isi `library/` ditulis **script** (`verify_library.py
  --link`), tak pernah backend/AI (L4 KUNCI 10/11).

---

## 2. Pertanyaan 1 — Di mana state "menunggu review" disimpan?

**Analisis.** Tiga kandidat rumah, masing-masing dengan preseden:
1. **`job.json` (extend `JobStatus` + field)** — dekat dengan pipeline. Tapi
   `artifacts/` **git-ignored & fana**: keputusan yang harus bertahan **7 hari kalender**
   dan bisa diveto "hari lain" tak boleh bergantung pada folder yang `artifacts.py`
   sendiri bilang boleh dihapus dengan file manager. Job juga sudah **selesai** begitu
   node-nya lahir; menahan job di status baru demi edge = mencampur dua siklus hidup.
2. **Tabel DB baru (`PendingEdge`)** — query enak. Tapi repo **berulang kali menolak**
   menyimpan state yang sumber kebenarannya di file ke DB (job state file-vs-DB ditolak
   2026-08-22; toleransi ML `data/`-vs-kolom ditolak M6). Edge tujuannya `edges.yaml`
   (git); menaruh state antaranya di DB = dua sumber yang bisa menyimpang.
3. **File YAML git-committed di `data/`, sejajar `edges.yaml`** — konsisten dengan
   "edges = YAML di-commit & di-diff", punya preseden langsung (`edges.proposed.yaml`),
   dan **tak terbaca `load_edges`** sehingga edge pending otomatis tak pernah mengunci
   Bryant selama menunggu.

**Keputusan:** **opsi 3 — file baru `data/domains/<domain>/edges.pending.yaml`**,
per-domain (mengikuti lokasi `edges.yaml`). Tiap entri:

```yaml
edges:
  - from: n004_query_param_default
    to: n014_cookie_param
    type: hard              # yang DIUSULKAN; belum berlaku sampai promosi
    source_ref_id: fastapi_docs_cookie_params
    library_file: library/fastapi-produksi/01-parameter-request/cookie-param.md
    job_id: r4-20260916T104348-eb79be   # jejak ke artifact asal
    queued_at: 2026-09-18T10:43:00Z      # jam mulai klok 7 hari
    note: "Usul L4 (AI) — menunggu veto Isyah s/d queued_at + 7 hari."
    # diisi hanya bila diveto:
    # vetoed_at: ...
    # veto_reason: ...
```

**Alasan (kode):** (a) `edges.pending.yaml` **git-committed** = veto bisa berupa `git`
diff/revert, dan keputusan bertahan lintas hari — hal yang `artifacts/` fana tak bisa
jamin; (b) `load_edges` cuma baca `edges.yaml`, jadi **selama menunggu, edge itu tak ada
untuk loop** → node tetap `available`, tak pernah terkunci — persis rasa aman yang
Amandemen B minta; (c) satu keadaan = satu file (pending vs live = dua file, dua makna),
menghindari kolom DB yang ditolak berulang; (d) `queued_at` di file = klok 7 hari punya
satu sumber, bukan diturunkan dari mtime (rapuh) atau `job.created_at` (fana).

---

## 3. Pertanyaan 2 — Bagaimana saya melihat antrian review?

**Analisis.** Kandidat: (a) halaman UI baru; (b) command Claude Code; (c) extend yang
sudah ada; (d) baca `edges.pending.yaml` langsung di git/Obsidian. Command Claude Code
salah arah: veto adalah tindakan **manusia yang menilai kualitas kurikulum**, bukan kerja
agent (dan `queue/page.tsx` sendiri menyebut dirinya "meja kerja Isyah"). Halaman baru
mubazir: `/authoring` **sudah** meja audit yang merender edge findings + kontrol pending,
dan veto edge adalah persis "peninjauan manusia yang pindah ke belakang" yang jadi alasan
halaman itu ada.

**Keputusan:** **extend meja audit `/authoring`** — tambah bagian "Edge `hard` menunggu
veto" yang datanya dari **`GET /authoring/audit` yang diperluas** (field baru
`pending_edges`), bukan endpoint/halaman baru. Tiap baris menampilkan
`from → to`, `library_file`, dan **hitung mundur** (`matures_at = queued_at + 7d`, plus
label `menunggu` / `matang, siap promosi` / `diveto`). File `edges.pending.yaml` tetap
jadi jalur baca alternatif (git-committed, bisa dibuka di Obsidian) — konsisten dengan
"Isyah bisa membuka & grep job dengan file manager biasa".

**Alasan (kode):** `AuditOut` sudah membawa `edge_findings`/`AuditEdge` dan halaman sudah
merender kontrol read-only tanpa endpoint (`retire`/`set-destination`) — menambah
`pending_edges` mengikuti pola yang persis sudah ada, bukan permukaan UI baru yang harus
dirawat sendiri. Backend hanya **MEMBACA** `edges.pending.yaml` di sini (sama seperti
audit membaca telemetri) — tak ada penulisan di jalur baca.

---

## 4. Pertanyaan 3 — Bagaimana saya melakukan veto?

**Analisis.** Kandidat: (a) endpoint baru `POST …/veto`; (b) edit file langsung;
(c) dari UI. Endpoint mirip `reject_job` memang ergonomis dan backend **boleh** menulis
`data/` edges (ia sudah menulis `edges.yaml` di promosi). TAPI dua hal menariknya ke
jalur script: (1) promosi-setelah-7-hari **wajib** lewat script (lihat §5 — tak ada
scheduler), dan begitu satu tool sudah memiliki siklus hidup `edges.pending.yaml`,
memecah veto ke endpoint = dua penulis untuk satu file; (2) preseda terkuat repo untuk
tulisan kurasi yang menentukan urutan adalah **script, bukan backend/AI**
(`verify_library.py --link`, `fetch_source.py`).

**Keputusan:** **veto lewat script** yang memiliki file pending —
`scripts/promote_pending_edges.py --veto <edge_id> [--reason "..."]` — yang **MENANDAI**
entri dengan `vetoed_at` + `veto_reason`. Usulan **tetap ada** di `edges.pending.yaml`,
ditandai ditolak — **tak pernah dihapus**, supaya jejak keputusan jelas dan terbaca di
git-diff maupun meja audit. **Edit `edges.pending.yaml` langsung** tetap sah sebagai
break-glass (git = otoritas akhir), dan cara menandainya sama (isi `vetoed_at`, bukan
hapus baris). **Bukan** endpoint backend. UI audit (§3) menampilkan antrian **read-only**
+ mencetak perintah siap-tempel (preseden L4 §15 mencetak perintah copy-paste;
`--candidates` = laporan, bukan gerbang).

**Alasan (kode):** satu penulis untuk lajur pending (script), cermin `verify_library.py`
yang memiliki lajur `library↔node`; veto rare (hanya saat Isyah tak setuju) sehingga biaya
ergonomi kecil; `git` memberi audit-trail & undo tanpa menulis mekanisme sendiri; dan
menampilkan aksi sebagai kontrol yang tindakannya di luar backend **persis** pola
`retire`/`set-destination` yang sudah dirender di meja audit.

**Batas diterima sadar:** ini menaruh dua gerbang (veto + promosi, lihat §5) di script
yang sama; bila kelak veto-dari-UI diinginkan, tombolnya harus memanggil logika script
yang sama, bukan menduplikasi aturannya di backend.

---

## 5. Pertanyaan 4 — Apa yang terjadi bila tak ada veto dalam 7 hari?

**Analisis.** Amandemen B: "bila TIDAK diveto dalam 7 hari kalender sejak masuk antrian,
dianggap disetujui dan **boleh dipromosikan** jadi `hard` sungguhan." "Boleh dipromosikan"
= tak butuh approval lagi, **bukan** "otomatis oleh timer". Dan memang tak ada timer:
aplikasi tak punya scheduler (fakta §1). "Tetap menunggu selamanya" salah — itu
mengembalikan model opt-in yang Amandemen B tolak sebagai tak skalabel.

**Keputusan:** **auto-promote setelah matang, dieksekusi oleh script yang Isyah
jalankan MANUAL saat ia mau — bukan cron OS, bukan `/schedule` harness, bukan timer
in-app.** `scripts/promote_pending_edges.py` mempromosikan **hanya** entri yang
`now ≥ queued_at + 7d` **dan** tak ber-`vetoed_at`: ia meng-**append** entri itu ke
`edges.yaml` sebagai `type: hard` (jalur append-teks + reparse yang sama dengan
`_append_soft_edge`, agar komentar kurasi selamat), lalu menghapusnya dari
`edges.pending.yaml`. Meja audit `/authoring` menampilkan **pengingat "X edge siap
promosi"** (matang + tak diveto) supaya Isyah tahu kapan ada yang menunggu dijalankan —
tapi **tak satu pun tulisan terjadi sampai Isyah menjalankan script itu sendiri.**

**Alasan (kode):** aplikasi memang tak punya scheduler (fakta §1), dan menambah satu =
dependency besar yang repo tolak berulang (Alembic, Docker ditolak demi minimal-deps).
Menjalankan promosi manual justru konsisten dengan seluruh kurasi lain yang bergerak
atas perintah Isyah (`load_nodes.py`, `fetch_source.py`, `verify_library.py`) dan dengan
sifat local-first single-user. Meja audit hanya **MEMBACA** `edges.pending.yaml` untuk
menghitung pengingat — tak ada tulisan di jalur baca. Selama belum dipromosikan, edge
matang hanya "eligible" dan tetap **tak terbaca loop** (masih di `edges.pending.yaml`)
→ node tetap `available`, tak ada bahaya.

**Batas diterima sadar:** bila script tak pernah dijalankan, edge matang tak pernah jadi
`hard` — konsekuensinya **aman** (tetap soft/absen), hanya menunda manfaat urutan. Ini
sengaja: sistem yang diam gagal ke sisi "tak mengunci Bryant", bukan sisi "mengunci tanpa
ditinjau".

---

## 6. Pertanyaan 5 — Menempel di `/authoring/jobs` atau jalur terpisah?

**Analisis.** `/authoring/jobs` = job artifact (`list_jobs` membaca `artifacts/*/job.json`).
Sebuah pending-hard-edge **bukan** job: (a) hidupnya **melampaui** job — node lahir & job
`approved` seketika, sedang edge menunggu 7 hari; (b) rumahnya git-committed & durable,
lawan `artifacts/` fana; (c) job = produksi artifact per-peran, edge = kurasi urutan
kurikulum. Menyatukan state-nya ke `job.json` mengikat keputusan 7-hari ke artifact yang
`artifacts.py` bilang boleh dihapus — kerapuhan yang persis diperingatkan modul itu.

**Keputusan:** **jalur STATE terpisah** (`edges.pending.yaml` + script pemiliknya),
tapi **rumah UI yang sama** (`/authoring` meja audit) dan konvensi endpoint yang sama
(perluas `GET /authoring/audit`). Job tetap mengurus kelahiran node & promosi node;
edge pending adalah objek terpisah yang lebih panjang umur.

**Alasan (kode):** memisah state menjaga dua siklus hidup (fana vs durable) tetap bersih —
matikan integrasi/hapus `artifacts/`, antrian edge tetap utuh di git; sekaligus tak
membuat halaman baru karena meja audit memang tempat "mata Isyah di level kurikulum".

---

## 7. Bentuk konkret yang direkomendasikan (ringkasan)

| Aspek | Keputusan | Preseden kode |
|---|---|---|
| State | `data/domains/<domain>/edges.pending.yaml` (git-committed) | `edges.yaml`, `edges.proposed.yaml` |
| Klok 7 hari | field `queued_at` di entri; `matures_at = +7d` | — (baru, tapi satu sumber) |
| Lihat antrian | perluas `GET /authoring/audit` → `pending_edges`; render di `/authoring` | `AuditOut.edge_findings` |
| Veto | `--veto <id>` **menandai** `vetoed_at`/`veto_reason` (tak menghapus); UI read-only | `verify_library.py --link`, `reject()` |
| Timeout 7 hari | script promosi dijalankan **MANUAL oleh Isyah**: matang + tak diveto → append `hard` ke `edges.yaml`, hapus dari pending; meja audit tampilkan "X siap promosi" | `_append_soft_edge` (append teks + reparse) |
| Jalur | state terpisah dari `/authoring/jobs`; UI menyatu di `/authoring` | `artifacts.py` (fana vs durable) |

**Yang TIDAK berubah (invariant utuh):** node tetap lahir lewat gerbang mesin & langsung
`available`; verdict mastery tetap eksekusi kode (§1.2); AI tak pernah menulis `hard` ke
`edges.yaml` langsung; selama menunggu, edge pending tak terbaca loop sehingga tak pernah
mengunci Bryant. Isyah tetap **satu-satunya** yang bisa veto.

## 8. Keputusan terkunci & satu item untuk execution-plan

**Sudah dikunci (2026-09-18):**

1. **`edge_id` stabil = `<from_id>__<to_id>`.** Diverifikasi atas kurikulum nyata: dari
   **23 edge** di 3 domain (`edges.yaml`) + **14** di `edges.proposed.yaml`, **0 pasangan
   `from→to` duplikat** — satu pasangan node punya paling banyak satu edge, dan `from`/`to`
   sudah unik lintas domain (prefix `n`/`m`/`r`). Jadi pasangan itu identitas yang cukup;
   tak perlu hash atau timestamp di dalam id.
2. **Veto = TANDAI, bukan hapus.** `--veto` mengisi `vetoed_at` + `veto_reason`; entri
   **tetap ada** di `edges.pending.yaml`, ditandai ditolak. Jejak keputusan jelas dan
   terbaca di git-diff maupun meja audit, bukan lenyap.
3. **Script promosi dijalankan MANUAL oleh Isyah.** Bukan cron OS, bukan `/schedule`
   harness, bukan timer in-app (lihat §5). Meja audit hanya mengingatkan "X siap promosi".

**Masih terbuka (dirinci di execution-plan, bukan di sini):**

- **Percabangan `_promote_node_genesis`.** Saat Amandemen B aktif, jalur `prereq_node_id`
  harus bercabang: usul `hard` → tulis ke `edges.pending.yaml` (bukan `_append_soft_edge`
  ke `edges.yaml`); usul `soft` → tetap seperti sekarang. Detail cabang ini milik
  execution-plan.
