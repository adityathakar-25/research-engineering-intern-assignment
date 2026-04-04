"""Time-series route — daily post volume over a date range."""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

router = APIRouter(prefix="/api", tags=["timeseries"])


# ── Response model ──────────────────────────────────────────────────
class TimeseriesPoint(BaseModel):
    date: str
    count: int
    community: str


class TimeseriesResponse(BaseModel):
    query: str
    start: str
    end: str
    platform: str
    data: list[TimeseriesPoint]


# ── Route ───────────────────────────────────────────────────────────
@router.get("/timeseries", response_model=TimeseriesResponse)
async def get_timeseries(
    query: str = Query("", description="Search query to filter posts"),
    start: str = Query("2025-02-01", description="Start date (YYYY-MM-DD)"),
    end: str = Query("2025-02-28", description="End date (YYYY-MM-DD)"),
    platform: str = Query("reddit", description="Platform filter"),
):
    """Return daily post counts per community within the date range.

    When implemented: queries clean.parquet, filters by date range and
    optional text query, groups by (date, community), returns counts.
    """
    return TimeseriesResponse(
        query=query,
        start=start,
        end=end,
        platform=platform,
        data=[
            TimeseriesPoint(date="2025-02-01", count=42, community="Anarchism"),
            TimeseriesPoint(date="2025-02-01", count=18, community="Communalists"),
            TimeseriesPoint(date="2025-02-02", count=37, community="Anarchism"),
            TimeseriesPoint(date="2025-02-02", count=22, community="Communalists"),
            TimeseriesPoint(date="2025-02-03", count=55, community="Anarchism"),
            TimeseriesPoint(date="2025-02-03", count=15, community="Communalists"),
        ],
    )
