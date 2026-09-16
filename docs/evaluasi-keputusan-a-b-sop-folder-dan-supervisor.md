# Evaluasi Lanjutan — Dampak Keputusan A & B terhadap Kebutuhan 1 & 2

> **Status:** dokumen evaluasi/analisis, **bukan** milestone dan **bukan** keputusan final.
> Tidak mengubah roadmap atau invariant apa pun dengan sendirinya. Merekam evaluasi dua
> keputusan desain baru (diajukan Isyah) terhadap dua kebutuhan fitur yang dievaluasi
> sebelumnya, berdasarkan kondisi kode & dokumen nyata per tanggal dicatat di bawah.
>
> Sumber kebenaran produk tetap [`../PRD-reproduction-learning-engine-v1.2.md`](../PRD-reproduction-learning-engine-v1.2.md)
> dan invariant di [`../CLAUDE.md`](../CLAUDE.md) §1. Kalau ada konflik, **invariant menang** —
> dokumen ini tidak berwenang melonggarkannya.
>
> Lanjutan dari: [`evaluasi-kebutuhan-generate-materi-dan-upload-catatan.md`](evaluasi-kebutuhan-generate-materi-dan-upload-catatan.md).
> — **Dicatat:** 2026-09-16

---

## Konteks

Isyah membuat dua keputusan desain untuk membuka blokir yang ditemukan di evaluasi
sebelumnya:

- **Keputusan A — SOP Struktur Folder**, menggantikan batasan "satu file per panggilan"
  di `note-refine`: eksekusi bertahap per submateri (satu folder = satu sesi), AI hanya
  membaca folder spesifik dan terisolasi.
- **Keputusan B — Isyah sebagai Supervisor**, menggantikan larangan mutlak AI menentukan
  urutan: AI boleh mengusulkan (bahkan membuat keputusan awal) tentang urutan/prasyarat/
  struktur modul, tapi hasilnya menunggu review Isyah (Terima / Revisi / Tolak) sebelum
  dieksekusi.

Dievaluasi berdasarkan pembacaan langsung: SKILL.md `note-refine`, `course-intake`,
`learn-intake`, `forge-node`; `library/README.md`; `backend/app/routers/authoring.py`;
`backend/app/claude/review_queue.py`; `scripts/library_scaffold.py` (termasuk flag
`--dry-run`, yang generik untuk semua `kind` spec, bukan khusus `course-intake`).

---

## Keputusan A: SOP Struktur Folder

### 1. Apakah cukup sebagai pengaman pengganti "satu file per panggilan"?

**Sebagian.** Struktur foldernya sendiri **sudah beku dan sudah punya pengamannya** —
bukan hal baru: `library/README.md` mengunci bentuk
`library/<course>/<NN-modul>/<materi>.md` + 8 field frontmatter wajib, ditegakkan
`course-intake` (create-only scaffolder) dan `verify_library.py` (validator baca:
`source_refs`/`node_ids` ⊆ registry, dan untuk `type: roadmap` ada gerbang kutipan
verbatim). SOP folder tidak menambah apa pun ke lapisan ini — lapisan ini sudah menjaga
"di mana file boleh mendarat" dan "apakah id yang disebut nyata".

Yang **tidak** dijaga oleh SOP folder: apakah `note-refine` menambah isi yang tak diminta
Bryant. Batasan "satu file per panggilan" awalnya bukan (hanya) penjaga salah-tempat — ia
eksplisit dicatat di CLAUDE.md §7 2026-09-04 sebagai **"guard lunak = disiplin skill +
Bryant baca diff"**, karena L2 memang menulis ke stub yang *sudah ada isinya* (overwrite,
bukan create-only), jadi git-diff adalah satu-satunya rem. Membatch N file dalam satu
panggilan tidak menghapus rem ini (git tetap undo-nya, persis preseden yang sudah diterima
di L2), tapi mengubah beban baca dari "1 diff per sesi" jadi "N diff per sesi" — itu
pergeseran beban review, bukan lubang keamanan baru.

**Catatan yang memperbaiki bacaan evaluasi pertama:** kalau yang dimaksud "upload catatan"
adalah Bryant **sudah menulis sendiri** file-file `.md` itu (bukan AI mengarang isi dari
topik), maka batch ini secara substansi = "note-refine, tapi bahan mentahnya dibaca dari
file, bukan di-paste ke chat satu-satu" — isi tetap 100% tulisan Bryant, kontrak "editor,
bukan penulis" tidak tersentuh. Ini jauh lebih aman daripada asumsi di evaluasi pertama.

### 2. Struktur folder yang paling masuk akal

Jangan bikin struktur baru — sambungkan ke bentuk yang sudah beku:

```
library/_inbox/<course-slug>/<NN-modul>/*.md   # mentah, tulisan Bryant, tanpa frontmatter wajib
library/<course-slug>/<NN-modul>/*.md          # hasil course-intake (stub) → target overwrite note-refine
```

"Satu submateri per sesi" (contoh kasus Bryant: "Supervised Learning" dulu, baru "Neural
Network") persis dipetakan ke **satu folder `_inbox/<course>/<NN-modul>/`** = satu unit
kerja. Ini juga yang membuat "AI membaca folder spesifik & terisolasi" jadi literal benar:
AI dibatasi baca satu subfolder, bukan `library/` penuh atau seluruh project.

### 3. Yang perlu dibangun/diubah

- **Tidak ada** perubahan backend/schema/DB — `verify_library.py --capture` sudah
  per-file dan idempoten; memanggilnya N kali dalam satu sesi skill secara mekanis
  identik dengan N sesi terpisah.
- **SKILL.md `note-refine` perlu direvisi**: ganti "satu file per panggilan" jadi "satu
  folder submateri per panggilan, iterasi file-per-file di dalamnya, lapor tiap file
  (bukan ringkasan agregat)" — poin terakhir penting supaya rem "Bryant baca diff" tidak
  melemah diam-diam saat dibatch.
- **Konvensi `_inbox/` perlu didokumentasikan** (di `library/README.md`) — siapa yang
  menaruh file di sana (Bryant, manual, di luar skill mana pun) dan kapan AI boleh
  membacanya.
- Opsional (bukan wajib): wrapper kecil `--capture-many <folder>` di
  `verify_library.py` untuk laporan gabungan — kenyamanan, bukan kapabilitas baru.

### 4. Invariant lain yang bertabrakan?

Tidak ditemukan tabrakan baru. Justru §7 2026-09-04 (L2) sudah secara eksplisit menolak
"refuse-on-dirty-tree" (gerbang blokir per commit) karena dianggap terlalu berfriksi —
ini konsisten mendukung model "git sebagai rem", bukan gerbang per-file. Satu-satunya
risiko murni prosedural (bukan arsitektur): SOP wajib eksplisit meminta diff per file
ditampilkan, kalau tidak "Bryant baca diff" jadi janji kosong saat volumenya naik.

**Kesimpulan Keputusan A:** cukup untuk membuka bagian *mekanisme* dari batasan lama
(tempat file, isolasi folder) — **Kecil**, murni SOP + edit SKILL.md, nol kode backend.

---

## Keputusan B: Isyah Supervisor (bukan Eksekutor)

### 1. Mekanisme review yang sudah ada dan bisa diperluas?

**Sebagian sudah ada, sebagian tidak — dan yang ada terpisah di dua jalur berbeda:**

- **Jalur Forge (authoring jobs, M5/M7):** `POST /authoring/jobs/{id}/approve`
  (= "Terima") dan `/reject` (= "Tolak") **masih ada di kode** (`review_queue.py`),
  hanya dibypass default sejak M7 (`CLAUDE_AUTO_PROMOTE`). `GET /authoring/jobs/{id}`
  sudah mengembalikan `existing` — diff antara isi lama vs artifact baru, persis
  "format mudah di-review" yang diminta. **Yang TIDAK ada: "Revisi bagian tertentu".**
  Semua promosi di `review_queue.py` bersifat **semua-atau-tak-ada**
  (`_promote_node_genesis` eksplisit: node setengah jadi merusak seluruh domain) —
  tidak ada mekanisme "terima 3 dari 5 modul, revisi 2".
- **Jalur Library (course-intake/learn-intake):** tidak pakai job/approve sama sekali.
  AI merakit `spec.yaml` → scaffolder menulis langsung ke `library/` (create-only) →
  git adalah rem-nya. Tapi scaffolder **sudah punya flag `--dry-run`** (generik,
  berlaku untuk `kind: outline` maupun `kind: roadmap`) yang melaporkan path apa yang
  AKAN ditulis tanpa menulis — pratinjau siap pakai yang belum dijadikan langkah SOP
  wajib.

Kesimpulan: "Ya/Tidak" bisa langsung dipetakan ke pola yang sudah ada di kedua jalur.
**"Revisi" tidak ada mekanismenya di mana pun** dan harus dibangun/didefinisikan baru —
atau, kalau reviewnya terjadi dalam satu sesi Claude Code langsung (bukan async terpisah
waktu), "revisi" itu sebenarnya cuma percakapan iteratif yang sudah berjalan hari ini
tanpa kode tambahan sama sekali. Ini bergantung apakah Keputusan B dimaksudkan sebagai
flow **sinkron dalam sesi** atau **async lintas waktu** (job dibuat, Isyah review nanti)
— dokumen permintaan tidak menyebutkan ini.

### 2. Yang perlu dibangun agar usulan urutan + struktur modul mudah di-review

- **Kalau menempel di jalur Library** (lebih pas secara konsep — urutan/struktur adalah
  konsep course, bukan konsep node/grader): jadikan `--dry-run` + isi `spec.yaml` (sudah
  manusiawi karena YAML) sebagai langkah SOP wajib sebelum scaffolder dijalankan
  sungguhan. Nyaris nol kode — hanya satu langkah eksplisit di SKILL.md: "tampilkan
  spec.yaml + hasil `--dry-run`, tunggu Ya/Tidak/Revisi sebelum menjalankan tanpa
  `--dry-run`".
- **Titik yang benar-benar butuh keputusan baru: edge/urutan prasyarat.** Baca literal
  Keputusan B ("AI boleh mengusulkan DAN **membuat keputusan awal** tentang urutan,
  prasyarat") ambigu antara dua makna dengan konsekuensi arsitektur sangat berbeda:
  1. AI mengusulkan edge `soft` seperti sekarang (L4 `_append_soft_edge` — tak mengunci
     apa pun), Isyah lalu **secara manual** menaikkan sebagian jadi `hard` dengan
     mengedit `edges.yaml` langsung — ini **sudah menjadi cara kerja Isyah hari ini**
     (file itu penuh komentar "difinalkan Isyah 2026-08-22 ..."). **Nol kode baru.**
     §1/§5.1 tidak tersentuh sama sekali: Isyah tetap satu-satunya yang menandai `hard`.
  2. Urutan/edge usulan AI dianggap berlaku (bahkan sebagai `hard`) kecuali Isyah
     menolaknya (default opt-out, bukan opt-in) — ini **membalik** §5.1 ("Bryant/AI
     tidak pernah menyentuh definisi graf prerequisite" berubah jadi "AI menyentuh,
     manusia hanya veto") dan **butuh perubahan invariant tertulis**, bukan cuma fitur
     baru.

  Dokumen permintaan tidak cukup eksplisit menentukan (1) atau (2).
  ⚠️ **Perlu keputusan Isyah secara sadar** — evaluasi ini mengasumsikan (1) sebagai
  bacaan yang konsisten dengan seluruh riwayat §7 (terutama entri 2026-09-01 yang
  eksplisit menolak edge hard dari usulan AI), dan itulah yang membuat estimasi di
  bawah relatif kecil.

### 3. Perlu perubahan PRD formal, atau catatan CLAUDE.md §7?

Ikuti preseden yang sudah berulang kali dipakai di repo ini untuk perubahan sekelas ini
(termasuk yang terbesar, pencabutan approve-blokir 2026-08-31): **catatan CLAUDE.md §7**,
bukan edit PRD — PRD tetap "kebenaran produk yang tak berubah", §7 menyerap evolusi
operasional. Ini berlaku **hanya jika Keputusan B dibaca sebagai makna (1) di atas** —
soft-propose + human-hand-promote, yang tidak mengubah teks §1/§5.1 sama sekali, cuma
mendokumentasikan alur baru di atasnya. Kalau dibaca sebagai makna (2), itu mengubah
*siapa yang berwenang secara default* atas graf prasyarat — itu levelnya perubahan
invariant §1/§5.1 dan semestinya tercermin di PRD, bukan cuma catatan §7 (§7 sendiri
berulang kali menegaskan format "alasan + alternatif ditolak" justru untuk hal sebesar
ini).

### 4. Dampak ke estimasi kompleksitas

**Kebutuhan 1:** tidak berubah pada bagian intinya — "materi bacaan di muka" tetap
bertabrakan langsung dengan gerbang 403 (Keputusan A/B tidak menyentuh itu sama sekali),
jadi tetap **Besar**. Yang berubah: satu dari empat risiko yang tadinya "belum
diputuskan" (orkestrasi "satu topik → beberapa node berurutan") sekarang punya jalur
konkret — AI usul urutan lengkap + edge soft sekali jalan, Isyah review sekali (spec.yaml
+ dry-run), baru `forge-node` dipanggil berkali-kali sesuai rencana yang disetujui.
Sub-bagian ini turun dari "terbuka" jadi **Sedang** (butuh langkah SOP review eksplisit,
nol perubahan skema/gate) — tapi tidak menurunkan rating keseluruhan Kebutuhan 1 karena
blocker 403-nya tetap berdiri sendiri.

**Kebutuhan 2:** di sinilah dampaknya besar. Estimasi lama untuk versi otomatis ("Besar")
ditopang tiga blocker bertumpuk: (a) tak ada mekanisme batch-ingest, (b) graf prasyarat
otomatis-AI bertentangan §1/§5.1, (c) L4 belum terbukti stabil.

- (a) → turun jadi **Kecil** lewat Keputusan A (SOP + edit skill, nol kode).
- (b) → **jika dibaca sebagai makna (1) di atas** (soft-propose, human hand-promotes via
  `edges.yaml`), ini sebetulnya bukan mekanisme baru — ia **sudah bisa dijalankan hari
  ini** dengan alur kerja Isyah yang sudah ada. Tidak menambah kompleksitas build sama
  sekali; hanya perlu didokumentasikan sebagai SOP resmi (Kecil).
- (c) → **tidak berubah oleh A maupun B.** Ini blocker independen: belum ada satu node
  pun yang benar-benar lahir lewat L4 (terhenti di `HTTP 429`, bukan ditolak gerbang),
  dan roadmap sendiri menaruh "tuntaskan acceptance L4" sebagai pekerjaan berikutnya
  setelah L5.

**Estimasi baru untuk versi otomatis Kebutuhan 2: turun dari Besar → Sedang**, dengan
syarat eksplisit: (i) makna Keputusan B untuk edge dikonfirmasi sebagai soft-propose +
human-hand-promote (bukan opt-out default), dan (ii) acceptance L4 dituntaskan lebih
dulu — Sedang di sini berarti "butuh milestone kecil (SOP inbox + langkah review eksplisit
di skill)", bukan "siap pakai hari ini", karena fondasinya (L4) sendiri belum terbukti
jalan sekali pun secara end-to-end.

---

## Ringkasan tabel

| | Kebutuhan 1 | Kebutuhan 2 (versi otomatis) |
|---|---|---|
| Estimasi sebelumnya | Besar | Besar |
| Estimasi setelah Keputusan A+B | **Besar** (403 masih menghalangi inti permintaan) | **Sedang** (turun signifikan, tapi digantung ketidakpastian L4 + makna edge di Keputusan B) |
| Blocker yang benar-benar hilang | tidak ada | batch-ingest (A), graf-prasyarat-otomatis *jika dibaca sebagai (1)* (B) |
| Blocker yang tetap berdiri | gerbang 403 untuk materi-di-muka | L4 belum terbukti stabil; makna Keputusan B untuk edge perlu diperjelas |

---

## Hal yang perlu diklarifikasi Isyah sebelum ini jadi rencana kerja

⚠️ **Perlu verifikasi/klarifikasi:**

1. Apakah Keputusan B untuk edge dimaksudkan sebagai *AI usul soft + Isyah manual
   promote lewat `edges.yaml`* (nol konflik invariant, nol kode baru) atau *urutan AI
   berlaku kecuali diveto* (mengubah §5.1, butuh amandemen PRD)?
2. Apakah review "Ya/Tidak/Revisi" terjadi sinkron dalam satu sesi Claude Code, atau
   async lintas waktu (menentukan apakah "Revisi" butuh mekanisme state-machine baru
   sama sekali, atau cukup percakapan iteratif yang sudah berjalan hari ini)?
