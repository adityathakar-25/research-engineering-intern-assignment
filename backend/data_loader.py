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
    # Always parse as UTC then strip timezone so dt.date gives correct calendar dates.
    # This prevents the X-axis from showing wrong years (e.g. Jul 2024 vs Feb 2025).
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    df["timestamp"] = df["timestamp"].dt.tz_convert("UTC").dt.tz_localize(None)
    return df
