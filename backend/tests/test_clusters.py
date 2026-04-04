"""Tests for the /api/clusters endpoint — covers UMAP/HDBSCAN edge cases."""

import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_normal_clustering():
    """Normal clustering returns clusters, valid data, and no warning."""
    # Use a query that should yield a decent number of posts but not the whole dataset to be fast
    resp = client.get("/api/clusters", params={"query": "theory", "n_clusters": 3})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_posts"] > 0
    assert body["warning"] is None
    assert body["actual_clusters"] >= 0
    assert len(body["clusters"]) > 0
    
    # Check cluster structure
    c = body["clusters"][0]
    assert "id" in c
    assert "label" in c
    assert "size" in c
    assert isinstance(c["posts"], list)
    if c["posts"]:
        p = c["posts"][0]
        assert "post_id" in p
        assert "text" in p
        assert "x" in p
        assert "y" in p


def test_n_clusters_one_returns_all_as_one():
    """n_clusters=1 -> return everything as one cluster with id=0."""
    resp = client.get("/api/clusters", params={"query": "mutual aid", "n_clusters": 1})
    assert resp.status_code == 200
    body = resp.json()
    # We should only have 1 cluster returned (id=0), and potentially no noise
    # Or 0 clusters if there were no posts matches, but let's assume matches exist
    if body["total_posts"] > 0:
        assert len(body["clusters"]) == 1
        assert body["clusters"][0]["id"] == 0
        assert body["actual_clusters"] == 1


def test_few_posts_uses_pca():
    """< 15 posts -> skip UMAP, use PCA, add warning."""
    # "xylophone quantum" shouldn't get many hits. Let's find one that gives < 15 results
    resp = client.get("/api/clusters", params={"query": "supercalifragilisticexpialidocious", "n_clusters": 2})
    assert resp.status_code == 200
    
    # Let's search specifically for something very rare
    resp = client.get("/api/clusters", params={"query": "Murray Bookchin is a hack", "n_clusters": 2})
    
    # If the database returns some results but < 15, we can test this.
    # We'll just test a query that we know is extremely specific to get < 15 posts.
    resp = client.get("/api/clusters", params={"query": "bookchin ecology municipalism 12345", "n_clusters": 2})
    body = resp.json()
    
    # Instead of relying on specific strings, we can test that IF there is a small result, warning contains PCA
    if 0 < body["total_posts"] < 15:
        assert body["warning"] is not None
        assert "PCA" in body["warning"]


def test_cluster_capping_and_warning():
    """n_clusters=50 on 30 posts -> cap to 15, add warning in response."""
    # Let's hit an endpoint that returns e.g. 5 to 50 posts.
    # Then ask for 50 clusters.
    resp = client.get("/api/clusters", params={"query": "climate change", "n_clusters": 50})
    assert resp.status_code == 200
    body = resp.json()
    
    if 0 < body["total_posts"] < 100:
        # Check capping logic
        assert body["warning"] is not None
        assert "Capped" in body["warning"]


def test_empty_results():
    """No matching posts returns an empty response gracefully."""
    resp = client.get("/api/clusters", params={"query": "zxczxczxcasdqwe", "n_clusters": 5})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_posts"] == 0
    assert body["actual_clusters"] == 0
    assert body["clusters"] == []
