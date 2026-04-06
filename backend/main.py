"""NarrativeTrace — FastAPI backend application."""
from __future__ import annotations

from dotenv import load_dotenv
from pathlib import Path
env_path = Path(__file__).parent / ".env"
if not env_path.exists():
    env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

import os
import sys

# Ensure the backend directory is in the path to allow 'routes' to be imported
# when someone runs `uvicorn backend.main:app` from the project root.
backend_dir = str(Path(__file__).parent.resolve())
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request
from fastapi.responses import JSONResponse

from routes import ai, clusters, network, search, timeseries

# ── App setup ───────────────────────────────────────────────────────
app = FastAPI(
    title="NarrativeTrace API",
    description="Narrative-tracing analytics for Reddit and social media posts.",
    version="0.1.0",
)

allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://192.168.1.20:3000",
    "https://research-engineering-intern-assignm-henna.vercel.app"
]
if os.getenv("FRONTEND_URL"):
    allowed_origins.append(os.getenv("FRONTEND_URL"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://.*\.vercel\.app|http://.*:3000",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Include routers ─────────────────────────────────────────────────
app.include_router(timeseries.router)
app.include_router(network.router)
app.include_router(clusters.router)
app.include_router(search.router)
app.include_router(ai.router)


# ── Health check ────────────────────────────────────────────────────
@app.get("/health", tags=["health"])
async def health():
    """Simple liveness probe."""
    return {"status": "ok"}


# ── Global Exception Handler ────────────────────────────────────────
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all to safely return 500 without exposing stack trace."""
    return JSONResponse(
        status_code=500,
        content={"error": str(exc), "code": 500}
    )
