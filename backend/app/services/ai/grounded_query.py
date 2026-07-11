from datetime import date, datetime, time, timedelta, timezone
from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

from ...config import Settings
from ...models import Activity, AiReport, DailyHealth, DerivedMetric
from .provider import create_ai_provider
from .prompt_builder import build_grounded_prompt


class GroundedQueryService:
    def __init__(self, db: Session, settings: Settings):
        self.db = db
        self.settings = settings
        self.provider = create_ai_provider(settings)

    def analyze_today(self) -> AiReport:
        evidence = self.collect_evidence(days=30)
        question = "請分析今日恢復狀態、是否適合高強度訓練，以及最近訓練負荷是否過高。"
        return self._create_report("today", question, evidence)

    def answer_question(self, question: str) -> AiReport:
        evidence = self.collect_evidence(days=self._infer_days(question))
        return self._create_report("query", question, evidence)

    def latest_usable_health(self) -> DailyHealth | None:
        usable = (
            self.db.query(DailyHealth)
            .filter(sql_health_signal_filter())
            .order_by(DailyHealth.date.desc())
            .first()
        )
        return usable or self.db.query(DailyHealth).order_by(DailyHealth.date.desc()).first()

    def collect_evidence(self, days: int) -> dict[str, Any]:
        latest_health = self.latest_usable_health()
        anchor_date = latest_health.date if latest_health else date.today()
        latest_metric = self.db.query(DerivedMetric).filter(DerivedMetric.date == anchor_date).one_or_none()
        start_date = anchor_date - timedelta(days=days - 1)
        start_dt = datetime.combine(start_date, time.min, tzinfo=timezone.utc)
        end_dt = datetime.combine(anchor_date + timedelta(days=1), time.min, tzinfo=timezone.utc)

        health_rows = (
            self.db.query(DailyHealth)
            .filter(DailyHealth.date >= start_date, DailyHealth.date <= anchor_date)
            .order_by(DailyHealth.date.asc())
            .all()
        )
        metric_rows = (
            self.db.query(DerivedMetric)
            .filter(DerivedMetric.date >= start_date, DerivedMetric.date <= anchor_date)
            .order_by(DerivedMetric.date.asc())
            .all()
        )
        activity_rows = (
            self.db.query(Activity)
            .filter(Activity.start_time >= start_dt, Activity.start_time < end_dt)
            .order_by(Activity.start_time.desc())
            .limit(80)
            .all()
        )

        return {
            "has_data": bool(health_rows or activity_rows),
            "range": {"start_date": start_date.isoformat(), "end_date": anchor_date.isoformat(), "days": days},
            "latest_health": serialize_health(latest_health) if latest_health else None,
            "latest_metric": serialize_metric(latest_metric) if latest_metric else None,
            "daily_health": [serialize_health(row) for row in health_rows],
            "derived_metrics": [serialize_metric(row) for row in metric_rows],
            "activities": [serialize_activity(row) for row in activity_rows],
        }

    def _create_report(self, report_type: str, question: str, evidence: dict[str, Any]) -> AiReport:
        prompt = build_grounded_prompt(question, evidence)
        answer = self.provider.generate(prompt, evidence)
        report_date = date.fromisoformat(evidence["range"]["end_date"]) if evidence.get("range") else date.today()
        report = AiReport(
            report_date=report_date,
            report_type=report_type,
            question=question,
            answer=answer,
            evidence_json=evidence,
            model=self.provider.model_name,
        )
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return report

    def _infer_days(self, question: str) -> int:
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


def serialize_activity(row: Activity) -> dict[str, Any]:
    return {
        "activity_id": row.activity_id,
        "activity_type": row.activity_type,
        "activity_name": row.activity_name,
        "start_time": row.start_time.isoformat() if row.start_time else None,
        "duration_seconds": row.duration_seconds,
        "distance_meters": row.distance_meters,
        "average_hr": row.average_hr,
        "max_hr": row.max_hr,
        "training_load": row.training_load,
        "calories": row.calories,
    }


def serialize_health(row: DailyHealth | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return {
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
    }


def serialize_metric(row: DerivedMetric | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return {
        "date": row.date.isoformat(),
        "acute_load_7d": row.acute_load_7d,
        "chronic_load_28d": row.chronic_load_28d,
        "acwr": row.acwr,
        "sleep_7d_avg": row.sleep_7d_avg,
        "hrv_7d_avg": row.hrv_7d_avg,
        "rhr_7d_avg": row.rhr_7d_avg,
        "recovery_score": row.recovery_score,
        "risk_level": row.risk_level,
    }


HEALTH_SIGNAL_FIELDS = [
    "resting_hr",
    "sleep_hours",
    "stress_avg",
    "body_battery_min",
    "body_battery_max",
    "hrv_avg",
]


def sql_health_signal_filter():
    return or_(DailyHealth.steps > 0, *(getattr(DailyHealth, field).isnot(None) for field in HEALTH_SIGNAL_FIELDS))
