from datetime import date, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import Settings
from app.database import Base
from app.models import AiReport, DailyHealth, DerivedMetric
from app.store import SqlDataStore


def make_session():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, future=True)()


def test_dashboard_uses_latest_usable_health_not_empty_today():
    db = make_session()
    today = date(2026, 7, 12)
    yesterday = today - timedelta(days=1)

    db.add(DailyHealth(date=today))
    db.add(
        DailyHealth(
            date=yesterday,
            sleep_hours=7.1,
            hrv_avg=48,
            resting_hr=52,
            stress_avg=28,
            steps=8200,
        )
    )
    db.add(DerivedMetric(date=today, recovery_score=12, risk_level="high"))
    db.add(DerivedMetric(date=yesterday, recovery_score=82, risk_level="low"))
    db.add(AiReport(report_date=today, report_type="today", answer="today blank", model="test"))
    db.add(AiReport(report_date=yesterday, report_type="today", answer="yesterday useful", model="test"))
    db.commit()

    store = SqlDataStore(db, Settings())

    summary = store.summary()
    dashboard = store.dashboard_today()

    assert summary["latest_health_date"] == yesterday.isoformat()
    assert dashboard["health"]["date"] == yesterday.isoformat()
    assert dashboard["derived_metric"]["recovery_score"] == 82
    assert dashboard["ai_report"]["answer"] == "yesterday useful"
