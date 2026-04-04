"""AI route — Summary generation and Chat with Anthropic."""

from __future__ import annotations

import json
import os
import re

import anthropic
from fastapi import APIRouter, Body, Query
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api", tags=["ai"])

# ── Setup Anthropic Client ──────────────────────────────────────────
# Gracefully fall back to empty string if no key is provided,
# handled during execution via try/except.
_api_key = os.environ.get("ANTHROPIC_API_KEY", "")
client = anthropic.Anthropic(api_key=_api_key)

MODEL_NAME = "claude-sonnet-4-20250514"


# ── Response models ─────────────────────────────────────────────────
class SummaryResponse(BaseModel):
    summary: str | None = None
    error: str | None = None


# ── Chat models ─────────────────────────────────────────────────────
class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., description="User message")
    history: list[ChatMessage] = Field(default_factory=list, description="Prior conversation turns")
    context: str = Field("", description="Optional context filter (e.g. community name)")


class ChatResponse(BaseModel):
    answer: str | None = None
    suggestions: list[str] | None = None
    error: str | None = None


# ── Routes ──────────────────────────────────────────────────────────
@router.post("/summary", response_model=SummaryResponse)
@router.get("/summary", response_model=SummaryResponse)
async def get_summary(
    data: list | dict = Body(...),
    query: str = Query("", description="Topic or query to summarize"),
    chart_type: str = Query("timeseries", description="Which chart's data to summarize"),
):
    """Generate an AI summary of chart data for a given query."""
    system_prompt = (
        "You are an analyst summarizing social media data for a non-technical audience. "
        "Be specific — mention exact numbers, dates, and names from the data. Maximum 3 sentences."
    )

    # Dump the data safely (up to 50 elements if it's a list)
    if isinstance(data, list):
        data_to_pass = data[:50]
    else:
        data_to_pass = data

    user_prompt = (
        f"Here is {chart_type} data for the query '{query}': "
        f"{json.dumps(data_to_pass)}. Write a plain-language summary."
    )

    try:
        response = client.messages.create(
            model=MODEL_NAME,
            max_tokens=250,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )
        return SummaryResponse(summary=response.content[0].text)
    except Exception as e:
        return SummaryResponse(error="AI service unavailable")


@router.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest):
    """RAG-powered chatbot that answers questions grounded in data patterns."""
    system_prompt = (
        "You are an analyst assistant for NarrativeTrace, a social media analysis dashboard studying information integrity. "
        f"The user is currently analyzing: {body.context}. Answer based on data patterns. "
        "After answering, always end with: SUGGESTIONS: [query1] | [query2] | [query3]"
    )

    # Build multi-turn messages
    messages = []
    for m in body.history:
        messages.append({"role": m.role, "content": m.content})
    messages.append({"role": "user", "content": body.message})

    try:
        response = client.messages.create(
            model=MODEL_NAME,
            max_tokens=500,
            system=system_prompt,
            messages=messages
        )
        full_text = response.content[0].text

        # Parse suggestions pattern: SUGGESTIONS: [one] | [two] | [three]
        suggestions_match = re.search(r"SUGGESTIONS:\s*(.*)", full_text, flags=re.IGNORECASE)
        suggestions = []
        if suggestions_match:
            raw_sugs = suggestions_match.group(1).split("|")
            suggestions = [s.strip().strip("[]") for s in raw_sugs if s.strip()]
            # Remove the SUGGESTIONS line from the final answer text
            answer = re.sub(r"SUGGESTIONS:\s*(.*)", "", full_text, flags=re.IGNORECASE).strip()
        else:
            answer = full_text.strip()

        return ChatResponse(answer=answer, suggestions=suggestions)
    except Exception as e:
        return ChatResponse(error="AI service unavailable")

@router.get("/nomic-url")
async def get_nomic_url():
    """Returns the Nomic mapping URL or local filepath endpoint statically."""
    from pathlib import Path
    url_file = Path("data/nomic_url.txt")
    if not url_file.exists():
        return {"url": None}
        
    url = url_file.read_text(encoding="utf-8").strip()
    if url == "local":
        return {"url": "/embedding_viz.html"}
        
    return {"url": url}
