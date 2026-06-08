"""Ingest loose COROS FIT files and sync repo records.

This script:
1. Moves loose root-level `.fit` files into a dated batch folder.
2. Removes matching `:Zone.Identifier` sidecars.
3. Writes `SHA256SUMS.txt` and processed CSV/JSONL summaries.
4. Creates or updates matching daily logs from objective FIT data.
5. Creates or updates the current week's weekly log.
6. Refreshes the managed current-week block in `README.md`.
7. Writes a batch manifest.

It intentionally automates factual recordkeeping only. Subjective recovery
signals, coaching interpretation, and plan changes remain manual.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import tarfile
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen
from zoneinfo import ZoneInfo

import summarize_coros_fit as summarize

REPO_ROOT = Path(__file__).resolve().parent.parent
LOCAL_TZ = ZoneInfo("America/New_York")
README_PATH = REPO_ROOT / "README.md"
DAILY_TEMPLATE = REPO_ROOT / "templates" / "daily_log_template.md"
WEEKLY_TEMPLATE = REPO_ROOT / "templates" / "weekly_log_template.md"
README_START = "<!-- current-week:start -->"
README_END = "<!-- current-week:end -->"
WEEKLY_START = "<!-- auto-summary:start -->"
WEEKLY_END = "<!-- auto-summary:end -->"
IMPORT_NOTE_PREFIX = "- Imported from `"
FIT_NOTE_PREFIX = "- FIT summary:"
OPEN_METEO_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
MANAGED_NOTES_HEADING = "## Managed Notes"
MANUAL_NOTES_HEADING = "## Manual Notes"
RECOVERY_HEADING = "## Recovery Signals"


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
        return (
            f"- Weather at start: `{temperature_f} F` at `{observed_at}` "
            f"from `{source}`."
        )


@dataclass
class DayPlan:
    day_name: str
    planned: str
    purpose: str
    notes: str
    day_date: date


@dataclass
class WeekPlan:
    source_relpath: str
    week_start: date
    target_mileage: str
    primary_purpose: str
    day_plans: list[DayPlan]

@dataclass
class ArchivedMonth:
    month_start: date
    archive_dir: Path
    summary_path: Path
    moved_logs: list[Path]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--date",
        type=str,
        help="Override import batch date in YYYY-MM-DD format.",
    )
    parser.add_argument(
        "--no-readme",
        action="store_true",
        help="Skip README current-week refresh.",
    )
    parser.add_argument(
        "--no-logs",
        action="store_true",
        help="Skip daily/weekly log updates.",
    )
    parser.add_argument(
        "--sync-only",
        action="store_true",
        help="Do not import loose FIT files. Refresh logs/README from existing data.",
    )
    parser.add_argument(
        "--no-weather",
        action="store_true",
        help="Skip Open-Meteo start-time weather enrichment.",
    )
    parser.add_argument(
        "--weather-timeout",
        type=float,
        default=10.0,
        help="Timeout in seconds for each Open-Meteo request.",
    )
    return parser.parse_args()


def format_int(value: int) -> str:
    return f"{value:,}"


def monday_of(target: date) -> date:
    return target - timedelta(days=target.weekday())

def month_start_of(target: date) -> date:
    return target.replace(day=1)

def next_month_start(target: date) -> date:
    if target.month == 12:
        return date(target.year + 1, 1, 1)
    return date(target.year, target.month + 1, 1)


def parse_start_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=LOCAL_TZ)
    return parsed

def row_start_time_value(row: dict[str, str]) -> str:
    return (
        row.get("start_time")
        or row.get("start_time_local")
        or row.get("start_time_utc")
        or ""
    )


def find_loose_fit_files() -> list[Path]:
    return sorted(
        path
        for path in REPO_ROOT.glob("*.fit")
        if path.is_file()
    )


def batch_dir_for(import_date: date) -> Path:
    return REPO_ROOT / "data" / "coros_exports" / f"COROS_export_{import_date.isoformat()}"


def processed_paths_for(import_date: date) -> tuple[Path, Path]:
    stem = f"coros_export_{import_date.isoformat()}_summary"
    return (
        REPO_ROOT / "data" / "processed" / f"{stem}.csv",
        REPO_ROOT / "data" / "processed" / f"{stem}.jsonl",
    )

def root_daily_log_path(day_date: date) -> Path:
    return REPO_ROOT / "logs" / "daily" / f"{day_date.isoformat()}.md"

def daily_archive_dir(day_date: date) -> Path:
    month_key = day_date.strftime("%Y-%m")
    return REPO_ROOT / "logs" / "daily" / f"{day_date.year}" / month_key

def archived_daily_log_path(day_date: date) -> Path:
    return daily_archive_dir(day_date) / f"{day_date.isoformat()}.md"

def resolve_daily_log_path(day_date: date) -> Path:
    archived_path = archived_daily_log_path(day_date)
    if archived_path.exists():
        return archived_path
    root_path = root_daily_log_path(day_date)
    if root_path.exists():
        return root_path
    if archived_path.parent.exists():
        return archived_path
    return root_path


def import_loose_fit_files(import_date: date) -> tuple[Path, list[Path], int]:
    fit_files = find_loose_fit_files()
    export_dir = batch_dir_for(import_date)
    export_dir.mkdir(parents=True, exist_ok=True)
    removed_sidecars = 0
    moved_files: list[Path] = []
    for source_path in fit_files:
        target_path = export_dir / source_path.name
        source_path.rename(target_path)
        moved_files.append(target_path)
        sidecar = REPO_ROOT / f"{source_path.name}:Zone.Identifier"
        if sidecar.exists():
            sidecar.unlink()
            removed_sidecars += 1
    return export_dir, moved_files, removed_sidecars


def write_sha256s(export_dir: Path, rows: Iterable[dict[str, str]]) -> int:
    hash_path = export_dir / "SHA256SUMS.txt"
    with hash_path.open("w") as handle:
        count = 0
        for row in rows:
            handle.write(f"{row['source_sha256']}  {row['source_relpath']}\n")
            count += 1
    return count


def generate_summaries(export_dir: Path) -> tuple[Path, Path, list[dict[str, str]]]:
    import_date = export_dir.name.removeprefix("COROS_export_")
    output_csv, output_jsonl = processed_paths_for(date.fromisoformat(import_date))
    fit_files = sorted(export_dir.glob("*.fit"))
    if fit_files:
        rows = summarize.parse_fit_files(fit_files)
    else:
        archive_path = export_dir / "fit_files.tar.gz"
        if not archive_path.exists():
            rows = []
        else:
            with TemporaryDirectory() as temp_dir_name:
                temp_dir = Path(temp_dir_name)
                with tarfile.open(archive_path, "r:gz") as archive:
                    archive.extractall(temp_dir)
                archived_fit_files = sorted(temp_dir.rglob("*.fit"))
                rows = summarize.parse_fit_files(archived_fit_files)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=summarize.FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    summarize.write_jsonl(output_jsonl, rows)
    return output_csv, output_jsonl, rows

def write_processed_outputs(
    output_csv: Path,
    output_jsonl: Path,
    rows: list[dict[str, str]],
) -> None:
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=summarize.FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    summarize.write_jsonl(output_jsonl, rows)

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
        "hourly": "temperature_2m",
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
    return {
        "weather_temp_c": f"{temperature_c_float:.1f}",
        "weather_temp_f": f"{(temperature_c_float * 9 / 5) + 32:.1f}",
        "weather_source": "open-meteo",
        "weather_observation_time": target_time,
        "weather_fetch_error": "",
    }

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


def load_template(path: Path) -> str:
    return path.read_text()


def set_field(lines: list[str], field_name: str, value: str) -> None:
    prefix = f"- {field_name}:"
    for index, line in enumerate(lines):
        if line.startswith(prefix):
            lines[index] = f"{prefix} {value}"
            return
    raise ValueError(f"Missing field {field_name}")


def ensure_daily_log_structure(text: str) -> str:
    if MANAGED_NOTES_HEADING in text and MANUAL_NOTES_HEADING in text:
        return text
    if "## Notes" in text:
        text = text.replace("## Notes", MANAGED_NOTES_HEADING, 1)
    if MANUAL_NOTES_HEADING not in text and RECOVERY_HEADING in text:
        text = text.replace(
            RECOVERY_HEADING,
            f"{MANUAL_NOTES_HEADING}\n\n- \n\n{RECOVERY_HEADING}",
            1,
        )
    return text


def parse_duration_to_seconds(value: str) -> int:
    cleaned = value.strip()
    if not cleaned:
        return 0
    parts = cleaned.split(":")
    if len(parts) == 2:
        minutes, seconds = parts
        return int(minutes) * 60 + int(seconds)
    if len(parts) == 3:
        hours, minutes, seconds = parts
        return (int(hours) * 3600) + (int(minutes) * 60) + int(seconds)
    return 0


def format_duration(seconds: int) -> str:
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def format_pace_label(total_seconds: int, total_miles: float) -> str:
    if total_seconds <= 0 or total_miles <= 0:
        return ""
    pace_seconds = round(total_seconds / total_miles)
    minutes, seconds = divmod(pace_seconds, 60)
    return f"{minutes}:{seconds:02d}/mi"


def parse_daily_log_file(path: Path) -> dict[str, str]:
    fields = {
        "planned": "",
        "completed": "",
        "time": "",
        "distance": "",
        "pace": "",
        "effort": "",
        "notes": "",
        "sleep": "",
        "soreness": "",
        "stress": "",
        "warning_signs": "",
    }
    manual_notes_started = False
    recovery_started = False
    notes_lines: list[str] = []
    text = ensure_daily_log_structure(path.read_text())
    for raw_line in text.splitlines():
        if raw_line == MANAGED_NOTES_HEADING:
            manual_notes_started = False
            recovery_started = False
            continue
        if raw_line == MANUAL_NOTES_HEADING:
            manual_notes_started = True
            recovery_started = False
            continue
        if raw_line == RECOVERY_HEADING:
            manual_notes_started = False
            recovery_started = True
            continue
        if raw_line.startswith("- Planned:"):
            fields["planned"] = raw_line.removeprefix("- Planned:").strip()
        elif raw_line.startswith("- Completed:"):
            fields["completed"] = raw_line.removeprefix("- Completed:").strip()
        elif raw_line.startswith("- Time:"):
            fields["time"] = raw_line.removeprefix("- Time:").strip()
        elif raw_line.startswith("- Distance:"):
            fields["distance"] = raw_line.removeprefix("- Distance:").strip()
        elif raw_line.startswith("- Pace:"):
            fields["pace"] = raw_line.removeprefix("- Pace:").strip()
        elif raw_line.startswith("- Effort:"):
            fields["effort"] = raw_line.removeprefix("- Effort:").strip()
        elif raw_line.startswith("- Sleep:"):
            fields["sleep"] = raw_line.removeprefix("- Sleep:").strip()
        elif raw_line.startswith("- Soreness:"):
            fields["soreness"] = raw_line.removeprefix("- Soreness:").strip()
        elif raw_line.startswith("- Stress:"):
            fields["stress"] = raw_line.removeprefix("- Stress:").strip()
        elif raw_line.startswith("- Warning signs:"):
            fields["warning_signs"] = raw_line.removeprefix("- Warning signs:").strip()
        elif manual_notes_started and raw_line.startswith("- "):
            notes_lines.append(raw_line)
    filtered_notes = [line.removeprefix("- ").strip() for line in notes_lines]
    fields["notes"] = " ".join(note for note in filtered_notes if note)
    return fields


def replace_managed_notes(lines: list[str], activity: Activity) -> list[str]:
    note_start = lines.index(MANAGED_NOTES_HEADING) + 1
    manual_index = lines.index(MANUAL_NOTES_HEADING)
    managed = [activity.import_note, activity.fit_note]
    if activity.weather_note:
        managed.append(activity.weather_note)
    new_notes = [""] + managed + [""]
    return lines[:note_start] + new_notes + lines[manual_index:]


def create_daily_log_stub(day_date: date, planned: str) -> Path:
    log_path = resolve_daily_log_path(day_date)
    if log_path.exists():
        return log_path
    log_path.parent.mkdir(parents=True, exist_ok=True)
    text = load_template(DAILY_TEMPLATE).replace("YYYY-MM-DD", day_date.isoformat())
    text = ensure_daily_log_structure(text)
    lines = text.splitlines()
    set_field(lines, "Planned", planned)
    log_path.write_text("\n".join(lines) + "\n")
    return log_path


def upsert_daily_log(activity: Activity) -> Path:
    log_path = resolve_daily_log_path(activity.local_date)
    if log_path.exists():
        text = ensure_daily_log_structure(log_path.read_text())
    else:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        text = load_template(DAILY_TEMPLATE).replace("YYYY-MM-DD", activity.local_date.isoformat())
        text = ensure_daily_log_structure(text)
    lines = text.splitlines()
    set_field(lines, "Completed", activity.completed_label)
    set_field(lines, "Time", activity.time_label)
    set_field(lines, "Distance", f"{activity.row['distance_mi']} mi")
    set_field(lines, "Pace", activity.pace_label)
    current_effort = next(line for line in lines if line.startswith("- Effort:"))
    if current_effort == "- Effort:":
        set_field(lines, "Effort", "imported")
    updated = replace_managed_notes(lines, activity)
    log_path.write_text("\n".join(updated) + "\n")
    return log_path


def parse_day_logs(week_start: date) -> dict[date, dict[str, str]]:
    result: dict[date, dict[str, str]] = {}
    for offset in range(7):
        day_date = week_start + timedelta(days=offset)
        path = resolve_daily_log_path(day_date)
        if not path.exists():
            continue
        result[day_date] = parse_daily_log_file(path)
    return result


def seed_missing_planned_day_logs(week_plan: WeekPlan, today: date) -> list[Path]:
    created_paths: list[Path] = []
    for day_plan in week_plan.day_plans:
        if day_plan.day_date > today:
            continue
        if day_plan.planned.strip().lower() in {"rest", "off"}:
            continue
        log_path = resolve_daily_log_path(day_plan.day_date)
        if log_path.exists():
            continue
        created_paths.append(create_daily_log_stub(day_plan.day_date, day_plan.planned))
    return created_paths


def parse_pre_block_week(target_week: date) -> WeekPlan | None:
    path = REPO_ROOT / "plans" / "2026-half-marathon" / "01_pre_block_ramp.md"
    text = path.read_text()
    pattern = re.compile(
        r"## Week of (?P<date>\d{4}-\d{2}-\d{2})\n\n"
        r"- Target mileage: (?P<target>.+)\n"
        r"- Primary purpose: (?P<purpose>.+)\n\n"
        r"\| Day \| Run \| Purpose \| Notes \|\n"
        r"\| --- \| --- \| --- \| --- \|\n"
        r"(?P<table>(?:\| .+\n)+)"
    )
    for match in pattern.finditer(text):
        week_start = date.fromisoformat(match.group("date"))
        if week_start != target_week:
            continue
        rows: list[DayPlan] = []
        for offset, line in enumerate(match.group("table").strip().splitlines()):
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            rows.append(
                DayPlan(
                    day_name=cells[0],
                    planned=cells[1],
                    purpose=cells[2],
                    notes=cells[3],
                    day_date=week_start + timedelta(days=offset),
                )
            )
        return WeekPlan(
            source_relpath="plans/2026-half-marathon/01_pre_block_ramp.md",
            week_start=week_start,
            target_mileage=match.group("target"),
            primary_purpose=match.group("purpose"),
            day_plans=rows,
        )
    return None


def parse_week_file(target_week: date) -> WeekPlan | None:
    week_path = REPO_ROOT / "plans" / "2026-half-marathon" / f"week_{target_week.isoformat()}.md"
    if not week_path.exists():
        candidates = sorted((REPO_ROOT / "plans" / "2026-half-marathon").glob("week_*_*.md"))
        for path in candidates:
            if path.name.endswith(f"_{target_week.isoformat()}.md"):
                week_path = path
                break
    if not week_path.exists():
        return None
    text = week_path.read_text()
    target_match = re.search(r"- Target mileage: (?P<target>.+)", text)
    purpose_match = re.search(r"- Primary purpose: (?P<purpose>.+)", text)
    table_match = re.search(
        r"\| Day \| Run \| Purpose \| Notes \|\n"
        r"\| --- \| --- \| --- \| --- \|\n"
        r"(?P<table>(?:\| .+\n)+)",
        text,
    )
    if not (target_match and purpose_match and table_match):
        return None
    rows: list[DayPlan] = []
    for offset, line in enumerate(table_match.group("table").strip().splitlines()):
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        rows.append(
            DayPlan(
                day_name=cells[0],
                planned=cells[1],
                purpose=cells[2],
                notes=cells[3],
                day_date=target_week + timedelta(days=offset),
            )
        )
    return WeekPlan(
        source_relpath=f"plans/2026-half-marathon/{week_path.name}",
        week_start=target_week,
        target_mileage=target_match.group("target"),
        primary_purpose=purpose_match.group("purpose"),
        day_plans=rows,
    )


def load_week_plan(target_week: date) -> WeekPlan:
    plan = parse_week_file(target_week)
    if plan is None:
        plan = parse_pre_block_week(target_week)
    if plan is None:
        raise SystemExit(f"No week plan found for {target_week.isoformat()}")
    return plan


def actual_miles_from_distance(distance: str) -> float:
    match = re.match(r"(?P<value>\d+(?:\.\d+)?)", distance)
    if not match:
        return 0.0
    return float(match.group("value"))


def sentence(text: str, prefix: str = "") -> str:
    cleaned = text.strip()
    if not cleaned:
        return ""
    cleaned = cleaned.rstrip(".")
    return f"{prefix}{cleaned}."


def summarize_day(fields: dict[str, str]) -> tuple[str, str]:
    completed = fields["completed"] or "x"
    note_parts: list[str] = []
    note_text = fields["notes"]
    if fields["time"] and fields["pace"]:
        note_parts.append(f"{fields['time']} at {fields['pace']}.")
    elif fields["time"]:
        note_parts.append(f"Time {fields['time']}.")
    if note_text:
        note_parts.append(sentence(note_text))
    soreness = fields["soreness"]
    if soreness and soreness.lower() not in note_text.lower() and "sore" not in note_text.lower():
        note_parts.append(sentence(fields["soreness"], "Soreness: "))
    if fields["warning_signs"]:
        note_parts.append(sentence(fields["warning_signs"], "Warning signs: "))
    return completed, " ".join(part.strip() for part in note_parts if part.strip()) or "x"


def build_monthly_summary(month_start: date, archive_dir: Path) -> str:
    month_end = next_month_start(month_start) - timedelta(days=1)
    daily_paths = sorted(
        path for path in archive_dir.glob("*.md")
        if path.name != "monthly_summary.md"
    )
    records: list[tuple[date, dict[str, str]]] = []
    for path in daily_paths:
        day_date = date.fromisoformat(path.stem)
        records.append((day_date, parse_daily_log_file(path)))

    run_records = [
        (day_date, fields)
        for day_date, fields in records
        if actual_miles_from_distance(fields["distance"]) > 0
    ]
    total_miles = sum(actual_miles_from_distance(fields["distance"]) for _, fields in run_records)
    total_seconds = sum(parse_duration_to_seconds(fields["time"]) for _, fields in run_records)
    logged_run_days = len(run_records)
    average_distance = total_miles / logged_run_days if logged_run_days else 0.0
    longest_run_label = "n/a"
    if run_records:
        longest_day, longest_fields = max(
            run_records,
            key=lambda item: actual_miles_from_distance(item[1]["distance"]),
        )
        longest_run_label = (
            f"`{longest_fields['distance']}` on `{longest_day.isoformat()}`"
        )
    soreness_days = sum(1 for _, fields in records if fields["soreness"])
    warning_days = sum(1 for _, fields in records if fields["warning_signs"])
    manual_note_days = sum(1 for _, fields in records if fields["notes"])
    average_pace = format_pace_label(total_seconds, total_miles) or "n/a"
    total_time = format_duration(total_seconds) if total_seconds else "0:00"

    lines = [
        f"# {month_start.strftime('%Y-%m')} Daily Log Summary",
        "",
        f"- Month: `{month_start.strftime('%Y-%m')}`",
        f"- Date span: `{month_start.isoformat()}` to `{month_end.isoformat()}`",
        f"- Daily logs archived: `{len(records)}`",
        f"- Logged run days: `{logged_run_days}`",
        f"- Total mileage: `{total_miles:.2f} mi`",
        f"- Total logged time: `{total_time}`",
        f"- Average pace across logged miles: `{average_pace}`",
        f"- Average distance per logged run: `{average_distance:.2f} mi`",
        f"- Longest logged run: {longest_run_label}",
        f"- Days with manual notes: `{manual_note_days}`",
        f"- Days with soreness notes: `{soreness_days}`",
        f"- Days with warning-sign notes: `{warning_days}`",
        "",
        "## Daily Index",
        "",
        "| Date | Planned | Completed | Distance | Effort | Notes |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for day_date, fields in records:
        note = fields["notes"] or "x"
        lines.append(
            f"| {day_date.isoformat()} | {fields['planned'] or 'x'} | "
            f"{fields['completed'] or 'x'} | {fields['distance'] or 'x'} | "
            f"{fields['effort'] or 'x'} | {note} |"
        )
    return "\n".join(lines) + "\n"


def archive_completed_daily_months(today: date) -> list[ArchivedMonth]:
    current_month_start = month_start_of(today)
    monthly_paths: dict[date, list[Path]] = defaultdict(list)
    for path in sorted((REPO_ROOT / "logs" / "daily").glob("*.md")):
        if path.name == ".gitkeep":
            continue
        try:
            day_date = date.fromisoformat(path.stem)
        except ValueError:
            continue
        day_month_start = month_start_of(day_date)
        if day_month_start >= current_month_start:
            continue
        monthly_paths[day_month_start].append(path)

    archived_months: list[ArchivedMonth] = []
    for month_start, paths in sorted(monthly_paths.items()):
        archive_dir = daily_archive_dir(month_start)
        archive_dir.mkdir(parents=True, exist_ok=True)
        moved_logs: list[Path] = []
        for source_path in paths:
            target_path = archive_dir / source_path.name
            source_path.rename(target_path)
            moved_logs.append(target_path)
        summary_path = archive_dir / "monthly_summary.md"
        summary_path.write_text(build_monthly_summary(month_start, archive_dir))
        archived_months.append(
            ArchivedMonth(
                month_start=month_start,
                archive_dir=archive_dir,
                summary_path=summary_path,
                moved_logs=moved_logs,
            )
        )
    return archived_months


def build_week_rows(week_plan: WeekPlan, day_logs: dict[date, dict[str, str]]) -> tuple[list[str], float, str]:
    rows = ["| Day | Planned | Actual | Notes |", "| --- | --- | --- | --- |"]
    total_miles = 0.0
    latest_logged: tuple[date, dict[str, str]] | None = None
    for day_plan in week_plan.day_plans:
        fields = day_logs.get(day_plan.day_date)
        actual = "x"
        note = "x"
        if fields:
            actual, note = summarize_day(fields)
            total_miles += actual_miles_from_distance(fields["distance"])
            if any(fields.values()):
                latest_logged = (day_plan.day_date, fields)
        rows.append(f"| {day_plan.day_name} | {day_plan.planned} | {actual} | {note} |")
    if latest_logged is None:
        status = "No days logged yet"
    else:
        latest_date, latest_fields = latest_logged
        label = latest_date.strftime("%A")
        completed = latest_fields.get("completed", "").lower()
        if completed == "rest day":
            status = f"{label} rest logged"
        elif completed:
            status = f"{label} run logged"
        else:
            status = f"{label} note logged"
    return rows, total_miles, status


def ensure_markers(text: str, start_marker: str, end_marker: str, heading: str, body: str) -> str:
    if start_marker in text and end_marker in text:
        pattern = re.compile(
            rf"{re.escape(start_marker)}.*?{re.escape(end_marker)}",
            re.DOTALL,
        )
        return pattern.sub(f"{start_marker}\n{body}\n{end_marker}", text, count=1)
    section_pattern = re.compile(
        rf"(?ms)^## {re.escape(heading)}\n.*?(?=^## |\Z)"
    )
    replacement = f"## {heading}\n\n{start_marker}\n{body}\n{end_marker}\n\n"
    if section_pattern.search(text):
        return section_pattern.sub(replacement, text, count=1)
    raise SystemExit(f"Could not find ## {heading} section for managed update.")


def build_readme_current_week(week_plan: WeekPlan, rows: list[str], total_miles: float, status: str) -> str:
    lines = [
        f"Source: [{Path(week_plan.source_relpath).name}]({week_plan.source_relpath})",
        "",
        f"Week of `{week_plan.week_start.isoformat()}`",
        "",
        f"- Target mileage: `{week_plan.target_mileage}`",
        f"- Actual mileage so far: `{total_miles:.2f}`",
        f"- Primary purpose: {week_plan.primary_purpose}",
        f"- Week status: `{status}`",
        "",
        *rows,
        "",
        "The listed source plan is the live reference for this week.",
    ]
    return "\n".join(lines)


def update_readme(week_plan: WeekPlan, rows: list[str], total_miles: float, status: str) -> None:
    text = README_PATH.read_text()
    body = build_readme_current_week(week_plan, rows, total_miles, status)
    updated = ensure_markers(text, README_START, README_END, "Current Week", body)
    README_PATH.write_text(updated)


def build_weekly_log_body(week_plan: WeekPlan, rows: list[str], total_miles: float, status: str) -> str:
    lines = [
        f"- Source plan: `{week_plan.source_relpath}`",
        f"- Target mileage: `{week_plan.target_mileage}`",
        f"- Actual mileage so far: `{total_miles:.2f}`",
        f"- Primary purpose: {week_plan.primary_purpose}",
        f"- Status: `{status}`",
        "",
        *rows,
    ]
    return "\n".join(lines)


def upsert_weekly_log(week_plan: WeekPlan, rows: list[str], total_miles: float, status: str) -> Path:
    weekly_path = REPO_ROOT / "logs" / "weekly" / f"week_{week_plan.week_start.isoformat()}.md"
    body = build_weekly_log_body(week_plan, rows, total_miles, status)
    if weekly_path.exists():
        text = weekly_path.read_text()
        updated = ensure_markers(text, WEEKLY_START, WEEKLY_END, "Auto Summary", body)
    else:
        template = load_template(WEEKLY_TEMPLATE).replace("YYYY-MM-DD", week_plan.week_start.isoformat())
        updated = template.replace(WEEKLY_START, f"{WEEKLY_START}\n{body}")
    weekly_path.write_text(updated)
    return weekly_path


def write_manifest(
    export_dir: Path,
    import_date: date,
    fit_count: int,
    removed_sidecars: int,
    output_csv: Path,
    output_jsonl: Path,
    rows: list[dict[str, str]],
) -> Path:
    fit_files = sorted(export_dir.glob("*.fit"))
    payload_bytes = sum(path.stat().st_size for path in fit_files)
    folder_bytes = sum(path.stat().st_size for path in export_dir.iterdir() if path.is_file())
    parser_names = sorted({row.get("parser", "") for row in rows if row.get("parser", "")})
    manifest = export_dir / "manifest.md"
    first_source = fit_files[0].name if fit_files else ""
    lines = [
        f"# COROS Export Manifest - {import_date.isoformat()}",
        "",
        "## Import",
        "",
        f"- Source file: `{first_source}`" if fit_count == 1 else f"- Source files: `{fit_count}` files",
        f"- Repo folder: `data/coros_exports/{export_dir.name}/`",
        f"- Imported on: {import_date.isoformat()}",
        f"- FIT files: {fit_count}",
        f"- FIT payload bytes: {format_int(payload_bytes)}",
        f"- Removed sidecars: {removed_sidecars} `*:Zone.Identifier` file" + ("" if removed_sidecars == 1 else "s"),
        "",
        "## Integrity",
        "",
        "- Hash file: `SHA256SUMS.txt`",
        f"- Hash entries: {fit_count}",
        "",
        "## Processing",
        "",
        f"- Processed CSV: `{summarize.repo_relpath(output_csv)}`",
        f"- Processed JSONL: `{summarize.repo_relpath(output_jsonl)}`",
        f"- CSV activity rows: {len(rows)}",
        f"- JSONL rows: {len(rows)}",
        f"- Summary row count matches FIT count: {'yes' if len(rows) == fit_count else 'no'}",
        f"- Parser used for this batch: `{', '.join(parser_names) or 'unknown'}`",
        "",
        "## Archive",
        "",
        "- Archive status: not archived yet",
        "- Reason: current-month loose FIT files stay available for repair, reparse, or enrichment",
        f"- Folder bytes with loose FIT files: {format_int(folder_bytes)}",
        "",
        "## Notes",
        "",
        "- Raw FIT files are binary training records and may contain GPS, timestamps, heart rate, and device metadata.",
        "- Processed summaries should be written to `data/processed/`.",
    ]
    manifest.write_text("\n".join(lines) + "\n")
    return manifest


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


def sync_records(
    today: date,
    update_logs: bool,
    update_readme_flag: bool,
    recent_activities: list[Activity] | None = None,
) -> dict[str, object]:
    week_start = monday_of(today)
    week_end = week_start + timedelta(days=6)
    synced_daily_paths: list[Path] = []
    week_plan = load_week_plan(week_start)
    if update_logs:
        synced_daily_paths.extend(seed_missing_planned_day_logs(week_plan, today))
        activities = recent_activities
        if activities is None:
            activities = load_processed_activities_for_week(week_start)
        for activity in activities:
            if not (week_start <= activity.local_date <= week_end):
                continue
            synced_daily_paths.append(upsert_daily_log(activity))
    day_logs = parse_day_logs(week_start)
    rows, total_miles, status = build_week_rows(week_plan, day_logs)
    weekly_path: Path | None = None
    if update_logs:
        weekly_path = upsert_weekly_log(week_plan, rows, total_miles, status)
    if update_readme_flag:
        update_readme(week_plan, rows, total_miles, status)
    return {
        "week_plan": week_plan,
        "weekly_path": weekly_path,
        "synced_daily_paths": sorted(set(synced_daily_paths)),
        "total_miles": total_miles,
        "status": status,
    }


def main() -> int:
    args = parse_args()
    today = date.fromisoformat(args.date) if args.date else datetime.now(LOCAL_TZ).date()
    update_logs = not args.no_logs
    update_readme_flag = not args.no_readme
    weather_enabled = not args.no_weather

    moved_files: list[Path] = []
    removed_sidecars = 0
    rows: list[dict[str, str]] = []
    export_dir = batch_dir_for(today)
    output_csv, output_jsonl = processed_paths_for(today)
    manifest_path: Path | None = None
    daily_paths: list[Path] = []
    activities: list[Activity] = []
    archived_months = archive_completed_daily_months(today)

    if not args.sync_only:
        export_dir, moved_files, removed_sidecars = import_loose_fit_files(today)
        if moved_files:
            output_csv, output_jsonl, rows = generate_summaries(export_dir)
            if weather_enabled:
                activities = enrich_rows_with_weather(rows, timeout_s=args.weather_timeout)
                write_processed_outputs(output_csv, output_jsonl, rows)
            fit_count = write_sha256s(export_dir, rows)
            if not activities:
                activities = load_activities(rows)
            if update_logs:
                for activity in activities:
                    daily_paths.append(upsert_daily_log(activity))
            manifest_path = write_manifest(
                export_dir,
                today,
                fit_count,
                removed_sidecars,
                output_csv,
                output_jsonl,
                rows,
            )
    sync_result = sync_records(
        today,
        update_logs=update_logs,
        update_readme_flag=update_readme_flag,
        recent_activities=activities or None,
    )

    print(f"Import date: {today.isoformat()}")
    print(f"Moved FIT files: {len(moved_files)}")
    if moved_files:
        for path in moved_files:
            print(f"  - {summarize.repo_relpath(path)}")
    print(f"Removed sidecars: {removed_sidecars}")
    if archived_months:
        print(f"Archived daily months: {len(archived_months)}")
        for archived_month in archived_months:
            print(
                "  - "
                f"{archived_month.month_start.strftime('%Y-%m')}: "
                f"{len(archived_month.moved_logs)} logs -> "
                f"{summarize.repo_relpath(archived_month.archive_dir)} "
                f"(summary: {summarize.repo_relpath(archived_month.summary_path)})"
            )
    if rows:
        print(f"Processed activities: {len(rows)}")
        print(f"CSV summary: {summarize.repo_relpath(output_csv)}")
        print(f"JSONL summary: {summarize.repo_relpath(output_jsonl)}")
    if daily_paths:
        print(f"Daily logs updated: {len(daily_paths)}")
        for path in daily_paths:
            print(f"  - {summarize.repo_relpath(path)}")
    synced_daily_paths = sync_result["synced_daily_paths"]
    if isinstance(synced_daily_paths, list) and synced_daily_paths:
        print(f"Current-week daily logs synced: {len(synced_daily_paths)}")
        for path in synced_daily_paths:
            print(f"  - {summarize.repo_relpath(path)}")
    weekly_path = sync_result["weekly_path"]
    if isinstance(weekly_path, Path):
        print(f"Weekly log updated: {summarize.repo_relpath(weekly_path)}")
    if update_readme_flag:
        print(f"README current week refreshed: {summarize.repo_relpath(README_PATH)}")
    if manifest_path is not None:
        print(f"Manifest updated: {summarize.repo_relpath(manifest_path)}")
    print(
        "Manual follow-up: subjective recovery signals, coaching interpretation, "
        "and plan changes remain manual."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
