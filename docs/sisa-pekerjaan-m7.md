# Sisa pekerjaan M7 — apa yang belum, dan kenapa

> **Status:** catatan pekerjaan terbuka, bukan milestone baru. Ia melengkapi
> [`milestones/M7-machine-gates-and-curriculum-telemetry.md`](milestones/M7-machine-gates-and-curriculum-telemetry.md)
> dengan alasan di balik tiap butir yang sengaja ditinggalkan.
>
> Sumber kebenaran keputusan tetap [`../CLAUDE.md`](../CLAUDE.md) §7
> (entri **2026-08-31** dan **2026-09-01**).
> — **Dicatat:** 2026-09-01

Ringkas keadaan: gerbang mesin, telemetri, dan promosi otomatis **sudah jalan**
(151 test hijau; 39/39 instance lolos triad; 19/19 probe terbukti lewat eksekusi).
Yang belum ada di bawah ini, dibagi dua kelompok yang **sangat berbeda sifatnya**:

- **Kelompok A — menunggu keputusan/isian manusia.** Ini bukan hutang teknis. Ia
  memang tak boleh diotomasi, atau butuh keputusan yang bukan milik mesin.
- **Kelompok B — hutang teknis biasa.** Bisa dikerjakan kapan saja.

---

## Kelompok A — menunggu manusia (by design)

### A1. `destination` per domain

**Belum:** ketiga `data/domains/*/domain.yaml` belum punya field `destination`.
`GET /authoring/audit` sudah melaporkannya di `domains_without_destination`.

**Kenapa tidak diisi otomatis:** ini satu-satunya bagian M7 yang desainnya sendiri
menyatakan tak boleh diserahkan ke mesin. Telemetri bisa mengukur **daya beda dan
kesehatan** sebuah node; ia tak bisa mengukur apakah 40 node ini **kurikulum yang
benar untuk jadi apa**. Kalau 40 node trivia semuanya membedakan dengan rapi,
telemetri akan melaporkan semuanya sehat. Tak ada oracle untuk pertanyaan arah — di
sistem mana pun, termasuk Eero/Alter.

Mengisinya sendiri berarti agent menetapkan tujuan belajar Bryant, dan itu persis
kategori yang §1.4 dan entri 2026-08-31 pertahankan untuk manusia.

**Biaya:** menit, sekali per domain. Bukan per node.

### A2. Snapshot sumber `data/sources/<id>.md`

**Belum:** belum ada satu pun berkas snapshot.

**Kenapa tidak dibuat otomatis:** snapshot adalah **salinan verbatim** dokumentasi
otoritatif — itulah seluruh gunanya. Menulisnya dari ingatan model menghasilkan
teks yang *tampak* seperti sumber lalu dipakai untuk memverifikasi kutipan terhadap
dirinya sendiri. Itu bukan grounding; itu sirkularitas yang berpakaian grounding,
dan justru kegagalan yang paling mahal di peran ini (RISK-4).

**Akibat yang sudah ditangani:** job R3 tidak gagal karenanya. Sumber yang belum
di-snapshot **MENAHAN** promosi (job berhenti di `ready`, pesan errornya menyebut
path persis yang harus dibuat), sementara kutipan karangan **MENOLAK** artifact.
Pembedaan ini disengaja: "belum bisa diperiksa" bukan "terbukti salah", dan
menghukum keduanya sama hanya menyuruh model mengulang kerja yang sudah benar.

**Cara menutupnya:** salin teks halaman sumber ke `data/sources/<source_ref_id>.md`
(id-nya ada di `data/sources.yaml`). Cukup bagian yang relevan, bukan seluruh situs.
Begitu ada, materi R3 untuk sumber itu langsung mengalir otomatis.

### A3. Aturan "edge usulan AI hanya boleh `soft`" belum punya tempat ditegakkan

**Belum:** aturannya sudah diputuskan (CLAUDE.md §7 2026-09-01a) tapi belum ada kode
yang memaksakannya.

**Kenapa:** R1 (ekstraksi kandidat node/edge) masih manual/offline di v1 — tak ada
satu pun jalur kode yang mempromosikan edge buatan AI. Menulis penjaga untuk pipa
yang belum ada berarti kode yang tak pernah dijalankan, dan itu yang paling cepat
membusuk (preseden M6: grader `structural` ditunda dengan alasan sama).

**Kapan dikerjakan:** bersamaan dengan R1, bukan sebelumnya.

---

## Kelompok B — hutang teknis

### B1. Halaman audit di frontend

**Belum:** backend `GET /authoring/audit` sudah jalan (coverage + node bertanda +
edge belum terkukuhkan + domain tanpa `destination`). Halaman `/authoring` masih
menampilkan antrean approve gaya M5.

**Kenapa ditinggalkan:** M7 memindahkan peninjauan manusia dari **blokir** ke
**audit**, dan bagian yang menentukan apakah itu aman adalah **gerbangnya**, bukan
halamannya. Gerbang sudah terpasang dan teruji; UI-nya menunda kenyamanan, bukan
keamanan. Mengerjakannya lebih dulu akan menukar waktu untuk lapisan yang tak
menahan apa pun.

**Catatan bentuk saat dikerjakan:** ini **daftar bertanda**, bukan dashboard atau
graf. §8 menolak DAG explorer, dan telemetri yang tumbuh jadi visualisasi kurikulum
akan menyeret proyek ke gravitasi yang §1 lawan.

### B2. Tombol pensiun (retire node)

**Belum:** telemetri menandai node, tapi belum ada cara mencabutnya.

**Kenapa:** butuh satu keputusan desain yang belum diambil — **di mana keputusan
pensiun disimpan**. Tak boleh jadi kolom DB baru (skema sengaja domain-agnostic,
§9/M0, dan M7 menutup dengan "nol kolom DB baru"). Kandidat yang masuk akal:
`data/domains/<id>/retired.yaml` yang dihormati `node_loader` — ikut di-commit &
di-diff seperti kode, konsisten dengan cara `data/` menyimpan segalanya.

Menebak-nebak tempatnya sekarang berisiko menaruhnya di tempat yang salah, dan
memindahkannya belakangan lebih mahal daripada memutuskannya sekali.

**Catatan penting:** pensiun **selalu satu klik manusia** — tak ada pensiun otomatis
dari telemetri. Alasannya n=1: statistik per-node dari satu pelajar itu berisik, dan
pensiun otomatis akan mencabut node bagus di hari Bryant sedang buruk.

### B3. Repo belum `ruff format`-bersih (pre-existing)

**Belum:** 8 berkas di luar M7 akan berubah kalau `ruff format` dijalankan menyeluruh
(`app/db.py`, `app/routers/nodes.py`, `app/services/{attempt_service,node_loader,scaffold}.py`,
`tests/{test_claude_contracts,test_grader_unit_test}.py`, `scripts/load_nodes.py`).

**Kenapa dibiarkan:** sudah begitu sejak sebelum M7. CLAUDE.md §3 mewajibkan
`ruff check` (hijau), bukan `ruff format --check`. Memformatnya dalam commit M7 akan
mencampur churn tak berhubungan ke diff yang sedang di-review.

**Saran:** satu commit tersendiri, kapan pun, judul `chore: ruff format seluruh repo`.

---

## Yang sudah ditutup dan TIDAK akan dikerjakan

Dua langkah rencana M7 dibatalkan **dengan pengukuran**, bukan ditunda. Rinciannya di
CLAUDE.md §7 2026-09-01; disebut di sini supaya tak ada yang menghidupkannya kembali
sebagai "hutang":

- **Bukti edge statis sebagai gerbang pemblokir.** Diukur menandai 6–7 dari 14 edge
  hard dengan alasan yang salah semua. Sebabnya struktural: sidik jari harus dibangun
  dari token *jarang*, padahal konstruk node fondasi justru yang *paling sering*
  muncul — filternya membuang persis bukti yang dicari.
- **Deteksi tumpang-tindih varian.** Diuji: referensi `variant_a` `n001_paginate`
  LOLOS hidden test `variant_b`, dan kedua varian itu sah — untuk node fungsi murni,
  transfer memang diuji lewat DATA, bukan lewat kode yang berbeda.
