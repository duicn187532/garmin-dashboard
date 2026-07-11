from fastapi import APIRouter, Depends, Query

from ..store import MongoDataStore, SqlDataStore, get_store


router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/summary")
def summary(store: SqlDataStore | MongoDataStore = Depends(get_store)):
    return store.summary()


@router.get("/dashboard/today")
def dashboard_today(store: SqlDataStore | MongoDataStore = Depends(get_store)):
    return store.dashboard_today()


@router.get("/dashboard/trends")
def dashboard_trends(
    range_param: str = Query(default="30d", alias="range", pattern="^(7d|30d|90d)$"),
    store: SqlDataStore | MongoDataStore = Depends(get_store),
):
    return store.dashboard_trends(range_param)

