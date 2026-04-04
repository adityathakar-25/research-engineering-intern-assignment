"""Clusters route — UMAP + HDBSCAN topic clusters from embeddings."""

from __future__ import annotations

import re
from collections import Counter
from typing import Optional

import hdbscan
import umap
from fastapi import APIRouter, Query
from pydantic import BaseModel
from sklearn.decomposition import PCA

from backend.data_loader import get_dataframe
from backend.routes.search import _get_collection

router = APIRouter(prefix="/api", tags=["clusters"])

STOPWORDS = {"the", "a", "is", "and", "to", "of", "in", "it", "for", "on", "that", "this", "with", "was", "are"}


# ── Response models ─────────────────────────────────────────────────
class ClusterPost(BaseModel):
    post_id: str
    text: str
    author: float | str  # author might be nan/float or str
    x: float
    y: float


class ClusterInfo(BaseModel):
    id: int
    label: str
    size: int
    posts: list[ClusterPost]


class ClustersResponse(BaseModel):
    clusters: list[ClusterInfo]
    total_posts: int
    noise_count: int
    actual_clusters: int
    warning: Optional[str] = None


# ── Helpers ─────────────────────────────────────────────────────────
def _get_top_tokens(texts: list[str]) -> str:
    """Extract top 5 non-stopword tokens from texts."""
    counter = Counter()
    for text in texts:
        # Extract purely lowercase words
        words = re.findall(r'[a-z]+', text.lower())
        for w in words:
            if w not in STOPWORDS:
                counter[w] += 1
    
    # Get top 5
    top = [w for w, _ in counter.most_common(5)]
    return ", ".join(top) if top else "Unlabeled"


# ── Route ───────────────────────────────────────────────────────────
@router.get("/clusters", response_model=ClustersResponse)
async def get_clusters(
    query: str = Query("", description="Search query to filter posts"),
    n_clusters: int = Query(8, ge=1, le=50, description="Number of clusters"),
):
    """Return UMAP-projected points with HDBSCAN cluster labels."""
    df = get_dataframe().copy()
    
    # ── Filter by query ─────────────────────────────────────────────
    if query.strip():
        mask = df["text"].str.contains(query, case=False, na=False)
        df = df[mask]
        
    post_ids = df["post_id"].astype(str).tolist()
    if not post_ids:
        return ClustersResponse(clusters=[], total_posts=0, noise_count=0, actual_clusters=0)
        
    # ── Fetch embeddings and metadata from ChromaDB ─────────────────
    collection = _get_collection()
    results = collection.get(
        ids=post_ids,
        include=["embeddings", "metadatas", "documents"]
    )
    
    embeddings = results.get("embeddings", [])
    documents = results.get("documents", [])
    metadatas = results.get("metadatas", [])
    n_posts = len(embeddings)
    
    if n_posts == 0:
        return ClustersResponse(clusters=[], total_posts=0, noise_count=0, actual_clusters=0)
        
    warning = None
    
    # ── Dimensionality Reduction ────────────────────────────────────
    if n_clusters == 1:
        # Edge case: n_clusters = 1
        labels = [0] * n_posts
        if n_posts >= 2:
            coords = PCA(n_components=2, random_state=42).fit_transform(embeddings)
        else:
            coords = [[0.0, 0.0] for _ in range(n_posts)]
    else:
        # Check if we have enough posts for UMAP (needs 15 points minimum by default)
        if n_posts < 15:
            warning = "Too few posts for UMAP. Used PCA for dimensionality reduction."
            if n_posts >= 2:
                coords = PCA(n_components=2, random_state=42).fit_transform(embeddings)
            else:
                coords = [[0.0, 0.0] for _ in range(n_posts)]
        else:
            coords = umap.UMAP(
                n_components=2, 
                metric='cosine', 
                random_state=42, 
                min_dist=0.1
            ).fit_transform(embeddings)
            
        # ── Adjust n_clusters if necessary ──────────────────────────
        max_possible_clusters = max(1, n_posts // 2)
        capped_n_clusters = n_clusters
        
        if n_clusters > max_possible_clusters:
            capped_n_clusters = max_possible_clusters
            w_msg = f"Requested {n_clusters} clusters but only had {n_posts} posts. Capped n_clusters to {capped_n_clusters}."
            warning = w_msg if not warning else warning + " " + w_msg
            
        # ── Clustering ──────────────────────────────────────────────
        if capped_n_clusters <= 1:
            labels = [0] * n_posts
        else:
            min_cluster_size = max(5, n_posts // capped_n_clusters)
            clusterer = hdbscan.HDBSCAN(min_cluster_size=min_cluster_size)
            labels = clusterer.fit_predict(coords)
            
    # ── Group by cluster label ──────────────────────────────────────
    cluster_map = {}
    for i, label in enumerate(labels):
        cluster_map.setdefault(label, []).append(i)
        
    final_clusters = []
    noise_count = 0
    actual_clusters = sum(1 for k in cluster_map.keys() if k != -1)
    
    for label, indices in cluster_map.items():
        if label == -1:
            lbl_str = "Unclustered"
            noise_count = len(indices)
        else:
            texts_for_label = [documents[i] or metadatas[i].get("text", "") for i in indices]
            lbl_str = _get_top_tokens(texts_for_label)
            
        posts = []
        for i in indices:
            meta = metadatas[i]
            text = documents[i] or meta.get("text", "")
            # Truncate text to 150 chars
            trunc_text = text[:150] + ("..." if len(text) > 150 else "")
            
            author_val = meta.get("author", "")
            if author_val is None:
                author_val = ""
                
            posts.append(ClusterPost(
                post_id=meta.get("post_id", ""),
                text=trunc_text,
                author=str(author_val),
                x=float(coords[i][0]),
                y=float(coords[i][1])
            ))
            
        final_clusters.append(ClusterInfo(
            id=int(label),
            label=lbl_str,
            size=len(posts),
            posts=posts
        ))
        
    return ClustersResponse(
        clusters=final_clusters,
        total_posts=n_posts,
        noise_count=noise_count,
        actual_clusters=actual_clusters,
        warning=warning
    )
