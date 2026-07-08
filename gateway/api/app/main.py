"""Sjursen Digital Gateway App & API.

This is the central entry point for the self-hosted appliance.
It provides:
  1. Centralized user authentication (login/logout, user sessions).
  2. Cryptographic licensing verification and activation.
  3. Pluggable sub-app routing (gates access to modules like Komfyrvakt).
  4. Unified Admin UI at root `/`.
"""
import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager

# Resolve monorepo paths on boot so we can import any service module cleanly
current_dir = os.path.dirname(os.path.abspath(__file__))
monorepo_root = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
if monorepo_root not in sys.path:
    sys.path.insert(0, monorepo_root)

from fastapi import Depends, FastAPI, HTTPException, Header, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from sqlmodel import Session, select

from .auth import bootstrap_admin_user, get_current_user, create_session_token, verify_password
from .database import engine, init_db, get_session
from .licensing import verify_license, is_module_licensed
from .models import License, User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gateway")

STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    
    # Initialize mounted sub-app databases on boot
    try:
        from services.komfyrvakt.api.app.database import init_db as init_komfyrvakt_db
        init_komfyrvakt_db()
        logger.info("Successfully initialized Komfyrvakt sub-app database")
    except Exception as err:
        logger.error("Failed to initialize Komfyrvakt sub-app database: %s", err)

    with Session(engine) as session:
        # Bootstrap default admin
        raw_pwd = bootstrap_admin_user(session)
        if raw_pwd:
            logger.warning("=" * 72)
            logger.warning("FIRST STARTUP - gateway admin password created (save it):")
            logger.warning("  Username: admin")
            logger.warning("  Password: %s", raw_pwd)
            logger.warning("=" * 72)
    yield


app = FastAPI(title="Sjursen Digital Gateway", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------- Gating Middleware
@app.middleware("http")
async def gateway_gate_middleware(request: Request, call_next):
    path = request.url.path

    # Ingest / machine logs endpoints bypass all user session authentication.
    # Senders must supply their module-level ingest API Key in X-API-Key.
    if path == "/api/health" or path.endswith("/api/logs"):
        return await call_next(request)

    # If the user tries to access a modular service (e.g. /services/komfyrvakt...)
    if path.startswith("/services/"):
        parts = [p for p in path.split("/") if p]
        if len(parts) >= 2:
            module_name = parts[1]  # e.g. "komfyrvakt"
            
            # 1. Verify User Authentication (session cookie or Authorization header)
            auth_header = request.headers.get("Authorization")
            # We also check for an auth token in the query params or cookies for easy UI asset loading
            auth_token = None
            if auth_header and auth_header.startswith("Bearer "):
                auth_token = auth_header.split(" ")[1]
            else:
                auth_token = request.cookies.get("gateway_session")

            if not auth_token:
                # Redirect UI assets/pages to login; APIs get 401
                if any(path.endswith(ext) for ext in [".js", ".css", ".png", ".jpg", ".html"]) or "api" not in path:
                    return JSONResponse(
                        status_code=401,
                        content={"detail": "Unauthorized. Please log in to the gateway.", "redirect": "/"}
                    )
                return JSONResponse(status_code=401, content={"detail": "Gateway Session Expired"})

            # 2. Check Module Licensing Status
            with Session(engine) as db:
                lic_record = db.exec(select(License)).first()
                license_payload = verify_license(lic_record.license_key) if lic_record else None
                
                if not is_module_licensed(license_payload, module_name):
                    return JSONResponse(
                        status_code=403,
                        content={"detail": f"Module '{module_name}' is not licensed. Activate it at /keys"}
                    )

    return await call_next(request)


# ---------------------------------------------------------------- Gateway Auth API
class LoginIn(BaseModel):
    username: str
    password: str


@app.post("/api/auth/login")
def login(body: LoginIn, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.username == body.username, User.is_active == True)).first()  # noqa: E712
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Invalid username or password")
    
    token = create_session_token(user.username)
    return {"token": token, "username": user.username}


@app.get("/api/auth/me")
def me(current_user: User = Depends(get_current_user)):
    return {"username": current_user.username, "created_at": current_user.created_at}


# ---------------------------------------------------------------- Licensing & Modules API
class LicenseIn(BaseModel):
    license_key: str


@app.get("/api/system/license")
def get_license(session: Session = Depends(get_session)):
    lic = session.exec(select(License)).first()
    if not lic:
        return {"active": False, "dev_mode": is_dev_mode()}
    
    payload = verify_license(lic.license_key)
    if not payload:
        return {"active": False, "error": "Invalid or tampered license key", "dev_mode": is_dev_mode()}
    
    return {
        "active": True,
        "dev_mode": is_dev_mode(),
        "customer_name": payload["customer_name"],
        "customer_email": payload["customer_email"],
        "modules": payload["modules"],
        "expires_at": payload["expires_at"],
    }


@app.post("/api/system/license")
def activate_license(body: LicenseIn, session: Session = Depends(get_session)):
    payload = verify_license(body.license_key)
    if not payload:
        raise HTTPException(status_code=400, detail="Invalid signature. Only official Sjursen Digital licenses are accepted.")
    
    # Store the validated license key (we keep only one active)
    session.exec(select(License)).all() # load
    existing = session.exec(select(License)).first()
    if existing:
        session.delete(existing)
    
    new_lic = License(
        license_key=body.license_key,
        customer_name=payload["customer_name"],
        customer_email=payload["customer_email"],
        modules=payload["modules"],
        expires_at=payload["expires_at"]
    )
    session.add(new_lic)
    session.commit()
    return {"status": "ok", "message": f"Successfully activated license for {payload['customer_name']}"}


@app.delete("/api/system/license")
def revoke_license(session: Session = Depends(get_session)):
    existing = session.exec(select(License)).first()
    if existing:
        session.delete(existing)
        session.commit()
    return {"status": "ok"}


@app.get("/api/system/modules")
def list_modules(session: Session = Depends(get_session)):
    lic = session.exec(select(License)).first()
    payload = verify_license(lic.license_key) if lic else None

    modules_config = [
        {
            "id": "komfyrvakt",
            "name": "Komfyrvakt",
            "description": "Event safety & safety circuit breaker",
            "installed": True,
            "licensed": is_module_licensed(payload, "komfyrvakt"),
            "launch_url": "/services/komfyrvakt/"
        },
        {
            "id": "obsero",
            "name": "Obsero",
            "description": "QR physical maintenance logging",
            "installed": False,  # Ready to download / enable later
            "licensed": is_module_licensed(payload, "obsero"),
            "launch_url": "/services/obsero/"
        }
    ]
    return modules_config


# ---------------------------------------------------------------- Pluggable Sub-App Mounting
# Mount Komfyrvakt if it's available in the monorepo.
try:
    from services.komfyrvakt.api.app.main import app as komfyrvakt_subapp
    app.mount("/services/komfyrvakt", komfyrvakt_subapp)
    logger.info("Successfully loaded and mounted Komfyrvakt module at /services/komfyrvakt")
except ImportError as err:
    logger.error("Failed to import Komfyrvakt module: %s", err)


# SPA entry for Gateway's own admin UI. Excluded from schema.
@app.get("/{full_path:path}", include_in_schema=False)
async def spa(full_path: str):
    candidate = os.path.normpath(os.path.join(STATIC_DIR, full_path))
    if candidate.startswith(os.path.normpath(STATIC_DIR)) and os.path.isfile(candidate):
        return FileResponse(candidate)
    index = os.path.join(STATIC_DIR, "index.html")
    if os.path.isfile(index):
        return FileResponse(index)
    return JSONResponse({"service": "gateway", "hint": "Gateway UI not built."})
