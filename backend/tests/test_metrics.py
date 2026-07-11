from datetime import date, datetime, timedelta, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import Activity, DailyHealth
from app.services.metrics_service import MetricsService


def make_session():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, future=True)()


def test_metrics_calculate_acwr_and_recovery():
    db = make_session()
    anchor = date(2026, 1, 28)
    for idx in range(28):
        day = anchor - timedelta(days=27 - idx)
        db.add(
            DailyHealth(
                date=day,
                sleep_hours=7.0,
                hrv_avg=48,
                resting_hr=56,
                stress_avg=30,
                steps=8000,
            )
        )
        db.add(
            Activity(
                activity_id=f"a-{idx}",
                activity_type="running",
                activity_name="Run",
                start_time=datetime.combine(day, datetime.min.time(), tzinfo=timezone.utc),
                duration_seconds=3600,
                training_load=70 if idx >= 21 else 40,
                source="test",
            )
        )
    db.commit()

    metric = MetricsService(db).recalculate_for_date(anchor)
    assert metric.acute_load_7d == 70
    assert metric.chronic_load_28d == 47.5
    assert metric.acwr == 1.47
    assert metric.recovery_score is not None
    assert metric.risk_level in {"low", "medium", "high"}

