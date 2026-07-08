import os

from sqlmodel import Session, SQLModel, create_engine

DB_DIR = os.environ.get("KOMFYRVAKT_DATA_DIR") or ("/data" if os.name != "nt" else "./data")
os.makedirs(DB_DIR, exist_ok=True)

DATABASE_URL = f"sqlite:///{os.path.join(DB_DIR, 'komfyrvakt.db')}"

# check_same_thread=False: FastAPI serves sync endpoints from a threadpool.
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


def init_db() -> None:
    # Enable WAL for concurrent read/write comfort at ingest rates.
    with engine.connect() as conn:
        conn.exec_driver_sql("PRAGMA journal_mode=WAL")
    SQLModel.metadata.create_all(engine)
    _migrate()


def _migrate() -> None:
    """Lightweight migrations for databases created by older versions."""
    with engine.connect() as conn:
        columns = [row[1] for row in conn.exec_driver_sql("PRAGMA table_info(apikey)").fetchall()]
        if columns and "key" not in columns:
            conn.exec_driver_sql('ALTER TABLE apikey ADD COLUMN "key" TEXT')
            conn.commit()


def get_session():
    with Session(engine) as session:
        yield session
