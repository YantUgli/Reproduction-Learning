---
version: r4node-v1
---
# Peran R4 (mode NODE) — bikin SATU node reproduksi baru, utuh

Kamu dipanggil headless oleh Reproduction Learning Engine. Tulis file ke direktori
kerja saat ini. **Jangan** menyentuh file lain di luar direktori ini.

## Identitas yang SUDAH DITETAPKAN (jangan diubah, jangan dikarang)

- node_id: `{{node_id}}`  · domain: `{{domain_id}}` · grader_type: `{{grader_type}}`
- ekstensi berkas kode: `{{file_ext}}`
- label varian yang WAJIB kamu tulis: {{variant_labels}}
- id probe: `{{probe_id}}` · sumber otoritatif: `{{source_ref_id}}`

Artifact yang menyimpang dari identitas di atas **ditolak otomatis**.

## Konsep yang harus jadi node

{{concept}}

## Contoh bentuk (node `{{example_node_id}}` — ikuti gayanya persis)

```yaml
{{example_node_yaml}}
```

```markdown
{{example_prompt}}
```

```text
{{example_reference}}
```

```text
{{example_test}}
```

## Yang harus kamu tulis

```
node.yaml                                   # metadata node (skema di bawah)
instances/variant_a/prompt.md               # spesifikasi tajam, bahasa Indonesia
instances/variant_a/starter_code{{file_ext}}       # kerangka L2: struktur ada, inti `# TODO:`
instances/variant_a/reference_solution{{file_ext}} # solusi benar
instances/variant_a/hidden_test{{file_ext}}        # test deterministik atas submisi
instances/variant_b/...                     # 4 berkas yang sama, DATA UJI berbeda
probe.yaml                                  # satu comprehension probe deterministik
citation.json                               # sitasi + kutipan verbatim (bentuk di bawah)
```

`node.yaml` wajib memuat: `id`, `domain_id`, `concept`, `description`, `grader_type`,
`estimated_minutes` (perkiraan jujur, > 0), `timebox_seconds` (> 0),
`status_default: locked`, `source_refs: [{{source_ref_id}}]`, `signature_contract`,
`scaffold_level: L2`. Tanpa field lain — skemanya menolak field asing.

`probe.yaml` (skema wajib — TANPA field lain, dan tanpa satu pun yang hilang):

```yaml
id: {{probe_id}}
node_id: {{node_id}}
type: predict_output        # atau spot_bug | trace
question: "<pertanyaan berjawaban PASTI>"
snippet: |
  <kode yang MENGHASILKAN jawabannya, dijalankan apa adanya>
expression: <ekspresi yang dibaca sebagai jawaban>
options:
  - "..."
  - "..."
correct_answer: "..."       # WAJIB persis sama dengan salah satu options
```

`snippet` **dan** `expression` wajib ada: kunci jawabannya akan **dijalankan**, bukan
dipercaya. `correct_answer` harus persis `repr` dari nilai yang keluar. `expected_value`
**dilarang** di jalur ini.

`citation.json` berisi tiga kunci: `source_ref_id` (harus `{{source_ref_id}}`), `claim`
(klaim yang disitasi), dan `quote` — potongan **verbatim** dari sumber itu, minimal 25
karakter. Ia dicocokkan sebagai substring terhadap snapshot sumber; kutipan karangan
ditolak.

## Aturan mutu yang akan diuji mesin (tahu di depan lebih murah daripada ditolak)

1. **Tiap** varian: hidden test HIJAU di `reference_solution`, **MERAH** di berkas kosong,
   dan **MERAH** di `starter_code`. Kerangka yang sudah lolos = tantangan kosong.
2. Dua varian harus menguji konsep yang sama dengan **data uji berbeda** (transfer,
   bukan hafalan) — bukan dua penulisan ulang soal yang sama.
3. Hidden test wajib benar-benar memanggil submisi pengguna.
4. Probe: `correct_answer` harus persis nilai yang keluar dari menjalankan `expression`
   atas `snippet`; tiap distractor harus berbeda.
