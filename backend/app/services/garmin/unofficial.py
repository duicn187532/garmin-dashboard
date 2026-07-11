from datetime import date, datetime, time, timedelta, timezone
import math
from pathlib import Path
import random
from typing import Any, Callable

from ...config import Settings
from .base import GarminAuthError, GarminConnector, GarminNetworkError, GarminPayload


class UnofficialGarminConnector(GarminConnector):
    """Connector boundary for garminconnect/garth.

    The MVP intentionally falls back to deterministic demo data when credentials are
    absent. That keeps local development and CI safe while preserving a replaceable
    connector interface for the official Garmin API later.
    """

    def __init__(self, settings: Settings):
        self.settings = settings

    def fetch(self, days: int = 30) -> GarminPayload:
        if self.settings.demo_mode:
            return build_demo_payload(days=days)

        return self._fetch_with_garminconnect(days=days)

    def _fetch_with_garminconnect(self, days: int) -> GarminPayload:
        try:
            from garminconnect import Garmin  # type: ignore
        except ImportError as exc:
            raise GarminAuthError(
                "garminconnect is not installed. Set DEMO_MODE=true or install the optional connector dependency."
            ) from exc

        try:
            tokenstore = self.settings.garmin_tokenstore
            Path(tokenstore).mkdir(parents=True, exist_ok=True)
            client = Garmin(
                self.settings.garmin_email,
                self.settings.garmin_password,
                prompt_mfa=self._prompt_mfa,
            )
            client.login(tokenstore=tokenstore)
        except GarminAuthError:
            raise
        except Exception as exc:  # pragma: no cover - depends on external service
            raise GarminAuthError(
                "Garmin login failed. Check credentials, MFA, token state, or run "
                "`python -m app.jobs.setup_garmin_tokens` once. "
                f"Connector said: {exc}"
            ) from exc

        try:
            end = date.today()
            start = end - timedelta(days=days - 1)
            raw_activities = client.get_activities_by_date(start.isoformat(), end.isoformat())
            activities = [normalize_activity_with_details(item, client) for item in raw_activities]
            daily_health = []
            for offset in range(days):
                day = start + timedelta(days=offset)
                daily_health.append(normalize_daily_health(day, client))
            return {"source": "garminconnect", "activities": activities, "daily_health": daily_health}
        except GarminAuthError:
            raise
        except Exception as exc:  # pragma: no cover - depends on external service
            raise GarminNetworkError("Garmin API request failed or returned an unexpected payload.") from exc

    def _prompt_mfa(self) -> str:
        if self.settings.garmin_mfa_code:
            return self.settings.garmin_mfa_code
        raise GarminAuthError(
            "Garmin MFA is required. Temporarily set GARMIN_MFA_CODE in backend/.env "
            "or run `python -m app.jobs.setup_garmin_tokens` from a terminal."
        )


def normalize_activity(item: dict[str, Any]) -> dict[str, Any]:
    activity_id = str(item.get("activityId") or item.get("activity_id") or item.get("id"))
    start_time = item.get("startTimeLocal") or item.get("startTimeGMT") or item.get("start_time")
    activity_type = item.get("activityType", {})
    if isinstance(activity_type, dict):
        activity_type = activity_type.get("typeKey") or activity_type.get("typeId")
    return {
        "activity_id": activity_id,
        "activity_type": str(activity_type or "unknown"),
        "activity_name": item.get("activityName") or item.get("activity_name"),
        "start_time": start_time,
        "duration_seconds": item.get("duration") or item.get("elapsedDuration"),
        "distance_meters": item.get("distance"),
        "average_hr": item.get("averageHR") or item.get("average_hr"),
        "max_hr": item.get("maxHR") or item.get("max_hr"),
        "calories": item.get("calories"),
        "average_speed": item.get("averageSpeed"),
        "elevation_gain": item.get("elevationGain"),
        "training_load": item.get("activityTrainingLoad") or item.get("training_load"),
        "laps": [],
        "trackpoints": [],
        "raw_json": item,
    }


def normalize_activity_with_details(item: dict[str, Any], client: Any) -> dict[str, Any]:
    activity = normalize_activity(item)
    activity_id = activity["activity_id"]
    details = _safe_call(lambda: client.get_activity_details(activity_id), default={})
    splits = _safe_call(lambda: client.get_activity_splits(activity_id), default={})
    typed_splits = _safe_call(lambda: client.get_activity_typed_splits(activity_id), default={})

    laps = normalize_laps(activity_id, splits, typed_splits)
    trackpoints = normalize_trackpoints(activity_id, details)
    if laps:
        activity["laps"] = laps
    if trackpoints:
        activity["trackpoints"] = trackpoints
    activity["raw_json"] = {
        "summary": item,
        "details": details,
        "splits": splits,
        "typed_splits": typed_splits,
    }
    return activity


def normalize_daily_health(day: date, client: Any) -> dict[str, Any]:
    raw: dict[str, Any] = {"date": day.isoformat()}
    day_text = day.isoformat()
    raw["summary"] = _safe_call(lambda: client.get_stats(day_text), default=None)
    raw["summary_and_body"] = _safe_call(lambda: client.get_stats_and_body(day_text), default=None)
    raw["steps"] = _safe_call(lambda: client.get_steps_data(day_text), default=None)
    raw["sleep"] = _safe_call(lambda: client.get_sleep_data(day_text), default=None)
    raw["stress"] = _safe_call(lambda: client.get_stress_data(day_text), default=None)
    raw["all_day_stress"] = _safe_call(lambda: client.get_all_day_stress(day_text), default=None)
    raw["heart_rates"] = _safe_call(lambda: client.get_heart_rates(day_text), default=None)
    raw["rhr"] = _safe_call(lambda: client.get_rhr_day(day_text), default=None)
    raw["hrv"] = _safe_call(lambda: client.get_hrv_data(day_text), default=None)
    raw["body_battery"] = _safe_call(lambda: client.get_body_battery(day_text, day_text), default=None)
    raw["intensity_minutes"] = _safe_call(lambda: client.get_intensity_minutes_data(day_text), default=None)
    raw["body_composition"] = _safe_call(lambda: client.get_body_composition(day_text), default=None)

    return {
        "date": day_text,
        "steps": first_number(
            raw,
            ["summary.totalSteps", "summary.steps", "summary_and_body.totalSteps", "steps.totalSteps", "steps.steps"],
            integer=True,
        )
        or _extract_steps(raw.get("steps")),
        "resting_hr": first_number(
            raw,
            [
                "summary.restingHeartRate",
                "summary.restingHR",
                "summary_and_body.restingHeartRate",
                "heart_rates.restingHeartRate",
                "heart_rates.restingHeartRateDTO.restingHeartRate",
            ],
        )
        or extract_recursive_number(raw.get("rhr"), ["value", "restingHeartRate", "restingHr"]),
        "sleep_hours": _extract_sleep_hours(raw.get("sleep")),
        "stress_avg": first_number(
            raw,
            [
                "stress.avgStressLevel",
                "stress.averageStressLevel",
                "all_day_stress.avgStressLevel",
                "all_day_stress.averageStressLevel",
            ],
        ),
        "stress_max": first_number(raw, ["stress.maxStressLevel", "all_day_stress.maxStressLevel"]),
        "body_battery_min": extract_body_battery(raw.get("body_battery"), mode="min"),
        "body_battery_max": extract_body_battery(raw.get("body_battery"), mode="max"),
        "hrv_avg": first_number(
            raw,
            [
                "hrv.hrvSummary.lastNightAvg",
                "hrv.hrvSummary.lastNightAverage",
                "hrv.hrvSummary.weeklyAvg",
                "hrv.lastNightAvg",
                "hrv.average",
            ],
        )
        or extract_recursive_number(raw.get("hrv"), ["lastNightAvg", "lastNightAverage", "hrvAvg", "average"]),
        "intensity_minutes": extract_intensity_minutes(raw.get("intensity_minutes"))
        or first_number(raw, ["summary.intensityMinutes", "summary_and_body.intensityMinutes"], integer=True),
        "calories": first_number(
            raw,
            [
                "summary.totalKilocalories",
                "summary.calories",
                "summary_and_body.totalKilocalories",
                "summary_and_body.calories",
            ],
        ),
        "weight": normalize_weight(
            first_number(
                raw,
                [
                    "body_composition.totalAverage.weight",
                    "body_composition.totalAverage.weightInGrams",
                    "summary_and_body.weight",
                ],
            )
        ),
        "raw_json": raw,
    }


def normalize_laps(activity_id: str, splits: Any, typed_splits: Any) -> list[dict[str, Any]]:
    source = _first_list_by_key(splits, ["lapDTOs", "splitSummaries", "splits", "activitySplits"])
    if not source:
        source = _first_list_by_key(typed_splits, ["lapDTOs", "splitSummaries", "splits", "activitySplits"])
    laps: list[dict[str, Any]] = []
    for index, item in enumerate(source or [], start=1):
        if not isinstance(item, dict):
            continue
        laps.append(
            {
                "activity_id": activity_id,
                "lap_index": int(first_number(item, ["lapIndex", "splitNumber", "lapNumber"], integer=True) or index),
                "start_time": first_value(item, ["startTimeGMT", "startTimeLocal", "startTime"]),
                "duration_seconds": first_number(item, ["duration", "movingDuration", "elapsedDuration", "timerDuration"]),
                "distance_meters": first_number(item, ["distance", "totalDistance", "distanceMeters"]),
                "average_hr": first_number(item, ["averageHR", "averageHr", "avgHr", "averageHeartRate"]),
                "max_hr": first_number(item, ["maxHR", "maxHr", "maxHeartRate"]),
                "average_speed": first_number(item, ["averageSpeed", "avgSpeed", "speed"]),
                "calories": first_number(item, ["calories", "caloriesBurned"]),
                "raw_json": item,
            }
        )
    return laps


def normalize_trackpoints(activity_id: str, details: Any) -> list[dict[str, Any]]:
    points = normalize_chart_metrics(activity_id, details)
    if points:
        return points
    return normalize_polyline_points(activity_id, details)


def normalize_chart_metrics(activity_id: str, details: Any) -> list[dict[str, Any]]:
    metrics = _first_list_by_key(details, ["activityDetailMetrics", "metrics"])
    points: list[dict[str, Any]] = []
    for index, item in enumerate(metrics or []):
        if not isinstance(item, dict):
            continue
        flat = flatten_metric_item(item)
        timestamp = first_value(flat, ["startTimeGMT", "startTimeLocal", "timestamp", "sampleTime", "clockDuration"])
        points.append(
            {
                "activity_id": activity_id,
                "timestamp": timestamp,
                "latitude": first_number(flat, ["directLatitude", "latitude", "lat", "positionLat"]),
                "longitude": first_number(flat, ["directLongitude", "longitude", "lon", "lng", "positionLong"]),
                "heart_rate": first_number(flat, ["heartRate", "heart_rate", "heartrate", "hr"]),
                "speed": first_number(flat, ["speed", "enhancedSpeed", "velocity"]),
                "distance_meters": first_number(flat, ["sumDistance", "distance", "totalDistance"]),
                "altitude": first_number(flat, ["directElevation", "elevation", "altitude", "enhancedAltitude"]),
                "raw_json": item,
            }
        )
    return [point for point in points if any(point.get(key) is not None for key in ["heart_rate", "latitude", "speed"])]


def normalize_polyline_points(activity_id: str, details: Any) -> list[dict[str, Any]]:
    polyline = _first_list_by_key(details, ["polyline", "geoPolyline", "geoPolylineDTO.polyline"])
    points: list[dict[str, Any]] = []
    for item in polyline or []:
        if not isinstance(item, dict):
            continue
        points.append(
            {
                "activity_id": activity_id,
                "timestamp": first_value(item, ["timestamp", "time"]),
                "latitude": first_number(item, ["lat", "latitude"]),
                "longitude": first_number(item, ["lon", "lng", "longitude"]),
                "heart_rate": first_number(item, ["heartRate", "hr"]),
                "speed": first_number(item, ["speed"]),
                "distance_meters": first_number(item, ["distance", "sumDistance"]),
                "altitude": first_number(item, ["altitude", "elevation"]),
                "raw_json": item,
            }
        )
    return [point for point in points if point.get("latitude") is not None and point.get("longitude") is not None]


def flatten_metric_item(item: dict[str, Any]) -> dict[str, Any]:
    flat = dict(item)
    metrics = item.get("metrics")
    if isinstance(metrics, list):
        for metric in metrics:
            if not isinstance(metric, dict):
                continue
            key = metric.get("key") or metric.get("metricKey") or metric.get("type") or metric.get("name")
            value = metric.get("value") if "value" in metric else metric.get("values")
            if key:
                flat[str(key)] = value
    elif isinstance(metrics, dict):
        flat.update(metrics)
    return flat


def _extract_steps(raw: Any) -> int | None:
    if isinstance(raw, list) and raw:
        return sum(int(item.get("steps", 0) or 0) for item in raw if isinstance(item, dict))
    if isinstance(raw, dict):
        value = raw.get("totalSteps") or raw.get("steps")
        return int(value) if value is not None else None
    return None


def _extract_sleep_hours(raw: Any) -> float | None:
    if not isinstance(raw, dict):
        return None
    seconds = (
        raw.get("dailySleepDTO", {}).get("sleepTimeSeconds")
        or raw.get("dailySleepDTO", {}).get("sleepSeconds")
        or raw.get("dailySleepDTO", {}).get("totalSleepSeconds")
        or raw.get("sleepTimeSeconds")
        or raw.get("sleepSeconds")
        or raw.get("totalSleepSeconds")
    )
    return round(float(seconds) / 3600, 2) if seconds else None


def _extract_nested_number(raw: Any, keys: list[str]) -> float | None:
    if not isinstance(raw, dict):
        return None
    for key in keys:
        if raw.get(key) is not None:
            return float(raw[key])
    return None


def _safe_call(call: Callable[[], Any], default: Any = None) -> Any:
    try:
        return call()
    except Exception:
        return default


def first_value(raw: Any, paths: list[str]) -> Any:
    for path in paths:
        value = get_path(raw, path)
        if value is not None:
            return value
    return None


def first_number(raw: Any, paths: list[str], integer: bool = False) -> float | int | None:
    value = first_value(raw, paths)
    number = coerce_number(value)
    if number is None:
        return None
    return int(number) if integer else number


def get_path(raw: Any, path: str) -> Any:
    current = raw
    for part in path.split("."):
        if isinstance(current, dict):
            current = current.get(part)
        elif isinstance(current, list):
            if part.isdigit() and int(part) < len(current):
                current = current[int(part)]
            else:
                current = first_dict_value(current, part)
        else:
            return None
        if current is None:
            return None
    return current


def first_dict_value(items: list[Any], key: str) -> Any:
    for item in items:
        if isinstance(item, dict) and item.get(key) is not None:
            return item.get(key)
    return None


def coerce_number(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.strip().replace(",", "")
        if not cleaned:
            return None
        try:
            return float(cleaned)
        except ValueError:
            return None
    if isinstance(value, dict):
        for key in ["value", "amount", "weight", "average", "avg"]:
            number = coerce_number(value.get(key))
            if number is not None:
                return number
    return None


def extract_recursive_number(raw: Any, keys: list[str]) -> float | None:
    if isinstance(raw, dict):
        for key in keys:
            number = coerce_number(raw.get(key))
            if number is not None:
                return number
        for value in raw.values():
            number = extract_recursive_number(value, keys)
            if number is not None:
                return number
    elif isinstance(raw, list):
        for item in raw:
            number = extract_recursive_number(item, keys)
            if number is not None:
                return number
    return None


def extract_body_battery(raw: Any, mode: str) -> float | None:
    values = collect_body_battery_values(raw)
    if not values:
        return None
    return float(min(values) if mode == "min" else max(values))


def collect_body_battery_values(raw: Any) -> list[float]:
    values: list[float] = []
    if isinstance(raw, dict):
        for key in ["bodyBatteryValuesArray", "bodyBatteryValues", "values"]:
            nested = raw.get(key)
            if nested is not None:
                values.extend(collect_body_battery_values(nested))
        for key in ["bodyBatteryValue", "bodyBattery", "value"]:
            number = coerce_number(raw.get(key))
            if number is not None and 0 <= number <= 100:
                values.append(number)
        for value in raw.values():
            if isinstance(value, (dict, list)):
                values.extend(collect_body_battery_values(value))
    elif isinstance(raw, list):
        for item in raw:
            if isinstance(item, list):
                for candidate in reversed(item):
                    number = coerce_number(candidate)
                    if number is not None and 0 <= number <= 100:
                        values.append(number)
                        break
            else:
                values.extend(collect_body_battery_values(item))
    return values


def extract_intensity_minutes(raw: Any) -> int | None:
    if not raw:
        return None
    direct = first_number(
        raw,
        [
            "totalIntensityMinutes",
            "intensityMinutes",
            "weeklyTotal",
            "moderateIntensityMinutes",
            "vigorousIntensityMinutes",
        ],
        integer=True,
    )
    if direct is not None and not isinstance(raw, dict):
        return int(direct)
    if isinstance(raw, dict):
        moderate = first_number(raw, ["moderateIntensityMinutes", "moderateValue", "moderate"], integer=True) or 0
        vigorous = first_number(raw, ["vigorousIntensityMinutes", "vigorousValue", "vigorous"], integer=True) or 0
        total = first_number(raw, ["totalIntensityMinutes", "intensityMinutes", "total"], integer=True)
        if total is not None:
            return int(total)
        if moderate or vigorous:
            return int(moderate + vigorous * 2)
    return None


def _first_list_by_key(raw: Any, paths: list[str]) -> list[Any] | None:
    for path in paths:
        value = get_path(raw, path)
        if isinstance(value, list):
            return value
    if isinstance(raw, list):
        return raw
    return None


def normalize_weight(value: float | int | None) -> float | None:
    if value is None:
        return None
    numeric = float(value)
    if numeric > 1000:
        numeric = numeric / 1000
    return round(numeric, 2)


def build_demo_payload(days: int = 30) -> GarminPayload:
    rng = random.Random(4207)
    today = date.today()
    start = today - timedelta(days=days - 1)
    daily_health: list[dict[str, Any]] = []
    activities: list[dict[str, Any]] = []

    for offset in range(days):
        day = start + timedelta(days=offset)
        weekday = day.weekday()
        sleep = 6.4 + 0.6 * math.sin(offset / 4) + (0.35 if weekday in {5, 6} else 0)
        hrv = 46 + 4 * math.sin(offset / 5) - (3 if offset % 11 in {0, 1} else 0)
        rhr = 56 - 2 * math.sin(offset / 6) + (2 if sleep < 6.3 else 0)
        stress = 32 + 8 * math.cos(offset / 7) + (6 if weekday == 0 else 0)
        steps = 6200 + int(2300 * math.sin(offset / 3)) + rng.randint(0, 1800)
        body_max = 78 + int(9 * math.sin(offset / 5))
        daily_health.append(
            {
                "date": day.isoformat(),
                "steps": max(2500, steps),
                "resting_hr": round(rhr, 1),
                "sleep_hours": round(max(4.5, sleep), 2),
                "stress_avg": round(max(12, stress), 1),
                "stress_max": round(max(45, stress + 28), 1),
                "body_battery_min": max(5, body_max - 58),
                "body_battery_max": body_max,
                "hrv_avg": round(max(25, hrv), 1),
                "intensity_minutes": 20 + (35 if weekday in {1, 3, 5} else 5),
                "calories": 2050 + rng.randint(0, 450),
                "weight": 70.5 + round(math.sin(offset / 10) * 0.4, 1),
                "raw_json": {"demo": True, "date": day.isoformat()},
            }
        )

        if weekday in {1, 3, 5}:
            kind = "fencing" if weekday == 3 else ("running" if weekday == 5 else "cycling")
            start_dt = datetime.combine(day, time(hour=18 if weekday != 5 else 8), tzinfo=timezone.utc)
            duration = 3600 if kind == "fencing" else (2700 if kind == "running" else 4200)
            distance = 0 if kind == "fencing" else (8600 + rng.randint(-900, 900) if kind == "running" else 24500)
            avg_hr = 138 + (10 if kind == "fencing" else 4) + rng.randint(-5, 6)
            training_load = 62 + (22 if kind == "fencing" else 0) + rng.randint(-12, 18)
            activity_id = f"demo-{day.isoformat()}-{kind}"
            activities.append(
                {
                    "activity_id": activity_id,
                    "activity_type": kind,
                    "activity_name": f"{kind.title()} session",
                    "start_time": start_dt.isoformat(),
                    "duration_seconds": duration,
                    "distance_meters": distance,
                    "average_hr": avg_hr,
                    "max_hr": avg_hr + 34,
                    "calories": 420 + rng.randint(40, 180),
                    "average_speed": round(distance / duration, 2) if distance else None,
                    "elevation_gain": 38 if kind == "running" else 90 if kind == "cycling" else 0,
                    "training_load": training_load,
                    "laps": build_demo_laps(activity_id, start_dt, duration, distance, avg_hr),
                    "trackpoints": build_demo_trackpoints(activity_id, start_dt, duration, distance, avg_hr),
                    "raw_json": {"demo": True, "date": day.isoformat(), "kind": kind},
                }
            )

    return {"source": "demo", "activities": activities, "daily_health": daily_health}


def build_demo_laps(
    activity_id: str, start_dt: datetime, duration: float, distance: float, avg_hr: float
) -> list[dict[str, Any]]:
    laps = []
    for idx in range(4):
        lap_duration = duration / 4
        lap_distance = distance / 4 if distance else 0
        laps.append(
            {
                "activity_id": activity_id,
                "lap_index": idx + 1,
                "start_time": (start_dt + timedelta(seconds=idx * lap_duration)).isoformat(),
                "duration_seconds": lap_duration,
                "distance_meters": lap_distance,
                "average_hr": avg_hr + idx * 2,
                "max_hr": avg_hr + idx * 2 + 20,
                "average_speed": round(lap_distance / lap_duration, 2) if lap_distance else None,
                "calories": 110 + idx * 12,
                "raw_json": {"demo": True},
            }
        )
    return laps


def build_demo_trackpoints(
    activity_id: str, start_dt: datetime, duration: float, distance: float, avg_hr: float
) -> list[dict[str, Any]]:
    points = []
    for idx in range(24):
        ratio = idx / 23
        lat = 25.033 + 0.006 * math.sin(ratio * math.pi * 2)
        lon = 121.565 + 0.006 * math.cos(ratio * math.pi * 2)
        points.append(
            {
                "activity_id": activity_id,
                "timestamp": (start_dt + timedelta(seconds=duration * ratio)).isoformat(),
                "latitude": round(lat, 6),
                "longitude": round(lon, 6),
                "heart_rate": round(avg_hr + 14 * math.sin(ratio * math.pi), 1),
                "speed": round((distance / duration) * (0.9 + 0.16 * math.sin(ratio * math.pi * 3)), 2)
                if distance
                else None,
                "distance_meters": round(distance * ratio, 1) if distance else 0,
                "altitude": round(21 + 8 * math.sin(ratio * math.pi * 2), 1),
                "raw_json": {"demo": True},
            }
        )
    return points
