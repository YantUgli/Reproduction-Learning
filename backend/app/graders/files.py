"""Lokasi berkas milik satu `ChallengeInstance` (M6).

`hidden_test_path` di DB adalah pointer ke `data/`; seluruh berkas lain milik
instance itu adalah sibling-nya. Modul ini satu-satunya tempat yang tahu aturan itu,
dan ia **tak pernah** mengasumsikan bahasa: `reference_solution.py` untuk
FastAPI/ML, `reference_solution.jsx` untuk React — dicari dari nama dasar, bukan
ekstensi (lihat M6 §Keputusan: menambah domain = menambah grader, bukan menambah
cabang di sana-sini).
"""

from pathlib import Path

from app.config import REPO_ROOT
from app.models import ChallengeInstance
from app.services.node_loader import find_instance_file


def hidden_test_path(instance: ChallengeInstance) -> Path:
    return REPO_ROOT / instance.hidden_test_path


def instance_dir(instance: ChallengeInstance) -> Path:
    return hidden_test_path(instance).parent


def sibling(instance: ChallengeInstance, stem: str) -> Path | None:
    return find_instance_file(instance_dir(instance), stem)


def reference_solution_path(instance: ChallengeInstance) -> Path:
    """Solusi referensi — dipakai worked example L3 & gerbang mutu authoring.

    Mengembalikan path walau berkasnya tak ada (pemanggil yang memutuskan artinya);
    kalau tak ketemu, tebak `.py` supaya pesan errornya tetap menunjuk sesuatu.
    """
    found = sibling(instance, "reference_solution")
    return found or (instance_dir(instance) / "reference_solution.py")


#: Ekstensi berkas instance → mode editor Monaco. Ini SATU-SATUNYA pemetaan bahasa di
#: aplikasi, dan sengaja diturunkan dari berkas node itu sendiri — bukan dari
#: `domain_id`. Menambah domain berbahasa lain = menambah satu baris di sini, bukan
#: cabang `if domain == ...` di UI atau di loop.
_EDITOR_LANGUAGE_BY_SUFFIX = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
}


def editor_language(instance: ChallengeInstance) -> str:
    """Bahasa untuk highlight editor sandbox. `plaintext` bila tak dikenali —
    highlight yang salah lebih menyesatkan daripada tanpa highlight."""
    suffix = hidden_test_path(instance).suffix.lower()
    return _EDITOR_LANGUAGE_BY_SUFFIX.get(suffix, "plaintext")


def read_hidden_test(instance: ChallengeInstance) -> str:
    path = hidden_test_path(instance)
    if not path.exists():
        raise FileNotFoundError(
            f"hidden_test tidak ditemukan: {path} (instance {instance.id})"
        )
    return path.read_text(encoding="utf-8")
