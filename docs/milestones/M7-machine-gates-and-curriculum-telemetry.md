# M7 — Gerbang Mesin & Telemetri Kurikulum (autonomi authoring)

> Peta PRD: §10 (peran R1–R4) · Dependency: M5 + M6 · Estimasi: variabel

## Tujuan

Mencabut **approve manusia sebagai gerbang blokir** tanpa membiarkan kurikulum
berjalan tanpa pemeriksa. Setelah M7: artifact Claude Code yang lolos **gerbang
mesin** dipromosikan otomatis ke `data/`/DB, dan Bryant bisa belajar serta mendapat
materi **tanpa Isyah di jalur**. Peninjauan manusia tetap ada, tapi pindah ke
belakang — audit, bukan antrean.

## Konteks & alasan

Keputusan §7 CLAUDE.md **2026-08-31** (baca dulu; milestone ini adalah pelaksanaannya).
Intinya: peran Isyah di sistem ini **tak pernah** gerbang *mastery* — verdict selalu
eksekusi kode (§1.2) — melainkan gerbang **kualitas konten**. Karena itu §1.2 dan §1.3
tidak tersentuh di M7; yang dilonggarkan hanya §1.4 dan gate approve M5.

Asimetri yang menopangnya: **node buruk memakan waktu Bryant** (terlihat, terbatas,
bisa dicabut retroaktif); **verdict mastery buruk menanam keyakinan palsu** (tak
terlihat, korosif). Hanya kategori pertama yang diotomasi.

**Urutan milestone ini tidak boleh dibalik.** Bagian A (gerbang) wajib selesai sebelum
Bagian C (pencabutan approve). Kalau approve dicabut lebih dulu, ada jendela waktu di
mana kurikulum berjalan tanpa pemeriksa mana pun — persis keadaan yang M7 ada untuk
mencegahnya.

## Prerequisite

- **M5 selesai** — pipeline artifact, `contracts.py`, `review_queue`, `/authoring`.
- **M6 selesai** — gerbang harus bekerja lintas 3 domain. Ini bukan formalitas: gate
  R4 hari ini masih meng-hardcode `.py` (lihat Langkah 1), jadi tanpa domain
  kedua/ketiga kebocorannya tak akan terlihat.

## File / komponen yang dibuat

```
backend/app/claude/jobs.py                 # _gate_r4: dua-pemeriksaan -> TRIAD, dan agnostik ekstensi
backend/app/services/node_schema.py        # ProbeSchema + field snippet/expression
backend/app/services/probe_verifier.py     # (b) jalankan snippet probe lewat Executor
backend/app/services/grounding.py          # (c) kutipan verbatim vs snapshot sumber
backend/app/services/edge_evidence.py      # (d) bukti konstruk + validasi prediktif
backend/app/services/overlap.py            # (e) deteksi tumpang-tindih node
backend/app/services/telemetry.py          # sinyal kualitas per node dari Attempt/ScheduleItem
backend/app/routers/authoring.py           # /authoring: antrean approve -> meja audit + pensiun
data/sources/<source_ref_id>.md            # snapshot teks sumber otoritatif
scripts/verify_nodes.py                    # ikut menegakkan triad + probe + grounding
backend/tests/
  test_gate_triad.py  test_probe_verifier.py  test_grounding.py
  test_edge_evidence.py  test_telemetry.py
```

## Langkah implementasi (berurutan)

### Bagian A — gerbang mesin (wajib selesai sebelum Bagian C)

1. **Triad eksekusi + hapus hardcode ekstensi.** `_gate_r4` di `claude/jobs.py`
   sekarang punya dua pemeriksaan (referensi HIJAU, starter MERAH) dan membaca
   `reference_solution.py`/`starter_code.py` secara literal — artinya gerbang R4
   diam-diam **hanya bekerja untuk domain Python**. Perbaiki dua-duanya sekaligus:
   pakai `graders/files.py` (`find_instance_file`, seperti `verify_nodes.py`) agar
   `.jsx` ikut tergerbang, dan tambahkan pemeriksaan ketiga: **berkas solusi kosong
   wajib MERAH**. Starter merah itu lemah — starter yang cuma `pass` lolos pemeriksaan
   lama sebagai "tantangan sah".
2. **Probe terverifikasi eksekusi.** Hari ini `probe_*.yaml` murni prosa
   (`n013_probe_01` mendeskripsikan `page=3, size=10` dan mengklaim `correct_answer:
   '20'`) — `node_schema.py` hanya memastikan `correct_answer` **ada di dalam
   `options`**, tak pernah bahwa ia **benar**. Tambahkan field opsional `snippet` +
   `expression` di `ProbeSchema`; `probe_verifier.py` menjalankannya lewat `Executor`
   domain yang sama dan menuntut: `correct_answer` sama dengan output nyata, **dan
   setiap distractor berbeda** dari output nyata. Probe tanpa snippet dilewati **dengan
   peringatan** sampai migrasi (Langkah 6) selesai.
3. **Grounding verbatim.** `sources.yaml` hari ini hanya `citation` + `url_or_locator`,
   jadi mesin cuma bisa memastikan ID sumber **ada** — persis alasan M5 dulu mewajibkan
   Isyah. Snapshot teks sumber ke `data/sources/<id>.md` (di-commit, bisa di-diff), lalu
   `grounding.py` menuntut tiap klaim R3 membawa kutipan yang **cocok sebagai substring**
   dari snapshot. Normalisasi whitespace; jangan normalisasi isi.
4. **Bukti edge, bukan asersi.** `edge_evidence.py`, dua pemeriksaan yang saling
   melengkapi: **(i) statis** — konstruk yang diperkenalkan node hulu harus benar-benar
   terpakai di `reference_solution` node hilir; **(ii) prediktif** — dari data `Attempt`,
   kegagalan di hulu harus berkorelasi dengan kegagalan di hilir. Yang statis jalan sejak
   edge diusulkan; yang prediktif baru berbunyi setelah ada data, jadi ia **menandai**
   edge tak terdukung, tidak memblokirnya.
5. **Deteksi tumpang-tindih.** `overlap.py`: `reference_solution` node yang sudah ada
   tak boleh lolos hidden test node baru. Kalau lolos, node barunya duplikat — tolak.

### Bagian B — telemetri kurikulum

6. **Migrasi 19 node existing** agar punya `snippet`/`expression` di probe-nya, lalu
   naikkan field itu dari opsional jadi **wajib**. Urutannya penting: menjadikannya
   wajib lebih dulu akan membuat seluruh kurikulum yang ada gagal dimuat.
7. **`services/telemetry.py`** — sinyal kualitas per node, seluruhnya dari data yang
   **sudah** tersimpan (`Attempt`, `ScheduleItem`); tidak ada kolom baru:

   | Sinyal | Sumber | Menandai node macam apa |
   |---|---|---|
   | Lolos 100% pada percobaan pertama, tak pernah gagal | `Attempt.result` | **trivia** — tak membedakan apa pun |
   | Tak pernah lolos | `Attempt.result` | rusak / salah scope / prasyarat bolong |
   | Median `duration_seconds` jauh di luar `estimated_minutes` | `Attempt` | salah kalibrasi atau menggabung lebih dari satu konsep |
   | Lapse rate tinggi | transisi `ScheduleItem.status` | scope terlalu lebar / dihafal, bukan dipahami |
   | Probe selalu benar atau selalu salah | `Attempt.probe_result` | probe mati atau probe menyesatkan |

   Ambang **longgar**, dengan jumlah attempt minimum sebelum sebuah sinyal berbunyi
   (lihat Keputusan: n=1).
8. **`/authoring` berubah fungsi** dari antrean approve jadi **meja audit**: daftar node
   & edge tertandai + alasan + angkanya + **tombol pensiun** (satu klik manusia).

### Bagian C — pencabutan (hanya setelah A hijau)

9. **Promosi otomatis.** `review_queue.approve` dipanggil oleh pipeline saat seluruh
   gerbang Bagian A lolos, bukan oleh klik manusia. `POST /jobs/{id}/approve` tetap ada
   untuk kasus manual. `reject` tetap ada. Kill switch `CLAUDE_INTEGRATION_ENABLED` tak
   berubah.
10. **`destination` per domain.** Tambahkan ke `domain.yaml` — ditetapkan manusia
    **sekali per domain**, bukan per node. Ini sisa tanggung jawab manusia yang tak bisa
    dilepas (lihat Keputusan).

## Keputusan teknis penting

- **Gerbang dulu, cabut belakangan.** Bagian C tanpa Bagian A = kurikulum tanpa
  pemeriksa. Ini urutan, bukan preferensi.
- **Telemetri MENANDAI, tidak memensiunkan.** n=1: statistik per-node dari satu pelajar
  itu berisik — Bryant gagal sebuah node bisa berarti node-nya buruk, bisa juga berarti
  dia sedang tidak fokus. Pencabutan selalu satu klik manusia.
- **Relevansi terhadap tujuan tak punya oracle** — di sistem mana pun, termasuk
  Eero/Alter. Ia ditetapkan manusia sekali per domain (`destination`). Jangan mencoba
  mengotomasi ini; yang bisa dilakukan telemetri adalah daya beda & kesehatan node,
  bukan arah kurikulum.
- **Kekhususan gerbang hidup di `data/`, bukan kolom DB** — `snippet` di `probe_*.yaml`,
  snapshot di `data/sources/`. Preseden: toleransi ML (`expected.json`) di M6, yang
  sengaja tak jadi kolom `rtol`. **Nol kolom DB baru di M7.**
- **Gerbang memakai `Executor`/`Grader` yang sama** dengan yang menilai submisi Bryant.
  Preseden M6: `verify_nodes.py` yang punya salinan aturannya sendiri adalah bug.

## Hal yang harus diperhatikan

- **19 node existing** (13 FastAPI, 3 React, 3 ML) punya probe prosa tanpa snippet.
  Langkah 6 harus selesai sebelum field itu jadi wajib — kalau dibalik, seluruh
  kurikulum gagal dimuat.
- **Jangan biarkan meja audit tumbuh jadi dashboard/graf.** §8 menolak DAG explorer;
  telemetri di sini adalah **daftar bertanda**, bukan visualisasi kurikulum.
- **Prosa penjelasan buatan AI tidak pernah mendarat di `library/`.** Setelah approve
  dicabut, gerbang **403** (`GET /nodes/{id}/explanation`) menjadi satu-satunya
  perlindungan tersisa terhadap content library §8.
- **Gerbang prediktif (4-ii) diam di awal.** Tanpa data attempt ia tak punya sinyal;
  itu benar, bukan bug. Jangan menambal dengan ambang agresif yang berbunyi di n kecil.

## Testing / validasi

```bash
cd backend && pytest tests/test_gate_triad.py tests/test_probe_verifier.py \
  tests/test_grounding.py tests/test_edge_evidence.py tests/test_telemetry.py -v
cd backend && pytest && ruff check .
python scripts/verify_nodes.py            # triad, lintas 3 domain
```

Uji negatif wajib (gerbang yang tak pernah menolak apa pun bukan gerbang): soal dengan
starter yang lolos, solusi kosong yang lolos, probe dengan `correct_answer` salah, klaim
R3 dengan kutipan yang tak ada di snapshot, edge tanpa bukti konstruk, dan node duplikat
— **semuanya harus ditolak otomatis**, tanpa manusia.

## Expected result

- Artifact R2/R3/R4 yang lolos gerbang mesin masuk `data/`/DB **tanpa klik manusia**.
- Artifact yang cacat ditolak otomatis dengan alasan yang terbaca.
- Node bermasalah muncul tertandai di `/authoring` beserta angkanya.
- Loop, scaffold, scheduler, mastery: **tidak berubah sama sekali**. M7 tak menyentuh
  §1.2/§1.3.

## Acceptance criteria

- [x] `_gate_r4` menegakkan **triad** (kosong MERAH, starter MERAH, referensi HIJAU)
      dan bekerja untuk ketiga domain — tak ada lagi `.py` yang di-hardcode.
      Aturannya satu salinan di `services/quality_gate.py`, dipakai bersama
      `verify_nodes.py`; `test_gate_triad.py` merah kalau salah satu pemanggil
      menulis aturannya sendiri lagi.
- [x] Probe diverifikasi **eksekusi**. Pemeriksaan distractor DICABUT: ia mustahil
      gagal (distractor didefinisikan sebagai opsi yang bukan `correct_answer`, jadi
      begitu kuncinya cocok, semuanya otomatis berbeda). Cacat yang sesungguhnya
      dituju — dua opsi sama-sama benar — ditangkap validator `options` unik tanpa
      eksekusi sama sekali.
- [x] Grounding R3 naik dari "ID sumber ada" ke "kutipan verbatim cocok" dengan
      `data/sources/<id>.md`. **Snapshot-nya belum ada** dan sengaja tidak dibuat
      otomatis: ia salinan verbatim sumber asli, dan mengarangnya justru kebalikan
      dari gunanya. Sampai Bryant membuatnya, job R3 ditolak dengan pesan yang
      menyebut path persisnya.
- [x] ~~Edge butuh bukti konstruk; edge tanpa bukti ditolak~~ → **diturunkan jadi
      laporan.** Diukur atas kurikulum nyata, versi yang memblokir menandai 6–7 dari
      14 edge hard dengan alasan yang salah semua. Penggantinya: korroborasi
      (melaporkan), bukti prediktif (menandai), dan aturan **edge usulan AI hanya
      boleh `soft`**. Lihat CLAUDE.md §7 2026-09-01(a).
- [x] ~~Node duplikat terdeteksi lewat reference solution node lain~~ → **dibatalkan
      dengan bukti**: di `n001_paginate`, referensi `variant_a` LOLOS hidden test
      `variant_b`, dan kedua varian itu sah. Aturannya akan menolak pekerjaan yang
      benar. Lihat CLAUDE.md §7 2026-09-01(b).
- [x] Telemetri menandai node trivia / rusak / salah kalibrasi / probe mati dari data
      yang sudah ada. **Tak ada pensiun otomatis.** `coverage()` ikut melaporkan
      berapa node yang PUNYA data, supaya "tak ada temuan" tak terbaca sebagai
      "semuanya sehat".
- [x] Promosi otomatis aktif (`CLAUDE_AUTO_PROMOTE`, default hidup); mematikannya
      mengembalikan jaminan M5 utuh — diuji.
- [ ] `/authoring` jadi meja audit: **endpoint `GET /authoring/audit` sudah ada,
      halaman frontend-nya BELUM.** Tombol pensiun juga belum — retirement butuh
      tempat menyimpan keputusannya (`data/`, bukan kolom DB) dan belum dirancang.
- [x] **Nol kolom DB baru.** `snippet`/`expression`/`expected_value` hidup di
      `probe_*.yaml`, snapshot sumber di `data/sources/`.
- [x] 19 node existing termigrasi. `verify_nodes.py`: **39/39 instance lolos triad,
      19/19 probe terverifikasi eksekusi** lintas 3 domain.
- [ ] `destination` per domain: endpoint audit sudah MELAPORKAN domain yang belum
      punya, tapi ketiganya masih kosong — pengisiannya keputusan manusia, dan itu
      memang satu-satunya bagian M7 yang tak boleh diotomasi.
- [ ] Status implementasi di CLAUDE.md §7 entri 2026-08-31 diperbarui dari
      "BELUM DIBANGUN" begitu M7 selesai — **belum**, karena dua butir di atas
      belum tuntas.
