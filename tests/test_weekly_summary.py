from datetime import date
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from weekly_entries import WeeklyDayEntry, build_weekly_log_body
from weekly_plan import WeekPlan


def make_plan():
    return WeekPlan(
        week_start=date(2026, 7, 20),
        target_mileage="about 34-37",
        primary_purpose="build a stable platform",
        source_relpath="plans/2026-half-marathon/01_pre_block_ramp.md",
        day_plans=[],
    )


def test_body_has_day_digest_and_warning_rollup():
    entries = {
        date(2026, 7, 20): WeeklyDayEntry(
            day_date=date(2026, 7, 20), completed="5.57 mi run",
            distance="5.57 mi", pace="10:44/mi", effort="imported"),
        date(2026, 7, 22): WeeklyDayEntry(
            day_date=date(2026, 7, 22), completed="5.62 mi run",
            distance="5.62 mi", pace="11:00/mi", effort="imported",
            warning_signs="Right calf: slight sharp pain, watch closely"),
    }
    body = build_weekly_log_body(make_plan(), [], 11.19, "Wednesday run logged", entries)
    assert "- Days: Mon 5.57mi @10:44/mi | Wed 5.62mi @11:00/mi ⚠" in body
    assert "- Warnings: Wed: Right calf: slight sharp pain, watch closely" in body


def test_body_without_warnings_says_none():
    body = build_weekly_log_body(make_plan(), [], 0.0, "No days logged yet", {})
    assert "- Warnings: none logged" in body
    assert "- Days: none yet" in body


from datetime import datetime
from zoneinfo import ZoneInfo
from ingest_coros_fit_weather import Activity
from weekly_entries import build_managed_notes_lines


def make_activity(**overrides):
    row = {
        "source_file": "479051765975646409.fit",
        "start_time": "2026-07-20T17:25:54-04:00",
        "distance_mi": "5.57", "duration_s": "3586",
        "avg_hr": "141", "max_hr": "161", "ascent_m": "66",
        "weather_temp_f": "83.7", "weather_dew_point_f": "49.4",
        "heat_load_sum": "133",
        "weather_observation_time": "2026-07-20T17:00",
        "weather_source": "open-meteo",
    }
    row.update(overrides)
    start = datetime(2026, 7, 20, 17, 25, 54, tzinfo=ZoneInfo("America/New_York"))
    return Activity(row=row, local_start=start, local_date=start.date(),
                    timezone_name="America/New_York")


def test_managed_notes_is_one_compact_line():
    lines = build_managed_notes_lines(make_activity())
    assert len(lines) == 1
    line = lines[0]
    assert line.startswith("  - Imported 479051765975646409.fit | start 17:25 | HR 141/161 | asc 66m | ")
    assert "84°F + 49°F dew = 133" in line
    assert "Heat-neutral equivalent" in line


def test_managed_notes_without_heat_falls_back_to_temp():
    lines = build_managed_notes_lines(make_activity(heat_load_sum="", weather_dew_point_f=""))
    assert lines == [
        "  - Imported 479051765975646409.fit | start 17:25 | HR 141/161 | asc 66m | 83.7°F"
    ]
