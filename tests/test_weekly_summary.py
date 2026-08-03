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
