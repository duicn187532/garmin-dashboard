from datetime import date

from fastapi import APIRouter, Depends, Query

from ..schemas import DailyHealthResponse
from ..store import MongoDataStore, SqlDataStore, get_store


router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("/daily", response_model=list[DailyHealthResponse])
def daily_health(
    start_date: date | None = None,
    end_date: date | None = None,
    store: SqlDataStore | MongoDataStore = Depends(get_store),
):
    return store.health_daily(start_date, end_date)


@router.get("/trends")
def health_trends(
    metric: str = Query(pattern="^(sleep|hrv|rhr|stress|steps|body_battery)$"),
    range_param: str = Query(default="30d", alias="range", pattern="^(7d|30d|90d)$"),
    store: SqlDataStore | MongoDataStore = Depends(get_store),
):
    return store.health_trend(metric, range_param)

