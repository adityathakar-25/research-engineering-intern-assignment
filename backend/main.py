"""NarrativeTrace — FastAPI backend application."""
from __future__ import annotations

from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path(__file__).parent.parent / ".env")

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request
from fastapi.responses import JSONResponse

from backend.routes import ai, clusters, network, search, timeseries

# ── App setup ───────────────────────────────────────────────────────
app = FastAPI(
    title="NarrativeTrace API",
    description="Narrative-tracing analytics for Reddit and social media posts.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://192.168.1.20:3000"
    ],
    allow_origin_regex=r"http://.*:3000",
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
