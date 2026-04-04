"""Search route — semantic search over posts using ChromaDB."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api", tags=["search"])


# ── Request / Response models ───────────────────────────────────────
class SearchRequest(BaseModel):
    query: str = Field(..., description="Natural-language search query")
    limit: int = Field(20, ge=1, le=100, description="Max results to return")


class SearchResult(BaseModel):
    post_id: str
    text: str
    author: str
    community: str
    timestamp: str
    platform: str
    score: float  # cosine similarity


class SearchResponse(BaseModel):
    query: str
    count: int
    results: list[SearchResult]


# ── Route ───────────────────────────────────────────────────────────
@router.post("/search", response_model=SearchResponse)
async def search_posts(body: SearchRequest):
    """Semantic search over the embedded posts collection.

    When implemented: encodes the query with all-MiniLM-L6-v2, queries
    ChromaDB for nearest neighbours, and returns ranked results with
    cosine similarity scores.
    """
    mock_results = [
        SearchResult(
            post_id="1ir8tnp",
            text="Who do you think is the most powerful anarchist thinker?",
            author="RevoltWriter",
            community="Anarchism",
            timestamp="2025-02-14T12:30:00+00:00",
            platform="reddit",
            score=0.92,
        ),
        SearchResult(
            post_id="1is3abc",
            text="Social ecology and the rejection of state authority in modern praxis.",
            author="EcoAnarchist",
            community="Communalists",
            timestamp="2025-02-15T08:10:00+00:00",
            platform="reddit",
            score=0.87,
        ),
        SearchResult(
            post_id="1it7xyz",
            text="Mutual aid networks are the foundation of any real movement.",
            author="MutualAidBot",
            community="Anarchism",
            timestamp="2025-02-16T19:45:00+00:00",
            platform="reddit",
            score=0.81,
        ),
    ]
    return SearchResponse(
        query=body.query,
        count=len(mock_results),
        results=mock_results,
    )
