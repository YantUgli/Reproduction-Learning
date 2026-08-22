# M5 — Claude Code Integration (Fase 3)

> Peta PRD: Fase 3 · Dependency: M4 · Estimasi: 3–4 minggu (paling tidak pasti)

## Tujuan

Mengotomasi peran Claude Code (§10 PRD) yang selama M2–M4 dipakai manual/offline,
lewat integrasi **async berbasis file artifact**: aplikasi memanggil Claude Code
headless dengan prompt terstruktur → Claude Code menulis output ke direktori kerja
→ aplikasi membaca, memvalidasi, dan menyodorkannya ke Isyah untuk review sebelum
masuk sistem. Diurutkan dari risiko terendah ke tertinggi: **R3 → R4 → R2**.

## Konteks & alasan

Claude Code adalah **agent CLI async, bukan HTTP API** (§10) — ini bagian **paling
tidak pasti** dari seluruh proyek (RISK-3): latency, format output tak konsisten,
butuh review manusia. Karena itu M3/M4 sengaja dirancang bernilai **tanpa** M5.
M5 adalah akselerator authoring & personalisasi, **bukan** fondasi.

**Invariant yang tidak boleh tergores di sini:** AI tetap **tidak pernah** menetapkan
edge final, menyatakan mastery, atau menilai teks bebas (§1 CLAUDE.md). Semua output
R2/R4 adalah *usulan/hipotesis* yang wajib melewati gate (Isyah / Attempt).

## Prerequisite

- **M4 selesai** (loop penuh + FSRS + data node cukup).
- Claude Code CLI tersedia di environment yang menjalankan backend (headless).
- Konvensi direktori artifact disepakati (lihat Langkah 1).

## File / komponen yang dibuat

```
backend/app/
  claude/
    runner.py            # panggil Claude Code headless, tunggu artifact, timeout
    contracts.py         # skema pydantic tiap output artifact (validasi ketat)
    review_queue.py      # antrean artifact menunggu review Isyah
  routers/
    authoring.py         # trigger R3/R4/R2; endpoint review Isyah (approve/reject)
frontend/app/
  authoring/page.tsx     # UI review Isyah: lihat artifact, diff, approve/prune
artifacts/               # direktori kerja output Claude Code (git-ignored kecuali contoh)
backend/tests/
  test_claude_contracts.py   # artifact valid diterima; artifact cacat ditolak
  test_review_gate.py        # tak ada artifact masuk sistem tanpa approve Isyah
```

## Urutan integrasi (dari risiko terendah)

### 1. R3 — Materi just-in-time (paling aman, dulukan)
- Input: `node_id` + hasil Attempt yang gagal.
- Output: `explanation.md` (pendek, bersitasi) + worked example beranotasi.
- Gate: **sitasi wajib bisa diverifikasi**. Materi pendek & just-in-time (bukan bab).
- Kenapa dulu: objeknya **materi**, yang memang boleh di-research & diverifikasi
  lewat sumber eksternal (§10 catatan). Risiko terhadap invariant paling rendah.

### 2. R4 — Generator soal (dengan review Isyah)
- Input: `node_id` + kontrak signature.
- Output: `ChallengeInstance` varian + hidden test + `ComprehensionProbe`.
- Gate: **Isyah review** + **hidden test wajib deterministik & hijau di solusi
  referensi** — jalankan otomatis lewat `verify_nodes.py`/`Executor` (M1/M2) sebelum
  masuk antrean review. Test merah = artifact ditolak otomatis, tak sampai ke Isyah.

### 3. R2 — Bukti codebase (paling sensitif terhadap invariant)
- Input: path repo Bryant + daftar node.
- Output: `hypotheses.json` (`node_id`, `confidence`, `rationale`, `evidence_locator`).
- Gate: **masuk sebagai `SkillHypothesis` berstatus `unverified`** — **tidak pernah**
  jadi verdict. Wajib dikonfirmasi/dibantah oleh `Attempt`
  (`confirmed_by_attempt`/`refuted_by_attempt`). Codebase Bryant mungkin ditulis
  dengan AI → ia bukti *pengenalan*, bukan *produksi* (RISK-4).

## Langkah implementasi (berurutan)

1. **Konvensi artifact.** Tetapkan struktur `artifacts/<role>/<timestamp>/` dan
   nama file output per peran. Semua output ditulis ke sini, dibaca aplikasi, tak
   pernah langsung ke DB.

2. **`runner.py`.** Panggil Claude Code headless dengan prompt terstruktur + working
   dir. Tangani **async**: timeout, retry terbatas, deteksi output tak lengkap.
   Jangan blokir request UI — jadikan job latar (status: `pending/ready/failed`).

3. **`contracts.py`.** Skema pydantic ketat untuk tiap artifact (explanation, node,
   probe, hypotheses). Output yang tak sesuai skema **ditolak** sebelum menyentuh
   review — melindungi dari "format output tak konsisten" (RISK-3).

4. **`review_queue.py` + `authoring/page.tsx`.** Setiap artifact valid masuk antrean
   review Isyah: tampilkan isi + diff terhadap yang ada, tombol approve/prune/reject.
   **Tidak ada** artifact yang masuk sistem tanpa approve (kecuali R3 yang mungkin
   auto dengan sitasi terverifikasi — putuskan & catat).

5. **Sambungkan gate otomatis R4.** Sebelum artifact soal R4 sampai ke Isyah,
   jalankan hidden test-nya lawan solusi referensi (Executor M1). Merah → tolak.

6. **R2 → SkillHypothesis.** Muat `hypotheses.json` sebagai `SkillHypothesis`
   `unverified`. Sambungkan ke loop: saat Attempt terkait terjadi, update status
   hipotesis. Hipotesis boleh **memengaruhi urutan/penjadwalan usulan**, tak pernah
   status mastery.

## Keputusan teknis penting

- **Async by design, bukan request/response.** Perlakukan Claude Code seperti job
  queue eksternal: state `pending → ready/failed`, bukan `await` sinkron di router.
- **Validasi skema sebelum review manusia.** Manusia me-review *konten*, bukan
  membetulkan *format*. Format dijaga `contracts.py`.
- **Gate berlapis untuk R4.** Otomatis (test hijau) lalu manusia (Isyah). Dua-duanya
  wajib.
- **R2 tak pernah jadi verdict — jangan pernah dilonggarkan** (RISK-4). Kalau ada
  tekanan "kan confidence-nya tinggi", tolak: confidence tinggi tetap hipotesis.

## Hal yang harus diperhatikan

- Jangan biarkan kegagalan/latency Claude Code **memblokir** loop inti. Kalau M5
  down, M3/M4 harus tetap jalan penuh (RISK-3 mitigasi).
- Prompt untuk tiap peran harus terstruktur & versioned — simpan di repo, bukan
  hardcode tersebar.
- Materi R3 tetap **pendek & just-in-time**. AI cenderung menghasilkan panjang;
  batasi lewat prompt + review (§8 Guardrails: content library ditolak).
- Jangan memberi Claude Code kemampuan menulis langsung ke DB atau ke `data/` final.
  Ia menulis ke `artifacts/`; promosi ke sistem hanya lewat gate.

## Testing / validasi

```bash
cd backend && pytest tests/test_claude_contracts.py tests/test_review_gate.py -v
```
Uji manual: trigger R3 untuk node yang gagal → artifact muncul di antrean review →
Isyah approve → materi tampil di sesi node. Trigger R4 → artifact dengan test merah
ditolak otomatis; test hijau → masuk review. Trigger R2 → hipotesis masuk sebagai
`unverified`, lalu berubah status setelah Attempt.

## Expected result

- Ketiga peran (R3, R4, R2) berjalan async lewat artifact + review Isyah.
- Tidak ada artifact yang masuk sistem tanpa lolos gate (skema + test + Isyah).
- Hipotesis codebase masuk sebagai `unverified` dan hanya berubah lewat Attempt.
- Loop inti (M3/M4) tetap berfungsi penuh walau integrasi Claude Code dimatikan.

## Acceptance criteria

- [x] R3, R4, R2 terintegrasi async via file artifact (bukan HTTP sinkron).
      `claude -p` dipanggil dengan cwd = direktori job; router hanya membuat job
      (`202 pending`) dan menyerahkannya ke `BackgroundTasks`. Ketiganya sudah
      dijalankan **melawan CLI sungguhan**, bukan cuma runner palsu.
- [x] `contracts.py` menolak artifact yang tak sesuai skema sebelum review.
      — `tests/test_claude_contracts.py` (22 test: sitasi tak dikenal, materi
      kepanjangan, probe tanpa jawaban di options, test tak meng-import `solution`,
      confidence di luar 0..1, artifact yang membawa field `status`).
- [x] Gate R4 otomatis menolak soal yang hidden test-nya merah di solusi referensi —
      **plus** soal yang `starter_code`-nya sudah lolos (tantangan kosong).
      — `tests/test_review_gate.py`.
- [x] `SkillHypothesis` dari R2 masuk `unverified` dan **tidak pernah** jadi verdict.
      Hanya attempt mode `verification`/`review`/`placement` yang mengubahnya;
      attempt berscaffold (`acquisition`) tidak dihitung sebagai bukti.
- [x] Review Isyah wajib untuk **ketiga** peran (keputusan tercatat di CLAUDE.md §7:
      R3 tidak auto-approve, karena "sitasi terverifikasi" yang bisa dicek mesin
      hanyalah *keberadaan* source_ref, bukan *kebenaran* klaimnya).
- [x] Mematikan integrasi Claude Code tidak merusak loop M3/M4.
      `CLAUDE_INTEGRATION_ENABLED=0` → trigger balas 503; test membuktikan submit
      attempt tetap jalan setelah kill switch & setelah job gagal total.
- [x] Tidak ada jalur di mana AI menetapkan edge final, mastery, atau menilai teks
      bebas. `edges.yaml` tak pernah ditulis kode M5; promosi R4 memakai validasi M2
      yang sama dengan node tulisan tangan; probe tetap `correct_answer` deterministik.
