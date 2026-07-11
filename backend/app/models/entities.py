from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Activity(Base):
    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    activity_id: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    activity_type: Mapped[str | None] = mapped_column(String(80), index=True)
    activity_name: Mapped[str | None] = mapped_column(String(240))
    start_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    duration_seconds: Mapped[float | None] = mapped_column(Float)
    distance_meters: Mapped[float | None] = mapped_column(Float)
    average_hr: Mapped[float | None] = mapped_column(Float)
    max_hr: Mapped[float | None] = mapped_column(Float)
    calories: Mapped[float | None] = mapped_column(Float)
    average_speed: Mapped[float | None] = mapped_column(Float)
    elevation_gain: Mapped[float | None] = mapped_column(Float)
    training_load: Mapped[float | None] = mapped_column(Float)
    source: Mapped[str] = mapped_column(String(40), default="garmin")
    raw_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    laps: Mapped[list["ActivityLap"]] = relationship(
        back_populates="activity", cascade="all, delete-orphan", passive_deletes=True
    )
    trackpoints: Mapped[list["ActivityTrackpoint"]] = relationship(
        back_populates="activity", cascade="all, delete-orphan", passive_deletes=True
    )


class ActivityLap(Base):
    __tablename__ = "activity_laps"
    __table_args__ = (UniqueConstraint("activity_id", "lap_index", name="uq_activity_lap_index"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    activity_id: Mapped[str] = mapped_column(
        String(80), ForeignKey("activities.activity_id", ondelete="CASCADE"), index=True, nullable=False
    )
    lap_index: Mapped[int] = mapped_column(Integer, nullable=False)
    start_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration_seconds: Mapped[float | None] = mapped_column(Float)
    distance_meters: Mapped[float | None] = mapped_column(Float)
    average_hr: Mapped[float | None] = mapped_column(Float)
    max_hr: Mapped[float | None] = mapped_column(Float)
    average_speed: Mapped[float | None] = mapped_column(Float)
    calories: Mapped[float | None] = mapped_column(Float)
    raw_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    activity: Mapped[Activity] = relationship(back_populates="laps")


class ActivityTrackpoint(Base):
    __tablename__ = "activity_trackpoints"
    __table_args__ = (UniqueConstraint("activity_id", "timestamp", name="uq_activity_trackpoint_timestamp"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    activity_id: Mapped[str] = mapped_column(
        String(80), ForeignKey("activities.activity_id", ondelete="CASCADE"), index=True, nullable=False
    )
    timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    heart_rate: Mapped[float | None] = mapped_column(Float)
    speed: Mapped[float | None] = mapped_column(Float)
    distance_meters: Mapped[float | None] = mapped_column(Float)
    altitude: Mapped[float | None] = mapped_column(Float)
    raw_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    activity: Mapped[Activity] = relationship(back_populates="trackpoints")


class DailyHealth(Base):
    __tablename__ = "daily_health"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[date] = mapped_column(Date, unique=True, index=True, nullable=False)
    steps: Mapped[int | None] = mapped_column(Integer)
    resting_hr: Mapped[float | None] = mapped_column(Float)
    sleep_hours: Mapped[float | None] = mapped_column(Float)
    stress_avg: Mapped[float | None] = mapped_column(Float)
    stress_max: Mapped[float | None] = mapped_column(Float)
    body_battery_min: Mapped[float | None] = mapped_column(Float)
    body_battery_max: Mapped[float | None] = mapped_column(Float)
    hrv_avg: Mapped[float | None] = mapped_column(Float)
    intensity_minutes: Mapped[int | None] = mapped_column(Integer)
    calories: Mapped[float | None] = mapped_column(Float)
    weight: Mapped[float | None] = mapped_column(Float)
    raw_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class DerivedMetric(Base):
    __tablename__ = "derived_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[date] = mapped_column(Date, unique=True, index=True, nullable=False)
    acute_load_7d: Mapped[float | None] = mapped_column(Float)
    chronic_load_28d: Mapped[float | None] = mapped_column(Float)
    acwr: Mapped[float | None] = mapped_column(Float)
    sleep_7d_avg: Mapped[float | None] = mapped_column(Float)
    hrv_7d_avg: Mapped[float | None] = mapped_column(Float)
    rhr_7d_avg: Mapped[float | None] = mapped_column(Float)
    recovery_score: Mapped[float | None] = mapped_column(Float)
    risk_level: Mapped[str | None] = mapped_column(String(20))
    notes_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class AiReport(Base):
    __tablename__ = "ai_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    report_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    report_type: Mapped[str] = mapped_column(String(40), index=True, nullable=False)
    question: Mapped[str | None] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    model: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)

