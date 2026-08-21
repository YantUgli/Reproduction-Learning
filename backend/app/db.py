"""Engine SQLite + session helper.

check_same_thread=False wajib supaya subprocess/thread pool (M1) tidak error saat
mengakses session dari thread lain.
"""

from collections.abc import Generator

from sqlmodel import Session, SQLModel, create_engine

from app.config import DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)


def init_db() -> None:
    """Buat semua tabel yang terdaftar di SQLModel.metadata.

    Import `app.models` di sini (bukan di top-level) supaya seluruh tabel sudah
    ter-register sebelum create_all dipanggil.
    """
    from app import models  # noqa: F401  (register tabel ke metadata)

    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency: satu session per request."""
    with Session(engine) as session:
        yield session
