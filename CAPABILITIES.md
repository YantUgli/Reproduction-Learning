# 📋 Apa yang Bisa Dilakukan Sistem Ini?

Sistem ini adalah **aplikasi belajar coding untuk satu orang** (Bryant), dibangun untuk menjawab pertanyaan yang lebih ketat daripada kebanyakan platform belajar: bukan "apakah kamu sudah *membaca* materinya?", tapi **"bisakah kamu *memproduksi ulang* kodenya dari nol, tanpa bantuan AI?"**. Setiap topik disajikan sebagai tantangan menulis kode kecil yang diperiksa dengan menjalankan kode itu sungguhan (bukan dinilai tebak-tebakan atau dinilai oleh AI). Sistem ini juga punya bagian "peta belajar" (Library) yang membantu Bryant menemukan sumber belajar resmi dan mencatatnya, serta bagian "dapur konten" (Forge authoring) yang memakai AI untuk *membantu membuat* soal-soal baru — tapi selalu dengan pemeriksaan mesin sebelum soal itu boleh dipakai.

---

## ✅ Fitur yang Sudah Jalan

### 1. Loop belajar inti: pudarkan bantuan sampai bisa sendiri
Setiap topik ("node") punya 4 tingkat bantuan yang makin lama makin sedikit:
- **L3 — Contoh lengkap**: Bryant melihat solusi jadi yang sudah beranotasi, sebagai contoh.
- **L2 — Latihan berkerangka**: kerangka kode sudah ada, bagian inti kosong untuk diisi.
- **L1 — Hanya spesifikasi**: cuma nama fungsi & deskripsi tugas, tanpa kerangka.
- **L0 — Verifikasi murni**: editor kosong, soal beda variasi dari yang dilihat sebelumnya, ada batas waktu (timebox), dan inilah yang benar-benar "dihitung" sebagai bukti bisa.

Contoh konkret: Bryant belajar topik "pagination" di FastAPI. Ia lihat contoh lengkap (L3), coba isi kerangka (L2), lalu coba dari spesifikasi kosong (L1), dan akhirnya diuji dengan soal variasi berbeda tanpa bantuan apa pun (L0). Hanya L0 yang menentukan status "sudah bisa".

### 2. Penilaian otomatis dengan menjalankan kode sungguhan
Kode yang ditulis Bryant dieksekusi betulan (bukan ditebak benar/salah oleh AI). Ada 3 jenis pemeriksaan tergantung topiknya:
- **unit_test** — untuk topik FastAPI: kode dijalankan dan diuji dengan test Python (pytest).
- **dom_behavior** — untuk topik React: kode dijalankan di lingkungan browser tiruan (jsdom) dan diuji dengan vitest.
- **value_assert** — untuk topik Machine Learning: hasil hitungan numerik dibandingkan dengan jawaban acuan (dengan toleransi kesalahan kecil yang wajar).

Hasilnya selalu **PASS** atau **FAIL** — tidak ada nilai abu-abu, dan pesan error/output test ditampilkan apa adanya ke Bryant supaya ia bisa belajar dari kegagalannya.

### 3. Editor kode tanpa bantuan AI (sandbox)
Editor kode di layar verifikasi (Monaco, seperti di VSCode) **sengaja mematikan semua fitur pintar**: tidak ada auto-complete cerdas, tidak ada saran kode, tidak ada Copilot. Ini memastikan saat "diuji", Bryant betul-betul menulis sendiri.

### 4. Pemahaman diuji dengan pertanyaan berjawaban pasti (bukan esai)
Setelah lolos test kode, kadang muncul "comprehension probe" — pertanyaan pilihan ganda tipe "tebak output", "cari bug", atau "telusuri alur kode" yang jawabannya pasti benar/salah (diperiksa string cocok-tidaknya di server, bukan dinilai AI). Kalau kode lolos tapi jawaban probe salah, sistem mencatat "produksi terbukti, tapi pemahamannya masih rapuh" — dan ini memperlambat jadwal pengulangannya (lihat poin 6).

### 5. Placement: menemukan level awal tanpa bertanya
Alih-alih bertanya "kamu sudah bisa apa?" (yang jawabannya sering tidak akurat), sistem memberi Bryant serangkaian tantangan dari yang paling sulit/hilir ke yang paling dasar, dan **berhenti di soal pertama yang berhasil ia kerjakan dari nol**. Itulah titik awal belajarnya — ditemukan lewat bukti, bukan pengakuan sendiri.

### 6. Penjadwalan pengulangan otomatis (spaced repetition)
Sistem memakai algoritma FSRS (metode pengulangan berjarak yang sudah teruji, bukan buatan sendiri) untuk menjadwalkan kapan sebuah topik perlu direview lagi supaya tidak lupa. Topik yang baru lolos perlu diulang lebih cepat; topik yang sering lolos berturut-turut jaraknya makin panjang. Kalau saat review gagal, topik itu turun status jadi "lapsed" (luntur) dan mulai dari jadwal pendek lagi.

### 7. Dashboard & peta progres
Halaman utama menampilkan: persentase "reproduce-without-AI" (berapa persen usaha verifikasi yang lolos tanpa bantuan), jumlah topik yang sudah dikuasai penuh (mastered), berapa topik yang jatuh tempo direview hari ini, dan daftar semua topik dikelompokkan per domain (FastAPI / React / ML) dengan status masing-masing (terkunci / tersedia / sudah dikuasai / dsb).

### 8. Materi bantuan yang hanya muncul setelah gagal ("gerbang 403")
Kalau Bryant gagal mengerjakan sebuah topik, barulah ia boleh membuka penjelasan tambahan (materi just-in-time) untuk topik itu. **Materi ini terkunci di server** — bukan cuma disembunyikan di tampilan — sehingga tidak bisa dibaca dulu sebelum mencoba. Ini sengaja dirancang supaya sistem tidak berubah jadi "buku bab" yang tinggal dibaca.

### 9. Library: peta belajar bersitasi (bukan buku bacaan)
Ada bagian terpisah bernama "Library" yang berisi catatan, kerangka course, dan peta jalan belajar yang ditulis Bryant sendiri (dibantu proses AI yang diawasi ketat). Library **tidak berisi penjelasan panjang buatan AI** — hanya kerangka, catatan asli Bryant, dan kutipan-kutipan yang tertaut ke sumber resmi (dokumentasi asli, dsb). Progres di halaman ini dihitung dari **"berapa yang sudah dibuktikan bisa dikerjakan"**, bukan "berapa yang sudah dibaca" — jadi kalaupun Bryant membaca semua catatan, angkanya tidak akan naik sebelum ia benar-benar mengerjakan topiknya dan lolos.

### 10. Dapur konten berbantuan AI (Forge authoring), dengan pemeriksaan berlapis
Ada sistem di belakang layar yang memakai Claude Code untuk membantu membuat soal-soal baru, variasi baru, atau menghubungkan entri Library ke topik baru di Forge. **AI tidak pernah langsung memutuskan soal itu baik atau tidak** — semua hasil kerja AI harus lolos serangkaian pemeriksaan otomatis dulu (dijalankan kodenya, dicek soal kosong pasti gagal, dicek kerangka soal pasti belum bisa lolos begitu saja, dicek kutipan sumbernya benar-benar ada kata-katanya di sumber asli) sebelum masuk ke sistem. Fitur ini bisa dimatikan sepenuhnya tanpa mengganggu fitur belajar inti (poin 1–8).

### 11. Meja audit kurikulum (bukan pengawasan manual per soal)
Alih-alih Bryant/pengelola harus menyetujui satu per satu setiap soal baru sebelum dipakai, sistem memakai data pemakaian nyata (berapa kali lolos, berapa kali gagal, berapa lama dikerjakan dibanding perkiraan) untuk **menandai** topik yang kelihatan bermasalah (misalnya "lolos 100% tanpa pernah gagal" = kemungkinan terlalu mudah/trivial, atau "tak pernah lolos" = kemungkinan rusak). Pengelola tinggal melihat daftar tertanda ini dan memutuskan mana yang perlu dicabut.

---

## 🔌 Daftar Endpoint / Aksi yang Tersedia

| Aksi yang Bisa Dilakukan | Cara Aksesnya | Keterangan Singkat |
|---|---|---|
| Melihat daftar semua topik & statusnya | `GET /nodes` | Dipakai untuk peta progres di dashboard |
| Melihat detail satu topik | `GET /nodes/{id}` | Nama, deskripsi, status, level yang tersedia |
| Membuka satu tingkat bantuan (L3–L0) | `GET /nodes/{id}/level/{level}` | Isi soal, kode kerangka, atau editor kosong sesuai level |
| Membuka materi bantuan setelah gagal | `GET /nodes/{id}/explanation` | Ditolak (403) kalau belum pernah gagal di topik itu |
| Mengambil pertanyaan pemahaman | `GET /nodes/{id}/probe` | Pertanyaan tebak-output/cari-bug, tanpa jawaban ikut terkirim |
| Mengirim kode untuk dinilai | `POST /attempts` | Jantung sistem: kode dijalankan, hasil PASS/FAIL dikembalikan |
| Melihat riwayat percobaan suatu topik | `GET /nodes/{id}/attempts` | Semua usaha yang pernah dikirim untuk topik itu |
| Menjawab pertanyaan pemahaman | `POST /probes/answer` | Cek jawaban benar/salah, lalu jadwal pengulangan diperbarui |
| Memulai sesi pencarian level awal | `POST /placement/start` | Mulai rangkaian tantangan menurun untuk menemukan titik mulai |
| Melihat status sesi pencarian level | `GET /placement/{id}` | Progres sesi placement yang sedang berjalan |
| Mengirim jawaban di sesi pencarian level | `POST /placement/{id}/submit` | Lanjut ke tantangan berikutnya atau berhenti kalau lolos |
| Melihat topik yang perlu direview hari ini | `GET /review/due` | Daftar topik jatuh tempo pengulangan |
| Mengambil soal review (variasi baru) | `GET /review/{id}/challenge` | Selalu soal berbeda dari yang terakhir dikerjakan |
| Mengirim jawaban review | `POST /review/submit` | Menilai kode; kalau gagal, langsung memutuskan hasil |
| Menjawab pertanyaan pemahaman saat review | `POST /review/probe` | Menentukan jadwal pengulangan berikutnya |
| Melihat ringkasan statistik belajar | `GET /stats` | Angka-angka untuk dashboard (KPI) |
| Melihat progres Library (peta belajar) | `GET /library/progress` | Persen "sudah dibuktikan bisa", per course/modul |
| Memicu AI membuat materi penjelasan | `POST /authoring/r3` | Bagian dapur konten — perlu topik yang pernah gagal dulu |
| Memicu AI membuat variasi soal baru | `POST /authoring/r4` | Bagian dapur konten — hasilnya harus lolos pemeriksaan mesin |
| Memicu AI membuat topik baru dari Library | `POST /authoring/node` | Menautkan entri peta belajar jadi topik baru yang bisa dikerjakan |
| Memicu AI mencari hipotesis dari kode | `POST /authoring/r2` | Membaca kode proyek lain untuk usulan topik (belum jadi verdict) |
| Melihat daftar pekerjaan AI (jobs) | `GET /authoring/jobs` | Status tiap permintaan pembuatan konten oleh AI |
| Melihat detail satu pekerjaan AI | `GET /authoring/jobs/{id}` | Isi lengkap + file yang akan diubah |
| Menyetujui hasil kerja AI secara manual | `POST /authoring/jobs/{id}/approve` | Jalur manual (kalau mode promosi-otomatis dimatikan) |
| Menolak hasil kerja AI | `POST /authoring/jobs/{id}/reject` | Menolak dengan alasan |
| Melihat meja audit kurikulum | `GET /authoring/audit` | Topik/edge yang ditandai mencurigakan dari data pemakaian |
| Melihat status integrasi AI | `GET /authoring/status` | Menyala/mati, jumlah pekerjaan per status |

---

## 🚧 Yang Masih Dalam Pengerjaan

- **Tombol "pensiunkan topik"** di meja audit sudah dirancang tampilannya, tapi belum ada endpoint backend yang menjalankannya — tombolnya sengaja dinonaktifkan (bukan pura-pura berfungsi).
- **Tombol "tetapkan arah domain" (destination)** di meja audit juga sudah dirancang tapi belum punya endpoint backend — sama, dinonaktifkan sengaja.
- **Ketiga domain (FastAPI, React, ML) belum punya "destination" (arah tujuan) yang ditetapkan** — ini satu-satunya keputusan yang memang sengaja menunggu manusia, bukan bug.
- **Deteksi topik yang isinya tumpang-tindih (duplikat)** sempat dicoba tapi dibatalkan karena aturannya salah-tuduh — belum ada gantinya.
- **Bukti otomatis bahwa satu topik benar-benar prasyarat topik lain** (dari kemiripan kode) diturunkan jadi laporan saja, bukan pemeriksaan yang memblokir — karena hasil ujicobanya banyak salah-tuduh.
- ⚠️ Perlu verifikasi: apakah node hasil pembuatan otomatis via `/authoring/node` (poin 10 di atas) sudah pernah benar-benar berhasil selesai sampai masuk sistem — catatan internal proyek menyebut ada percobaan yang masih terbentur limit teknis (bukan gagal pemeriksaan mutu).

---

## 📊 Seberapa Jauh Progresnya?

- **Loop belajar inti (topik → level bantuan → verifikasi → dikuasai)**: ~95% selesai — jalur utamanya lengkap dan sudah teruji.
- **Penilaian otomatis multi-domain (FastAPI/React/ML)**: ~90% selesai — ketiga jenis pemeriksaan sudah berjalan; jenis pemeriksaan lain (mis. untuk soal arsitektur) sengaja belum dibangun karena belum ada topiknya.
- **Penjadwalan pengulangan otomatis (spaced repetition)**: ~90% selesai — sudah lengkap dan teruji.
- **Pencarian level awal (placement)**: ~90% selesai.
- **Dashboard & statistik**: ~85% selesai.
- **Library (peta belajar & catatan)**: ~75% selesai — mekanismenya lengkap, tapi isinya baru sedikit (baru 2 course, sekitar 11 berkas catatan).
- **Dapur konten berbantuan AI (Forge authoring)**: ~75% selesai — pipeline pembuatan soal & materi sudah lengkap dengan pemeriksaan mesin; pembuatan topik baru dari Library (fitur terbaru) masih perlu lebih banyak bukti berjalan mulus.
- **Meja audit kurikulum**: ~60% selesai — bagian "melihat dan menandai" sudah jalan; bagian "bertindak" (pensiun, tetapkan arah) belum ada tombol yang benar-benar berfungsi.

Kurikulum yang sudah ada saat ini: **19 topik** (13 FastAPI, 3 React, 3 Machine Learning), semuanya sudah lolos pemeriksaan mutu otomatis.

---

## 🗺️ Gambaran Besar Alur Penggunaan

1. **Bryant membuka dashboard.** Ia melihat berapa persen usaha "tanpa bantuan AI"-nya berhasil, berapa topik sudah dikuasai, dan apakah ada yang perlu direview hari ini.
2. **Kalau baru mulai**, Bryant menjalankan sesi *placement*: diberi soal dari yang sulit ke yang mudah, sampai ketemu soal pertama yang berhasil ia kerjakan sendiri. Itu jadi titik awalnya, dan prasyarat-prasyaratnya otomatis terbuka untuk dicoba.
3. **Bryant memilih satu topik** dari peta progres dan membuka sesi belajarnya: lihat contoh lengkap (L3) → coba isi kerangka (L2) → coba dari spesifikasi kosong (L1) → **diuji murni tanpa bantuan (L0)** dengan batas waktu.
4. **Kode yang ditulis dijalankan sungguhan** oleh sistem. Kalau lolos di level L0, kadang muncul pertanyaan pemahaman (tebak output/cari bug) untuk memastikan bukan sekadar coba-coba yang kebetulan benar.
5. **Kalau lolos bersih**, topik itu berstatus "acquired" dan masuk jadwal pengulangan otomatis. Setelah beberapa kali lolos berturut-turut dengan jarak waktu, statusnya naik jadi "mastered".
6. **Kalau gagal**, Bryant boleh membuka materi bantuan (yang baru muncul setelah kegagalan ini), lalu bisa naik lagi ke level bantuan yang lebih tinggi dan coba ulang.
7. **Setiap hari**, Bryant mengecek halaman Review untuk mengerjakan ulang topik-topik yang jatuh tempo — selalu dengan variasi soal berbeda supaya tidak sekadar menghafal jawaban.
8. **Di sisi lain**, Bryant (atau pengelola) bisa membuka Library untuk menyusun peta belajar topik baru, mencatat sumber-sumber resmi, lalu memakai dapur konten AI untuk mengusulkan soal-soal baru — yang semuanya harus lolos pemeriksaan mesin dulu sebelum bisa dikerjakan seperti topik lain.
9. **Sesekali**, pengelola membuka meja audit untuk melihat topik mana yang datanya menunjukkan tanda mencurigakan (terlalu mudah, tak pernah lolos, dsb.) dan memutuskan mana yang perlu diperbaiki atau dicabut.
