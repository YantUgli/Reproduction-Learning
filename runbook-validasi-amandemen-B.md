# Runbook — Validasi Amandemen B (Async Hard-Edge Review)

> **Tujuan tahap ini:** membuktikan Amandemen B aman & benar saat flag dinyalakan,
> **sebelum** ditumpuk pekerjaan batch (Kebutuhan 2). Ini validasi *postur keamanan*,
> bukan pengembangan fitur baru.
>
> **Basis kode:** commit `f55a605` (mekanisme async review, 216 test hijau).
> **Lingkungan:** env uji / lokal — **JANGAN** di produksi.
> **Pelaksana:** Isyah.
>
> ⚠️ *Catatan akurasi:* runbook diturunkan dari catatan desain sesi 2026-09-21, bukan
> dari membaca ulang source. Perintah CLI, flag, dan path sudah verbatim dari catatan.
> Titik bertanda **⚠️ verifikasi** perlu dicocokkan sekali ke kode asli sebelum jalan.

---

## 0. Properti yang mau dibuktikan

Amandemen B menambah kemungkinan: sebuah `hard` edge bisa **diusulkan** lewat L4,
menunggu di antrian, dan **dianggap disetujui bila tidak diveto dalam 7 hari kalender**.
Yang kita uji bukan cuma "fitur jalan", tapi bahwa **pertahanan berlapisnya masih pegang**:

```
Klamp A1 (flag)   →   Antrian veto 7 hari   →   Promosi manual
 sakelar induk         penjaga kedua              Isyah yang jalankan
```

Klaim inti yang harus tetap benar sepanjang uji:

- **P1 — Loop buta ke pending.** Selama sebuah edge masih di `edges.pending.yaml`,
  loop belajar tidak pernah membacanya → Bryant tidak pernah terkunci keluar dari node
  yang harusnya `available`.
- **P2 — Tidak ada promosi tak sengaja.** Edge `hard` hanya berlaku setelah
  `promote_pending_edges.py` dijalankan manual. Tidak ada cron/scheduler.
- **P3 — Veto = tanda, bukan hapus.** Edge yang diveto tidak ikut promosi, tapi jejaknya
  tetap ada (`vetoed_at` + `veto_reason`).
- **P4 — Gagal ke sisi aman.** Bila apa pun meleset, konsekuensinya selalu "edge tetap
  tidak mengunci Bryant", bukan sebaliknya.

Kalau salah satu dari P1–P4 tidak terbukti → **stop, jangan lanjut**, B belum layak aktif.

---

## 1. Pre-flight (flag masih OFF)

- [ ] **PF-1 — Pastikan env uji.** Bukan database/produksi. Konfirmasi `.venv`, working
      dir repo, dan branch yang benar.
- [ ] **PF-2 — Git bersih & tahu titik dasar.**
      ```bash
      git status              # bersih / paham perubahan yang ada
      git log --oneline -1    # pastikan berpijak di f55a605 atau turunannya
      ```
- [ ] **PF-3 — Baseline test hijau dengan flag OFF.**
      ```bash
      cd backend && pytest -q
      ```
      **Lolos bila:** `216 passed, 0 failed` (atau ≥ itu tanpa merah).
      Kalau ada merah di sini, benahi dulu — jangan menyalakan flag di atas baseline retak.
- [ ] **PF-4 — Snapshot state awal edge** (buat pembanding nanti). Untuk domain uji
      (mis. `fastapi`):
      ```bash
      cp data/domains/fastapi/edges.yaml            /tmp/edges.yaml.before
      cp data/domains/fastapi/edges.pending.yaml    /tmp/edges.pending.yaml.before 2>/dev/null || echo "(belum ada pending — normal)"
      ```
- [ ] **PF-5 — Catat node target uji.** Pilih pasangan (`from` → `to`) yang **tidak**
      mengganggu urutan belajar nyata, atau pakai node throwaway. Contoh preseden dari
      sesi lalu: `n004_query_param_default` → `n014_cookie_param`.

---

## 2. Langkah validasi (flag ON, hanya lokal)

### S1 — Nyalakan flag & pastikan sistem hidup
- [ ] Jalankan backend dengan flag ON **hanya di sesi ini**:
      ```bash
      REPRO_AMENDMENT_B=1 uvicorn app.main:app
      ```
- [ ] Cek status integrasi:
      ```
      GET /authoring/status
      ```
      **Lolos bila:** status menyala, tidak error saat boot dengan flag ON.

> Catatan: flag ini **tidak** dinyalakan di file/env permanen. Begitu sesi uvicorn ini
> mati, sistem balik ke OFF (default). Itu memang yang kita mau.

---

### S2 — Usulan `hard` mendarat di PENDING, bukan di `edges.yaml`
Ini inti Amandemen B: dengan flag ON, Klamp A1 tidak lagi memaksa `soft`.

- [ ] Picu L4 (`forge-node`) untuk sebuah kandidat node yang menandai `prereq_node_id`,
      dengan `edge_type: hard`:
      ```
      POST /authoring/node
      ```
      ⚠️ **verifikasi** bentuk payload: field `edge_type` sudah pasti (pintu HTTP
      `TriggerNodeIn.edge_type`); nama field lain (kandidat/prereq/domain) cocokkan ke
      schema `TriggerNodeIn` di `routers/authoring.py`.

      > Ingat temuan arsitektur: edge **tidak** datang dari LLM. "AI usul hard" pada
      > praktiknya = kamu memicu L4 → menandai prereq sebagai hard → masuk jendela veto.
- [ ] Pantau job sampai selesai:
      ```
      GET /authoring/jobs/{id}
      ```
- [ ] Periksa file edge domain uji:
      ```bash
      grep -n "type: hard" data/domains/fastapi/edges.pending.yaml   # HARUS ada usulannya
      diff /tmp/edges.yaml.before data/domains/fastapi/edges.yaml     # HARUS kosong (edges.yaml TIDAK berubah)
      ```

**Lolos bila:** usulan muncul di `edges.pending.yaml` dengan `type: hard`, `queued_at`
terisi, dan `edges.yaml` **tidak** bertambah edge. **Gagal (serius) bila:** edge `hard`
langsung nongol di `edges.yaml` — berarti Klamp/pintu bocor, **stop**.

---

### S3 — Loop tetap buta ke pending saat flag ON (bukti P1)
- [ ] Pastikan node hilir (`to`) tetap bisa dikerjakan / tidak terkunci gara-gara usulan
      pending:
      ```
      GET /nodes            # status node target
      GET /nodes/{to_id}    # harus tetap available, bukan locked oleh pending
      ```
- [ ] Jalankan sekali regresi loop dalam kondisi flag ON (uji manual atas properti yang
      sudah dijaga test otomatis):
      ```bash
      cd backend && pytest -q tests/test_pending_edges.py
      ```

**Lolos bila:** node hilir tetap `available` dan jumlah Edge yang dibaca loop identik
seperti sebelum ada pending. **Gagal (serius) bila:** node jadi `locked` karena usulan
yang belum berlaku — P1 pecah, **stop**.

---

### S4 — `--dry-run`: pending terbaca, belum matang
- [ ] Lihat antrian tanpa mengubah apa pun:
      ```bash
      python scripts/promote_pending_edges.py --dry-run
      ```
      ⚠️ **verifikasi** format output ke isi `scripts/promote_pending_edges.py`.
- [ ] Silang-cek dengan meja audit:
      ```
      GET /authoring/audit    # cek blok pending_edges + ready_to_promote + hitung mundur
      ```

**Lolos bila:** edge dari S2 tampil sebagai *pending*, dengan status **belum** ready
(umur < 7 hari), dan hitung mundur `matures_at` masuk akal. Tidak ada file yang berubah
oleh dry-run.

---

### S5 — Jalur veto (bukti P3)
- [ ] Veto edge uji:
      ```bash
      python scripts/promote_pending_edges.py --veto <from_id>__<to_id> --reason "uji validasi B"
      ```
      (`edge_id` = `<from_id>__<to_id>`, mis. `n004_query_param_default__n014_cookie_param`)
- [ ] Periksa hasilnya di `edges.pending.yaml`:
      ```bash
      grep -nA2 "<from_id>__<to_id>" data/domains/fastapi/edges.pending.yaml
      ```
- [ ] Uji **re-veto menimpa alasan**:
      ```bash
      python scripts/promote_pending_edges.py --veto <from_id>__<to_id> --reason "alasan kedua"
      ```
- [ ] Konfirmasi edge yang diveto **tidak** ikut ready-to-promote:
      ```bash
      python scripts/promote_pending_edges.py --dry-run
      ```

**Lolos bila:** `vetoed_at` + `veto_reason` terisi (bukan barisnya dihapus), re-veto
mengganti `veto_reason` jadi "alasan kedua", dan edge tersebut tidak muncul sebagai
kandidat promosi.

---

### S6 — Jalur promosi (bukti P2)
Karena tak mungkin menunggu 7 hari nyata, pakai **edge uji terpisah** dan mundurkan
`queued_at`-nya. Jangan pakai edge yang barusan diveto di S5.

- [ ] Siapkan satu edge pending uji yang **belum diveto**, lalu backdate `queued_at`-nya
      ke > 7 hari lalu langsung di `data/domains/fastapi/edges.pending.yaml`, contoh:
      ```yaml
      queued_at: 2026-09-01T00:00:00Z   # > 7 hari sebelum "hari ini" env uji
      ```
- [ ] Dry-run harus menandainya **ready**:
      ```bash
      python scripts/promote_pending_edges.py --dry-run
      ```
- [ ] Promosikan sungguhan:
      ```bash
      python scripts/promote_pending_edges.py
      ```
- [ ] Verifikasi perpindahan kotak:
      ```bash
      grep -n "<from_id>__<to_id>" data/domains/fastapi/edges.yaml           # HARUS sekarang ada di sini
      diff /tmp/edges.pending.yaml.before data/domains/fastapi/edges.pending.yaml   # entri matang sudah keluar dari pending
      ```

**Lolos bila:** hanya edge yang matang **dan** tidak diveto yang pindah ke `edges.yaml`;
edge yang belum matang dan yang diveto tetap tinggal di pending.

---

### S7 — (Opsional, disarankan) Edge yang sudah promoted benar mengunci loop
- [ ] Setelah promosi, cek node hilir sekarang **terkunci** sampai prereq `acquired`:
      ```
      GET /nodes/{to_id}    # kini locked oleh hard edge yang sudah berlaku
      ```
**Lolos bila:** perilaku loop berubah **hanya setelah** promosi manual — menutup rantai
bukti bahwa "berlaku" ≠ "diusulkan".

---

## 3. Pembersihan / rollback

- [ ] **Matikan flag.** Hentikan sesi `uvicorn` yang jalan dengan `REPRO_AMENDMENT_B=1`.
      Restart normal (tanpa env var) → sistem kembali OFF.
- [ ] **Kembalikan state edge** kalau ini murni latihan:
      ```bash
      cp /tmp/edges.yaml.before          data/domains/fastapi/edges.yaml
      cp /tmp/edges.pending.yaml.before  data/domains/fastapi/edges.pending.yaml 2>/dev/null || rm -f data/domains/fastapi/edges.pending.yaml
      ```
      (Atau, kalau memang mau menyimpan node/edge uji, commit sadar — jangan tercampur
      artefak uji tak sengaja.)
- [ ] **Baseline ulang dengan flag OFF:**
      ```bash
      cd backend && pytest -q      # harus balik 216 passed, 0 failed
      ```
- [ ] `git status` bersih (atau perubahan yang tersisa memang disengaja).

---

## 4. Kriteria sign-off

B layak dianggap **"aktif teruji"** hanya bila semua ini ✅:

- [ ] S2 — usulan `hard` mendarat di pending, `edges.yaml` tak tersentuh
- [ ] S3 — P1 terbukti: loop buta ke pending, Bryant tidak terkunci
- [ ] S4 — dry-run membaca pending & menghitung kematangan dengan benar
- [ ] S5 — P3 terbukti: veto menandai (bukan hapus), re-veto menimpa, veto ≠ promosi
- [ ] S6 — P2 terbukti: hanya edge matang & tak-diveto yang promosi, dan hanya lewat script manual
- [ ] Rollback bersih & baseline balik hijau

Kalau semua hijau → aman merencanakan batch Kebutuhan 2 di atas fondasi ini. Kalau ada
yang merah di P1–P4 → catat temuannya, jangan aktifkan B di lingkungan mana pun dulu.

---

## 5. Referensi cepat

**Perintah kunci**
```bash
# Nyalakan Amandemen B (hanya sesi lokal/uji)
REPRO_AMENDMENT_B=1 uvicorn app.main:app

# Lihat antrian tanpa efek
python scripts/promote_pending_edges.py --dry-run

# Veto sebuah edge
python scripts/promote_pending_edges.py --veto <from>__<to> --reason "..."

# Promosi edge matang (manual)
python scripts/promote_pending_edges.py

# Test suite
cd backend && pytest -q
```

**File & konsep**
- State usulan: `data/domains/<domain>/edges.pending.yaml` (git-committed, bukan DB)
- State berlaku: `data/domains/<domain>/edges.yaml` (satu-satunya yang dibaca loop)
- `edge_id` = `<from_id>__<to_id>`
- `PENDING_REVIEW_DAYS = 7`
- Klamp A1 = pengaman di titik kelahiran `job.request` yang memaksa `soft` selama flag OFF
- Pintu HTTP = `TriggerNodeIn.edge_type` → diteruskan ke trigger L4

**Skema entri `edges.pending.yaml` (beku)**
```yaml
edges:
  - from: n004_query_param_default
    to: n014_cookie_param
    type: hard                 # yang DIUSULKAN; belum berlaku
    source_ref_id: fastapi_docs_cookie_params
    library_file: library/fastapi-produksi/01-parameter-request/cookie-param.md
    job_id: r4-20260916T104348-eb79be
    queued_at: 2026-09-16T10:43:00Z
    note: "Usul L4 (AI) — menunggu veto Isyah s/d queued_at + 7 hari."
    # diisi HANYA saat veto:
    # vetoed_at: 2026-09-19T08:00:00Z
    # veto_reason: "prasyarat terlalu longgar"
```

**Dokumen terkait di repo**
- `docs/design-async-review-mechanism.md` — rancangan (final 2026-09-18)
- `docs/execution-plan-async-review.md` — langkah implementasi
- `CLAUDE.md` §7 — Amandemen A/B/C (2026-09-16) + entri implementasi (2026-09-21)
