"""Generate sentence embeddings for clean posts and store them in ChromaDB."""

import logging
import pathlib

import chromadb
import pandas as pd
from sentence_transformers import SentenceTransformer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
)
log = logging.getLogger(__name__)

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
PARQUET_PATH = BASE_DIR / "data" / "processed" / "clean.parquet"
CHROMA_PATH = str(BASE_DIR / "data" / "chroma")
COLLECTION_NAME = "posts"
MODEL_NAME = "all-MiniLM-L6-v2"
BATCH_SIZE = 256


def _safe_meta(value):
    """Coerce a value to str/int/float for ChromaDB metadata compatibility."""
    if isinstance(value, (str, int, float)):
        return value
    if value is None:
        return ""
    return str(value)


def embed() -> int:
    # ------------------------------------------------------------------
    # 1. Load clean parquet
    # ------------------------------------------------------------------
    df = pd.read_parquet(PARQUET_PATH)
    log.info("Loaded %d rows from %s", len(df), PARQUET_PATH.name)

    # ------------------------------------------------------------------
    # 2. Init ChromaDB and check if already embedded
    # ------------------------------------------------------------------
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_or_create_collection(name=COLLECTION_NAME)

    existing = collection.count()
    if existing >= len(df):
        log.info(
            "Collection '%s' already has %d docs (parquet has %d). Skipping.",
            COLLECTION_NAME, existing, len(df),
        )
        print(f"Final count: {existing}")
        return existing

    if existing > 0:
        log.info("Collection has %d docs but parquet has %d — re-embedding from scratch.", existing, len(df))
        client.delete_collection(name=COLLECTION_NAME)
        collection = client.create_collection(name=COLLECTION_NAME)

    # ------------------------------------------------------------------
    # 3. Load sentence-transformers model (cached after first download)
    # ------------------------------------------------------------------
    log.info("Loading model '%s' ...", MODEL_NAME)
    model = SentenceTransformer(MODEL_NAME)
    log.info("Model loaded.")

    # ------------------------------------------------------------------
    # 4. Generate embeddings in batches and upsert into ChromaDB
    # ------------------------------------------------------------------
    texts = df["text"].tolist()
    total = len(texts)

    for start in range(0, total, BATCH_SIZE):
        end = min(start + BATCH_SIZE, total)
        batch_texts = texts[start:end]
        batch_df = df.iloc[start:end]

        # Encode
        embeddings = model.encode(batch_texts, show_progress_bar=False).tolist()

        # Build metadata list
        metadatas = []
        for _, row in batch_df.iterrows():
            metadatas.append({
                "post_id": _safe_meta(row["post_id"]),
                "author": _safe_meta(row["author"]),
                "timestamp": row["timestamp"].isoformat() if pd.notna(row["timestamp"]) else "",
                "platform": _safe_meta(row["platform"]),
                "community": _safe_meta(row["community"]),
                "text": _safe_meta(row["text"][:500]),
            })

        ids = [str(row["post_id"]) for _, row in batch_df.iterrows()]

        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=batch_texts,
            metadatas=metadatas,
        )

        # Progress logging every 1000 rows
        if end % 1000 < BATCH_SIZE or end == total:
            log.info("Embedded %d / %d rows (%.1f%%)", end, total, end / total * 100)

    # ------------------------------------------------------------------
    # 5. Final count
    # ------------------------------------------------------------------
    final = collection.count()
    log.info("Done. Collection '%s' has %d documents.", COLLECTION_NAME, final)
    print(f"Final count: {final}")
    return final


if __name__ == "__main__":
    embed()
