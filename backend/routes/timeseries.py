"""Time-series route — daily post volume over a date range."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from data_loader import get_dataframe

router = APIRouter(prefix="/api", tags=["timeseries"])


# ── Response models ─────────────────────────────────────────────────
class TimeseriesPoint(BaseModel):
    date: str
    count: int
    platform: str


class DateRange(BaseModel):
    start: str
    end: str


class TimeseriesResponse(BaseModel):
    query: str
    total_count: int
    date_range_used: DateRange
    data: list[TimeseriesPoint]


# ── Route ───────────────────────────────────────────────────────────
@router.get("/timeseries", response_model=TimeseriesResponse)
async def get_timeseries(
    query: str = Query(..., min_length=0, max_length=500, description="Search query to filter posts"),
    start: str | None = Query(None, description="Start date (YYYY-MM-DD). Omit for earliest."),
    end: str | None = Query(None, description="End date (YYYY-MM-DD). Omit for latest."),
    platform: str | None = Query(None, description="Platform filter: 'reddit' or 'twitter'"),
):
    """Return daily post counts grouped by platform within the date range.

    Filters posts whose text contains *query* (case-insensitive), then
    groups by (date, platform) and returns counts per day.
    """
    # ── Validate query ──────────────────────────────────────────────
    if len(query.strip()) < 2:
        raise HTTPException(status_code=400, detail="Query must be at least 2 characters")

    df = get_dataframe().copy()

    # ── Filter by query text (case-insensitive contains) ────────────
    mask = df["text"].str.contains(query, case=False, na=False)
    df = df[mask]

    # ── Filter by platform ──────────────────────────────────────────
    if platform:
        df = df[df["platform"].str.lower() == platform.lower()]

    # ── Determine date range ────────────────────────────────────────
    if df.empty:
        # No matches — return an empty result immediately
        used_start = start or ""
        used_end = end or ""
        return TimeseriesResponse(
            query=query,
            total_count=0,
            date_range_used=DateRange(start=used_start, end=used_end),
            data=[],
        )

    # Normalise the date column for grouping
    df["date"] = df["timestamp"].dt.date

    dataset_start = df["date"].min()
    dataset_end = df["date"].max()

    # Apply optional date filters
    if start:
        from datetime import date as _date
        try:
            s = _date.fromisoformat(start)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start date format. Use YYYY-MM-DD.")
        df = df[df["date"] >= s]
        used_start = str(s)
    else:
        used_start = str(dataset_start)

    if end:
        from datetime import date as _date
        try:
            e = _date.fromisoformat(end)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end date format. Use YYYY-MM-DD.")
        df = df[df["date"] <= e]
        used_end = str(e)
    else:
        used_end = str(dataset_end)

    # ── Group by (date, platform) and count ─────────────────────────
    if df.empty:
        return TimeseriesResponse(
            query=query,
            total_count=0,
            date_range_used=DateRange(start=used_start, end=used_end),
            data=[],
        )

    grouped = (
        df.groupby(["date", "platform"])
        .size()
        .reset_index(name="count")
        .sort_values("date")
    )

    points = [
        TimeseriesPoint(date=str(row["date"]), count=int(row["count"]), platform=row["platform"])
        for _, row in grouped.iterrows()
    ]

    return TimeseriesResponse(
        query=query,
        total_count=int(grouped["count"].sum()),
        date_range_used=DateRange(start=used_start, end=used_end),
        data=points,
    )
