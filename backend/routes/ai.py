"""AI route — RAG-powered chatbot and summary generation."""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api", tags=["ai"])


# ── Chat models ─────────────────────────────────────────────────────
class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., description="User message")
    history: list[ChatMessage] = Field(default_factory=list, description="Prior conversation turns")
    context: str = Field("", description="Optional context filter (e.g. community name)")


class ChatResponse(BaseModel):
    reply: str
    sources: list[str]


# ── Summary models ──────────────────────────────────────────────────
class SummaryResponse(BaseModel):
    query: str
    chart_type: str
    summary: str
    key_findings: list[str]


# ── Routes ──────────────────────────────────────────────────────────
@router.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest):
    """RAG-powered chatbot that answers questions grounded in post data.

    When implemented: retrieves relevant posts from ChromaDB via semantic
    search, constructs a prompt with the retrieved context, and calls an
    LLM (e.g. Gemini / OpenAI) to generate a grounded answer. Returns
    the reply and the post_ids used as sources.
    """
    return ChatResponse(
        reply=(
            f"Based on the data, here's what I found about '{body.message}': "
            "The Anarchism subreddit shows the highest cross-posting activity, "
            "with several authors bridging into Communalists. Key themes include "
            "mutual aid, direct action, and social ecology theory."
        ),
        sources=["1ir8tnp", "1is3abc", "1it7xyz"],
    )


@router.get("/summary", response_model=SummaryResponse)
async def get_summary(
    query: str = Query("", description="Topic or query to summarize"),
    chart_type: str = Query("timeseries", description="Which chart's data to summarize"),
):
    """Generate an AI summary of chart data for a given query.

    When implemented: fetches the relevant chart data, formats it into a
    prompt, and asks an LLM to produce a concise narrative summary with
    key findings.
    """
    return SummaryResponse(
        query=query,
        chart_type=chart_type,
        summary=(
            "Post activity peaked in mid-February 2025, driven primarily by "
            "discussions around social ecology and mutual aid. The Anarchism "
            "subreddit contributed 65% of total volume."
        ),
        key_findings=[
            "Peak activity on Feb 14-15, 2025",
            "Anarchism subreddit dominates with 65% of posts",
            "Cross-posting between Anarchism and Communalists increased 3x",
            "Key bridging authors: RevoltWriter, EcoAnarchist",
        ],
    )
