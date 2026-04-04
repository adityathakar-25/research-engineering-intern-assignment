"""Explore every raw data file in data/raw/ (CSV and JSONL).

Prints filename, row count, column names, dtypes, date ranges of
timestamp-like columns, null counts, and sample rows — then returns
a dict summary for interactive inspection.
"""

import pathlib

import pandas as pd

RAW_DIR = pathlib.Path(__file__).parent / "data" / "raw"

# Columns whose names suggest they hold timestamps
_TS_HINTS = {"timestamp", "created_utc", "created_at", "date", "datetime", "time"}


def _detect_timestamp_cols(df: pd.DataFrame) -> list[str]:
    """Return column names that look like timestamps."""
    ts_cols: list[str] = []
    for col in df.columns:
        if col.lower() in _TS_HINTS:
            ts_cols.append(col)
            continue
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            ts_cols.append(col)
    return ts_cols


def _load_file(path: pathlib.Path) -> pd.DataFrame | None:
    """Load a single CSV or JSONL file into a DataFrame."""
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix in {".jsonl", ".ndjson"}:
        return pd.read_json(path, lines=True)
    return None


def explore(raw_dir: pathlib.Path = RAW_DIR) -> dict:
    """Explore all supported files in *raw_dir* and return a summary dict.

    Supported formats: .csv, .jsonl, .ndjson
    """
    summary: dict = {}
    files = sorted(raw_dir.glob("*"))
    supported = [f for f in files if f.suffix.lower() in {".csv", ".jsonl", ".ndjson"}]

    if not supported:
        print(f"No CSV/JSONL files found in {raw_dir}")
        return summary

    for path in supported:
        print("=" * 72)
        print(f"FILE: {path.name}")
        print("=" * 72)

        df = _load_file(path)
        if df is None:
            print("  ⚠ Unsupported format, skipping.\n")
            continue

        # ── Row count ───────────────────────────────────────────────
        print(f"\nRows: {len(df):,}")

        # ── Columns & dtypes ────────────────────────────────────────
        print(f"\nColumns ({len(df.columns)}):")
        for col in df.columns:
            print(f"  {col:30s}  {df[col].dtype}")

        # ── Date ranges ────────────────────────────────────────────
        ts_cols = _detect_timestamp_cols(df)
        if ts_cols:
            print("\nTimestamp ranges:")
            for col in ts_cols:
                series = pd.to_datetime(df[col], errors="coerce", unit="s" if df[col].dtype.kind in "fi" else None)
                valid = series.dropna()
                if not valid.empty:
                    print(f"  {col}: {valid.min()} → {valid.max()}")
                else:
                    print(f"  {col}: (no valid timestamps)")
        else:
            print("\nNo timestamp columns detected.")

        # ── Null counts ─────────────────────────────────────────────
        nulls = df.isnull().sum()
        print("\nNull counts:")
        for col, n in nulls.items():
            pct = n / len(df) * 100 if len(df) else 0
            print(f"  {col:30s}  {n:>7,}  ({pct:.1f}%)")

        # ── Sample rows ────────────────────────────────────────────
        print("\nSample rows (first 3):")
        print(df.head(3).to_string())
        print()

        # ── Build summary entry ─────────────────────────────────────
        summary[path.name] = {
            "path": str(path),
            "rows": len(df),
            "columns": list(df.columns),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "null_counts": nulls.to_dict(),
            "timestamp_cols": ts_cols,
            "sample": df.head(3).to_dict(orient="records"),
        }

    print(f"\nExplored {len(summary)} file(s).")
    return summary


if __name__ == "__main__":
    result = explore()
