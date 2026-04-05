"""AI route — Summary generation and Chat with Google Gemini (google-genai SDK)."""

from __future__ import annotations

import json
import os
import re
import time

from google import genai
from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api", tags=["ai"])

GEMINI_MODEL = "gemini-2.0-flash"

# Simple in-memory cache for summaries
summary_cache: dict = {}


# ── Gemini client factory ────────────────────────────────────────────
def get_client():
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise ValueError("GEMINI_API_KEY not set")
    return genai.Client(api_key=key)


def _generate_with_retry(client, prompt: str, max_retries: int = 3) -> str:
    """Call Gemini with exponential backoff on rate-limit errors."""
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
            )
            return response.text
        except Exception as e:
            err_str = str(e).lower()
            is_rate_limit = "429" in err_str or "resource_exhausted" in err_str or "rate" in err_str
            if is_rate_limit and attempt < max_retries - 1:
                wait = 2 ** (attempt + 1)   # 2s, 4s, 8s
                print(f"[gemini] Rate limited, retrying in {wait}s (attempt {attempt+1}/{max_retries})")
                time.sleep(wait)
            else:
                raise


# ── Response models ─────────────────────────────────────────────────
class SummaryResponse(BaseModel):
    summary: str | None = None
    error: str | None = None


class SummaryRequest(BaseModel):
    query: str = Field("", description="Topic or query to summarize")
    chart_type: str = Field("timeseries", description="Which chart's data to summarize")
    data: list = Field(default_factory=list, description="Chart data to summarize")


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., description="User message")
    history: list[ChatMessage] = Field(default_factory=list)
    context: str = Field("", description="Dashboard context")


class ChatResponse(BaseModel):
    answer: str | None = None
    suggestions: list[str] | None = None
    error: str | None = None


# ── Routes ──────────────────────────────────────────────────────────
@router.post("/summary", response_model=SummaryResponse)
async def get_summary(body: SummaryRequest):
    """Generate an AI summary of chart data for a given query."""

    # Check cache first
    cache_key = (body.query, body.chart_type)
    if cache_key in summary_cache:
        ts, cached = summary_cache[cache_key]
        if time.time() - ts < 60:
            return SummaryResponse(summary=cached)

    try:
        client = get_client()
    except ValueError:
        return SummaryResponse(error="AI service unavailable")

    system_prompt = (
        "You are an analyst summarizing social media data for a non-technical audience. "
        "Be specific — mention exact numbers, dates, and names from the data. Maximum 3 sentences."
    )

    user_prompt = (
        f"Here is {body.chart_type} data for the query '{body.query}': "
        f"{json.dumps(body.data[:50])}. Write a plain-language summary."
    )

    full_prompt = f"{system_prompt}\n\n{user_prompt}"

    try:
        text = _generate_with_retry(client, full_prompt)
        summary_cache[cache_key] = (time.time(), text)
        return SummaryResponse(summary=text)
    except Exception as e:
        print(f"[summary] Gemini error: {e}")
        return SummaryResponse(error="AI rate limited — try again in a minute")


@router.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest):
    """Chatbot that answers questions grounded in data patterns."""

    try:
        client = get_client()
    except ValueError:
        return ChatResponse(error="AI service unavailable")

    system_prompt = (
        "You are a data analyst assistant for NarrativeTrace. "
        "You have full access to analyze the Reddit dataset (Feb 2025, 8799 posts). "
        "Always give specific answers with actual names, numbers, and subreddits from the data. "
        "Never say you cannot access data — you are summarizing patterns from the dashboard's live data.\n"
        f"Current context: {body.context}\n"
        "After answering, end with: SUGGESTIONS: [q1] | [q2] | [q3]"
    )

    history_text = ""
    for m in body.history:
        role_label = "User" if m.role == "user" else "Assistant"
        history_text += f"{role_label}: {m.content}\n"

    full_prompt = (
        f"{system_prompt}\n\n"
        f"{history_text}"
        f"User: {body.message}\nAssistant:"
    )

    try:
        full_text = _generate_with_retry(client, full_prompt)

        suggestions_match = re.search(r"SUGGESTIONS:\s*(.*)", full_text, flags=re.IGNORECASE)
        suggestions = []
        if suggestions_match:
            raw_sugs = suggestions_match.group(1).split("|")
            suggestions = [s.strip().strip("[]") for s in raw_sugs if s.strip()]
            answer = re.sub(r"SUGGESTIONS:\s*(.*)", "", full_text, flags=re.IGNORECASE).strip()
        else:
            answer = full_text.strip()

        return ChatResponse(answer=answer, suggestions=suggestions)
    except Exception as e:
        print(f"[chat] Gemini error: {e}")
        return ChatResponse(error="AI rate limited — try again in a minute")


@router.get("/nomic-url")
async def get_nomic_url():
    """Returns the Nomic mapping URL or local filepath."""
    from pathlib import Path
    url_file = Path("data/nomic_url.txt")
    if not url_file.exists():
        return {"url": None}
    url = url_file.read_text(encoding="utf-8").strip()
    if url == "local":
        return {"url": "/embedding_viz.html"}
    return {"url": url}