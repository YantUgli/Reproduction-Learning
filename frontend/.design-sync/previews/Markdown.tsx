import { Markdown } from "reproduction-learning-engine-frontend";

// Renderer markdown minimal untuk prompt/materi node (heading, list, bold, code).
const PROMPT = `### Path parameter dengan 404

Buat endpoint \`GET /items/{item_id}\` yang:

- mengembalikan item bila **ada** di penyimpanan
- membalas **404** dengan detail \`"item tidak ditemukan"\` bila tidak

\`\`\`python
@app.get("/items/{item_id}")
def read_item(item_id: int):
    ...
\`\`\`

Uji lewat \`reference_solution\`, bukan lewat membaca contoh.`;

export function NodePrompt() {
  return (
    <div style={{ maxWidth: 620 }}>
      <Markdown>{PROMPT}</Markdown>
    </div>
  );
}
