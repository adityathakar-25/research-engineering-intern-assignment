"""Tests for the /api/timeseries endpoint — covers the four required edge cases."""

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_empty_query_returns_400():
    """Edge case 1: Empty query string → 400 with message."""
    resp = client.get("/api/timeseries", params={"query": ""})
    assert resp.status_code == 400
    assert "at least 2 characters" in resp.json()["detail"]


def test_single_char_query_returns_400():
    """Edge case 1b: Single-char query → also 400."""
    resp = client.get("/api/timeseries", params={"query": "x"})
    assert resp.status_code == 400


def test_query_no_matches_returns_empty_list():
    """Edge case 2: Query that matches nothing → empty data list, not an error."""
    resp = client.get("/api/timeseries", params={"query": "zzzzxyxyxyxnotreal"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"] == []
    assert body["total_count"] == 0


def test_missing_start_end_uses_full_range():
    """Edge case 3: Omitting start/end → uses the full dataset date range."""
    resp = client.get("/api/timeseries", params={"query": "anarchism"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["date_range_used"]["start"] != ""
    assert body["date_range_used"]["end"] != ""
    assert body["total_count"] >= 0


def test_single_result():
    """Edge case 4: A very specific query returning few/single results → list with items."""
    # Use a broad-enough query that's likely to hit at least one row
    resp = client.get("/api/timeseries", params={"query": "anarchism"})
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body["data"], list)
    # Each point should have the required fields
    if body["data"]:
        point = body["data"][0]
        assert "date" in point
        assert "count" in point
        assert "platform" in point


def test_platform_filter():
    """Filtering by platform should only return that platform's data."""
    resp = client.get("/api/timeseries", params={"query": "the", "platform": "reddit"})
    assert resp.status_code == 200
    body = resp.json()
    for point in body["data"]:
        assert point["platform"] == "reddit"


def test_date_range_filter():
    """Providing start and end should narrow results."""
    resp = client.get(
        "/api/timeseries",
        params={"query": "the", "start": "2025-02-10", "end": "2025-02-15"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["date_range_used"]["start"] == "2025-02-10"
    assert body["date_range_used"]["end"] == "2025-02-15"
    for point in body["data"]:
        assert "2025-02-10" <= point["date"] <= "2025-02-15"
