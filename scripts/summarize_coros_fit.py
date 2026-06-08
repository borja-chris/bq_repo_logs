#!/usr/bin/env python3
"""Summarize COROS FIT files into reviewable CSV and JSONL outputs.

Requires the optional `fitparse` package:

    python -m pip install fitparse
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

try:
    from fitparse import FitFile as FITPARSE_FILE
except ImportError:
    FITPARSE_FILE = None

try:
    import fitdecode as FITDECODE
except ImportError:
    FITDECODE = None


FIELDS = [
    "import_batch",
    "source_file",
    "source_relpath",
    "source_sha256",
    "activity_id",
    "start_time",
    "start_time_raw",
    "start_time_utc",
    "start_timezone",
    "start_time_resolution",
    "start_lat",
    "start_lon",
    "sport",
    "sub_sport",
    "distance_mi",
    "duration_s",
    "avg_hr",
    "max_hr",
    "ascent_m",
    "weather_temp_c",
    "weather_temp_f",
    "weather_source",
    "weather_observation_time",
    "weather_fetch_error",
    "parser",
    "parse_error",
]

DEFAULT_TIMEZONE = "America/New_York"

def stringify_datetime(value: Any) -> str:
    if value in (None, ""):
        return ""
    if isinstance(value, datetime):
        return value.isoformat(sep=" ")
    return str(value)

def parse_datetime_value(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).strip()
    if not text:
        return None
    normalized = text.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)

def infer_timezone_name(latitude: str, longitude: str) -> tuple[str, str]:
    if not latitude or not longitude:
        return DEFAULT_TIMEZONE, "default_fallback"

    lat = float(latitude)
    lon = float(longitude)

    # Prefer a deterministic built-in heuristic over a hard dependency on a
    # polygon timezone database. This covers the activity locations currently
    # present in the repo and preserves DST via IANA zone names.
    if 51.0 <= lat <= 72.0 and -180.0 <= lon <= -129.0:
        return "America/Anchorage", "gps_inferred"
    if 18.0 <= lat <= 23.0 and -161.0 <= lon <= -154.0:
        return "Pacific/Honolulu", "gps_inferred"
    if 24.0 <= lat <= 50.0 and -125.0 <= lon <= -66.0:
        if lon >= -82.5:
            return "America/New_York", "gps_inferred"
        if lon >= -97.5:
            return "America/Chicago", "gps_inferred"
        if lon >= -110.5:
            return "America/Denver", "gps_inferred"
        return "America/Los_Angeles", "gps_inferred"

    return DEFAULT_TIMEZONE, "default_fallback"

def normalize_start_time(
    raw_start_time: Any,
    latitude: str,
    longitude: str,
) -> tuple[str, str, str, str, str]:
    parsed = parse_datetime_value(raw_start_time)
    raw_text = stringify_datetime(raw_start_time)
    if parsed is None:
        return "", raw_text, "", "", ""

    timezone_name, resolution = infer_timezone_name(latitude, longitude)
    local_tz = ZoneInfo(timezone_name)

    if parsed.tzinfo is None:
        utc_start = parsed.replace(tzinfo=timezone.utc)
        if resolution == "default_fallback":
            resolution = "naive_utc_default_timezone"
        else:
            resolution = "naive_utc_gps_timezone"
    else:
        utc_start = parsed.astimezone(timezone.utc)
        resolution = "source_offset"

    local_start = utc_start.astimezone(local_tz)
    return (
        local_start.isoformat(),
        raw_text,
        utc_start.isoformat(),
        timezone_name,
        resolution,
    )

def localize_utc_to_timezone(utc_text: str, timezone_name: str) -> str:
    utc_start = parse_datetime_value(utc_text)
    if utc_start is None:
        return ""
    if utc_start.tzinfo is None:
        utc_start = utc_start.replace(tzinfo=timezone.utc)
    else:
        utc_start = utc_start.astimezone(timezone.utc)
    return utc_start.astimezone(ZoneInfo(timezone_name)).isoformat()

def refine_default_timezones(rows: list[dict[str, str]]) -> None:
    anchors: list[tuple[datetime, str]] = []
    for row in rows:
        utc_text = row.get("start_time_utc", "")
        timezone_name = row.get("start_timezone", "")
        if not utc_text or not timezone_name:
            continue
        if not row.get("start_lat") or not row.get("start_lon"):
            continue
        utc_start = parse_datetime_value(utc_text)
        if utc_start is None:
            continue
        if utc_start.tzinfo is None:
            utc_start = utc_start.replace(tzinfo=timezone.utc)
        else:
            utc_start = utc_start.astimezone(timezone.utc)
        anchors.append((utc_start, timezone_name))

    for row in rows:
        if row.get("start_time_resolution") != "naive_utc_default_timezone":
            continue
        utc_text = row.get("start_time_utc", "")
        utc_start = parse_datetime_value(utc_text)
        if utc_start is None:
            continue
        if utc_start.tzinfo is None:
            utc_start = utc_start.replace(tzinfo=timezone.utc)
        else:
            utc_start = utc_start.astimezone(timezone.utc)
        nearby_timezone = ""
        nearby_delta_s = None
        for anchor_start, anchor_timezone in anchors:
            delta_s = abs((anchor_start - utc_start).total_seconds())
            if delta_s > 12 * 3600:
                continue
            if nearby_delta_s is None or delta_s < nearby_delta_s:
                nearby_delta_s = delta_s
                nearby_timezone = anchor_timezone
        if not nearby_timezone:
            continue
        row["start_timezone"] = nearby_timezone
        row["start_time"] = localize_utc_to_timezone(utc_text, nearby_timezone)
        row["start_time_resolution"] = "naive_utc_nearby_activity_timezone"


def field_map(message: Any) -> dict[str, Any]:
    return {field.name: field.value for field in message}


def miles(meters: Any) -> str:
    if meters in (None, ""):
        return ""
    return f"{float(meters) / 1609.344:.2f}"


def seconds(value: Any) -> str:
    if value in (None, ""):
        return ""
    return f"{float(value):.0f}"

def semicircles_to_degrees(value: Any) -> str:
    if value in (None, ""):
        return ""
    return f"{float(value) * 180.0 / (2 ** 31):.6f}"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def repo_relpath(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(Path.cwd().resolve()))
    except ValueError:
        return str(path)


def build_row(path: Path) -> dict[str, str]:
    row = {field: "" for field in FIELDS}
    row["import_batch"] = path.parent.name
    row["source_file"] = path.name
    row["source_relpath"] = repo_relpath(path)
    row["source_sha256"] = sha256(path)
    row["activity_id"] = path.stem
    return row


def parse_fit(path: Path, row: dict[str, str] | None = None) -> dict[str, str]:
    row = build_row(path) if row is None else row
    raw_start_time: Any = ""

    def apply_start_time() -> None:
        (
            row["start_time"],
            row["start_time_raw"],
            row["start_time_utc"],
            row["start_timezone"],
            row["start_time_resolution"],
        ) = normalize_start_time(
            raw_start_time,
            row["start_lat"],
            row["start_lon"],
        )

    def apply_values(values: dict[str, Any], parser_name: str) -> None:
        nonlocal raw_start_time
        raw_start_time = values.get("start_time", "")
        apply_start_time()
        row["sport"] = str(values.get("sport", ""))
        row["sub_sport"] = str(values.get("sub_sport", ""))
        row["distance_mi"] = miles(values.get("total_distance"))
        row["duration_s"] = seconds(values.get("total_elapsed_time"))
        row["avg_hr"] = str(values.get("avg_heart_rate", "") or "")
        row["max_hr"] = str(values.get("max_heart_rate", "") or "")
        row["ascent_m"] = str(values.get("total_ascent", "") or "")
        row["parser"] = parser_name
        if not row["start_lat"] or not row["start_lon"]:
            apply_position(
                values.get("start_position_lat"),
                values.get("start_position_long"),
            )

    def apply_position(latitude: Any, longitude: Any) -> bool:
        if latitude in (None, "") or longitude in (None, ""):
            return False
        row["start_lat"] = semicircles_to_degrees(latitude)
        row["start_lon"] = semicircles_to_degrees(longitude)
        apply_start_time()
        return True

    fitparse_exc: Exception | None = None
    if FITPARSE_FILE is not None:
        try:
            fit_file = FITPARSE_FILE(str(path))
            for message in fit_file.get_messages():
                values = field_map(message)
                if message.name == "session":
                    apply_values(values, "fitparse")
                elif message.name == "record" and not row["start_lat"]:
                    apply_position(
                        values.get("position_lat"),
                        values.get("position_long"),
                    )
                if row["parser"] and row["start_lat"] and row["start_lon"]:
                    break
        except Exception as exc:
            fitparse_exc = exc

    if not row["parser"]:
        if FITDECODE is None:
            if fitparse_exc is not None:
                row["parse_error"] = f"{type(fitparse_exc).__name__}: {fitparse_exc}"
            else:
                row["parse_error"] = "Missing optional dependencies `fitparse` and `fitdecode`."
            return row

        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                with FITDECODE.FitReader(str(path)) as fit_file:
                    for frame in fit_file:
                        if frame.frame_type != FITDECODE.FIT_FRAME_DATA:
                            continue
                        values = {field.name: field.value for field in frame.fields}
                        if frame.name == "session":
                            apply_values(values, "fitdecode")
                        elif frame.name == "record" and not row["start_lat"]:
                            apply_position(
                                values.get("position_lat"),
                                values.get("position_long"),
                            )
                        if row["parser"] and row["start_lat"] and row["start_lon"]:
                            break
        except Exception as fitdecode_exc:
            if fitparse_exc is not None:
                row["parse_error"] = (
                    f"fitparse {type(fitparse_exc).__name__}: {fitparse_exc}; "
                    f"fitdecode {type(fitdecode_exc).__name__}: {fitdecode_exc}"
                )
            else:
                row["parse_error"] = (
                    f"fitdecode {type(fitdecode_exc).__name__}: {fitdecode_exc}"
                )

    return row


def parse_fit_files(paths: list[Path]) -> list[dict[str, str]]:
    rows = [parse_fit(path, row=build_row(path)) for path in paths]
    refine_default_timezones(rows)
    return rows


def write_jsonl(output_path: Path, rows: list[dict[str, str]]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True))
            handle.write("\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_dir", type=Path)
    parser.add_argument("output_csv", type=Path)
    parser.add_argument(
        "--jsonl",
        type=Path,
        help="Optional newline-delimited JSON output for machine processing.",
    )
    args = parser.parse_args()

    fit_files = sorted(args.input_dir.glob("*.fit"))
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    rows = parse_fit_files(fit_files)

    with args.output_csv.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    if args.jsonl:
        write_jsonl(args.jsonl, rows)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
