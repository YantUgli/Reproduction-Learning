# M4 — Full Loop: FSRS + Placement + Dashboard (Fase 2)

> Peta PRD: Fase 2 · Dependency: M3 **+ Gerbang 0 diputuskan** · Estimasi: 2–3 minggu

## ⚠️ Gerbang 0 wajib sebelum M4

**Jangan mulai M4 sebelum keputusan Build-vs-Buy (Gerbang 0) dibuat.** Di M4 biaya
sesungguhnya mulai keluar (FSRS + placement + dashboard + seluruh node A2). Kalau
Execute Program (~$39/bln) ternyata cukup untuk kebutuhan Bryant pada primitif
bahasa, roadmap boleh **berhenti di M3**. Lihat PRD §12 (Gerbang 0) & RISK-5.
Keputusan ini mengikat dan harus dicatat di CLAUDE.md §7.

## Tujuan

Mengubah loop M3 menjadi **loop belajar penuh**: penjadwalan spaced repetition
nyata (FSRS), penemuan lantai awal (placement probe), mastery berjarak
(`acquired → mastered`), dan dashboard yang menampilkan node aktif + review jatuh
tempo. Seluruh node (A1 dari M2 + A2 yang diarang paralel) masuk sistem.

## Konteks & alasan

M3 membuktikan sinyal terbaca; M4 membuatnya **berkelanjutan**. Tanpa spaced
retrieval, "ilmu menguap setelah selesai" (keluhan Bryant) tidak tertangani.
Tanpa placement, lantai awal *diasumsikan* — padahal PRD menegaskan lantai harus
**ditemukan** karena self-report Bryant tidak reliabel (§6).

Unit yang dijadwalkan adalah **reproduksi node**, bukan flashcard recognition —
inilah yang membedakan produk dari Anki (§7.5).

## Prerequisite

- **M3 selesai** (loop L3→L0→probe jalan, Attempt tercatat).
- **Gerbang 0 diputuskan "lanjut".**
- Track Authoring **A2** mulai berjalan (node A2 diarang paralel, pakai format &
  gerbang mutu M2). M4 tidak menunggu seluruh A2 selesai; ia menampung node yang
  sudah hijau.

## File / komponen yang dibuat/diubah

```
backend/app/
  services/
    scheduler.py         # wrapper py-fsrs: rate Attempt -> update ScheduleItem
    mastery.py           # transisi status: acquired -> mastered (N sukses berjarak); lapsed
    placement.py         # placement probe: cari batas fail->pass pertama
  routers/
    review.py            # GET review jatuh tempo hari ini; POST hasil review
    placement.py         # GET/POST sesi placement
frontend/app/
  page.tsx               # dashboard penuh: node aktif · due hari ini · peta progres linear
  placement/page.tsx     # sesi placement (sekali di awal + berkala)
  review/page.tsx        # sesi review harian
backend/tests/
  test_scheduler.py      # FSRS: due_at maju saat sukses; reset saat gagal
  test_mastery.py        # mastered setelah N=4 berjarak; lapsed menurunkan status
  test_placement.py      # berhenti di batas fail->pass pertama
```

## Langkah implementasi (berurutan)

1. **Pasang `py-fsrs`.** Tambah dependency. **Jangan tulis algoritma SR sendiri**
   (§7.5, CLAUDE.md §2). Kalau Isyah sudah punya SR engine, nebeng ke situ.

2. **`scheduler.py`.** Terjemahkan hasil Attempt review menjadi rating FSRS,
   perbarui `ScheduleItem.fsrs_stability`, `fsrs_difficulty`, `due_at`,
   `review_count`, `consecutive_success`. Simpan mapping "pass/fail (+ opsi probe)"
   → rating FSRS di satu tempat. *Open question PRD Q5:* apakah hasil probe ikut
   memberi rating FSRS atau hanya gate — putuskan & catat.

3. **`mastery.py`.** Transisi status `ScheduleItem`:
   - lolos verifikasi pertama → `acquired`.
   - tiap jatuh tempo harus lolos lagi dengan **instance berbeda**.
   - `mastered` setelah **N sukses berjarak** (default `N=4` dari config M0).
   - gagal di interval mana pun → `lapsed`, interval reset. *Open question Q3:*
     `lapsed` turun ke `acquired` atau `available` penuh — putuskan & catat.

4. **`placement.py` + `placement/page.tsx`.** Rangkaian tantangan reproduksi
   **menurun**: unit framework → primitif bahasa/logika. **Berhenti di batas
   fail→pass pertama** — itu lantai awal Bryant. *Open question Q4:* batas jumlah
   node maksimum supaya tak melelahkan — putuskan & catat. Placement dijalankan
   sekali di awal dan berkala.

5. **`review.py` + `review/page.tsx`.** Sesi review harian: tampilkan node yang
   `due_at <= sekarang`, verifikasi ulang dengan **instance berbeda**, salurkan
   hasil ke `scheduler` + `mastery`.

6. **Dashboard penuh (`page.tsx`).** Node aktif · review jatuh tempo hari ini · peta
   progres **daftar linear** (bukan graf visual — §8 tetap berlaku). Tampilkan KPI
   inti: `reproduce-without-AI pass rate per node` & jumlah node `mastered` (§9).

7. **Muat seluruh node.** Jalankan `load_nodes.py` (M2) untuk A1+A2. Node `locked`
   sampai `hard` edge prasyaratnya `acquired`; node independen `available`.

## Keputusan teknis penting

- **FSRS lewat library, titik.** DSR model (difficulty/stability/retrievability)
  sudah jadi default modern; menulis sendiri = bug + waktu terbuang.
- **Yang dijadwalkan = reproduksi, bukan recognition.** ScheduleItem menunjuk node
  yang harus **diproduksi ulang**, bukan kartu untuk dikenali. Ini invariant produk.
- **`mastered` butuh N sukses BERJARAK.** Empat kali berturut dalam satu sesi ≠
  mastered. Jarak (spacing) adalah bagian definisi. Enforce lewat `due_at`.
- **Placement menemukan lantai, tidak mengasumsikan.** Jangan menambahkan langkah
  "tanya Bryant sudah bisa apa" — itu melanggar premis illusion of competence (§1).
- **Tiga open question PRD (Q3, Q4, Q5) diputuskan di sini** dan dicatat di
  CLAUDE.md §7. Jangan biarkan menggantung — mereka memengaruhi perilaku loop.

## Hal yang harus diperhatikan

- FSRS mengharapkan rating (again/hard/good/easy). Pemetaan dari verdict biner
  pass/fail + probe harus eksplisit & konsisten; dokumentasikan.
- Review harus pakai **instance berbeda** tiap kali; kalau varian habis, itu sinyal
  butuh lebih banyak varian (naikkan ke authoring). Jangan mengulang instance sama —
  itu mengubah reproduksi jadi hafalan.
- Dashboard tetap **daftar linear**. Setiap kali tergoda bikin graf DAG interaktif,
  ingat §8: "versi builder dari avoidance trap".
- A2 adalah ~30–60 jam kerja authoring (RISK-1) — M4 engineering bisa selesai
  sebelum node cukup; itu normal, node menetes masuk.

## Testing / validasi

```bash
cd backend && pytest tests/test_scheduler.py tests/test_mastery.py tests/test_placement.py -v
uvicorn app.main:app --reload
cd ../frontend && npm run dev
```
Uji manual: jalankan placement → dapat lantai; selesaikan node → `acquired`; lewati
beberapa siklus review berjarak (bisa dipercepat dengan memundurkan `due_at`) →
node jadi `mastered` setelah N=4; sengaja gagalkan review → `lapsed` + interval reset.

## Expected result

- Node bergerak `locked → available → acquired → mastered`, dan `lapsed` saat gagal.
- Placement menghentikan Bryant di batas fail→pass pertama (lantai ditemukan).
- Dashboard menampilkan due hari ini + KPI pass rate & jumlah `mastered`.
- Review harian memakai instance berbeda dan menjadwalkan ulang via FSRS.

## Acceptance criteria

- [x] Gerbang 0 tercatat sebagai "lanjut" di CLAUDE.md §7 sebelum M4 dimulai.
- [x] `py-fsrs` terpasang; **tidak ada** algoritma SR buatan sendiri.
      (`fsrs>=6,<7`; `services/scheduler.py` hanya memetakan verdict↔Rating dan
      ScheduleItem↔Card.)
- [x] Transisi status lengkap & teruji: `acquired`, `mastered` (N=4 berjarak),
      `lapsed` (reset interval). — `tests/test_mastery.py`, termasuk uji bahwa 4 sukses
      dalam SATU sesi **tidak** memberi `mastered`.
- [x] Placement probe berhenti di batas fail→pass pertama, node maksimum terputuskan
      (`PLACEMENT_MAX_NODES = 7`, PRD Q4). — `tests/test_placement.py`.
- [x] Review harian memakai instance berbeda dan menjadwal ulang lewat FSRS.
      — `tests/test_review_flow.py`.
- [x] Dashboard menampilkan KPI `reproduce-without-AI pass rate` & jumlah `mastered`;
      tetap daftar linear (bukan graf).
- [x] Open question PRD Q3, Q4, Q5 diputuskan & dicatat di CLAUDE.md §7.
