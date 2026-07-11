from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from ..models import Activity, ActivityLap, ActivityTrackpoint, DailyHealth
from ..schemas import SyncResponse
from .garmin.base import GarminConnector, GarminConnectorError
from .metrics_service import MetricsService


LAST_SYNC_STATUS: dict[str, Any] = {
    "state": "never_run",
    "message": "Sync has not run in this process.",
    "finished_at": None,
}


class SyncService:
    def __init__(self, db: Session, connector: GarminConnector):
        self.db = db
        self.connector = connector

    def sync(self, days: int = 30) -> SyncResponse:
        try:
            payload = self.connector.fetch(days=days)
            counts = {
                "activities_created": 0,
                "activities_updated": 0,
                "daily_health_created": 0,
                "daily_health_updated": 0,
            }

            for item in payload.get("activities", []):
                created = self._upsert_activity(item, payload["source"])
                counts["activities_created" if created else "activities_updated"] += 1

            for item in payload.get("daily_health", []):
                created = self._upsert_daily_health(item)
                counts["daily_health_created" if created else "daily_health_updated"] += 1

            self.db.flush()
            metrics_updated = MetricsService(self.db).recalculate_all()
            response = SyncResponse(
                status="ok",
                source=payload["source"],
                derived_metrics_updated=metrics_updated,
                **counts,
            )
            LAST_SYNC_STATUS.update(
                {
                    "state": "ok",
                    "message": "Sync completed.",
                    "finished_at": datetime.now(timezone.utc).isoformat(),
                    "response": response.model_dump(),
                }
            )
            return response
        except GarminConnectorError as exc:
            self.db.rollback()
            LAST_SYNC_STATUS.update(
                {
                    "state": "error",
                    "message": str(exc),
                    "finished_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            raise

    def _upsert_activity(self, item: dict[str, Any], source: str) -> bool:
        activity_id = str(item["activity_id"])
        activity = self.db.query(Activity).filter(Activity.activity_id == activity_id).one_or_none()
        created = activity is None
        if activity is None:
            activity = Activity(activity_id=activity_id)
            self.db.add(activity)

        fields = [
            "activity_type",
            "activity_name",
            "duration_seconds",
            "distance_meters",
            "average_hr",
            "max_hr",
            "calories",
            "average_speed",
            "elevation_gain",
            "training_load",
        ]
        for field in fields:
            setattr(activity, field, item.get(field))
        activity.start_time = parse_datetime(item.get("start_time"))
        activity.source = source
        activity.raw_json = item.get("raw_json") or item

        self.db.query(ActivityLap).filter(ActivityLap.activity_id == activity_id).delete(synchronize_session=False)
        self.db.query(ActivityTrackpoint).filter(ActivityTrackpoint.activity_id == activity_id).delete(
            synchronize_session=False
        )

        for lap in item.get("laps", []):
            self.db.add(
                ActivityLap(
                    activity_id=activity_id,
                    lap_index=int(lap.get("lap_index") or 0),
                    start_time=parse_datetime(lap.get("start_time")),
                    duration_seconds=lap.get("duration_seconds"),
                    distance_meters=lap.get("distance_meters"),
                    average_hr=lap.get("average_hr"),
                    max_hr=lap.get("max_hr"),
                    average_speed=lap.get("average_speed"),
                    calories=lap.get("calories"),
                    raw_json=lap.get("raw_json") or lap,
                )
            )

        for point in item.get("trackpoints", []):
            self.db.add(
                ActivityTrackpoint(
                    activity_id=activity_id,
                    timestamp=parse_datetime(point.get("timestamp")),
                    latitude=point.get("latitude"),
                    longitude=point.get("longitude"),
                    heart_rate=point.get("heart_rate"),
                    speed=point.get("speed"),
                    distance_meters=point.get("distance_meters"),
                    altitude=point.get("altitude"),
                    raw_json=point.get("raw_json") or point,
                )
            )

        return created

    def _upsert_daily_health(self, item: dict[str, Any]) -> bool:
        health_date = parse_date(item["date"])
        health = self.db.query(DailyHealth).filter(DailyHealth.date == health_date).one_or_none()
        created = health is None
        if health is None:
            health = DailyHealth(date=health_date)
            self.db.add(health)

        for field in [
            "steps",
            "resting_hr",
            "sleep_hours",
            "stress_avg",
            "stress_max",
            "body_battery_min",
            "body_battery_max",
            "hrv_avg",
            "intensity_minutes",
            "calories",
            "weight",
        ]:
            setattr(health, field, item.get(field))
        health.raw_json = item.get("raw_json") or item
        return created


def parse_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    text = str(value).replace("Z", "+00:00")
    parsed = datetime.fromisoformat(text)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def parse_date(value: Any) -> date:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    return date.fromisoformat(str(value)[:10])

