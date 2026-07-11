from abc import ABC, abstractmethod
from typing import Any, TypedDict


class GarminConnectorError(RuntimeError):
    pass


class GarminAuthError(GarminConnectorError):
    pass


class GarminNetworkError(GarminConnectorError):
    pass


class GarminActivity(TypedDict, total=False):
    activity_id: str
    activity_type: str
    activity_name: str
    start_time: str
    duration_seconds: float
    distance_meters: float
    average_hr: float
    max_hr: float
    calories: float
    average_speed: float
    elevation_gain: float
    training_load: float
    laps: list[dict[str, Any]]
    trackpoints: list[dict[str, Any]]
    raw_json: dict[str, Any]


class DailyHealth(TypedDict, total=False):
    date: str
    steps: int
    resting_hr: float
    sleep_hours: float
    stress_avg: float
    stress_max: float
    body_battery_min: float
    body_battery_max: float
    hrv_avg: float
    intensity_minutes: int
    calories: float
    weight: float
    raw_json: dict[str, Any]


class GarminPayload(TypedDict):
    source: str
    activities: list[GarminActivity]
    daily_health: list[DailyHealth]


class GarminConnector(ABC):
    @abstractmethod
    def fetch(self, days: int = 30) -> GarminPayload:
        """Fetch normalized Garmin data for the requested lookback window."""

