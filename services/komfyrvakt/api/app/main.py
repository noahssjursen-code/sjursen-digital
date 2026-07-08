import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from sqlmodel import Session

from .auth import bootstrap_admin_key
from .database import engine, init_db
from .routers import router
from .scheduler import run_scheduler
from .selftest import run_startup_selftest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("komfyrvakt")

STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    with Session(engine) as session:
        raw = bootstrap_admin_key(session)
    if raw:
        logger.info("First startup - admin API key created: %s (also visible on the dashboard's Keys page)", raw)
    elif os.environ.get("KOMFYRVAKT_ADMIN_KEY"):
        logger.info("Admin key from KOMFYRVAKT_ADMIN_KEY is active")

    tasks = [asyncio.create_task(run_scheduler())]
    if os.environ.get("KOMFYRVAKT_SELFTEST", "1") != "0":
        tasks.append(asyncio.create_task(run_startup_selftest(app)))
    yield
    for task in tasks:
        task.cancel()


app = FastAPI(title="Komfyrvakt", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


# SPA fallback: serve built UI files, and index.html for client-side routes.
# Registered last so /api/* always wins.
@app.get("/{full_path:path}", include_in_schema=False)
async def spa(full_path: str):
    candidate = os.path.normpath(os.path.join(STATIC_DIR, full_path))
    if candidate.startswith(os.path.normpath(STATIC_DIR)) and os.path.isfile(candidate):
        return FileResponse(candidate)
    index = os.path.join(STATIC_DIR, "index.html")
    if os.path.isfile(index):
        return FileResponse(index)
    return JSONResponse({"service": "komfyrvakt", "hint": "UI not built. See /docs for the API."})
