"""NarrativeTrace — FastAPI backend application."""

from __future__ import annotations

import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes import ai, clusters, network, search, timeseries

# ── Load environment variables ──────────────────────────────────────
load_dotenv()

# ── App setup ───────────────────────────────────────────────────────
app = FastAPI(
    title="NarrativeTrace API",
    description="Narrative-tracing analytics for Reddit and social media posts.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
