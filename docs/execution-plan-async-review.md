# Plan Eksekusi — Mekanisme Review ASYNC (Amandemen C / pengaktif Amandemen B)

> **Status:** ⏳ **BELUM DIEKSEKUSI — rancangan langkah.** Turunan langsung dari
> [`design-async-review-mechanism.md`](design-async-review-mechanism.md) (final 2026-09-18)
> dan keputusan [`../CLAUDE.md`](../CLAUDE.md) §7 Amandemen B & C (2026-09-16).
>
> **Ditulis agar bisa dikerjakan bertahap & diverifikasi satu per satu:** tiap langkah
> punya daftar berkas, Definition of Done yang dibuktikan **kode nyata** (bukan niat),
> dan urutan ketergantungan.
>
> **Bukan** pelonggaran invariant. Kalau ada konflik dengan §1 CLAUDE.md,
> **invariant menang.**

---

## 0. Peta cepat (baca ini dulu)

Amandemen B mengizinkan AI mengusulkan edge **`hard`**, tapi ditulis **tidak aktif**
sampai mekanisme C ini terpasang **di depan** jalur promosi. Plan ini membangun lajur
pending edge (state + script + audit) lalu, **paling akhir**, menyambungkan
`_promote_node_genesis` ke lajur itu — dengan default tetap `soft` sehingga tak ada
`hard` yang bocor sebelum semua pengaman siap.

### Temuan yang membentuk plan ini (diperiksa langsung di kode)

| Fakta | Bukti |
|---|---|
| Edge dari AI ditulis backend **selalu `soft`** via append-teks | [`review_queue.py:304`](../backend/app/claude/review_queue.py#L304) `_append_soft_edge` |
| `_promote_node_genesis` menambah edge di dalam promosi atomik (rollback backup `edges.yaml`) | [`review_queue.py:255-273`](../backend/app/claude/review_queue.py#L255) |
| Loop **hanya** membaca `edges.yaml` — file lain tak tersentuh | [`node_loader.py:181`](../backend/app/services/node_loader.py#L181) `load_edges` |
| Tak ada scheduler in-app (hanya `BackgroundTasks` fana + `py-fsrs`) | `config.py`, tak ada APScheduler/celery |
| Meja audit sudah merender edge + kontrol read-only tanpa endpoint | [`authoring.py:333-372`](../backend/app/routers/authoring.py#L333), `AuditOut` |
| Pasangan `from→to` **unik** (0 duplikat dari 23+14 edge) → `edge_id = <from>__<to>` sah | verifikasi 2026-09-18 (design §8) |

### Yang dibangun

| Berkas | Peran | Langkah |
|---|---|---|
| `data/domains/<domain>/edges.pending.yaml` | Store usulan `hard` menunggu veto (git-committed). | 1 |
| `backend/app/services/pending_edges.py` (baru) | Baca pending + hitung state (`menunggu`/`matang`/`diveto`) + `edge_id`. **READ-only untuk backend.** | 1 |
| `scripts/promote_pending_edges.py` (baru) | `--veto <id>` (tandai) + promosi manual (matang & tak diveto → append `hard`, hapus dari pending). | 2 |
| `backend/app/routers/authoring.py` (perluasan) | `GET /authoring/audit` + field `pending_edges` + `ready_to_promote` count. | 3 |
| `frontend/app/authoring/page.tsx` + `lib/api.ts` | Bagian "Edge hard menunggu veto" + pengingat "X siap promosi". | 3 |
| `backend/app/claude/review_queue.py` + `jobs.py` (perluasan) | Cabang `edge_type`: `hard` → pending; `soft` → `_append_soft_edge` (sekarang). **Default `soft`.** | 4 |
| test di `backend/tests/` + `scripts/` | Penjaga tiap langkah. | 1–4 |

**Definisi selesai (ringkas):** usulan `hard` dari L4 mendarat di `edges.pending.yaml`
(bukan `edges.yaml`), terlihat di meja audit dengan hitung mundur, bisa diveto (ditandai,
tak dihapus), dan — **hanya lewat script yang Isyah jalankan manual** — dipromosikan jadi
`hard` di `edges.yaml` sesudah 7 hari tanpa veto. Sepanjang itu **loop tak pernah membaca
pending**, jadi node tak pernah terkunci; dan **sampai langkah 4 diaktifkan, tak ada
`hard` yang diproduksi sama sekali**.

---

## 1. Ruang lingkup & garis pengaman (BACA sebelum menyentuh kode)

**PENGAMAN UTAMA — Amandemen B tetap INAKTIF sampai seluruh plan ini hijau.** Sampai
langkah 4 selesai **dan** diaktifkan secara sadar (satu switch, lihat §4-langkah-4):
- `_append_soft_edge` tetap **satu-satunya** jalur penulisan edge dari AI, tetap `soft`.
- Tak satu pun langkah 1–3 boleh membuat AI menulis `hard` — mereka membangun store,
  script, dan tampilan yang bekerja penuh **atas berkas pending buatan-tangan** (test),
  tanpa produsen `hard` otomatis.
- Langkah 4 (satu-satunya yang menyambung produsen `hard`) **default-nya `soft`**;
  mengizinkan `hard` = perubahan input eksplisit (mis. field request `edge_type: hard`
  atau flag), bukan efek samping dari merge langkah 4.

**Kenapa urutan ini aman:** komponen yang bisa menulis `hard` ke `edges.yaml` adalah
**script promosi (langkah 2)**, dan ia hanya memproses entri pending yang matang & tak
diveto. Selama langkah 4 belum mengaktifkan produksi `hard`, `edges.pending.yaml` tak
pernah terisi dari AI → tak ada yang bisa dipromosikan → nol kebocoran. Membangun 1→2→3
lebih dulu memastikan **saat** entri `hard` pertama lahir (langkah 4), veto & visibilitas
sudah ada di depannya.

**Di luar ruang lingkup:** node genesis itu sendiri (sudah ada, tak berubah); mengubah
`load_edges`/loop; scheduler/cron; UI veto-tombol (tetap read-only + perintah tempel).

---

## 2. Keputusan yang sudah dikunci (dari design doc — jangan ditawar ulang)

1. State = `data/domains/<domain>/edges.pending.yaml` (git-committed, per-domain).
2. `edge_id = <from_id>__<to_id>` (terverifikasi unik).
3. Veto = **TANDAI** (`vetoed_at` + `veto_reason`), entri tetap ada.
4. **Veto ulang = UPDATE.** Memveto edge yang sudah diveto **menimpa** `vetoed_at` +
   `veto_reason` dengan yang baru; veto selalu berhasil, hasil akhir = veto terakhir
   (idempoten-aman, tak pernah menolak).
5. Promosi 7-hari = **script dijalankan MANUAL Isyah** (bukan cron/scheduler/timer).
6. Lihat antrian = perluas `GET /authoring/audit` + render di `/authoring` (bukan halaman
   baru, bukan command Claude Code).
7. State pending **terpisah** dari `/authoring/jobs`; loop **tak pernah** membacanya.

Skema entri (beku):
```yaml
edges:
  - from: n004_query_param_default
    to: n014_cookie_param
    type: hard                 # yang DIUSULKAN; belum berlaku
    source_ref_id: fastapi_docs_cookie_params
    library_file: library/fastapi-produksi/01-parameter-request/cookie-param.md
    job_id: r4-20260916T104348-eb79be
    queued_at: 2026-09-18T10:43:00Z
    note: "Usul L4 (AI) — menunggu veto Isyah s/d queued_at + 7 hari."
    # diisi HANYA saat veto (veto ulang menimpa keduanya):
    # vetoed_at: 2026-09-19T08:00:00Z
    # veto_reason: "prasyarat terlalu longgar"
```

---

## 3. Langkah-langkah

> Disusun dalam **urutan ketergantungan**, bukan urutan nomor di permintaan. Pemetaan ke
> item permintaan disebut di tiap judul. Alasan langkah "percabangan" (item 1 permintaan)
> ada di **akhir**: ia satu-satunya yang menyalakan produsen `hard`, jadi harus mendarat
> setelah veto & visibilitas siap (garis pengaman §1).

### Langkah 1 — Store `edges.pending.yaml` + reader (permintaan item 2) · design §2

**Sentuh:**
- `data/domains/<domain>/edges.pending.yaml` — dibuat kosong/absen; **bukan** git-ignored
  (kebalikan `artifacts/`). Absennya = "belum ada usulan", bukan error.
- `backend/app/services/pending_edges.py` (baru): reader murni + model entri (pydantic/
  dataclass mengikuti skema §2) + `edge_id(entry)` + `state(entry, now)` →
  `{"menunggu"|"matang"|"diveto"}` dengan `matures_at = queued_at + 7d`.
- `backend/app/services/node_loader.py` — **tidak berubah**; ditambah test regresi bahwa
  `load_edges` mengabaikan `edges.pending.yaml`.

**DoD (dibuktikan kode):**
- `test_pending_edges.py`: parse berkas contoh → entri; `edge_id` = `<from>__<to>`;
  `state` benar untuk tiga kasus (queued_at 1 hari lalu = `menunggu`; 8 hari lalu =
  `matang`; ada `vetoed_at` = `diveto` **walau** 8 hari lalu).
- **Regresi loop:** test yang menaruh `edges.pending.yaml` berisi satu entri `hard` di
  domain, lalu `load_domain_into_db` + query Edge → jumlah edge **identik** dengan tanpa
  berkas pending (loop buta terhadap pending). Ini penjaga pengaman §1.
- Berkas absen → reader balas list kosong, bukan exception.

**Bergantung pada:** — (fondasi).

---

### Langkah 2 — `scripts/promote_pending_edges.py` (permintaan item 3) · design §4, §5

**Sentuh:**
- `scripts/promote_pending_edges.py` (baru). Dua sub-fungsi, satu pemilik berkas pending:
  - `--veto <edge_id> [--reason "..."]`: cari entri (semua domain), isi `vetoed_at`
    (UTC now) + `veto_reason`; **tak menghapus**. **Veto ulang = UPDATE (§2 keputusan 4):**
    entri yang sudah ber-`vetoed_at` **ditimpa** dengan `vetoed_at`/`veto_reason` baru —
    veto selalu berhasil, hasil akhir = veto terakhir, tak pernah menolak dengan pesan.
  - **promosi manual (default, tanpa flag veto):** untuk tiap entri `state == matang`
    (matang & **tak** ber-`vetoed_at`): append ke `edges.yaml` domain-nya sebagai
    `type: hard` lewat **jalur append-teks + reparse yang sama** dengan `_append_soft_edge`
    (komentar kurasi selamat), lalu hapus entri dari `edges.pending.yaml`. Backup kedua
    berkas → rollback bila reparse gagal (pola rollback `_promote_node_genesis`).
  - `--dry-run`: laporkan apa yang akan dipromosikan/diveto tanpa menulis (preseden
    `verify_library.py --candidates` = laporan).
- Faktorisasi: ekstrak helper append-edge bersama (mis. di `review_queue.py`) supaya
  `soft` (backend) & `hard` (script) memakai **satu** penulis — dua salinan cepat
  menyimpang (preseden `run_triad`, `grounding` di-import bukan disalin).

**DoD (dibuktikan kode):**
- `scripts/test_promote_pending_edges.py`:
  - **veto menandai, tak menghapus:** setelah `--veto`, entri masih ada + `vetoed_at`
    terisi; `edges.yaml` **byte-identik** dengan semula (veto tak menyentuh live).
  - **veto ulang = UPDATE:** veto entri yang sudah diveto dengan `--reason` baru →
    **berhasil** (bukan error); `veto_reason` = alasan baru, `vetoed_at` = waktu baru;
    entri tetap satu (tak ganda). Menjalankan veto 3× berturut → hasil akhir = veto ke-3.
  - **promosi matang:** entri 8-hari-tanpa-veto → sesudah run: baris `type: hard` muncul
    di `edges.yaml` (parse ulang sah), entri hilang dari pending, komentar kurasi di
    `edges.yaml` **utuh**.
  - **promosi menahan yang belum matang / diveto:** entri 1-hari → tak dipromosikan;
    entri 8-hari **ber-`vetoed_at`** → tak dipromosikan; keduanya tetap di pending.
  - **rollback:** paksa reparse gagal (entri cacat) → `edges.yaml` **dan**
    `edges.pending.yaml` kembali byte-identik dengan semula.
  - **idempoten:** jalankan promosi 2× → hasil sama, tak ada baris ganda.

**Bergantung pada:** Langkah 1 (reader + `edge_id` + `state`).

---

### Langkah 3 — Audit `pending_edges` + render + pengingat (permintaan item 4) · design §3

**Sentuh:**
- `backend/app/routers/authoring.py`: `AuditOut` dapat `pending_edges: list[PendingEdgeOut]`
  (from/to/library_file/state/queued_at/matures_at/veto_reason) + `ready_to_promote: int`
  (jumlah `state == matang`). `audit()` memanggil `pending_edges` service (**READ-only**).
- `frontend/lib/api.ts`: tipe `PendingEdgeOut` + perluas `AuditOut`.
- `frontend/app/authoring/page.tsx`: bagian baru "Edge hard menunggu veto" (daftar +
  label state + hitung mundur), dan **pengingat "X edge siap promosi"** bila
  `ready_to_promote > 0`, dengan **perintah tempel** `scripts/promote_pending_edges.py`
  (read-only, pola kontrol pending `retire`/`set-destination` yang sudah ada).

**DoD (dibuktikan kode):**
- `test_audit_pending_edges.py`: dengan `edges.pending.yaml` buatan-tangan (1 matang, 1
  menunggu, 1 diveto) → `GET /authoring/audit` mengembalikan 3 entri dengan `state` benar
  dan `ready_to_promote == 1`.
- Backend **tak menulis**: bandingkan mtime/byte `edges.pending.yaml` sebelum/sesudah GET
  (pola `test_membaca_tidak_pernah_menulis` L5).
- Frontend: build lolos (`npm run build`), pengingat muncul hanya saat `ready_to_promote>0`
  (verifikasi manual §5 + snapshot bila ada).

**Bergantung pada:** Langkah 1. (Independen dari Langkah 2 — bisa paralel; tapi perintah
tempel yang ditampilkan menunjuk script Langkah 2, jadi finalisasi teks setelah 2.)

---

### Langkah 4 — Percabangan `_promote_node_genesis` (permintaan item 1) · design §8 · **PALING AKHIR**

**Sentuh:**
- `backend/app/claude/jobs.py` `trigger_r4_node`: tambah `edge_type` ke `job.request`,
  **default `"soft"`**. (Belum ada konsumen `hard` selama B inaktif.)
- `backend/app/claude/review_queue.py` `_promote_node_genesis`: cabang berdasarkan
  `job.request.get("edge_type", "soft")`:
  - `"soft"` → `_append_soft_edge` **seperti sekarang** (jalur & rollback tak berubah).
  - `"hard"` → tulis entri ke `edges.pending.yaml` domain (via penulis pending, isi
    `queued_at`, `job_id`, `source_ref_id`, `library_file`, `type: hard`) — **bukan** ke
    `edges.yaml`. Masuk dalam blok try/rollback yang sama (backup pending file).
- **Switch aktivasi B (terpisah, terakhir):** hanya SETELAH 1–3 hijau, izinkan input
  `edge_type: hard` mengalir (mis. `TriggerNodeIn.edge_type` + prompt R4 boleh mengusulkan
  hard). Sampai switch itu, endpoint & trigger **memaksa `soft`**.

**DoD (dibuktikan kode):**
- `test_promote_node_genesis_edge_branch.py`:
  - `edge_type` absen/`"soft"` → perilaku **identik** sekarang: baris `soft` di
    `edges.yaml`, `edges.pending.yaml` tak tersentuh. (regresi: test L4 lama tetap hijau.)
  - `edge_type="hard"` → **nol** perubahan di `edges.yaml`; satu entri `hard` di
    `edges.pending.yaml` dengan `queued_at` terisi + `job_id` benar.
  - **rollback:** paksa `assemble_node` gagal → folder node hilang lagi **dan**
    `edges.pending.yaml` byte-identik dengan semula (sama disiplin L4).
- **Pengaman §1 terbukti:** test tingkat-integrasi bahwa jalur endpoint `POST /authoring/
  node` (tanpa switch B) tetap menghasilkan **`soft`** apa pun isi request — `hard` tak
  bisa lolos tanpa aktivasi eksplisit.
- **End-to-end (smoke §5):** entri `hard` buatan langkah 4 → terlihat di audit (langkah 3)
  → diveto/dipromosikan (langkah 2). Ketiganya nyambung.

**Bergantung pada:** Langkah 1 (penulis pending), **dan** Langkah 2 + 3 harus sudah hijau
sebelum switch aktivasi (garis pengaman §1). Cabang kode boleh mendarat lebih dulu selama
default `soft`; **aktivasi `hard`** adalah tindakan terakhir.

---

## 4. Urutan build (ketergantungan)

```
Langkah 1 (store + reader + regresi loop)
   ├─→ Langkah 2 (script veto + promosi)      ─┐
   └─→ Langkah 3 (audit + frontend + pengingat)─┤
                                                └─→ Langkah 4 (cabang, default soft)
                                                       └─→ [SWITCH] aktifkan edge_type hard
                                                            (Amandemen B ON — hanya bila 1–3 hijau)
```

- 1 wajib pertama (semua bergantung pada reader + `edge_id` + `state`).
- 2 & 3 boleh paralel setelah 1.
- 4 mendarat setelah 1; **switch `hard` di 4 hanya setelah 2 & 3 hijau.**

---

## 5. Definition of Done (checklist — dibuktikan kode nyata)

- [ ] `pending_edges.py` reader + `edge_id` + `state`; test 3-kasus hijau; **regresi loop**
      membuktikan `load_edges` buta terhadap `edges.pending.yaml`.
- [ ] `promote_pending_edges.py`: veto **menandai** (entri tetap ada, `edges.yaml`
      byte-identik); **veto ulang meng-UPDATE** (selalu berhasil, hasil = veto terakhir);
      promosi matang menulis `hard` (komentar kurasi utuh) & menghapus dari pending;
      menahan yang belum-matang/diveto; rollback byte-identik; idempoten.
- [ ] `GET /authoring/audit` membawa `pending_edges` + `ready_to_promote`; backend
      **tak menulis** (byte/mtime sama sebelum/sesudah); frontend build lolos & pengingat
      muncul hanya saat ada yang matang.
- [ ] `_promote_node_genesis` bercabang: `soft` identik sekarang; `hard` → pending, nol
      sentuhan `edges.yaml`; rollback pending byte-identik; **test L4 lama tetap hijau.**
- [ ] **Pengaman §1:** tanpa switch aktivasi, `POST /authoring/node` **selalu** `soft`;
      test membuktikan `hard` tak bisa bocor ke `edges.yaml` di titik mana pun sebelum
      promosi manual pasca-7-hari.
- [ ] `ruff` bersih (dari `backend/`); `pytest` backend + `scripts/` hijau.
- [ ] Entri §7 CLAUDE.md ditulis (mencatat aktivasi B, penyimpangan bila ada); design doc
      §8 item terbuka ditandai selesai.
- [ ] **Invariant utuh:** tak ada verdict mastery dari AI; loop tak pernah baca pending;
      node tetap `available` selama edge menunggu; Isyah satu-satunya yang bisa veto.

---

## 6. Verifikasi manual (smoke) — setelah 1–4 hijau

```bash
# 0. (pengaman) tanpa aktivasi B: node lahir seperti biasa, edge tetap soft
curl -X POST localhost:8000/authoring/node -d '{...}'   # → edges.yaml dapat SOFT, pending kosong

# 1. aktifkan B (switch), picu usulan hard → cek mendarat di PENDING, bukan live
#    git diff data/domains/<domain>/edges.yaml      → KOSONG
#    git diff data/domains/<domain>/edges.pending.yaml → satu entri hard, queued_at hari ini

# 2. lihat antrian
curl -s localhost:8000/authoring/audit | jq '.pending_edges, .ready_to_promote'
#    buka /authoring → bagian "Edge hard menunggu veto" + hitung mundur

# 3. veto satu entri (script, manual); veto ulang menimpa reason
python scripts/promote_pending_edges.py --veto n004_query_param_default__n0XX_slug --reason "..."
#    → entri MASIH ada + vetoed_at terisi; edges.yaml tak berubah

# 4. promosi manual (setelah memundurkan queued_at >7 hari di entri uji, atau entri matang lain)
python scripts/promote_pending_edges.py --dry-run     # laporan dulu
python scripts/promote_pending_edges.py               # → hard mendarat di edges.yaml, hilang dari pending
```

---

## 7. Gotchas / jebakan yang harus dihindari

- **Jangan** menyalin aturan append-edge di script; ekstrak **satu** penulis dari
  `review_queue` (dua salinan → `soft` & `hard` menyimpang diam-diam).
- **Jangan** membuat `load_edges`/loop membaca `edges.pending.yaml` demi "kelengkapan" —
  itu justru pintu yang mengunci Bryant dari edge yang belum ditinjau (seluruh alasan
  lajur pending ada).
- **Jangan** menyalakan `edge_type: hard` di endpoint/prompt sebelum 2 & 3 hijau
  (kebocoran sebagian yang diperingatkan §1).
- **Jangan** menaruh state pending di `job.json`/DB (design §2/§6 menolaknya) — `queued_at`
  fana atau ganda = klok 7-hari tak bisa dipercaya.
- Veto ulang & promosi ganda **harus idempoten** — script bisa dijalankan kapan saja,
  berkali-kali, tanpa merusak berkas. Veto ulang selalu berhasil dan menimpa (§2 keputusan 4).
