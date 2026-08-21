# M0 — Scaffolding & Data Model

> Peta PRD: prasyarat semua fase · Dependency: — · Estimasi: 1–2 hari

## Tujuan

Menyiapkan kerangka repo yang bisa dibangun di atasnya oleh semua milestone
berikutnya: struktur folder, backend FastAPI yang bisa `uvicorn`-boot, database
SQLite dengan skema data domain-agnostic (§9 PRD), dan skeleton frontend Next.js.
**Belum ada fitur.** Selesai M0 = "ada rangka yang hidup dan bisa diisi".

## Konteks & alasan

Semua milestone lain menyentuh model data yang sama (`Node`, `Edge`, `Attempt`,
`ScheduleItem`, dst). Kalau skema ini tidak dibekukan lebih dulu, tiap milestone
akan mendefinisikan ulang bentuk data dan saling bertabrakan. M0 membekukan
**bentuk data** (bukan logika) sesuai §9 PRD, yang sengaja *domain-agnostic* —
tidak ada field yang meng-hardcode "FastAPI". Itulah bentuk extensibility yang
dipilih PRD: skema yang tidak tahu domainnya apa, bukan pipeline ingestion.

## Prerequisite

- Tidak ada. Ini milestone pertama.
- Terpasang: Python 3.11+, Node.js 18+, `git`.

## File / komponen yang dibuat

```
backend/
  pyproject.toml                 # deps: fastapi, uvicorn, sqlmodel, pydantic, ruff, pytest
  app/
    __init__.py
    main.py                      # FastAPI app + health route
    db.py                        # engine SQLite + get_session()
    models.py                    # SEMUA tabel SQLModel (§9 PRD)
    config.py                    # path DB, konstanta (N=4, dst)
  tests/
    test_health.py
    test_models.py               # smoke: create + query tiap tabel
frontend/
  package.json                   # next, react, @monaco-editor/react
  app/
    layout.tsx
    page.tsx                     # placeholder "M0 alive"
data/
  domains/
    fastapi/
      domain.yaml                # id, name, status (placeholder)
      nodes/                      # kosong; diisi M2
      edges.yaml                 # kosong list; diisi M2
  sources.yaml                   # SourceRef awal (CS2023, TOC buku, docs FastAPI)
.gitignore
```

## Langkah implementasi (berurutan)

1. **Root housekeeping.** Buat `.gitignore` (Python `.venv/`, `__pycache__/`,
   `*.db`, `*.sqlite3`; Node `node_modules/`, `.next/`; OS junk). Commit awal.

2. **Backend project.** Buat `backend/pyproject.toml` dengan dependency minimum:
   `fastapi`, `uvicorn[standard]`, `sqlmodel`, `pydantic>=2`, dan dev `ruff`,
   `pytest`, `httpx` (untuk TestClient). Buat venv & `pip install -e .`.

3. **`app/config.py`.** Konstanta terpusat: `DATABASE_URL` (default
   `sqlite:///./app.db`), `MASTERY_SUCCESSES_DEFAULT = 4`, path ke `data/`.
   Semua angka "ajaib" dari PRD masuk sini, jangan sebar di kode.

4. **`app/db.py`.** Engine SQLModel untuk SQLite (`connect_args={"check_same_thread": False}`),
   fungsi `init_db()` (create tables) dan dependency `get_session()`.

5. **`app/models.py` — bekukan skema §9 PRD.** Definisikan tabel SQLModel berikut.
   Ini kontrak lintas-milestone; ubah hanya lewat Log keputusan CLAUDE.md.
   - `Domain(id, name, status)`
   - `SourceRef(id, type, citation, url_or_locator)` — `type ∈ {cs2023_ku, textbook_toc, official_docs}`
   - `Node(id, domain_id, concept, description, grader_type, estimated_minutes, timebox_seconds, status_default)`
     — `grader_type ∈ {unit_test, structural, value_assert, metric_threshold, dom_behavior}`
   - `Edge(from_node_id, to_node_id, type, source_ref_id, note)` — `type ∈ {hard, soft}`
   - `ChallengeInstance(id, node_id, variant_label, prompt, starter_code, signature_contract, hidden_test_path, scaffold_level)`
   - `ComprehensionProbe(id, node_id, type, question, options, correct_answer)`
     — `type ∈ {predict_output, spot_bug, trace}`; `options` JSON
   - `Attempt(id, node_id, instance_id, timestamp, mode, scaffold_level, duration_seconds, submitted_code, result, test_output, probe_result)`
     — `mode ∈ {placement, acquisition, verification, review}`; `result ∈ {pass, fail}`
   - `SkillHypothesis(id, node_id, source, confidence, rationale, evidence_locator, created_at, status)`
     — `status ∈ {unverified, confirmed_by_attempt, refuted_by_attempt}`
   - `ScheduleItem(node_id, fsrs_stability, fsrs_difficulty, due_at, review_count, consecutive_success, status)`
     — `status ∈ {locked, available, acquired, mastered, lapsed}`
   - `Session(id, started_at, ended_at, mode, ai_available)` — `ai_available` selalu `False` untuk verification
   Pakai `str` enum lewat `Enum`/`Literal` + kolom string; jangan bikin enum DB
   khusus (SQLite tak butuh, dan string lebih mudah di-diff).

6. **`app/main.py`.** Buat `FastAPI()` app, panggil `init_db()` di startup, tambah
   route `GET /health` → `{"status": "ok"}`. Sertakan CORS untuk `localhost:3000`.

7. **Backend smoke tests.** `test_health.py` (TestClient hit `/health`).
   `test_models.py` (buat satu row tiap tabel di DB in-memory, query balik) — ini
   memvalidasi skema §5 benar-benar konsisten.

8. **Frontend skeleton.** Inisialisasi Next.js (App Router, TypeScript) di
   `frontend/`. Tambah `@monaco-editor/react` ke `package.json` (belum dipakai).
   `page.tsx` menampilkan teks statis + hasil fetch `GET /health` sebagai bukti
   backend↔frontend nyambung.

9. **Data placeholder.** `data/domains/fastapi/domain.yaml`, `edges.yaml` (list
   kosong), `sources.yaml` berisi 3 SourceRef awal (CS2023, satu TOC buku FastAPI/
   backend, docs resmi FastAPI). Node folder dibiarkan kosong (diisi M2).

## Keputusan teknis penting

- **SQLModel, bukan SQLAlchemy murni.** Idiom FastAPI, sekaligus memberi skema
  pydantic gratis. (CLAUDE.md §2)
- **Enum sebagai string, bukan tipe DB.** SQLite tak punya enum native; string
  lebih mudah di-diff & di-migrasi manual. Validasi nilai di layer pydantic.
- **Tidak pakai Alembic di v1.** Single-user, skema masih cair. `init_db()` +
  hapus `app.db` saat perlu reset cukup. Migrasi formal ditunda sampai ada data
  produksi yang tak boleh hilang.
- **Domain-agnostic dijaga ketat.** Tidak boleh ada kolom seperti `http_method`.
  Kekhususan domain hidup di `grader_type` + isi `data/`, bukan di skema.

## Hal yang harus diperhatikan

- Jangan menambah field yang "mungkin berguna nanti". Skema §9 sudah dipikirkan;
  penambahan spekulatif = utang. Tambah field hanya saat milestone yang butuh tiba.
- `Session.ai_available` untuk mode `verification` **harus** selalu `False`. Ini
  bukan sekadar flag; ia representasi invariant §2. Beri komentar di model.
- Pastikan `check_same_thread=False` supaya subprocess/thread pool M1 tidak error.

## Testing / validasi

```bash
cd backend
pip install -e .
pytest                       # test_health + test_models hijau
ruff check .                 # bersih
uvicorn app.main:app --reload
curl localhost:8000/health   # {"status":"ok"}

cd ../frontend
npm install && npm run dev    # buka :3000, lihat status "ok" dari backend
```

## Expected result

- `uvicorn` boot tanpa error, `/health` mengembalikan `{"status":"ok"}`.
- File `app.db` tercipta dengan **semua** tabel §9 (cek via
  `sqlite3 app.db ".tables"`).
- Frontend menampilkan status "ok" hasil fetch ke backend (bukti CORS & koneksi).
- `pytest` & `ruff` hijau.

## Acceptance criteria

- [ ] Struktur folder sesuai bagian "File/komponen" ada di repo.
- [ ] Seluruh 10 tabel §9 PRD terdefinisi di `models.py` dan tercipta di SQLite.
- [ ] `test_models.py` membuktikan create+query setiap tabel berhasil.
- [ ] `GET /health` hijau via TestClient dan via browser frontend.
- [ ] Tidak ada field yang meng-hardcode domain tertentu (domain-agnostic terjaga).
- [ ] `ruff check .` bersih; commit awal dibuat.
