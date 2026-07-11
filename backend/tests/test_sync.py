from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import Activity, DailyHealth
from app.services.garmin.unofficial import build_demo_payload
from app.services.sync_service import SyncService, parse_datetime


class StaticConnector:
    def __init__(self, payload):
        self.payload = payload

    def fetch(self, days: int = 30):
        return self.payload


def make_session():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, future=True)()


def test_sync_is_idempotent_for_activity_id_and_date():
    db = make_session()
    payload = build_demo_payload(days=10)
    connector = StaticConnector(payload)

    first = SyncService(db, connector).sync(days=10)
    second = SyncService(db, connector).sync(days=10)

    assert first.activities_created > 0
    assert second.activities_created == 0
    assert second.activities_updated == len(payload["activities"])
    assert db.query(Activity).count() == len(payload["activities"])
    assert db.query(DailyHealth).count() == len(payload["daily_health"])


def test_parse_datetime_ignores_duration_like_values():
    assert parse_datetime(325.24) is None
    assert parse_datetime("325.24") is None
    assert parse_datetime("not-a-date") is None
    assert parse_datetime("2026-07-11T12:00:00Z").isoformat() == "2026-07-11T12:00:00+00:00"
