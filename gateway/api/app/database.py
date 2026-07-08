import os

from sqlmodel import Session, SQLModel, create_engine

DB_DIR = os.environ.get("SJURSEN_DIGITAL_DATA_DIR") or ("/data" if os.name != "nt" else "./data")
os.makedirs(DB_DIR, exist_ok=True)

DATABASE_URL = f"sqlite:///{os.path.join(DB_DIR, 'gateway.db')}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


def init_db() -> None:
    with engine.connect() as conn:
        conn.exec_driver_sql("PRAGMA journal_mode=WAL")
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
