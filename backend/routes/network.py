"""Network route — author co-posting graph with centrality scores."""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

router = APIRouter(prefix="/api", tags=["network"])


# ── Response models ─────────────────────────────────────────────────
class NetworkNode(BaseModel):
    id: str
    label: str
    community: int
    pagerank: float
    post_count: int


class NetworkEdge(BaseModel):
    source: str
    target: str
    weight: float


class NetworkResponse(BaseModel):
    query: str
    node_count: int
    edge_count: int
    nodes: list[NetworkNode]
    edges: list[NetworkEdge]


# ── Route ───────────────────────────────────────────────────────────
@router.get("/network", response_model=NetworkResponse)
async def get_network(
    query: str = Query("", description="Search query to filter posts"),
    limit: int = Query(100, ge=1, le=500, description="Max nodes to return"),
):
    """Return an author co-posting network graph.

    When implemented: builds a graph where authors are nodes and edges
    connect authors who posted in the same community. Computes PageRank
    centrality and Louvain community detection.
    """
    mock_nodes = [
        NetworkNode(id="author_1", label="RevoltWriter", community=0, pagerank=0.034, post_count=28),
        NetworkNode(id="author_2", label="MutualAidBot", community=0, pagerank=0.028, post_count=19),
        NetworkNode(id="author_3", label="EcoAnarchist", community=1, pagerank=0.021, post_count=15),
        NetworkNode(id="author_4", label="DirectAction99", community=1, pagerank=0.019, post_count=12),
        NetworkNode(id="author_5", label="Communalist_X", community=2, pagerank=0.015, post_count=9),
    ]
    mock_edges = [
        NetworkEdge(source="author_1", target="author_2", weight=5.0),
        NetworkEdge(source="author_1", target="author_3", weight=3.0),
        NetworkEdge(source="author_2", target="author_4", weight=2.0),
        NetworkEdge(source="author_3", target="author_5", weight=4.0),
        NetworkEdge(source="author_4", target="author_5", weight=1.0),
    ]
    return NetworkResponse(
        query=query,
        node_count=len(mock_nodes),
        edge_count=len(mock_edges),
        nodes=mock_nodes,
        edges=mock_edges,
    )
