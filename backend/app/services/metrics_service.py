from datetime import date, datetime, time, timedelta, timezone
from statistics import mean

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models import Activity, DailyHealth, DerivedMetric


class MetricsService:
    def __init__(self, db: Session):
        self.db = db

    def recalculate_all(self) -> int:
        dates = {
            row[0]
            for row in self.db.query(DailyHealth.date).all()
            if row[0] is not None
        }
        activity_dates = {
            row[0]
            for row in self.db.query(func.date(Activity.start_time)).all()
            if row[0] is not None
        }
        for value in activity_dates:
            dates.add(date.fromisoformat(str(value)))

        updated = 0
        for metric_date in sorted(dates):
            self.recalculate_for_date(metric_date)
            updated += 1
        self.db.commit()
        return updated

    def recalculate_for_date(self, metric_date: date) -> DerivedMetric:
        acute_load_7d = self._load_average(metric_date, 7)
        chronic_load_28d = self._load_average(metric_date, 28)
        acwr = round(acute_load_7d / chronic_load_28d, 2) if chronic_load_28d else None
        health_window = self._health_window(metric_date, 7)

        sleep_7d_avg = avg([item.sleep_hours for item in health_window])
        hrv_7d_avg = avg([item.hrv_avg for item in health_window])
        rhr_7d_avg = avg([item.resting_hr for item in health_window])
        today = self.db.query(DailyHealth).filter(DailyHealth.date == metric_date).one_or_none()

        recovery_score = self._recovery_score(today, sleep_7d_avg, hrv_7d_avg, rhr_7d_avg, acwr)
        risk_level = self._risk_level(recovery_score, acwr)
        notes = {
            "method": "rule_based_mvp",
            "training_load": "acute_load_7d and chronic_load_28d are daily averages over calendar windows.",
            "medical_disclaimer": "Training guidance only; not a medical diagnosis.",
        }

        metric = self.db.query(DerivedMetric).filter(DerivedMetric.date == metric_date).one_or_none()
        if metric is None:
            metric = DerivedMetric(date=metric_date)
            self.db.add(metric)

        metric.acute_load_7d = acute_load_7d
        metric.chronic_load_28d = chronic_load_28d
        metric.acwr = acwr
        metric.sleep_7d_avg = sleep_7d_avg
        metric.hrv_7d_avg = hrv_7d_avg
        metric.rhr_7d_avg = rhr_7d_avg
        metric.recovery_score = recovery_score
        metric.risk_level = risk_level
        metric.notes_json = notes
        return metric

    def _load_average(self, end_date: date, days: int) -> float:
        start_dt = datetime.combine(end_date - timedelta(days=days - 1), time.min, tzinfo=timezone.utc)
        end_dt = datetime.combine(end_date + timedelta(days=1), time.min, tzinfo=timezone.utc)
        rows = (
            self.db.query(Activity.training_load, Activity.duration_seconds, Activity.average_hr)
            .filter(Activity.start_time >= start_dt, Activity.start_time < end_dt)
            .all()
        )
        total = 0.0
        for training_load, duration_seconds, average_hr in rows:
            if training_load is not None:
                total += float(training_load)
            elif duration_seconds and average_hr:
                total += (float(duration_seconds) / 3600) * (float(average_hr) / 2)
        return round(total / days, 2)

    def _health_window(self, end_date: date, days: int) -> list[DailyHealth]:
        start_date = end_date - timedelta(days=days - 1)
        return (
            self.db.query(DailyHealth)
            .filter(DailyHealth.date >= start_date, DailyHealth.date <= end_date)
            .order_by(DailyHealth.date.asc())
            .all()
        )

    def _recovery_score(
        self,
        today: DailyHealth | None,
        sleep_7d_avg: float | None,
        hrv_7d_avg: float | None,
        rhr_7d_avg: float | None,
        acwr: float | None,
    ) -> float | None:
        if today is None:
            return None

        score = 55.0
        if today.sleep_hours is not None:
            if today.sleep_hours >= 7.0:
                score += 15
            elif today.sleep_hours >= 6.0:
                score += 7
            else:
                score -= 8

        if today.hrv_avg is not None and hrv_7d_avg:
            delta = today.hrv_avg - hrv_7d_avg
            score += max(-15, min(12, delta * 1.4))

        if today.resting_hr is not None and rhr_7d_avg:
            delta = today.resting_hr - rhr_7d_avg
            score += max(-12, min(10, -delta * 3))

        if today.stress_avg is not None:
            if today.stress_avg <= 35:
                score += 10
            elif today.stress_avg >= 55:
                score -= 15

        if acwr is not None:
            if 0.8 <= acwr <= 1.3:
                score += 10
            elif acwr > 1.5:
                score -= 22
            elif acwr < 0.5:
                score -= 5

        return round(max(0, min(100, score)), 1)

    def _risk_level(self, recovery_score: float | None, acwr: float | None) -> str:
        if recovery_score is not None and recovery_score < 45:
            return "high"
        if acwr is not None and acwr > 1.5:
            return "high"
        if recovery_score is not None and recovery_score < 65:
            return "medium"
        if acwr is not None and acwr > 1.3:
            return "medium"
        return "low"


def avg(values: list[float | int | None]) -> float | None:
    cleaned = [float(value) for value in values if value is not None]
    return round(mean(cleaned), 2) if cleaned else None

