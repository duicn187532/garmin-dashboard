from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ActivityResponse(ORMModel):
    id: int | str
    activity_id: str
    activity_type: str | None = None
    activity_name: str | None = None
    start_time: datetime | None = None
    duration_seconds: float | None = None
    distance_meters: float | None = None
    average_hr: float | None = None
    max_hr: float | None = None
    calories: float | None = None
    average_speed: float | None = None
    elevation_gain: float | None = None
    training_load: float | None = None
    source: str
    created_at: datetime
    updated_at: datetime


class ActivityLapResponse(ORMModel):
    id: int | str
    activity_id: str
    lap_index: int
    start_time: datetime | None = None
    duration_seconds: float | None = None
    distance_meters: float | None = None
    average_hr: float | None = None
    max_hr: float | None = None
    average_speed: float | None = None
    calories: float | None = None


class ActivityTrackpointResponse(ORMModel):
    id: int | str
    activity_id: str
    timestamp: datetime | None = None
    latitude: float | None = None
    longitude: float | None = None
    heart_rate: float | None = None
    speed: float | None = None
    distance_meters: float | None = None
    altitude: float | None = None


class ActivityDetailResponse(ActivityResponse):
    laps_count: int = 0
    trackpoints_count: int = 0


class ActivityListResponse(BaseModel):
    items: list[ActivityResponse]
    total: int
    page: int
    page_size: int


class DailyHealthResponse(ORMModel):
    id: int | str
    date: date
    steps: int | None = None
    resting_hr: float | None = None
    sleep_hours: float | None = None
    stress_avg: float | None = None
    stress_max: float | None = None
    body_battery_min: float | None = None
    body_battery_max: float | None = None
    hrv_avg: float | None = None
    intensity_minutes: int | None = None
    calories: float | None = None
    weight: float | None = None
    created_at: datetime
    updated_at: datetime


class DerivedMetricResponse(ORMModel):
    id: int | str
    date: date
    acute_load_7d: float | None = None
    chronic_load_28d: float | None = None
    acwr: float | None = None
    sleep_7d_avg: float | None = None
    hrv_7d_avg: float | None = None
    rhr_7d_avg: float | None = None
    recovery_score: float | None = None
    risk_level: str | None = None
    notes_json: dict[str, Any] = Field(default_factory=dict)


class AiReportResponse(ORMModel):
    id: int | str
    report_date: date
    report_type: str
    question: str | None = None
    answer: str
    evidence_json: dict[str, Any] = Field(default_factory=dict)
    model: str
    created_at: datetime


class SyncRequest(BaseModel):
    days: int = Field(default=30, ge=1, le=365)


class SyncResponse(BaseModel):
    status: str
    source: str
    activities_created: int = 0
    activities_updated: int = 0
    daily_health_created: int = 0
    daily_health_updated: int = 0
    derived_metrics_updated: int = 0
    message: str | None = None


class AiAnalyzeRequest(BaseModel):
    report_type: str = Field(default="today")


class AiQueryRequest(BaseModel):
    question: str = Field(min_length=2, max_length=800)
