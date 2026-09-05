"""Helper konsol bersama untuk script di `scripts/`.

Dipisah karena tiga script L3 mencetak potongan TEKS SUMBER (dokumentasi resmi penuh
en-dash & kutip melengkung) ke konsol Windows cp1252. M7 sudah membayar bug ini sekali:
`verify_nodes.py` mati UnicodeEncodeError tepat ketika sedang melaporkan kegagalan.
"""
from __future__ import annotations

import sys


def force_utf8_stdio() -> None:
    """Paksa stdout/stderr ke UTF-8 (errors=replace). Aman dipanggil berkali-kali."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass  # stream diganti test (StringIO) — tak apa, tak ada yang perlu dipaksa
