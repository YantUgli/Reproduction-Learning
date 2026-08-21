# M1 — Execution Harness (subprocess)

> Peta PRD: Tahap 0b "Harness" · Dependency: M0 · Estimasi: 0,5–1 hari

## Tujuan

Membangun **runner pytest telanjang**: ambil solusi + hidden test, jalankan,
kembalikan `pass/fail + output`. Ini komponen paling fondasional produk — semua
verifikasi bermuara ke sini. Dibangun di balik interface `Executor` supaya backend
eksekusi (subprocess sekarang; Docker/Pyodide nanti) bisa ditukar tanpa mengubah
kode lain.

## Konteks & alasan

PRD mensyaratkan tiap hidden test **"lolos hijau di solusi referensi"** sebelum
dipakai (§10 R4). Itu **tidak bisa dibuktikan tanpa runner**. Maka runner harus
ada **sebelum** authoring apa pun (M2) — kalau tidak, kita mengarang node yang
test-nya belum pernah dijalankan sekali pun (RISK-1).

Runner ini **bukan pekerjaan ganda** dengan M3: ia versi telanjang dari runner yang
di M3 dibungkus pencatatan `Attempt` + isolasi tempdir. Kontraknya identik, jadi M3
tinggal menyelubunginya, bukan menulis ulang.

**Backend = subprocess + venv + tempdir, bukan Docker** (lihat docs/README §1 &
CLAUDE.md §2). Isolasi Docker "bukan soal keamanan"; yang dibutuhkan hanya
reproducibility (venv ter-pin) + isolasi ringan (tempdir + timeout).

## Prerequisite

- **M0 selesai** (backend package + venv ada). Harness memakai Python & venv yang
  sama supaya environment test = environment aplikasi.

## File / komponen yang dibuat

```
backend/app/executor/
  __init__.py
  base.py                # ExecutionResult + Executor Protocol
  subprocess_executor.py # implementasi default v1
harness/
  run.py                 # CLI telanjang: jalankan node instance dari data/
data/domains/fastapi/nodes/_example/   # 1 node contoh untuk menguji harness
  node.yaml
  instances/variant_a/
    prompt.md
    starter_code.py
    reference_solution.py
    hidden_test.py
backend/tests/
  test_executor.py       # solusi benar → pass; solusi rusak → fail; loop tak henti → timeout
```

## Kontrak interface (bekukan ini)

```python
# backend/app/executor/base.py
from dataclasses import dataclass
from typing import Protocol

@dataclass
class ExecutionResult:
    passed: bool          # True hanya jika seluruh test lolos & exit code 0
    stdout: str
    stderr: str
    duration_seconds: float
    timed_out: bool
    exit_code: int | None

class Executor(Protocol):
    def run(
        self,
        files: dict[str, str],   # nama_file -> isi (mis. {"solution.py": ..., "test_solution.py": ...})
        test_entry: str,         # nama file test yang dijalankan pytest
        timeout_seconds: int,
    ) -> ExecutionResult: ...
```

Interface ini adalah **satu-satunya** titik yang tahu *bagaimana* kode dieksekusi.
Grader (M3) dan harness CLI sama-sama memanggilnya.

## Langkah implementasi (berurutan)

1. **`base.py`.** Definisikan `ExecutionResult` dan `Executor` Protocol persis
   seperti di atas.

2. **`subprocess_executor.py` — `SubprocessExecutor`.** Implementasi `run()`:
   1. Buat `tempfile.TemporaryDirectory()` baru (isolasi per panggilan).
   2. Tulis seluruh `files` ke tempdir.
   3. Jalankan `pytest` via `subprocess.run([sys.executable, "-m", "pytest", test_entry, "-q"])`
      dengan `cwd=tempdir`, `timeout=timeout_seconds`, `capture_output=True`,
      `text=True`. Set `env` yang membersihkan variabel tak perlu; **jangan**
      wariskan API key apa pun.
   4. Tangani `subprocess.TimeoutExpired` → `timed_out=True`, `passed=False`.
   5. `passed = (returncode == 0)`; ukur `duration_seconds`.
   6. Tempdir otomatis terhapus saat context keluar (isolasi bersih).

3. **`harness/run.py` — CLI telanjang.** Terima path folder instance node
   (`.../instances/variant_a/`). Baca `reference_solution.py` + `hidden_test.py`,
   panggil `SubprocessExecutor.run(...)`, cetak hasil (`PASS`/`FAIL`), output test,
   durasi, dan exit non-zero kalau gagal. Ini alat yang dipakai Isyah saat
   mengarang node di M2.

4. **Node contoh `_example`.** Buat satu node trivial (mis. fungsi `add(a,b)`)
   lengkap dengan `reference_solution.py` yang benar dan `hidden_test.py` yang
   menguji beberapa kasus. Gunanya: membuktikan harness jalan end-to-end sebelum
   node FastAPI sungguhan (M2). Folder diawali `_` supaya jelas ini bukan node
   kurikulum.

5. **`test_executor.py`.** Tiga kasus wajib:
   - solusi **benar** → `passed=True`, `timed_out=False`.
   - solusi **sengaja rusak** (mis. `add` mengurangi) → `passed=False`.
   - solusi **loop tak berhenti** (`while True`) dengan `timeout_seconds=2` →
     `timed_out=True`, `passed=False`, dan proses benar-benar berhenti (tak
     menggantung).

## Keputusan teknis penting

- **Timeout wajib & di-enforce oleh subprocess, bukan oleh test.** Timebox adalah
  bagian dari desain integritas (§7.6 PRD); runner harus bisa membunuh kode yang
  menggantung. Uji kasus `while True` bukan opsional.
- **`sys.executable -m pytest`, bukan `pytest` di PATH.** Menjamin runner memakai
  interpreter/venv yang sama dengan aplikasi → environment test = environment app.
- **Tempdir baru per panggilan.** Ini seluruh "isolasi" yang dibutuhkan: tak ada
  state bocor antar attempt, tak ada file sisa. Tidak perlu Docker untuk ini.
- **Return `passed=False` untuk semua jalur gagal** (test gagal, error import,
  timeout). Grader di atasnya tidak perlu membedakan *kenapa* gagal untuk verdict;
  `stderr`/`stdout` disimpan untuk ditampilkan ke user.

## Hal yang harus diperhatikan

- Pastikan `env` yang diberikan ke subprocess **tidak** membawa kredensial/API key
  (`ANTHROPIC_API_KEY`, dll). Bukan soal keamanan kode Bryant, tapi kebersihan &
  determinisme environment.
- Jangan menambah dependency pihak ketiga di sini; stdlib (`subprocess`, `tempfile`)
  cukup. Kesederhanaan penting karena semua verifikasi bergantung padanya.
- Simpan kontrak `files: dict[str,str]` apa adanya — jangan optimasi ke "path saja".
  Bentuk in-memory ini yang membuat M3 mudah mengganti sumber file (dari DB/editor).

## Testing / validasi

```bash
cd backend && pytest tests/test_executor.py -v   # 3 kasus hijau, termasuk timeout

# Harness telanjang terhadap node contoh
python ../harness/run.py ../data/domains/fastapi/nodes/_example/instances/variant_a
# Output: PASS + durasi. Coba rusak reference_solution.py → harus FAIL.
```

## Expected result

- `SubprocessExecutor` mengembalikan `ExecutionResult` yang benar untuk solusi
  benar, rusak, dan menggantung.
- `harness/run.py` mencetak PASS/FAIL yang akurat dan exit code yang sesuai
  (0 = pass) — sehingga bisa dipakai dalam skrip/CI authoring.
- Kode yang menggantung benar-benar dibunuh oleh timeout (tidak ada proses zombie).

## Acceptance criteria

- [ ] `Executor` Protocol & `ExecutionResult` terdefinisi persis seperti kontrak
      di atas.
- [ ] `SubprocessExecutor` lolos 3 kasus test (pass / fail / timeout).
- [ ] `harness/run.py` bisa memverifikasi node contoh: hijau saat solusi benar,
      merah saat dirusak.
- [ ] Timeout terbukti membunuh proses menggantung (test `while True` selesai < 5s).
- [ ] Tidak ada dependency baru di luar stdlib untuk backend eksekusi.
- [ ] Interface siap dipakai M2 (verifikasi node) & M3 (grader) tanpa perubahan.
