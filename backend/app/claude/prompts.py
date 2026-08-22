"""Template prompt per peran — VERSIONED & di repo, bukan hardcode tersebar.

M5 §Hal yang harus diperhatikan: "Prompt untuk tiap peran harus terstruktur &
versioned — simpan di repo". Versi ikut tercatat di `job.json` supaya artifact lama
bisa dibaca ulang dengan tahu prompt versi mana yang menghasilkannya.

Format file (`prompts/<name>.md`):

    ---
    version: r3-v1
    ---
    <isi prompt, placeholder gaya {{nama}}>

Placeholder disubstitusi dengan `str.replace`, bukan `str.format`: isi prompt penuh
kurung kurawal (contoh kode, JSON) dan `format()` akan tersedak di situ.
"""

import re
from dataclasses import dataclass
from pathlib import Path

PROMPTS_DIR = Path(__file__).parent / "prompts"

_FRONT_MATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_PLACEHOLDER_RE = re.compile(r"\{\{(\w+)\}\}")


@dataclass
class RenderedPrompt:
    version: str
    text: str


def load_template(name: str) -> tuple[str, str]:
    """→ (version, body). Raise FileNotFoundError bila template tak ada."""
    path = PROMPTS_DIR / f"{name}.md"
    raw = path.read_text(encoding="utf-8")
    match = _FRONT_MATTER_RE.match(raw)
    if not match:
        raise ValueError(f"{path}: front matter `---\\nversion: ...\\n---` wajib ada")
    version = ""
    for line in match.group(1).splitlines():
        key, _, value = line.partition(":")
        if key.strip() == "version":
            version = value.strip()
    if not version:
        raise ValueError(f"{path}: front matter tanpa `version`")
    return version, raw[match.end() :]


def render(name: str, context: dict[str, str]) -> RenderedPrompt:
    """Isi placeholder. Placeholder yang tak punya nilai = error, bukan string kosong
    diam-diam — prompt setengah jadi menghasilkan artifact sampah yang mahal."""
    version, body = load_template(name)
    missing = {m for m in _PLACEHOLDER_RE.findall(body) if m not in context}
    if missing:
        raise ValueError(f"prompt {name}: placeholder tanpa nilai: {', '.join(sorted(missing))}")
    for key, value in context.items():
        body = body.replace("{{" + key + "}}", str(value))
    return RenderedPrompt(version=version, text=body.strip())
