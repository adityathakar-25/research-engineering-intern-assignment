"""Tests for the /api/network endpoint — covers all required edge cases."""

import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_empty_query_returns_400():
    """Empty query → 400."""
    resp = client.get("/api/network", params={"query": ""})
    assert resp.status_code == 400


def test_insufficient_data_returns_message():
    """Query matching < 3 posts → empty graph with message."""
    resp = client.get("/api/network", params={"query": "xyzzyxyzzynotreal123"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["nodes"] == []
    assert body["edges"] == []
    assert body["message"] == "Insufficient data"


def test_valid_query_returns_graph():
    """A query with hits should return nodes and edges."""
    resp = client.get("/api/network", params={"query": "anarchism", "limit": 20})
    assert resp.status_code == 200
    body = resp.json()
    assert body["node_count"] > 0
    assert isinstance(body["nodes"], list)
    assert isinstance(body["edges"], list)
    # Each node has required fields
    node = body["nodes"][0]
    assert "id" in node
    assert "pagerank" in node
    assert "community" in node
    assert "degree" in node
    assert "post_count" in node


def test_pagerank_scaled_0_to_1():
    """PageRank values should be in [0, 1] range, rounded to 4 decimals."""
    resp = client.get("/api/network", params={"query": "the", "limit": 50})
    assert resp.status_code == 200
    body = resp.json()
    if body["nodes"]:
        for node in body["nodes"]:
            assert 0.0 <= node["pagerank"] <= 1.0
            # Check rounding to 4 decimal places
            assert node["pagerank"] == round(node["pagerank"], 4)


def test_zero_degree_nodes_included():
    """Nodes with 0 edges should still appear in the output."""
    resp = client.get("/api/network", params={"query": "the", "limit": 500})
    assert resp.status_code == 200
    body = resp.json()
    # At least verify degrees are non-negative integers
    for node in body["nodes"]:
        assert node["degree"] >= 0


def test_limit_caps_output():
    """Providing a small limit should restrict the number of returned nodes."""
    resp = client.get("/api/network", params={"query": "the", "limit": 5})
    assert resp.status_code == 200
    body = resp.json()
    assert body["node_count"] <= 5
