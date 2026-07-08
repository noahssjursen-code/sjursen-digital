from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from contextlib import asynccontextmanager
from typing import List
import os

from app.database import create_db_and_tables, get_session
from app.models import Stream, StreamCreate, LogEntry, LogEntryCreate, Rule, Alert

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite tables on startup
    create_db_and_tables()
    yield

app = FastAPI(
    title="Komfyrvakt API",
    description="The self-hostable event monitoring and decision engine",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Ingestion & Event API Endpoints ---

@app.post("/api/streams", response_model=Stream, status_code=status.HTTP_201_CREATED)
def create_stream(stream: StreamCreate, session: Session = Depends(get_session)):
    db_stream = Stream.model_validate(stream)
    session.add(db_stream)
    session.commit()
    session.refresh(db_stream)
    return db_stream

@app.get("/api/streams", response_model=List[Stream])
def read_streams(session: Session = Depends(get_session)):
    streams = session.exec(select(Stream)).all()
    return streams

@app.post("/api/logs", response_model=LogEntry, status_code=status.HTTP_201_CREATED)
def post_log(log: LogEntryCreate, session: Session = Depends(get_session)):
    # Verify stream exists
    db_stream = session.get(Stream, log.stream_id)
    if not db_stream:
        raise HTTPException(status_code=404, detail="Stream not found")
        
    db_log = LogEntry.model_validate(log)
    session.add(db_log)
    
    # ----------------------------------------------------
    # TODO: Stream processing pipeline trigger
    # In a full build, this will analyze thresholds/duration rules
    # and trigger an async task queue or AI analysis block
    # ----------------------------------------------------
    
    session.commit()
    session.refresh(db_log)
    return db_log

@app.get("/api/logs/{stream_id}", response_model=List[LogEntry])
def read_logs(stream_id: int, limit: int = 100, session: Session = Depends(get_session)):
    logs = session.exec(
        select(LogEntry)
        .where(LogEntry.stream_id == stream_id)
        .order_by(LogEntry.timestamp.desc())
        .limit(limit)
    ).all()
    return logs

# --- Serving Frontend SPA in Production ---

# Path to static folder where compiled SvelteKit SPA will sit
UI_DIST_DIR = os.path.join(os.path.dirname(__file__), "../static")

if os.path.exists(UI_DIST_DIR):
    app.mount("/", StaticFiles(directory=UI_DIST_DIR, html=True), name="static")
else:
    @app.get("/")
    def read_root():
        return {
            "status": "online",
            "message": "Komfyrvakt API running. Mount compiled UI to static directory to serve SvelteKit app."
        }
