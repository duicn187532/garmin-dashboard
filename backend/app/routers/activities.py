from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query

from ..schemas import ActivityDetailResponse, ActivityLapResponse, ActivityListResponse, ActivityTrackpointResponse
from ..store import MongoDataStore, SqlDataStore, get_store


router = APIRouter(prefix="/api/activities", tags=["activities"])


@router.get("", response_model=ActivityListResponse)
def list_activities(
    start_date: date | None = None,
    end_date: date | None = None,
    activity_type: str | None = None,
    min_distance: float | None = None,
    max_distance: float | None = None,
    min_avg_hr: float | None = None,
    max_avg_hr: float | None = None,
    min_training_load: float | None = None,
    sort: str = Query(default="start_time_desc"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    store: SqlDataStore | MongoDataStore = Depends(get_store),
):
    return store.list_activities(
        {
            "start_date": start_date,
            "end_date": end_date,
            "activity_type": activity_type,
            "min_distance": min_distance,
            "max_distance": max_distance,
            "min_avg_hr": min_avg_hr,
            "max_avg_hr": max_avg_hr,
            "min_training_load": min_training_load,
            "sort": sort,
            "page": page,
            "page_size": page_size,
        }
    )


@router.get("/{activity_id}", response_model=ActivityDetailResponse)
def activity_detail(activity_id: str, store: SqlDataStore | MongoDataStore = Depends(get_store)):
    activity = store.activity_detail(activity_id)
    if activity is None:
        raise HTTPException(status_code=404, detail="Activity not found.")
    return activity


@router.get("/{activity_id}/laps", response_model=list[ActivityLapResponse])
def activity_laps(activity_id: str, store: SqlDataStore | MongoDataStore = Depends(get_store)):
    laps = store.activity_laps(activity_id)
    if laps is None:
        raise HTTPException(status_code=404, detail="Activity not found.")
    return laps


@router.get("/{activity_id}/trackpoints", response_model=list[ActivityTrackpointResponse])
def activity_trackpoints(activity_id: str, store: SqlDataStore | MongoDataStore = Depends(get_store)):
    trackpoints = store.activity_trackpoints(activity_id)
    if trackpoints is None:
        raise HTTPException(status_code=404, detail="Activity not found.")
    return trackpoints

