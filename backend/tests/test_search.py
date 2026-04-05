"""Tests for the /api/search endpoint — covers all critical requirements."""

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_empty_query_returns_400():
    """Empty query → 400 with message."""
    resp = client.post("/api/search", json={"query": ""})
    assert resp.status_code == 400
    assert "cannot be empty" in resp.json()["detail"]


def test_whitespace_only_query_returns_400():
    """Whitespace-only query → 400."""
    resp = client.post("/api/search", json={"query": "   "})
    assert resp.status_code == 400


def test_valid_query_returns_results():
    """Normal search should return ranked results."""
    resp = client.post("/api/search", json={"query": "anarchism", "limit": 5})
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] > 0
    assert len(body["results"]) <= 5
    # Each result has required fields
    r = body["results"][0]
    assert "post_id" in r
    assert "text" in r
    assert "author" in r
    assert "community" in r
    assert "timestamp" in r
    assert "platform" in r
    assert "score" in r


def test_scores_rounded_to_4_decimals():
    """All score values must be rounded to 4 decimal places."""
    resp = client.post("/api/search", json={"query": "mutual aid", "limit": 10})
    assert resp.status_code == 200
    for r in resp.json()["results"]:
        assert r["score"] == round(r["score"], 4)


def test_scores_sorted_descending():
    """Results must be sorted by score descending."""
    resp = client.post("/api/search", json={"query": "solidarity", "limit": 10})
    assert resp.status_code == 200
    scores = [r["score"] for r in resp.json()["results"]]
    assert scores == sorted(scores, reverse=True)


def test_non_english_query_not_rejected():
    """Non-English query → embed and search, never reject."""
    resp = client.post("/api/search", json={"query": "солидарность"})
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body["results"], list)
    # Should return results (embedding model handles multilingual to some degree)
    assert body["count"] >= 0


def test_single_char_query_accepted():
    """Very short query (1 char) → search anyway, do not reject."""
    resp = client.post("/api/search", json={"query": "a"})
    assert resp.status_code == 200
    assert resp.json()["count"] >= 0


def test_low_similarity_still_returns_results():
    """Even with low similarity, results should still be returned."""
    resp = client.post("/api/search", json={"query": "xylophone quantum", "limit": 5})
    assert resp.status_code == 200
    # ChromaDB always returns n_results, even if similarity is low
    assert resp.json()["count"] > 0


def test_suggested_queries_returned():
    """Response should include suggested_queries list."""
    resp = client.post("/api/search", json={"query": "anarchism", "limit": 5})
    assert resp.status_code == 200
    body = resp.json()
    assert "suggested_queries" in body
    assert isinstance(body["suggested_queries"], list)
    assert len(body["suggested_queries"]) <= 3
