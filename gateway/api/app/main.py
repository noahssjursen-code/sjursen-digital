"""Sjursen Digital Gateway App & API.

An out-of-process reverse proxy entrypoint for the Sjursen Digital suite.
Routes incoming traffic to isolated loopback sub-apps.
"""
import logging
import os
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gateway")

STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")

# Dynamic mapping of subordinate loopback ports
SERVICES_CONFIG = {}

# Persistent HTTPX AsyncClient for connection pooling and high performance
proxy_client = httpx.AsyncClient()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await proxy_client.aclose()


app = FastAPI(title="Sjursen Digital Gateway", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/system/modules")
def list_modules():
    """List available applications in the monorepo suite."""
    return [
        {
            "id": "app1",
            "name": "App 1",
            "description": "Ready to design. Click edit in your IDE to swap this module with your next big concept.",
            "installed": False,
            "launch_url": "/services/app1/"
        },
        {
            "id": "app2",
            "name": "App 2",
            "description": "Ready to design. Click edit in your IDE to swap this module with your next big concept.",
            "installed": False,
            "launch_url": "/services/app2/"
        },
        {
            "id": "app3",
            "name": "App 3",
            "description": "Ready to design. Click edit in your IDE to swap this module with your next big concept.",
            "installed": False,
            "launch_url": "/services/app3/"
        }
    ]


# ----------------------------------------------------------- Out-of-Process Reverse Proxy
@app.api_route("/services/{app_id}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
async def proxy_app(app_id: str, path: str, request: Request):
    """Asynchronously reverse-proxies requests to the respective service loopback port."""
    if app_id not in SERVICES_CONFIG:
        return JSONResponse(status_code=404, content={"detail": f"Service '{app_id}' not found."})
        
    config = SERVICES_CONFIG[app_id]
    port = config["port"]
    
    # Construct destination loopback URL (retaining path and query parameters)
    url = f"http://localhost:{port}/{path}"
    if request.url.query:
        url += f"?{request.url.query}"
        
    body = await request.body()
    
    # Exclude connection/hop-by-hop headers to prevent proxy contamination
    headers = {
        k: v for k, v in request.headers.items() 
        if k.lower() not in ("host", "connection", "content-length", "transfer-encoding")
    }
    
    try:
        # Stream response back for memory efficiency and supporting SSE/websockets
        req = proxy_client.build_request(
            method=request.method,
            url=url,
            headers=headers,
            content=body
        )
        resp = await proxy_client.send(req, stream=True)
        
        return StreamingResponse(
            resp.aiter_raw(),
            status_code=resp.status_code,
            headers=dict(resp.headers)
        )
    except httpx.RequestError as exc:
        logger.error("Failed to proxy request to sub-app '%s' at %s: %s", app_id, url, exc)
        return JSONResponse(status_code=502, content={"detail": f"Sub-app '{config['name']}' is offline."})


# Serving the main Gateway Launcher UI
@app.get("/{full_path:path}", include_in_schema=False)
async def spa(full_path: str):
    candidate = os.path.normpath(os.path.join(STATIC_DIR, full_path))
    if candidate.startswith(os.path.normpath(STATIC_DIR)) and os.path.isfile(candidate):
        return FileResponse(candidate)
    index = os.path.join(STATIC_DIR, "index.html")
    if os.path.isfile(index):
        return FileResponse(index)
    return JSONResponse({"service": "gateway", "hint": "Gateway UI static assets not found."})
