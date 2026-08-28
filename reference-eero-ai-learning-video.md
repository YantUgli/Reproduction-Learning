# Referensi — "How I Use AI to Learn Things" (Eero Alvar)

> **Status:** dokumen referensi/analisis, **bukan** milestone dan **bukan** keputusan.
> Tidak mengubah roadmap atau invariant apa pun. Ia merekam ide dari sebuah video
> eksternal + memetakan di mana ia bertemu dan berpisah dengan proyek ini, supaya
> diskusi lanjutan punya jangkar konteks yang stabil.
>
> Sumber kebenaran produk tetap [`../PRD-reproduction-learning-engine-v1.2.md`](../PRD-reproduction-learning-engine-v1.2.md)
> dan invariant di [`../CLAUDE.md`](../CLAUDE.md) §1. Kalau ada konflik, **invariant menang** —
> dokumen ini tidak berwenang melonggarkannya.

- **Sumber:** YouTube — *How I Use AI to Learn Things*, Eero Alvar
  (`https://youtu.be/kzcI5F4tGiU`)
- **Dicatat:** 2026-08-27
- **Kenapa dicatat:** Bahan diskusi. Videonya adalah *antitesis rapi* dari
  pendekatan proyek ini — berguna sebagai bukti-tanding untuk menguji ketahanan
  invariant, dan sebagai sumber fitur yang *mungkin* boleh dipinjam ke M5.

---

## 1. Ringkasan ide video (apa yang dia klaim)

**Diagnosis masalah.** Pembelajaran standar = relasi *many-to-many* antara pengajar
(guru/buku/kursus) dan siswa. Dua inefisiensi:
- **Satu pengajar → banyak siswa:** pengajaran massal tak bisa menyesuaikan diri
  dengan apa yang sudah/belum dipahami tiap individu.
- **Satu siswa → banyak sumber:** berpindah antar sumber memakan beban mental dan
  menurunkan rasa percaya pada materi, menghambat internalisasi.

**Solusi yang diusulkan.** Model *one-to-one*: satu siswa, satu "pengajar" AI yang
**mengagregasi** semua sumber ke satu antarmuka tepercaya, dengan verifikasi fakta
lewat agen pendukung.

**Dua prinsip sistem:**
1. *Optimasi pengajaran* — sesuaikan materi dengan pemahaman unik pengguna.
2. *Optimasi sumber daya mental* — pindahkan beban logistik (perencanaan,
   pencarian, verifikasi) ke AI agar pengguna fokus 100% pada kesulitan materi.

**Loop implementasi (Probe → Plan → Teach):**
1. **Probe** — ukur pemahaman via **kuis pilihan ganda** untuk memetakan yang sudah dikuasai.
2. **Plan** — AI menyusun jalur belajar, memverifikasi fakta lewat agen pendukung,
   membuat diagram **Mermaid** (klaim: memaksa AI bernalar logis).
3. **Teach** — mengajar langkah demi langkah + kuis berkala untuk memastikan
   pemahaman, "mencegah gaslighting diri sendiri", lalu mengunci lewat penerapan.

**Demo:** belajar *differential forms* di Obsidian — probing (mekanika → integral
garis → relativitas), rencana terstruktur, agen visualisasi SVG, lalu langkah demi
langkah (co-vectors → wedge products → generalized Stokes).

**Tesis penutup:** sistem bekerja karena fokus pada dua hal — *learning arc*
(dari pemahaman sekarang ke tujuan) dan *individual steps* (penjelasan bertahap).

---

## 2. Di mana ia **sepakat** dengan proyek ini

- **Tolak model one-to-many.** Sama dengan premis PRD: pengajaran massal tak
  bisa bertemu pengguna di titik pemahamannya sekarang.
- **Learning arc = DAG berurutan.** Framing "dari pemahaman sekarang → tujuan"
  praktis identik dengan daftar node berurutan proyek ini (CLAUDE.md §1: "DAG di
  v1 cukup daftar node berurutan di file data").
- **Optimasi sumber daya mental.** Sejalan dengan niat memindahkan beban logistik
  ke AI — **selama** yang dipindahkan hanya logistik, bukan penilaian.

---

## 3. Di mana ia **berpisah total** (dan kenapa itu penting)

Perbedaan intinya satu pertanyaan: **apa bukti seseorang sudah belajar?**

| Dimensi | Video (Eero) | Proyek ini (invariant) |
|---|---|---|
| Ukuran belajar | Probe MCQ lolos + penjelasan terasa dipahami | `reproduce-without-AI`, diverifikasi eksekusi kode |
| Yang jadi **gate** | Kuis pilihan ganda | Hanya `Attempt` + hidden test |
| Peran AI | Perencana **+ pengajar + penilai pemahaman** | Pengusul hipotesis; **tak pernah** penilai (§1.2) |
| Pemahaman diperiksa via | MCQ | Comprehension probe **deterministik** (predict output / spot bug / trace) |

**Pengakuan telak dari videonya sendiri:** ia menyebut failure mode "mencegah
gaslighting diri sendiri". Itu **persis** target invariant §1.1 (lawan gravitasi
"consumption comfort"). Bedanya:
- Video menambalnya dengan **kuis berkala** — yang justru masuk daftar **§8 PRD
  yang ditolak** (MCQ sebagai penilai utama).
- Proyek ini menolak MCQ-sebagai-gate sepenuhnya; gate satu-satunya = eksekusi kode.

Artinya: sistem video, dengan penjelasan mulus + MCQ, adalah mesin yang **efisien
memproduksi ilusi "consumption comfort"** — persis gravitasi yang proyek ini lawan.

---

## 4. Kruks: perbedaan ini **konsekuensi domain**, bukan selera

- Eero belajar **matematika** (differential forms). **Tidak ada oracle
  deterministik** untuk "paham differential forms". Tanpa tombol pass/fail yang
  jujur, ia **terpaksa** memakai comprehension probe sebagai proxy terbaik.
- Proyek ini **memilih domain kode** (FastAPI, `unit_test`) justru karena
  oracle-nya ada: status/body HTTP itu biner.

**Implikasi:** keputusan "domain pertama = FastAPI" (CLAUDE.md §2) bukan detail
teknis — ia **prasyarat** yang memungkinkan invariant §1.2 dipegang sama sekali.
Video ini jadi **bukti negatif** untuk keputusan itu: begitu domain kehilangan
executable oracle, sistem jatuh ke MCQ-as-judge dan seluruh kartu domino invariant
runtuh.

> Pertanyaan terbuka yang lahir dari sini (belum diputuskan): apakah akan pernah
> ada domain proyek yang *tak* punya executable oracle? Kalau ya — turunkan
> invariant §1.2, atau tolak domain semacam itu selamanya? (Bahan diskusi, bukan
> keputusan.)

---

## 5. Yang **layak dipinjam** ke M5 — tanpa melanggar invariant

Tiga kandidat; tiap poin dengan garis merahnya. Semua tunduk pada
[`M5-claude-code-integration`](milestones/M5-claude-code-integration.md) & peran
R1–R4 (CLAUDE.md §5).

1. **Struktur loop Probe → Plan → Teach** memetakan rapi ke R1–R4.
   - ✅ Boleh: memakai struktur alurnya.
   - ⛔ Jangan: menjadikan Probe sebuah *verdict*. Di proyek ini Probe = **generator
     hipotesis (R2)** yang **wajib** diverifikasi `Attempt`. Struktur boleh, gate jangan.

2. **Offload logistik ke AI** (perencanaan / pencarian / verifikasi fakta) = prinsip
   "optimasi sumber daya mental".
   - ✅ Boleh: menyusun materi just-in-time bersitasi (R3).
   - ⛔ Jangan: memutuskan node sudah dikuasai. Garis: offload **logistik** ya,
     offload **penilaian** tidak.

3. **Diagram Mermaid "memaksa AI bernalar"**.
   - ✅ Boleh (versi aman): diagram sebagai artifact **internal** proses R1 —
     cara AI menstruktur usulan node/edge sebelum di-prune Isyah.
   - ⛔ Jangan: diagram sebagai **fitur produk** untuk pengguna — graf visual/DAG
     explorer v1 sudah ditolak (§8 PRD, CLAUDE.md §1.5).

---

## 6. Yang **harus ditolak** dari video (langsung tabrak invariant)

- MCQ sebagai penilai utama pemahaman → §8 PRD, CLAUDE.md §1.5.
- AI sebagai penentu learning path final → §8; edge final = sumber otoritatif + Isyah (§1.4).
- AI sebagai penilai mastery → §1.2.
- Materi panjang / "bab yang enak dibaca" sebagai inti → §8 (content library ditolak).
- Graf visual untuk pengguna di v1 → §8.

---

## 7. Benang diskusi yang masih terbuka

1. Motivasi menonton: **uji ketahanan invariant** atau **cari fitur konkret** untuk M5?
2. Apakah akan ada domain ke-2 tanpa executable oracle (lihat §4)? Kalau ya, sikapnya apa?
3. Apakah comprehension probe deterministik proyek ini (predict output / spot bug /
   trace) adalah "versi lebih ketat" dari MCQ video — dan seberapa jauh ia boleh
   dipakai tanpa diam-diam menggeser gate dari eksekusi kode ke probe?
