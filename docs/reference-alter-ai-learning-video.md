# Referensi — "How To Become Dangerously Self-Educated With AI (for free)" (kerangka ALTER)

> **Status:** dokumen referensi/analisis, **bukan** milestone dan **bukan** keputusan.
> Tidak mengubah roadmap atau invariant apa pun. Ia merekam ide dari sebuah video
> eksternal + memetakan di mana ia bertemu dan berpisah dengan proyek ini, supaya
> diskusi lanjutan punya jangkar konteks yang stabil.
>
> Sumber kebenaran produk tetap [`../PRD-reproduction-learning-engine-v1.2.md`](../PRD-reproduction-learning-engine-v1.2.md)
> dan invariant di [`../CLAUDE.md`](../CLAUDE.md) §1. Kalau ada konflik, **invariant menang** —
> dokumen ini tidak berwenang melonggarkannya.

- **Sumber:** YouTube — *How To Become Dangerously Self-Educated With AI (for free)*
  (`https://youtu.be/3k6fR5EdLAo`)
- **Dicatat:** 2026-08-27
- **Kenapa dicatat:** Bahan diskusi. Video ini menawarkan kerangka **5 peran AI**
  (ALTER) untuk belajar otodidak. Berguna sebagai sumber fitur yang *mungkin* boleh
  dipinjam ke M5, sekaligus bukti-tanding untuk menguji ketahanan invariant.

---

## 1. Ringkasan ide video (apa yang dia klaim)

**Diagnosis masalah.** Materi kelas dunia (Harvard, MIT, Stanford, Oxford, dst.)
sudah gratis di internet, tapi **88% yang mendaftar tidak menyelesaikannya**. Yang
membuka inteligensi sejati bukan aksesnya, tapi **rasa ingin tahu + dorongan diri
(*self-driven*)**. Masalahnya bukan ketersediaan, tapi ketiadaan struktur & bimbingan
personal yang biasa didapat di universitas mahal.

**Solusi yang diusulkan.** Rakit "**University in a Box**": pakai AI untuk mengisi
lima peran yang biasanya disediakan institusi, dirangkum jadi akronim **ALTER**.

**Kerangka ALTER — lima peran AI:**

1. **A — Advisor (penasihat akademik).** Merancang jalur belajar personal. Membuat
   **5 keputusan utama**:
   - *Destination* — tujuan akhir yang mau dicapai.
   - *Baseline* — tingkat pemahaman awal pengguna sekarang.
   - *Sequencing* — urutan topik paling tepat untuk dipelajari.
   - *Cut List* — hal yang boleh diabaikan dulu.
   - *Milestones* — **output yang membuktikan penguasaan materi.**
   Alat: prompt gaya wawancara berurutan ("*act as my elite academic advisor…*"),
   model multimodal (Gemini) untuk topik visual, integrasi ke Google Docs/Calendar
   via Zapier MCP agar jadwal & tugas otomatis tercatat.

2. **L — Librarian (pustakawan).** Menyaring ribuan sumber → memilih ~10 sumber
   berkualitas tinggi (*signal* vs *noise*). Dilandasi temuan Stanford: 82% siswa
   SMP tak bisa membedakan konten bersponsor dari berita asli. Alat: fitur *deep
   research* (Gemini/Claude/ChatGPT); unggah materi ke **NotebookLM** untuk mengunci
   AI pada *ground truth*; ubah dokumen jadi format interaktif (audio/podcast).

3. **T — Tutor (pengajar pribadi 1-on-1).** Beda dari *teacher*: tutor
   **mendiagnosis kebingungan spesifik** satu-lawan-satu. Dilandasi **two-sigma
   problem** (Benjamin Bloom, 1980-an): siswa dengan bimbingan privat 1-on-1
   mengungguli 98% siswa kelas konvensional. Alat: mode suara (Gemini/ChatGPT
   Voice) untuk tanya-jawab; dua perintah utama: **"Teach me"** dan **"Test me"**.

4. **E — Editor (penyunting & penguji).** Analogi tim insinyur F1 yang memantau
   ribuan data real-time untuk koreksi kecil tiap putaran. Peran: umpan balik
   instan — menguji logika, menemukan kelemahan argumen, memotong pengulangan,
   memperjelas struktur pemikiran/karya.

5. **R — Roommate (teman sekamar / perspektif silang).** Nilai dari punya *range*.
   Contoh Pixar: animator ikut kelas seni pahat, staf akuntansi & keamanan ikut
   kelas menggambar — memperluas cara pandang. Instruksi ke AI: menghubungkan dua
   bidang tak berkaitan (mis. seni memasak ↔ keuangan; pola pikir pemusik jazz ↔
   membangun tim).

**Tesis penutup (perumpamaan perahu).** Seorang murid buru-buru bertanya perahu
mana yang paling cepat menyeberangi sungai. Jawab si pengayuh tua: *"Perahu paling
cepat adalah perahu yang kamu naiki dan mulai kamu dayung."* → eksekusi & konsistensi
mengalahkan pemilihan alat yang sempurna.

---

## 2. Di mana ia **sepakat** dengan proyek ini

- **Akses ≠ belajar.** Premis videonya (88% tak menyelesaikan materi gratis) sejalan
  dengan penolakan proyek pada "konsumsi materi" sebagai ukuran (CLAUDE.md §1.1).
  Keduanya menolak "menonton/membaca = menguasai".
- **Advisor: Baseline + Sequencing = DAG berurutan.** "Ukur pemahaman sekarang, lalu
  urutkan topik" praktis identik dengan daftar node berurutan proyek (CLAUDE.md §1:
  "DAG di v1 cukup daftar node berurutan di file data").
- **Advisor: Milestones = output yang membuktikan penguasaan.** Ini titik temu
  **paling penting**. Videonya sendiri menyebut ukuran keberhasilan = *output*, bukan
  konsumsi — persis semangat `reproduce-without-AI`. Bedanya: video tidak pernah
  meng-operasionalkannya (lihat §4).
- **Librarian: grounding ke *ground truth*.** Ide "kunci AI pada sumber
  terverifikasi" sejalan dengan kewajiban **sitasi verifiable** pada materi
  just-in-time (CLAUDE.md §5, R3).
- **Cut List.** "Buang dulu yang tak perlu" beririsan dengan disiplin §8 (menolak
  membangun yang bukan inti loop reproduksi).

---

## 3. Di mana ia **berpisah total** (dan kenapa itu penting)

Perbedaan intinya satu pertanyaan: **apa bukti seseorang sudah belajar?** Dari lima
peran ALTER, **empat** (Advisor, Librarian, Tutor, Editor) adalah mesin **konsumsi
& coaching** — memuluskan *jalan masuk* ke pemahaman. Hanya **satu klausa**
(Advisor → *Milestones*) yang menyentuh **produksi**, dan itu pun tidak pernah
dijadikan gate konkret.

| Dimensi | Video (ALTER) | Proyek ini (invariant) |
|---|---|---|
| Ukuran belajar | Penjelasan tutor terasa dipahami + lolos "Test me" | `reproduce-without-AI`, diverifikasi eksekusi kode |
| Yang jadi **gate** | Tidak ada gate keras; "Test me" AI sebagai proksi | Hanya `Attempt` + hidden test |
| Peran AI | Perencana **+ pengajar + penguji + penilai argumen** | Pengusul hipotesis; **tak pernah** penilai (§1.2) |
| Pemahaman diperiksa via | "Test me" (AI yang menilai jawaban) | Comprehension probe **deterministik** (predict output / spot bug / trace) |
| Penilaian teks bebas | Ya — Editor menilai logika & kualitas argumen | Tidak pernah (§1.3); refleksi teks tak pernah jadi gate |

**Titik pecah paling tajam:**

- **Tutor "Test me"** = AI menilai apakah jawaban pengguna benar → **AI-as-judge**,
  tabrak langsung invariant §1.2. Argumen *two-sigma* Bloom dipakai untuk menjual
  persis pintu masuk yang invariant ini tutup rapat.
- **Editor menilai argumen** = pemrosesan makna teks bebas → pintu masuk
  AI-sebagai-hakim, tabrak §1.3.

**Sifat retorika videonya.** Beatles, Aristoteles–Alexander, F1, Pixar, perumpamaan
perahu — ini **persuasi motivasional**, bukan spesifikasi rekayasa. Bahayanya bukan
pada idenya, tapi ia membuat "terasa belajar" terasa cukup. Itu **persis gravitasi
§1** ("consumption comfort") yang proyek ini lawan.

---

## 4. Kruks: klausa "Milestones" adalah lubang yang proyek ini isi

Video menyatakan ukuran keberhasilan = *output yang membuktikan penguasaan*, tapi
**berhenti sebagai vibe** — ia tak pernah mendefinisikan apa yang menjadikan sebuah
output "bukti", dan siapa/apa yang memutuskannya. Karena tak ada oracle deterministik,
keputusan itu bocor balik ke **Tutor/Editor** (AI yang menilai).

Proyek ini mengisi lubang tepat di situ: **milestone = sebuah `Attempt` yang hijau
di hidden test.** Bukti bukan "terasa paham", bukan "AI bilang benar" — melainkan
kode pengguna yang lolos eksekusi. Videonya menyediakan *kalimat yang benar*
(Milestones = output pembuktian); proyek ini menyediakan *mekanisme yang jujur*
untuk kalimat itu.

> Pertanyaan terbuka (belum diputuskan): peran **Advisor** menuntut *Sequencing*.
> Di proyek ini urutan (edge) **final** = sumber otoritatif + Isyah (§1.4), AI hanya
> **mengusulkan**. Sejauh mana usulan sequencing gaya-Advisor boleh dipakai sebelum
> diam-diam menggeser otoritas edge ke LLM? (Bahan diskusi, bukan keputusan.)

---

## 5. Yang **layak dipinjam** ke M5 — tanpa melanggar invariant

Semua tunduk pada [`M5-claude-code-integration`](milestones/M5-claude-code-integration.md)
& peran R1–R4 (CLAUDE.md §5). Tiap poin dengan garis merahnya.

1. **Dekomposisi 5-keputusan Advisor** (Destination / Baseline / Sequencing /
   Cut List / Milestones) sebagai **checklist untuk R1** (ekstraksi kandidat
   node/edge).
   - ✅ Boleh: memakainya sebagai kerangka usulan node/edge + memaksa klausa
     *Milestones* jadi konkret = `Attempt` hijau di hidden test.
   - ⛔ Jangan: menjadikan *Sequencing* Advisor sebagai edge **final** — itu tetap
     Isyah yang prune & tandai hard/soft (§1.4).

2. **Librarian sebagai R3** (materi just-in-time) dengan *grounding* ke sumber.
   - ✅ Boleh: menyusun penjelasan/worked example **bersitasi verifiable**; ide
     "kunci AI pada ground truth" memperkuat, bukan melemahkan, invariant sitasi.
   - ⛔ Jangan: materi panjang / "bab yang enak dibaca" sebagai inti produk
     (content library ditolak, §8).

3. **Roommate (perspektif lintas-bidang)** sebagai alat ideasi **tanpa gate**.
   - ✅ Boleh: memantik ide *transfer* — analogi lintas-bidang untuk memperkaya
     varian tantangan (yang menguji transfer lewat data uji berbeda).
   - ⛔ Jangan: menjadikannya penilaian apa pun; ini murni pemantik, bukan sinyal
     mastery.

4. **Semangat "optimasi sumber daya mental"** (offload logistik: perencanaan,
   pencarian, penjadwalan).
   - ✅ Boleh: offload **logistik** ke AI (menyusun kandidat, mencari sumber).
   - ⛔ Jangan: offload **penilaian**. Garis: logistik ya, verdict tidak.

---

## 6. Yang **harus ditolak** dari video (langsung tabrak invariant)

- **Tutor "Test me" sebagai penguji pemahaman** → AI-as-judge, tabrak §1.2.
- **Editor menilai kualitas logika/argumen (teks bebas)** → tabrak §1.3.
- **AI sebagai penentu learning path final** (Sequencing final) → §8; edge final =
  sumber otoritatif + Isyah (§1.4).
- **Ukuran keberhasilan = "penjelasan terasa dipahami"** → gravitasi "consumption
  comfort" yang dilawan §1.1.
- **Materi panjang / podcast interaktif sebagai inti belajar** → content library
  ditolak (§8).

---

## 7. Benang diskusi yang masih terbuka

1. Motivasi menonton: **uji ketahanan invariant** atau **cari fitur konkret** untuk M5?
2. Dekomposisi 5-keputusan Advisor — apakah cukup kuat dijadikan template resmi
   input R1, atau terlalu "generik motivasional" untuk domain kode?
3. Sampai mana usulan *Sequencing* gaya-Advisor boleh menyetir edge tanpa melanggar
   otoritas §1.4?
4. Peran **Editor** untuk kode: di proyek ini "editor" yang jujur sebenarnya =
   executor + grader (eksekusi), **bukan** AI. Perlukah ini ditegaskan eksplisit di
   M5 supaya tak ada yang menafsirkan "AI Editor" sebagai penilai?
