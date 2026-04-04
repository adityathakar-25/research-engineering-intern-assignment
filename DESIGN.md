# NarrativeTrace — Design Document

## Case Study
Leftist political ideology spread across Reddit (February 2025).
Subreddits: r/Anarchism, r/Communalists, and related communities.

## The Story
How do anarchist and leftist ideological narratives spread across Reddit?
NarrativeTrace answers: Which subreddits cross-post the same content?
Who are the key amplifiers bridging communities? What ideological clusters
exist — anarcho-nihilism vs social ecology vs communalism? Do bans or
removals affect narrative reach?

## Five Core Views
1. Time-series — Daily post volume per subreddit over Feb 2025.
   Shows activity spikes and community engagement patterns.
2. Network graph — Author co-posting network with PageRank centrality
   and Louvain communities. Shows who bridges multiple subreddits.
3. Topic clusters — UMAP+HDBSCAN clusters revealing ideological camps
   (nihilism, social ecology, mutual aid, direct action, theory).
4. Semantic search — Find posts about "rejecting state authority" without
   those keywords — tests genuine semantic retrieval.
5. AI chatbot — Ask "which authors post across multiple communities?"
   and get an answer grounded in actual data.

## Data Flow
data.jsonl → preprocess.py → clean.parquet → embed.py → ChromaDB
                                            ↓
                                   FastAPI routes → Next.js frontend

## Edge Cases
- Empty search → 400
- Non-English query → embed and search anyway
- n_clusters extremes (1, 50) → cap gracefully
- Graph < 3 nodes → message not broken graph
- Date range with no data → empty state card