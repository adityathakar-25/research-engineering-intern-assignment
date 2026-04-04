"""Search route — semantic search over posts using ChromaDB."""

from __future__ import annotations

import pathlib
import re
from functools import lru_cache

import chromadb
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer

router = APIRouter(prefix="/api", tags=["search"])

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent.parent
CHROMA_PATH = str(BASE_DIR / "data" / "chroma")
COLLECTION_NAME = "posts"
MODEL_NAME = "all-MiniLM-L6-v2"


# ── Cached loaders ─────────────────────────────────────────────────
@lru_cache(maxsize=1)
def _get_collection():
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    return client.get_collection(name=COLLECTION_NAME)


@lru_cache(maxsize=1)
def _get_model():
    return SentenceTransformer(MODEL_NAME)


# ── Request / Response models ───────────────────────────────────────
class SearchRequest(BaseModel):
    query: str = Field(..., min_length=0, max_length=500, description="Natural-language search query")
    limit: int = Field(20, ge=1, le=200, description="Max results to return")


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
    suggested_queries: list[str]


# ── Helpers ─────────────────────────────────────────────────────────
_STOPWORDS = frozenset(
    "i me my myself we our ours ourselves you your yours yourself yourselves "
    "he him his himself she her hers herself it its itself they them their "
    "theirs themselves what which who whom this that these those am is are "
    "was were be been being have has had having do does did doing a an the "
    "and but if or because as until while of at by for with about against "
    "between through during before after above below to from up down in out "
    "on off over under again further then once here there when where why how "
    "all both each few more most other some such no nor not only own same so "
    "than too very s t can will just don should now d ll m o re ve y ain "
    "aren couldn didn doesn hadn hasn haven isn ma mightn mustn needn shan "
    "shouldn wasn weren won wouldn also would could much many really like "
    "even still get got one two three make made thing things way people".split()
)


def _extract_suggestions(text: str, n: int = 3) -> list[str]:
    """Extract key noun-phrase-like terms from text using basic regex.

    Returns up to *n* candidate query strings derived from bigrams /
    trigrams of capitalised or meaningful words.
    """
    # Clean the text
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"[^a-zA-Z\s]", " ", text)
    words = text.split()

    # Filter to meaningful words (length > 2, not stopwords)
    meaningful = [
        w for w in words
        if len(w) > 2 and w.lower() not in _STOPWORDS
    ]

    if not meaningful:
        return []

    # Generate bigram candidates
    candidates: list[str] = []
    for i in range(len(meaningful) - 1):
        bigram = f"{meaningful[i]} {meaningful[i + 1]}"
        if bigram.lower() not in {c.lower() for c in candidates}:
            candidates.append(bigram)

    # If we don't have enough bigrams, add single meaningful words
    if len(candidates) < n:
        for w in meaningful:
            if w.lower() not in {c.lower() for c in candidates}:
                candidates.append(w)

    return candidates[:n]


# ── Route ───────────────────────────────────────────────────────────
@router.post("/search", response_model=SearchResponse)
async def search_posts(body: SearchRequest):
    """Semantic search over the embedded posts collection.

    Encodes the query with all-MiniLM-L6-v2, queries ChromaDB for
    nearest neighbours, and returns ranked results with cosine
    similarity scores.
    """
    # ── Validate ────────────────────────────────────────────────────
    if not body.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    # ── Embed the query ─────────────────────────────────────────────
    model = _get_model()
    query_embedding = model.encode([body.query])[0].tolist()

    # ── Query ChromaDB ──────────────────────────────────────────────
    collection = _get_collection()
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=body.limit,
    )

    # ── Build response ──────────────────────────────────────────────
    search_results: list[SearchResult] = []
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    for doc, meta, dist in zip(documents, metadatas, distances):
        # ChromaDB L2 distance → similarity score: 1 - distance
        # For cosine distance, score = 1 - distance (already in [0, 2] range)
        score = round(max(1.0 - dist, 0.0), 4)

        search_results.append(SearchResult(
            post_id=meta.get("post_id", ""),
            text=doc or meta.get("text", ""),
            author=meta.get("author", ""),
            community=meta.get("community", ""),
            timestamp=meta.get("timestamp", ""),
            platform=meta.get("platform", ""),
            score=score,
        ))

    # Sort by score descending (should already be, but enforce)
    search_results.sort(key=lambda r: r.score, reverse=True)

    # ── Suggested queries from the top result ───────────────────────
    suggested: list[str] = []
    if search_results:
        suggested = _extract_suggestions(search_results[0].text)

    return SearchResponse(
        query=body.query,
        count=len(search_results),
        results=search_results,
        suggested_queries=suggested,
    )
