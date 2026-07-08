import os
from sqlmodel import SQLModel, create_engine, Session

DB_DIR = "/data" if os.name != "nt" else "./data"
os.makedirs(DB_DIR, exist_ok=True)

DATABASE_URL = f"sqlite:///{DB_DIR}/komfyrvakt.db"

# connect_args={"check_same_thread": False} is required only for SQLite
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
