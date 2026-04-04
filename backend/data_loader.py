"""Shared data loader — loads clean.parquet once and caches it."""

from __future__ import annotations

import pathlib
from functools import lru_cache

import pandas as pd

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
PARQUET_PATH = BASE_DIR / "data" / "processed" / "clean.parquet"


@lru_cache(maxsize=1)
def get_dataframe() -> pd.DataFrame:
    """Load the cleaned parquet file into a DataFrame (cached after first call)."""
    df = pd.read_parquet(PARQUET_PATH)
    # Ensure timestamp is datetime for downstream filtering
    if not pd.api.types.is_datetime64_any_dtype(df["timestamp"]):
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    return df
