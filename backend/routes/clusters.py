"""Clusters route — UMAP + HDBSCAN topic clusters from embeddings."""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

router = APIRouter(prefix="/api", tags=["clusters"])


# ── Response models ─────────────────────────────────────────────────
class ClusterPoint(BaseModel):
    post_id: str
    x: float
    y: float
    cluster: int
    text_preview: str
    community: str


class ClusterInfo(BaseModel):
    cluster_id: int
    size: int
    top_terms: list[str]
    label: str


class ClustersResponse(BaseModel):
    query: str
    n_clusters: int
    points: list[ClusterPoint]
    clusters: list[ClusterInfo]


# ── Route ───────────────────────────────────────────────────────────
@router.get("/clusters", response_model=ClustersResponse)
async def get_clusters(
    query: str = Query("", description="Search query to filter posts"),
    n_clusters: int = Query(8, ge=2, le=50, description="Number of clusters"),
):
    """Return UMAP-projected points with HDBSCAN cluster labels.

    When implemented: retrieves embeddings from ChromaDB, runs UMAP for
    2D projection, applies HDBSCAN clustering, and extracts top terms per
    cluster using TF-IDF.
    """
    mock_points = [
        ClusterPoint(post_id="abc1", x=-2.3, y=1.1, cluster=0, text_preview="Mutual aid networks in ...", community="Anarchism"),
        ClusterPoint(post_id="abc2", x=-1.8, y=0.9, cluster=0, text_preview="Building dual power ...", community="Communalists"),
        ClusterPoint(post_id="abc3", x=3.1, y=-0.5, cluster=1, text_preview="Nihilism and the rejection ...", community="Anarchism"),
        ClusterPoint(post_id="abc4", x=3.4, y=-0.8, cluster=1, text_preview="Against all authority ...", community="Anarchism"),
        ClusterPoint(post_id="abc5", x=0.2, y=3.2, cluster=2, text_preview="Social ecology theory ...", community="Communalists"),
    ]
    mock_clusters = [
        ClusterInfo(cluster_id=0, size=2, top_terms=["mutual aid", "community", "solidarity"], label="Mutual Aid"),
        ClusterInfo(cluster_id=1, size=2, top_terms=["nihilism", "rejection", "authority"], label="Nihilism"),
        ClusterInfo(cluster_id=2, size=1, top_terms=["ecology", "social", "Bookchin"], label="Social Ecology"),
    ]
    return ClustersResponse(
        query=query,
        n_clusters=n_clusters,
        points=mock_points,
        clusters=mock_clusters,
    )
