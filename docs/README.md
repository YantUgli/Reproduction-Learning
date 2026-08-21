# Dokumentasi Implementasi — Reproduction Learning Engine

Folder ini memecah implementasi menjadi **milestone berurutan**. Tiap milestone
punya scope kecil, dapat divalidasi sendiri, dan menjadi prasyarat milestone
berikutnya. Baca dokumen ini lebih dulu sebelum masuk ke milestone mana pun.

> Sumber kebenaran produk adalah [`../PRD-reproduction-learning-engine-v1.2.md`](../PRD-reproduction-learning-engine-v1.2.md).
> Dokumentasi di sini adalah *cara membangunnya*, bukan *apa & kenapa*-nya.
> Kalau ada konflik, PRD menang untuk keputusan produk; dokumen ini menang untuk
> keputusan teknis implementasi (mis. eksekusi test — lihat catatan di bawah).

---

## 0. Satu paragraf konteks (baca ini kalau kamu developer baru)

Aplikasi ini **bukan** e-learning. Ukuran keberhasilannya tunggal:
**`reproduce-without-AI`** — apakah user (Bryant) bisa memproduksi sebuah konsep
dari nol tanpa AI, dibuktikan dengan menjalankan kode. AI **tidak pernah** boleh
menilai mastery; hanya eksekusi kode yang boleh. Setiap fitur diuji dengan
pertanyaan §2 PRD: *apakah ia menutup jurang produksi, atau hanya membuat
konsumsi terasa nyaman?* Kalau yang kedua, fitur itu gugur. Kalau kamu merasa
ingin menambah "bab materi yang enak dibaca" atau "visualisasi DAG interaktif",
berhenti dan baca §8 PRD (Guardrails) — keduanya sudah ditolak dengan alasan.

---

## 1. Penyimpangan resmi dari PRD (dicatat di sini, sengaja)

PRD §11 menulis **Docker container per attempt**. Implementasi memakai
**subprocess + virtualenv + tempdir** sebagai backend eksekusi default v1.

**Alasan:** PRD sendiri menyatakan isolasi Docker *"bukan soal keamanan — kodenya
milik Bryant sendiri"*. Karena keamanan bukan isu, yang tersisa hanyalah
*reproducibility* (dipenuhi venv ter-pin) dan *isolasi ringan* (dipenuhi tempdir
baru + subprocess + timeout). Docker per attempt menambah latency spin-up dan
beban ops tanpa membeli sesuatu yang dibutuhkan aplikasi single-user local-first.
Backend eksekusi disembunyikan di balik interface `Executor` (M1), sehingga
Docker/Pyodide bisa dipasang belakangan **tanpa mengubah kode lain**.

Pyodide sempat dipertimbangkan dan **ditolak untuk domain pertama**: FastAPI
(pydantic core Rust) rapuh di WASM, dan varians WASM-vs-CPython mengancam
kepercayaan sinyal pass/fail — nilai inti produk.

---

## 2. Peta milestone & dependency

```
M0  Scaffolding & Data Model ─┬─▶ M1  Execution Harness ─┬─▶ M2  Authoring + 5 Node (A1)
                              │                          │
                              │                          └─▶ M3  Vertical Slice (Fase 1) ◀── butuh M2
                              │                                        │
                              │                          ┌─────────────┘
                              │                          ▼
                              └────────────────────────▶ M4  Full Loop: FSRS+Placement+Dashboard (Fase 2)
                                                              │            ▲
                                                              │            └── GERBANG 0 wajib diputuskan sebelum sini
                                                              ├─▶ M5  Claude Code Integration (Fase 3)
                                                              └─▶ M6  Domain Kedua: React → ML (Fase 4)
```

| ID | Milestone | Peta PRD | Dependency | Est. | Status |
|----|-----------|----------|------------|------|--------|
| [M0](milestones/M0-scaffolding-and-data-model.md) | Scaffolding & Data Model | prasyarat | — | 1–2 hari | ✅ selesai |
| [M1](milestones/M1-execution-harness.md) | Execution Harness (subprocess) | Tahap 0b | M0 | 0,5–1 hari | ✅ selesai |
| [M2](milestones/M2-authoring-and-first-nodes.md) | Authoring Kit + 5 Node FastAPI | Track A1 | M1 | 4–5 hari |
| [M3](milestones/M3-vertical-slice-core-loop.md) | Vertical Slice / Core Loop | Fase 1 | M1, M2 | 2–3 minggu |
| [M4](milestones/M4-full-loop-fsrs-dashboard.md) | Full Loop: FSRS + Placement + Dashboard | Fase 2 | M3 + Gerbang 0 | 2–3 minggu |
| [M5](milestones/M5-claude-code-integration.md) | Claude Code Integration | Fase 3 | M4 | 3–4 minggu |
| [M6](milestones/M6-second-domain.md) | Domain Kedua (React → ML) | Fase 4 | M4 | variabel |

---

## 3. Gerbang keputusan (non-teknis, tapi mengikat roadmap)

**Gerbang 0 — Build-vs-Buy (Execute Program).** Sebelum mengerjakan **M4**,
keputusan lanjut-atau-berhenti **wajib** dibuat. Coba Execute Program (~$39/bln)
untuk primitif bahasa selama ~1 bulan — jalan **paralel** dengan M0–M3 (yang tetap
berguna apa pun keputusannya). Kalau Execute Program cukup untuk kebutuhan Bryant,
roadmap boleh berhenti di M3. Detail: PRD §12 & RISK-5.

M0–M3 adalah "slice pertama" yang murah (~3–4 minggu) dan **non-blocking** terhadap
gerbang ini.

---

## 4. Track Authoring vs Sumbu Engineering

Dua sumbu jalan **paralel** (PRD §12):

- **Engineering:** M0 → M1 → M3 → M4 → M5/M6.
- **Authoring:** M2 (5 node untuk menyalakan M3), lalu **A2** (~20 node sisa,
  ~30–60 jam) yang dikarang paralel sepanjang M4 dan seterusnya.

**Authoring adalah bottleneck sebenarnya (RISK-1), bukan kodenya.** Jangan
meremehkan bobot A2. Tiap node butuh ~1,5–3 jam kerja Isyah termasuk verifikasi
hidden test hijau di solusi referensi.

---

## 5. Cara memakai dokumen milestone

1. Baca **Prerequisite** — pastikan milestone sebelumnya lolos acceptance criteria.
2. Ikuti **Langkah implementasi** berurutan; jangan lompat.
3. Setiap ada **Keputusan teknis penting**, jangan diubah tanpa alasan tercatat —
   itu sudah dipertimbangkan.
4. Jalankan bagian **Testing/validasi** sebelum menyatakan selesai.
5. Milestone dianggap **selesai** hanya kalau seluruh **Acceptance criteria** hijau.

Kalau kamu menyelesaikan sebuah milestone, perbarui statusnya di tabel §2 dan catat
keputusan tak terduga di CLAUDE.md (bagian "Log keputusan").
