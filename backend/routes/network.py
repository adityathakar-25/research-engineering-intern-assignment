"""Network route — author co-posting graph with PageRank and Louvain communities."""

from __future__ import annotations

import numpy as np
import community as community_louvain  # python-louvain
import networkx as nx
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from backend.data_loader import get_dataframe

router = APIRouter(prefix="/api", tags=["network"])

# ── Tunables ────────────────────────────────────────────────────────
_CO_WINDOW = np.timedelta64(7 * 24, "h")   # 7 days — wider window for sparse dataset
_MAX_DISPLAY_NODES = 200


# ── Response models ─────────────────────────────────────────────────
class NetworkNode(BaseModel):
    id: str
    pagerank: float
    community: int
    degree: int
    post_count: int


class NetworkEdge(BaseModel):
    source: str
    target: str
    weight: int


class NetworkResponse(BaseModel):
    query: str
    node_count: int
    edge_count: int
    nodes: list[NetworkNode]
    edges: list[NetworkEdge]
    message: str = ""


# ── Helpers ─────────────────────────────────────────────────────────

def _build_graph(df) -> nx.DiGraph:
    """Build a directed co-posting graph from the filtered dataframe.

    Two authors share an edge if they posted in the same subreddit
    within 7 days of each other. Edge weight = number of such
    co-occurrences. Grouping by subreddit (community) gives far more
    connections on a small dataset than grouping by thread.
    """
    G = nx.DiGraph()

    # Add every unique author as a node (even if they have 0 edges)
    post_counts: dict[str, int] = df["author"].value_counts().to_dict()
    for author, count in post_counts.items():
        G.add_node(author, post_count=count)

    # Group by subreddit/community, then check temporal co-occurrence
    group_col = "community" if "community" in df.columns else "platform"
    for _subreddit, group in df.groupby(group_col):
        # Sort by timestamp for efficient sliding-window checking
        group = group.sort_values("timestamp")
        authors = group["author"].values
        timestamps = group["timestamp"].values

        n = len(group)
        for i in range(n):
            ts_i = timestamps[i]
            for j in range(i + 1, n):
                # All comparisons stay in numpy timedelta64 space
                delta = timestamps[j] - ts_i
                if delta > _CO_WINDOW:
                    break  # sorted, so no further j can be within window

                a_i, a_j = str(authors[i]), str(authors[j])
                if a_i == a_j:
                    continue

                # Add / increment directed edges in both directions
                if G.has_edge(a_i, a_j):
                    G[a_i][a_j]["weight"] += 1
                else:
                    G.add_edge(a_i, a_j, weight=1)

                if G.has_edge(a_j, a_i):
                    G[a_j][a_i]["weight"] += 1
                else:
                    G.add_edge(a_j, a_i, weight=1)

    return G


# ── Route ───────────────────────────────────────────────────────────
@router.get("/network", response_model=NetworkResponse)
async def get_network(
    query: str = Query(..., min_length=0, max_length=500, description="Search query to filter posts"),
    limit: int = Query(100, ge=1, le=200, description="Max nodes to return"),
):
    """Return an author co-posting network graph.

    Builds a directed graph where authors are nodes and edges connect
    authors who posted in the same community within 24h. Computes
    PageRank centrality and Louvain community detection.
    """
    if len(query.strip()) < 2:
        raise HTTPException(status_code=400, detail="Query must be at least 2 characters")

    df = get_dataframe().copy()

    # ── Filter by query ─────────────────────────────────────────────
    mask = df["text"].str.contains(query, case=False, na=False)
    df = df[mask]

    # ── Edge case: fewer than 2 matching posts ──────────────────────
    min_posts = 2 if len(query.strip()) > 2 else 3
    if len(df) < min_posts:
        return NetworkResponse(
            query=query,
            node_count=0,
            edge_count=0,
            nodes=[],
            edges=[],
            message="Insufficient data",
        )

    # ── Build graph ─────────────────────────────────────────────────
    G = _build_graph(df)

    # ── PageRank ────────────────────────────────────────────────────
    pr = nx.pagerank(G, alpha=0.85)

    # Scale to 0–1 range (max becomes 1.0)
    max_pr = max(pr.values()) if pr else 1.0
    if max_pr > 0:
        pr = {k: round(v / max_pr, 4) for k, v in pr.items()}
    else:
        pr = {k: 0.0 for k in pr}

    # ── Louvain community detection (on undirected copy) ────────────
    G_undirected = G.to_undirected()
    if G_undirected.number_of_nodes() > 0:
        partition = community_louvain.best_partition(G_undirected)
    else:
        partition = {}

    # ── Cap large graphs at _MAX_DISPLAY_NODES ──────────────────────
    effective_limit = min(limit, _MAX_DISPLAY_NODES) if G.number_of_nodes() > 500 else limit
    top_authors = sorted(pr, key=pr.get, reverse=True)[:effective_limit]
    top_set = set(top_authors)

    # ── Build response nodes ────────────────────────────────────────
    post_counts = nx.get_node_attributes(G, "post_count")
    nodes = [
        NetworkNode(
            id=author,
            pagerank=pr.get(author, 0.0),
            community=partition.get(author, 0),
            degree=G.degree(author),
            post_count=post_counts.get(author, 0),
        )
        for author in top_authors
    ]

    # ── Build response edges (only between nodes in the result set) ─
    edges = [
        NetworkEdge(source=u, target=v, weight=int(d["weight"]))
        for u, v, d in G.edges(data=True)
        if u in top_set and v in top_set
    ]

    return NetworkResponse(
        query=query,
        node_count=len(nodes),
        edge_count=len(edges),
        nodes=nodes,
        edges=edges,
    )
