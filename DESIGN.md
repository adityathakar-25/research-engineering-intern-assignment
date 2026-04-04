# NarrativeTrace — Design Document

## Case Study
Russian state media (RT, Sputnik) amplification patterns on Reddit and Twitter
during the 2022 Ukraine invasion (Jan 2022 – Dec 2022).

## The Story
On February 24 2022, Russia invaded Ukraine. RT and Sputnik links flooded 
Reddit and Twitter. Within weeks, both platforms banned these outlets. 
NarrativeTrace answers: Who was amplifying these narratives? Did banning 
actually work, or did the content migrate elsewhere? Which communities were 
most active, and who were the key nodes in the sharing network?

## Five Core Views
1. **Time-series** — Daily post volume around Feb 24 invasion date and 
   ban dates. Shows the spike, the ban effect, and post-ban behavior.
2. **Network graph** — Author co-sharing network with PageRank centrality 
   and Louvain communities. "Remove top node" shows network resilience.
3. **Topic clusters** — UMAP+HDBSCAN clusters showing what narratives 
   were being pushed (bioweapons, NATO, Zelensky, sanctions).
4. **Semantic search** — Find posts about "Western propaganda" without 
   those keywords — tests genuine semantic retrieval.
5. **AI chatbot** — Ask "what happened after the RT ban?" and get an 
   answer grounded in actual data.

## Data Flow
raw CSV → preprocess.py → clean.parquet → embed.py → ChromaDB
                                        ↓
                               FastAPI routes → Next.js frontend

## Edge Cases to Handle
- Empty search query → 400 with message
- Non-English query (Russian text) → embed and search anyway
- n_clusters at extremes (1, 50) → cap gracefully, never crash
- Graph with < 3 nodes → show message, not broken graph
- Date range with no data → empty state card, not error