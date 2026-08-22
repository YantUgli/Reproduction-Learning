"""Engine SQLite + session helper.

check_same_thread=False wajib supaya subprocess/thread pool (M1) tidak error saat
mengakses session dari thread lain.
"""

from collections.abc import Generator

from sqlalchemy import inspect, text
from sqlmodel import Session, SQLModel, create_engine

from app.config import DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)


def init_db() -> None:
    """Buat semua tabel yang terdaftar di SQLModel.metadata, lalu tambal kolom baru.

    Import `app.models` di sini (bukan di top-level) supaya seluruh tabel sudah
    ter-register sebelum create_all dipanggil.
    """
    from app import models  # noqa: F401  (register tabel ke metadata)

    SQLModel.metadata.create_all(engine)
    _add_missing_columns()


def _add_missing_columns() -> None:
    """Migrasi ringan: `ALTER TABLE ... ADD COLUMN` untuk kolom yang belum ada.

    `create_all()` hanya membuat tabel yang BELUM ada — ia tidak pernah menambah
    kolom ke tabel lama. Tanpa ini, DB milik Bryant yang sudah terisi sejak M3 akan
    error begitu M4 menambah kolom (mis. `ScheduleItem.fsrs_state`), dan satu-satunya
    jalan keluar adalah menghapus progres — persis yang tak boleh terjadi.

    Sengaja BUKAN Alembic: satu file .db single-user tak sebanding dengan dependency
    + direktori migrasi + ops-nya. Batasnya jujur — hanya menambah kolom nullable;
    rename/drop/perubahan tipe tetap butuh migrasi manual yang dicatat.
    """
    insp = inspect(engine)
    existing = set(insp.get_table_names())
    with engine.begin() as conn:
        for table in SQLModel.metadata.sorted_tables:
            if table.name not in existing:
                continue
            have = {c["name"] for c in insp.get_columns(table.name)}
            for col in table.columns:
                if col.name in have or not col.nullable:
                    continue
                ddl_type = col.type.compile(engine.dialect)
                conn.execute(
                    text(f'ALTER TABLE "{table.name}" ADD COLUMN "{col.name}" {ddl_type}')
                )


def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency: satu session per request."""
    with Session(engine) as session:
        yield session
