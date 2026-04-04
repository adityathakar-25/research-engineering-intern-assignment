"""Preprocess the raw SimPPL Reddit dataset into a clean Parquet file."""

import html
import logging
import pathlib

import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
)
log = logging.getLogger(__name__)

RAW_PATH = pathlib.Path(__file__).resolve().parent.parent / "data" / "raw" / "data.jsonl"
OUT_PATH = pathlib.Path(__file__).resolve().parent.parent / "data" / "processed" / "clean.parquet"

KEEP_COLUMNS = {
    "id": "post_id",
    "author": "author",
    "subreddit": "community",
    "score": "engagement",
    "num_comments": "num_comments",
    "created_utc": "timestamp",
    "selftext": "selftext",
    "title": "title",
}


def preprocess() -> pd.DataFrame:
    # ------------------------------------------------------------------
    # 1. Load raw JSONL
    # ------------------------------------------------------------------
    df = pd.read_json(RAW_PATH, lines=True)
    log.info("Loaded raw file: %d rows", len(df))

    # ------------------------------------------------------------------
    # 2. Flatten the nested "data" column
    # ------------------------------------------------------------------
    flat = pd.json_normalize(df["data"])
    log.info("After flattening 'data' column: %d rows, %d cols", len(flat), len(flat.columns))

    # ------------------------------------------------------------------
    # 3. Keep & rename columns
    # ------------------------------------------------------------------
    df = flat[list(KEEP_COLUMNS.keys())].rename(columns=KEEP_COLUMNS)
    log.info("After selecting/renaming columns: %d rows", len(df))

    # Convert timestamp from Unix epoch to UTC datetime
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s", utc=True)

    # ------------------------------------------------------------------
    # 4. URL: prefer url_overridden_by_dest, fall back to url
    # ------------------------------------------------------------------
    if "url_overridden_by_dest" in flat.columns:
        df["url"] = flat["url_overridden_by_dest"].where(
            flat["url_overridden_by_dest"].notna() & (flat["url_overridden_by_dest"] != ""),
            flat["url"],
        )
        log.info("URL column: used url_overridden_by_dest with url fallback")
    else:
        df["url"] = flat["url"]
        log.info("URL column: url_overridden_by_dest not found, using url")

    # ------------------------------------------------------------------
    # 5. Create "text" column = title + " " + selftext
    # ------------------------------------------------------------------
    df["selftext"] = df["selftext"].fillna("")
    df["text"] = df["title"] + " " + df["selftext"]
    log.info("After creating 'text' column: %d rows", len(df))

    # ------------------------------------------------------------------
    # 6. Add hardcoded "platform" column
    # ------------------------------------------------------------------
    df["platform"] = "reddit"

    # ------------------------------------------------------------------
    # 7. Drop rows where text is blank, "[deleted]", or "[removed]"
    # ------------------------------------------------------------------
    before = len(df)
    df = df[~df["text"].str.strip().isin(["", "[deleted]", "[removed]"])]
    log.info("Dropped %d blank/deleted/removed rows: %d -> %d", before - len(df), before, len(df))

    # ------------------------------------------------------------------
    # 8. Strip HTML entities from text
    # ------------------------------------------------------------------
    df["text"] = df["text"].apply(html.unescape)
    log.info("After HTML-unescaping text: %d rows", len(df))

    # ------------------------------------------------------------------
    # 9. Deduplicate by post_id
    # ------------------------------------------------------------------
    before = len(df)
    df = df.drop_duplicates(subset="post_id")
    log.info("Dropped %d duplicate post_ids: %d -> %d", before - len(df), before, len(df))

    # ------------------------------------------------------------------
    # 10. Save to Parquet
    # ------------------------------------------------------------------
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT_PATH, index=False)
    log.info("Saved %d rows to %s", len(df), OUT_PATH)

    return df


if __name__ == "__main__":
    preprocess()
