from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen
from zoneinfo import ZoneInfo

import ingest_coros_fit_batch as batch
import heat_adjust

REPO_ROOT = Path(__file__).resolve().parent.parent
LOCAL_TZ = ZoneInfo("America/New_York")
OPEN_METEO_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"


def row_start_time_value(row: dict[str, str]) -> str:
    return row.get("start_time") or row.get("start_time_local") or row.get("start_time_utc") or ""


def parse_start_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=LOCAL_TZ)
    return parsed


@dataclass
class Activity:
    row: dict[str, str]
    local_start: datetime
    local_date: date
    timezone_name: str

    @property
    def distance_mi(self) -> float:
        return float(self.row["distance_mi"] or 0.0)

    @property
    def duration_s(self) -> int:
        return int(float(self.row["duration_s"] or 0.0))

    @property
    def completed_label(self) -> str:
        sport = self.row.get("sport", "").strip() or "activity"
        noun = "run" if sport == "running" else sport.replace("_", " ")
        return f"{self.row['distance_mi']} mi {noun}"

    @property
    def pace_label(self) -> str:
        if self.distance_mi <= 0 or self.duration_s <= 0:
            return ""
        pace_seconds = round(self.duration_s / self.distance_mi)
        minutes, seconds = divmod(pace_seconds, 60)
        return f"{minutes}:{seconds:02d}/mi"

    @property
    def time_label(self) -> str:
        seconds = self.duration_s
        hours, remainder = divmod(seconds, 3600)
        minutes, secs = divmod(remainder, 60)
        if hours:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        return f"{minutes}:{secs:02d}"

    @property
    def import_note(self) -> str:
        return f"- Imported from `{self.row['source_relpath']}`."

    @property
    def fit_note(self) -> str:
        start_display = self.row.get("start_time", "").strip()
        return (
            f"- FIT summary: start `{start_display}`, avg HR "
            f"`{self.row['avg_hr'] or ''}`, max HR `{self.row['max_hr'] or ''}`, "
            f"ascent `{self.row['ascent_m'] or ''} m`."
        )

    @property
    def weather_note(self) -> str:
        temperature_f = self.row.get("weather_temp_f", "").strip()
        observed_at = self.row.get("weather_observation_time", "").strip()
        if not temperature_f or not observed_at:
            return ""
        source = self.row.get("weather_source", "").strip() or "weather"
        return f"- Weather at start: `{temperature_f} F` at `{observed_at}` from `{source}`."

    @property
    def heat_note(self) -> str:
        load_sum_raw = self.row.get("heat_load_sum", "").strip()
        temp_f = self.row.get("weather_temp_f", "").strip()
        dew_f = self.row.get("weather_dew_point_f", "").strip()
        if not load_sum_raw or not temp_f or not dew_f:
            return ""
        load_sum = int(load_sum_raw)
        if load_sum < 111:
            return ""
        if self.distance_mi <= 0 or self.duration_s <= 0:
            return ""
        actual_sec = round(self.duration_s / self.distance_mi)
        fraction = heat_adjust.pace_adjust_fraction(load_sum)
        neutral_sec = heat_adjust.heat_neutral_pace_seconds(actual_sec, fraction)
        label = heat_adjust.heat_band_label(load_sum)
        # Display the rounded components and their own sum so the printed line always
        # adds up. The stored, unrounded load_sum stays authoritative for the band,
        # threshold, and fraction; pct is derived from that same fraction so the
        # percentage and the neutral-pace math can never disagree within one note.
        temp_display = round(float(temp_f))
        dew_display = round(float(dew_f))
        pct = f"{fraction * 100:.1f}"

        def fmt(seconds: int) -> str:
            minutes, secs = divmod(seconds, 60)
            return f"{minutes}:{secs:02d}/mi"

        return (
            f"- Heat: {temp_display}°F + {dew_display}°F dew = {temp_display + dew_display} "
            f"({label}). Heat-neutral equivalent ~{fmt(neutral_sec)} "
            f"(ran {fmt(actual_sec)}, ~+{pct}%)."
        )


def weather_hour_key(local_start: datetime) -> str:
    hour_start = local_start.replace(minute=0, second=0, microsecond=0)
    return hour_start.strftime("%Y-%m-%dT%H:00")


def weather_group_key(activity: Activity) -> tuple[str, str, str] | None:
    latitude = activity.row.get("start_lat", "").strip()
    longitude = activity.row.get("start_lon", "").strip()
    if not latitude or not longitude:
        return None
    latitude_key = f"{float(latitude):.3f}"
    longitude_key = f"{float(longitude):.3f}"
    return latitude_key, longitude_key, activity.timezone_name


def fetch_open_meteo_archive(
    latitude: str,
    longitude: str,
    timezone_name: str,
    start_date: date,
    end_date: date,
    timeout_s: float,
) -> dict[str, object] | dict[str, str]:
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "hourly": "temperature_2m,dew_point_2m,apparent_temperature",
        "timezone": timezone_name,
    }
    url = f"{OPEN_METEO_ARCHIVE_URL}?{urlencode(params)}"
    try:
        with urlopen(url, timeout=timeout_s) as response:
            return json.load(response)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        return {"weather_fetch_error": f"{type(exc).__name__}: {exc}"}


def weather_update_from_hourly(activity: Activity, hourly: dict[str, object]) -> dict[str, str]:
    times = hourly.get("time", [])
    temperatures_c = hourly.get("temperature_2m", [])
    if not isinstance(times, list) or not isinstance(temperatures_c, list):
        return {"weather_fetch_error": "Open-Meteo hourly payload missing time series"}
    target_time = weather_hour_key(activity.local_start)
    try:
        index = times.index(target_time)
    except ValueError:
        return {"weather_fetch_error": f"Open-Meteo missing hourly point for {target_time}"}
    if index >= len(temperatures_c):
        return {"weather_fetch_error": f"Open-Meteo missing temperature for {target_time}"}
    temperature_c = temperatures_c[index]
    if temperature_c in (None, ""):
        return {"weather_fetch_error": f"Open-Meteo blank temperature for {target_time}"}
    temperature_c_float = float(temperature_c)
    temperature_f = (temperature_c_float * 9 / 5) + 32

    update = {
        "weather_temp_c": f"{temperature_c_float:.1f}",
        "weather_temp_f": f"{temperature_f:.1f}",
        "weather_source": "open-meteo",
        "weather_observation_time": target_time,
        "weather_fetch_error": "",
        "weather_dew_point_c": "",
        "weather_dew_point_f": "",
        "weather_apparent_temp_c": "",
        "weather_apparent_temp_f": "",
        "heat_load_sum": "",
        "heat_pace_adjust_pct": "",
    }

    dew_points_c = hourly.get("dew_point_2m", [])
    if isinstance(dew_points_c, list) and index < len(dew_points_c):
        dew_c = dew_points_c[index]
        if dew_c not in (None, ""):
            dew_c_float = float(dew_c)
            dew_f = (dew_c_float * 9 / 5) + 32
            update["weather_dew_point_c"] = f"{dew_c_float:.1f}"
            update["weather_dew_point_f"] = f"{dew_f:.1f}"
            load_sum = heat_adjust.heat_load_sum(temperature_f, dew_f)
            update["heat_load_sum"] = str(load_sum)
            update["heat_pace_adjust_pct"] = f"{heat_adjust.pace_adjust_fraction(load_sum) * 100:.1f}"

    apparent_c = hourly.get("apparent_temperature", [])
    if isinstance(apparent_c, list) and index < len(apparent_c):
        app_c = apparent_c[index]
        if app_c not in (None, ""):
            app_c_float = float(app_c)
            update["weather_apparent_temp_c"] = f"{app_c_float:.1f}"
            update["weather_apparent_temp_f"] = f"{(app_c_float * 9 / 5) + 32:.1f}"

    return update


def load_activities(rows: Iterable[dict[str, str]]) -> list[Activity]:
    activities: list[Activity] = []
    for row in rows:
        start_time_value = row_start_time_value(row)
        if not start_time_value:
            continue
        local_start = parse_start_time(start_time_value)
        activities.append(
            Activity(
                row=row,
                local_start=local_start,
                local_date=local_start.date(),
                timezone_name=row.get("start_timezone", "") or str(local_start.tzinfo or LOCAL_TZ),
            )
        )
    return activities


def load_processed_activities_for_week(week_start: date) -> list[Activity]:
    activities: list[Activity] = []
    week_end = week_start + timedelta(days=6)
    for path in sorted((REPO_ROOT / "data" / "processed").glob("*.jsonl")):
        with path.open() as handle:
            for raw_line in handle:
                row = json.loads(raw_line)
                start_time_value = row_start_time_value(row)
                if not start_time_value:
                    continue
                local_start = parse_start_time(start_time_value)
                local_date = local_start.date()
                if week_start <= local_date <= week_end:
                    activities.append(
                        Activity(
                            row=row,
                            local_start=local_start,
                            local_date=local_date,
                            timezone_name=row.get("start_timezone", "") or str(local_start.tzinfo or LOCAL_TZ),
                        )
                    )
    activities.sort(key=lambda activity: activity.local_start)
    return activities


def enrich_rows_with_weather(rows: list[dict[str, str]], timeout_s: float) -> list[Activity]:
    activities = load_activities(rows)
    grouped: dict[tuple[str, str, str], list[Activity]] = defaultdict(list)
    for activity in activities:
        key = weather_group_key(activity)
        if key is None:
            continue
        grouped[key].append(activity)

    for (latitude, longitude, timezone_name), group_activities in grouped.items():
        start_date = min(activity.local_date for activity in group_activities)
        end_date = max(activity.local_date for activity in group_activities)
        payload = fetch_open_meteo_archive(
            latitude=latitude,
            longitude=longitude,
            timezone_name=timezone_name,
            start_date=start_date,
            end_date=end_date,
            timeout_s=timeout_s,
        )
        if "weather_fetch_error" in payload:
            for activity in group_activities:
                activity.row.update(payload)
            continue
        hourly = payload.get("hourly", {})
        if not isinstance(hourly, dict):
            error = {"weather_fetch_error": "Open-Meteo payload missing hourly data"}
            for activity in group_activities:
                activity.row.update(error)
            continue
        for activity in group_activities:
            activity.row.update(weather_update_from_hourly(activity, hourly))
    return activities


def re_enrich_processed_batch_weather(
    import_date: date,
    timeout_s: float,
) -> tuple[Path, list[dict[str, str]], list[Activity]]:
    output_jsonl = batch.processed_paths_for(import_date)
    rows = batch.load_processed_rows(output_jsonl)
    if not rows:
        return output_jsonl, rows, []
    activities = enrich_rows_with_weather(rows, timeout_s=timeout_s)
    batch.write_processed_outputs(output_jsonl, rows)
    return output_jsonl, rows, activities


def weather_failures(rows: Iterable[dict[str, str]]) -> list[dict[str, str]]:
    failures: list[dict[str, str]] = []
    for row in rows:
        if row.get("weather_temp_f", "").strip():
            continue
        failures.append(row)
    return failures
