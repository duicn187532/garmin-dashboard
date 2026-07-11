from __future__ import annotations

from contextlib import contextmanager
from datetime import date, datetime, time, timedelta, timezone
from statistics import mean
from typing import Any, Iterator

from sqlalchemy import func, text

from .config import Settings, get_settings
from .database import SessionLocal
from .models import Activity, ActivityLap, ActivityTrackpoint, AiReport, DailyHealth, DerivedMetric
from .schemas import SyncResponse
from .services.ai.prompt_builder import build_grounded_prompt
from .services.ai.provider import create_ai_provider
from .services.garmin.base import GarminConnector
from .services.sync_service import SyncService, parse_datetime


class SqlDataStore:
    backend = "sqlite"

    def __init__(self, db, settings: Settings):
        self.db = db
        self.settings = settings

    def ping(self) -> None:
        self.db.execute(text("select 1"))

    def summary(self) -> dict[str, Any]:
        latest_health = self.db.query(func.max(DailyHealth.date)).scalar()
        latest_activity = self.db.query(func.max(Activity.start_time)).scalar()
        return {
            "activities": self.db.query(Activity).count(),
            "daily_health_days": self.db.query(DailyHealth).count(),
            "ai_reports": self.db.query(AiReport).count(),
            "latest_health_date": latest_health.isoformat() if latest_health else None,
            "latest_activity_time": latest_activity.isoformat() if latest_activity else None,
        }

    def dashboard_today(self) -> dict[str, Any]:
        health = self.db.query(DailyHealth).order_by(DailyHealth.date.desc()).first()
        metric = self.db.query(DerivedMetric).order_by(DerivedMetric.date.desc()).first()
        report = self.db.query(AiReport).order_by(AiReport.created_at.desc()).first()
        recent_activity = self.db.query(Activity).order_by(Activity.start_time.desc()).limit(5).all()
        return {
            "health": serialize_sql_health(health) if health else None,
            "derived_metric": serialize_sql_metric(metric) if metric else None,
            "ai_report": serialize_sql_report(report) if report else None,
            "recent_activities": [serialize_sql_activity(item) for item in recent_activity],
        }

    def dashboard_trends(self, range_key: str) -> dict[str, Any]:
        start = cutoff_date(range_to_days(range_key))
        health = self.db.query(DailyHealth).filter(DailyHealth.date >= start).order_by(DailyHealth.date.asc()).all()
        metrics = (
            self.db.query(DerivedMetric).filter(DerivedMetric.date >= start).order_by(DerivedMetric.date.asc()).all()
        )
        return {
            "range": range_key,
            "daily_health": [serialize_sql_health(row) for row in health],
            "derived_metrics": [serialize_sql_metric(row) for row in metrics],
        }

    def health_daily(self, start_date: date | None, end_date: date | None) -> list[dict[str, Any]]:
        query = self.db.query(DailyHealth)
        if start_date:
            query = query.filter(DailyHealth.date >= start_date)
        if end_date:
            query = query.filter(DailyHealth.date <= end_date)
        return [serialize_sql_health(row) for row in query.order_by(DailyHealth.date.desc()).limit(365).all()]

    def health_trend(self, metric: str, range_key: str) -> dict[str, Any]:
        start = cutoff_date(range_to_days(range_key))
        rows = self.db.query(DailyHealth).filter(DailyHealth.date >= start).order_by(DailyHealth.date.asc()).all()
        return {
            "metric": metric,
            "range": range_key,
            "points": [{"date": row.date.isoformat(), "value": health_metric_value(serialize_sql_health(row), metric)} for row in rows],
        }

    def list_activities(self, filters: dict[str, Any]) -> dict[str, Any]:
        query = self.db.query(Activity)
        start_date = filters.get("start_date")
        end_date = filters.get("end_date")
        if start_date:
            query = query.filter(Activity.start_time >= datetime.combine(start_date, time.min, tzinfo=timezone.utc))
        if end_date:
            query = query.filter(Activity.start_time < datetime.combine(end_date, time.max, tzinfo=timezone.utc))
        if filters.get("activity_type"):
            query = query.filter(Activity.activity_type.ilike(f"%{filters['activity_type']}%"))
        for key, column in [
            ("min_distance", Activity.distance_meters),
            ("min_avg_hr", Activity.average_hr),
            ("min_training_load", Activity.training_load),
        ]:
            if filters.get(key) is not None:
                query = query.filter(column >= filters[key])
        for key, column in [("max_distance", Activity.distance_meters), ("max_avg_hr", Activity.average_hr)]:
            if filters.get(key) is not None:
                query = query.filter(column <= filters[key])
        total = query.count()
        query = sql_apply_activity_sort(query, filters.get("sort") or "start_time_desc")
        page = filters.get("page") or 1
        page_size = filters.get("page_size") or 20
        rows = query.offset((page - 1) * page_size).limit(page_size).all()
        return {"items": [serialize_sql_activity(row) for row in rows], "total": total, "page": page, "page_size": page_size}

    def activity_detail(self, activity_id: str) -> dict[str, Any] | None:
        activity = self.db.query(Activity).filter(Activity.activity_id == activity_id).one_or_none()
        if activity is None:
            return None
        data = serialize_sql_activity(activity)
        data["laps_count"] = self.db.query(ActivityLap).filter(ActivityLap.activity_id == activity_id).count()
        data["trackpoints_count"] = self.db.query(ActivityTrackpoint).filter(ActivityTrackpoint.activity_id == activity_id).count()
        return data

    def activity_laps(self, activity_id: str) -> list[dict[str, Any]] | None:
        if self.activity_detail(activity_id) is None:
            return None
        rows = self.db.query(ActivityLap).filter(ActivityLap.activity_id == activity_id).order_by(ActivityLap.lap_index.asc()).all()
        return [serialize_sql_lap(row) for row in rows]

    def activity_trackpoints(self, activity_id: str) -> list[dict[str, Any]] | None:
        if self.activity_detail(activity_id) is None:
            return None
        rows = (
            self.db.query(ActivityTrackpoint)
            .filter(ActivityTrackpoint.activity_id == activity_id)
            .order_by(ActivityTrackpoint.timestamp.asc())
            .all()
        )
        return [serialize_sql_trackpoint(row) for row in rows]

    def sync(self, connector: GarminConnector, days: int) -> SyncResponse:
        return SyncService(self.db, connector).sync(days=days)

    def analyze_today(self) -> dict[str, Any]:
        return self._create_ai_report("today", "請分析今日恢復狀態、是否適合高強度訓練，以及最近訓練負荷是否過高。", 30)

    def answer_question(self, question: str) -> dict[str, Any]:
        return self._create_ai_report("query", question, infer_days(question))

    def latest_ai(self) -> dict[str, Any] | None:
        report = self.db.query(AiReport).order_by(AiReport.created_at.desc()).first()
        return serialize_sql_report(report) if report else None

    def ai_reports(self) -> list[dict[str, Any]]:
        return [serialize_sql_report(row) for row in self.db.query(AiReport).order_by(AiReport.created_at.desc()).limit(100).all()]

    def _create_ai_report(self, report_type: str, question: str, days: int) -> dict[str, Any]:
        from .services.ai.grounded_query import GroundedQueryService

        service = GroundedQueryService(self.db, self.settings)
        report = service.analyze_today() if report_type == "today" else service.answer_question(question)
        return serialize_sql_report(report)


class MongoDataStore:
    backend = "mongodb"

    def __init__(self, settings: Settings):
        if not settings.mongodb_uri:
            raise RuntimeError("MONGODB_URI is required when DATABASE_BACKEND=mongodb.")
        from pymongo import ASCENDING, DESCENDING, MongoClient

        self.settings = settings
        self.client = MongoClient(
            settings.mongodb_uri,
            appname="garmin-insight",
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
        )
        self.db = self.client[settings.mongodb_database]
        self.ASCENDING = ASCENDING
        self.DESCENDING = DESCENDING

    def ensure_indexes(self) -> None:
        self.db.activities.create_index("activity_id", unique=True)
        self.db.activities.create_index("start_time")
        self.db.activity_laps.create_index([("activity_id", self.ASCENDING), ("lap_index", self.ASCENDING)], unique=True)
        self.db.activity_trackpoints.create_index([("activity_id", self.ASCENDING), ("timestamp", self.ASCENDING)])
        self.db.daily_health.create_index("date", unique=True)
        self.db.derived_metrics.create_index("date", unique=True)
        self.db.ai_reports.create_index("created_at")

    def ping(self) -> None:
        self.client.admin.command("ping")

    def summary(self) -> dict[str, Any]:
        latest_health = self.db.daily_health.find_one(sort=[("date", -1)])
        latest_activity = self.db.activities.find_one(sort=[("start_time", -1)])
        return {
            "activities": self.db.activities.count_documents({}),
            "daily_health_days": self.db.daily_health.count_documents({}),
            "ai_reports": self.db.ai_reports.count_documents({}),
            "latest_health_date": latest_health.get("date") if latest_health else None,
            "latest_activity_time": encode_dt(latest_activity.get("start_time")) if latest_activity else None,
        }

    def dashboard_today(self) -> dict[str, Any]:
        health = self.db.daily_health.find_one(sort=[("date", -1)])
        metric = self.db.derived_metrics.find_one(sort=[("date", -1)])
        report = self.db.ai_reports.find_one(sort=[("created_at", -1)])
        recent = list(self.db.activities.find({}, sort=[("start_time", -1)], limit=5))
        return {
            "health": mongo_clean(health) if health else None,
            "derived_metric": mongo_clean(metric) if metric else None,
            "ai_report": mongo_clean(report) if report else None,
            "recent_activities": [mongo_clean(row) for row in recent],
        }

    def dashboard_trends(self, range_key: str) -> dict[str, Any]:
        start = cutoff_date(range_to_days(range_key)).isoformat()
        health = list(self.db.daily_health.find({"date": {"$gte": start}}, sort=[("date", 1)]))
        metrics = list(self.db.derived_metrics.find({"date": {"$gte": start}}, sort=[("date", 1)]))
        return {
            "range": range_key,
            "daily_health": [mongo_clean(row) for row in health],
            "derived_metrics": [mongo_clean(row) for row in metrics],
        }

    def health_daily(self, start_date: date | None, end_date: date | None) -> list[dict[str, Any]]:
        query: dict[str, Any] = {}
        if start_date or end_date:
            query["date"] = {}
            if start_date:
                query["date"]["$gte"] = start_date.isoformat()
            if end_date:
                query["date"]["$lte"] = end_date.isoformat()
        return [mongo_clean(row) for row in self.db.daily_health.find(query, sort=[("date", -1)], limit=365)]

    def health_trend(self, metric: str, range_key: str) -> dict[str, Any]:
        rows = self.dashboard_trends(range_key)["daily_health"]
        return {
            "metric": metric,
            "range": range_key,
            "points": [{"date": row["date"], "value": health_metric_value(row, metric)} for row in rows],
        }

    def list_activities(self, filters: dict[str, Any]) -> dict[str, Any]:
        query: dict[str, Any] = {}
        start_date = filters.get("start_date")
        end_date = filters.get("end_date")
        if start_date or end_date:
            query["start_time"] = {}
            if start_date:
                query["start_time"]["$gte"] = datetime.combine(start_date, time.min, tzinfo=timezone.utc)
            if end_date:
                query["start_time"]["$lte"] = datetime.combine(end_date, time.max, tzinfo=timezone.utc)
        if filters.get("activity_type"):
            query["activity_type"] = {"$regex": filters["activity_type"], "$options": "i"}
        add_range_filter(query, "distance_meters", filters.get("min_distance"), filters.get("max_distance"))
        add_range_filter(query, "average_hr", filters.get("min_avg_hr"), filters.get("max_avg_hr"))
        add_range_filter(query, "training_load", filters.get("min_training_load"), None)
        total = self.db.activities.count_documents(query)
        page = filters.get("page") or 1
        page_size = filters.get("page_size") or 20
        sort = mongo_activity_sort(filters.get("sort") or "start_time_desc")
        rows = list(self.db.activities.find(query, sort=sort, skip=(page - 1) * page_size, limit=page_size))
        return {"items": [mongo_clean(row) for row in rows], "total": total, "page": page, "page_size": page_size}

    def activity_detail(self, activity_id: str) -> dict[str, Any] | None:
        row = self.db.activities.find_one({"activity_id": activity_id})
        if not row:
            return None
        data = mongo_clean(row)
        data["laps_count"] = self.db.activity_laps.count_documents({"activity_id": activity_id})
        data["trackpoints_count"] = self.db.activity_trackpoints.count_documents({"activity_id": activity_id})
        return data

    def activity_laps(self, activity_id: str) -> list[dict[str, Any]] | None:
        if not self.db.activities.find_one({"activity_id": activity_id}, {"_id": 1}):
            return None
        return [mongo_clean(row) for row in self.db.activity_laps.find({"activity_id": activity_id}, sort=[("lap_index", 1)])]

    def activity_trackpoints(self, activity_id: str) -> list[dict[str, Any]] | None:
        if not self.db.activities.find_one({"activity_id": activity_id}, {"_id": 1}):
            return None
        return [mongo_clean(row) for row in self.db.activity_trackpoints.find({"activity_id": activity_id}, sort=[("timestamp", 1)])]

    def sync(self, connector: GarminConnector, days: int) -> SyncResponse:
        payload = connector.fetch(days=days)
        counts = {"activities_created": 0, "activities_updated": 0, "daily_health_created": 0, "daily_health_updated": 0}
        now = datetime.now(timezone.utc)
        for item in payload.get("activities", []):
            activity_id = str(item["activity_id"])
            doc = activity_doc(item, payload["source"], now)
            existing = self.db.activities.find_one({"activity_id": activity_id}, {"_id": 1, "created_at": 1})
            if existing:
                doc["created_at"] = existing.get("created_at", now)
                counts["activities_updated"] += 1
            else:
                counts["activities_created"] += 1
            self.db.activities.update_one({"activity_id": activity_id}, {"$set": doc}, upsert=True)
            self.db.activity_laps.delete_many({"activity_id": activity_id})
            self.db.activity_trackpoints.delete_many({"activity_id": activity_id})
            if item.get("laps"):
                self.db.activity_laps.insert_many([lap_doc(activity_id, lap) for lap in item["laps"]])
            if item.get("trackpoints"):
                self.db.activity_trackpoints.insert_many([trackpoint_doc(activity_id, point) for point in item["trackpoints"]])
        for item in payload.get("daily_health", []):
            health_date = str(item["date"])[:10]
            existing = self.db.daily_health.find_one({"date": health_date}, {"_id": 1, "created_at": 1})
            doc = daily_health_doc(item, now)
            if existing:
                doc["created_at"] = existing.get("created_at", now)
                counts["daily_health_updated"] += 1
            else:
                counts["daily_health_created"] += 1
            self.db.daily_health.update_one({"date": health_date}, {"$set": doc}, upsert=True)
        metrics_updated = self.recalculate_metrics()
        return SyncResponse(status="ok", source=payload["source"], derived_metrics_updated=metrics_updated, **counts)

    def recalculate_metrics(self) -> int:
        dates = {row["date"] for row in self.db.daily_health.find({}, {"date": 1}) if row.get("date")}
        for row in self.db.activities.find({}, {"start_time": 1}):
            if row.get("start_time"):
                dates.add(as_date(row["start_time"]).isoformat())
        for metric_date_text in sorted(dates):
            self.recalculate_metric_for_date(date.fromisoformat(metric_date_text))
        return len(dates)

    def recalculate_metric_for_date(self, metric_date: date) -> None:
        acute = self.load_average(metric_date, 7)
        chronic = self.load_average(metric_date, 28)
        acwr = round(acute / chronic, 2) if chronic else None
        start = (metric_date - timedelta(days=6)).isoformat()
        end = metric_date.isoformat()
        health_window = list(self.db.daily_health.find({"date": {"$gte": start, "$lte": end}}, sort=[("date", 1)]))
        latest = self.db.daily_health.find_one({"date": end})
        sleep_avg = avg([row.get("sleep_hours") for row in health_window])
        hrv_avg = avg([row.get("hrv_avg") for row in health_window])
        rhr_avg = avg([row.get("resting_hr") for row in health_window])
        recovery = recovery_score(latest, sleep_avg, hrv_avg, rhr_avg, acwr)
        risk = risk_level(recovery, acwr)
        self.db.derived_metrics.update_one(
            {"date": end},
            {
                "$set": {
                    "id": end,
                    "date": end,
                    "acute_load_7d": acute,
                    "chronic_load_28d": chronic,
                    "acwr": acwr,
                    "sleep_7d_avg": sleep_avg,
                    "hrv_7d_avg": hrv_avg,
                    "rhr_7d_avg": rhr_avg,
                    "recovery_score": recovery,
                    "risk_level": risk,
                    "notes_json": {"method": "mongo_rule_based_mvp"},
                }
            },
            upsert=True,
        )

    def load_average(self, end_date: date, days: int) -> float:
        start_dt = datetime.combine(end_date - timedelta(days=days - 1), time.min, tzinfo=timezone.utc)
        end_dt = datetime.combine(end_date + timedelta(days=1), time.min, tzinfo=timezone.utc)
        rows = self.db.activities.find({"start_time": {"$gte": start_dt, "$lt": end_dt}})
        total = 0.0
        for row in rows:
            if row.get("training_load") is not None:
                total += float(row["training_load"])
            elif row.get("duration_seconds") and row.get("average_hr"):
                total += (float(row["duration_seconds"]) / 3600) * (float(row["average_hr"]) / 2)
        return round(total / days, 2)

    def analyze_today(self) -> dict[str, Any]:
        return self.create_ai_report("today", "請分析今日恢復狀態、是否適合高強度訓練，以及最近訓練負荷是否過高。", 30)

    def answer_question(self, question: str) -> dict[str, Any]:
        return self.create_ai_report("query", question, infer_days(question))

    def create_ai_report(self, report_type: str, question: str, days: int) -> dict[str, Any]:
        evidence = self.collect_evidence(days)
        provider = create_ai_provider(self.settings)
        answer = provider.generate(build_grounded_prompt(question, evidence), evidence)
        latest_health = self.db.daily_health.find_one(sort=[("date", -1)])
        report_date = latest_health["date"] if latest_health else date.today().isoformat()
        now = datetime.now(timezone.utc)
        doc = {
            "id": str(now.timestamp()),
            "report_date": report_date,
            "report_type": report_type,
            "question": question,
            "answer": answer,
            "evidence_json": evidence,
            "model": provider.model_name,
            "created_at": now,
        }
        result = self.db.ai_reports.insert_one(doc)
        doc["_id"] = result.inserted_id
        return mongo_clean(doc)

    def collect_evidence(self, days: int) -> dict[str, Any]:
        latest_health = self.db.daily_health.find_one(sort=[("date", -1)])
        latest_metric = self.db.derived_metrics.find_one(sort=[("date", -1)])
        anchor = date.fromisoformat(latest_health["date"]) if latest_health else date.today()
        start_date = anchor - timedelta(days=days - 1)
        health = list(self.db.daily_health.find({"date": {"$gte": start_date.isoformat(), "$lte": anchor.isoformat()}}, sort=[("date", 1)]))
        metrics = list(self.db.derived_metrics.find({"date": {"$gte": start_date.isoformat(), "$lte": anchor.isoformat()}}, sort=[("date", 1)]))
        activities = list(
            self.db.activities.find(
                {"start_time": {"$gte": datetime.combine(start_date, time.min, tzinfo=timezone.utc)}},
                sort=[("start_time", -1)],
                limit=80,
            )
        )
        return {
            "has_data": bool(health or activities),
            "range": {"start_date": start_date.isoformat(), "end_date": anchor.isoformat(), "days": days},
            "latest_health": mongo_clean(latest_health) if latest_health else None,
            "latest_metric": mongo_clean(latest_metric) if latest_metric else None,
            "daily_health": [mongo_clean(row) for row in health],
            "derived_metrics": [mongo_clean(row) for row in metrics],
            "activities": [mongo_clean(row) for row in activities],
        }

    def latest_ai(self) -> dict[str, Any] | None:
        row = self.db.ai_reports.find_one(sort=[("created_at", -1)])
        return mongo_clean(row) if row else None

    def ai_reports(self) -> list[dict[str, Any]]:
        return [mongo_clean(row) for row in self.db.ai_reports.find({}, sort=[("created_at", -1)], limit=100)]


def get_store() -> Iterator[SqlDataStore | MongoDataStore]:
    settings = get_settings()
    if settings.database_backend == "mongodb":
        store = MongoDataStore(settings)
        store.ensure_indexes()
        yield store
        return
    db = SessionLocal()
    try:
        yield SqlDataStore(db, settings)
    finally:
        db.close()


@contextmanager
def store_context() -> Iterator[SqlDataStore | MongoDataStore]:
    yield from get_store()


def range_to_days(value: str) -> int:
    return {"7d": 7, "30d": 30, "90d": 90}.get(value, 30)


def cutoff_date(days: int) -> date:
    return date.today() - timedelta(days=days - 1)


def encode_dt(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def mongo_clean(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if row is None:
        return None
    data: dict[str, Any] = {}
    for key, value in row.items():
        if key == "_id":
            data["id"] = str(value) if "id" not in row else row["id"]
            continue
        if isinstance(value, datetime):
            data[key] = value.isoformat()
        else:
            data[key] = value
    if "id" not in data:
        data["id"] = data.get("activity_id") or data.get("date") or data.get("created_at") or "mongo"
    return data


def serialize_sql_activity(row: Activity) -> dict[str, Any]:
    return {
        "id": row.id,
        "activity_id": row.activity_id,
        "activity_type": row.activity_type,
        "activity_name": row.activity_name,
        "start_time": encode_dt(row.start_time),
        "duration_seconds": row.duration_seconds,
        "distance_meters": row.distance_meters,
        "average_hr": row.average_hr,
        "max_hr": row.max_hr,
        "calories": row.calories,
        "average_speed": row.average_speed,
        "elevation_gain": row.elevation_gain,
        "training_load": row.training_load,
        "source": row.source,
        "created_at": encode_dt(row.created_at),
        "updated_at": encode_dt(row.updated_at),
    }


def serialize_sql_health(row: DailyHealth) -> dict[str, Any]:
    return {
        "id": row.id,
        "date": row.date.isoformat(),
        "steps": row.steps,
        "resting_hr": row.resting_hr,
        "sleep_hours": row.sleep_hours,
        "stress_avg": row.stress_avg,
        "stress_max": row.stress_max,
        "body_battery_min": row.body_battery_min,
        "body_battery_max": row.body_battery_max,
        "hrv_avg": row.hrv_avg,
        "intensity_minutes": row.intensity_minutes,
        "calories": row.calories,
        "weight": row.weight,
        "created_at": encode_dt(row.created_at),
        "updated_at": encode_dt(row.updated_at),
    }


def serialize_sql_metric(row: DerivedMetric) -> dict[str, Any]:
    return {
        "id": row.id,
        "date": row.date.isoformat(),
        "acute_load_7d": row.acute_load_7d,
        "chronic_load_28d": row.chronic_load_28d,
        "acwr": row.acwr,
        "sleep_7d_avg": row.sleep_7d_avg,
        "hrv_7d_avg": row.hrv_7d_avg,
        "rhr_7d_avg": row.rhr_7d_avg,
        "recovery_score": row.recovery_score,
        "risk_level": row.risk_level,
        "notes_json": row.notes_json,
    }


def serialize_sql_report(row: AiReport) -> dict[str, Any]:
    return {
        "id": row.id,
        "report_date": row.report_date.isoformat(),
        "report_type": row.report_type,
        "question": row.question,
        "answer": row.answer,
        "evidence_json": row.evidence_json,
        "model": row.model,
        "created_at": encode_dt(row.created_at),
    }


def serialize_sql_lap(row: ActivityLap) -> dict[str, Any]:
    return {
        "id": row.id,
        "activity_id": row.activity_id,
        "lap_index": row.lap_index,
        "start_time": encode_dt(row.start_time),
        "duration_seconds": row.duration_seconds,
        "distance_meters": row.distance_meters,
        "average_hr": row.average_hr,
        "max_hr": row.max_hr,
        "average_speed": row.average_speed,
        "calories": row.calories,
    }


def serialize_sql_trackpoint(row: ActivityTrackpoint) -> dict[str, Any]:
    return {
        "id": row.id,
        "activity_id": row.activity_id,
        "timestamp": encode_dt(row.timestamp),
        "latitude": row.latitude,
        "longitude": row.longitude,
        "heart_rate": row.heart_rate,
        "speed": row.speed,
        "distance_meters": row.distance_meters,
        "altitude": row.altitude,
    }


def sql_apply_activity_sort(query, sort: str):
    mapping = {
        "start_time_asc": Activity.start_time.asc(),
        "distance_desc": Activity.distance_meters.desc(),
        "training_load_desc": Activity.training_load.desc(),
        "avg_hr_desc": Activity.average_hr.desc(),
    }
    return query.order_by(mapping.get(sort, Activity.start_time.desc()))


def mongo_activity_sort(sort: str):
    mapping = {
        "start_time_asc": [("start_time", 1)],
        "distance_desc": [("distance_meters", -1)],
        "training_load_desc": [("training_load", -1)],
        "avg_hr_desc": [("average_hr", -1)],
    }
    return mapping.get(sort, [("start_time", -1)])


def add_range_filter(query: dict[str, Any], field: str, minimum: Any, maximum: Any) -> None:
    if minimum is None and maximum is None:
        return
    query[field] = {}
    if minimum is not None:
        query[field]["$gte"] = minimum
    if maximum is not None:
        query[field]["$lte"] = maximum


def activity_doc(item: dict[str, Any], source: str, now: datetime) -> dict[str, Any]:
    return {
        "id": str(item["activity_id"]),
        "activity_id": str(item["activity_id"]),
        "activity_type": item.get("activity_type"),
        "activity_name": item.get("activity_name"),
        "start_time": parse_datetime(item.get("start_time")),
        "duration_seconds": item.get("duration_seconds"),
        "distance_meters": item.get("distance_meters"),
        "average_hr": item.get("average_hr"),
        "max_hr": item.get("max_hr"),
        "calories": item.get("calories"),
        "average_speed": item.get("average_speed"),
        "elevation_gain": item.get("elevation_gain"),
        "training_load": item.get("training_load"),
        "source": source,
        "raw_json": item.get("raw_json") or item,
        "created_at": now,
        "updated_at": now,
    }


def lap_doc(activity_id: str, item: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": f"{activity_id}:{item.get('lap_index')}",
        "activity_id": activity_id,
        "lap_index": int(item.get("lap_index") or 0),
        "start_time": parse_datetime(item.get("start_time")),
        "duration_seconds": item.get("duration_seconds"),
        "distance_meters": item.get("distance_meters"),
        "average_hr": item.get("average_hr"),
        "max_hr": item.get("max_hr"),
        "average_speed": item.get("average_speed"),
        "calories": item.get("calories"),
        "raw_json": item.get("raw_json") or item,
    }


def trackpoint_doc(activity_id: str, item: dict[str, Any]) -> dict[str, Any]:
    timestamp = parse_datetime(item.get("timestamp"))
    return {
        "id": f"{activity_id}:{timestamp.isoformat() if timestamp else len(str(item))}",
        "activity_id": activity_id,
        "timestamp": timestamp,
        "latitude": item.get("latitude"),
        "longitude": item.get("longitude"),
        "heart_rate": item.get("heart_rate"),
        "speed": item.get("speed"),
        "distance_meters": item.get("distance_meters"),
        "altitude": item.get("altitude"),
        "raw_json": item.get("raw_json") or item,
    }


def daily_health_doc(item: dict[str, Any], now: datetime) -> dict[str, Any]:
    health_date = str(item["date"])[:10]
    return {
        "id": health_date,
        "date": health_date,
        "steps": item.get("steps"),
        "resting_hr": item.get("resting_hr"),
        "sleep_hours": item.get("sleep_hours"),
        "stress_avg": item.get("stress_avg"),
        "stress_max": item.get("stress_max"),
        "body_battery_min": item.get("body_battery_min"),
        "body_battery_max": item.get("body_battery_max"),
        "hrv_avg": item.get("hrv_avg"),
        "intensity_minutes": item.get("intensity_minutes"),
        "calories": item.get("calories"),
        "weight": item.get("weight"),
        "raw_json": item.get("raw_json") or item,
        "created_at": now,
        "updated_at": now,
    }


def as_date(value: datetime | str) -> date:
    if isinstance(value, datetime):
        return value.date()
    return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date()


def avg(values: list[Any]) -> float | None:
    cleaned = [float(value) for value in values if value is not None]
    return round(mean(cleaned), 2) if cleaned else None


def recovery_score(today: dict[str, Any] | None, sleep_avg: float | None, hrv_avg: float | None, rhr_avg: float | None, acwr: float | None) -> float | None:
    if not today:
        return None
    score = 55.0
    sleep = today.get("sleep_hours")
    if sleep is not None:
        score += 15 if sleep >= 7 else 7 if sleep >= 6 else -8
    if today.get("hrv_avg") is not None and hrv_avg:
        score += max(-15, min(12, (today["hrv_avg"] - hrv_avg) * 1.4))
    if today.get("resting_hr") is not None and rhr_avg:
        score += max(-12, min(10, -(today["resting_hr"] - rhr_avg) * 3))
    stress = today.get("stress_avg")
    if stress is not None:
        score += 10 if stress <= 35 else -15 if stress >= 55 else 0
    if acwr is not None:
        score += 10 if 0.8 <= acwr <= 1.3 else -22 if acwr > 1.5 else -5 if acwr < 0.5 else 0
    return round(max(0, min(100, score)), 1)


def risk_level(recovery: float | None, acwr: float | None) -> str:
    if recovery is not None and recovery < 45:
        return "high"
    if acwr is not None and acwr > 1.5:
        return "high"
    if recovery is not None and recovery < 65:
        return "medium"
    if acwr is not None and acwr > 1.3:
        return "medium"
    return "low"


def health_metric_value(row: dict[str, Any], metric: str):
    if metric == "sleep":
        return row.get("sleep_hours")
    if metric == "hrv":
        return row.get("hrv_avg")
    if metric == "rhr":
        return row.get("resting_hr")
    if metric == "stress":
        return row.get("stress_avg")
    if metric == "steps":
        return row.get("steps")
    if metric == "body_battery":
        values = [value for value in [row.get("body_battery_min"), row.get("body_battery_max")] if value is not None]
        return round(sum(values) / len(values), 2) if values else None
    return None


def infer_days(question: str) -> int:
    if "90" in question or "三個月" in question:
        return 90
    if "30" in question or "一個月" in question or "最近一月" in question:
        return 30
    if "28" in question:
        return 28
    if "14" in question or "兩週" in question:
        return 14
    if "7" in question or "一週" in question:
        return 7
    return 30
