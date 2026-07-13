from __future__ import annotations

import importlib.util
import sys
from datetime import date, datetime
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch


def load_module():
    repo_root = Path(__file__).resolve().parents[1]
    scripts_dir = repo_root / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    module_path = scripts_dir / "ingest_coros_fit.py"
    spec = importlib.util.spec_from_file_location(
        "ingest_coros_fit_under_test",
        module_path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load ingest_coros_fit.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


m = load_module()


class IngestCorosFitHelpersTest(unittest.TestCase):
    def test_weekly_day_entry_round_trip_preserves_notes(self) -> None:
        entry = m.WeeklyDayEntry(
            day_date=date(2026, 6, 8),
            planned="easy 5",
            completed="5.0 mi run",
            time="41:30",
            distance="5.0 mi",
            pace="8:18/mi",
            effort="moderate",
            managed_notes_lines=[
                "  - Imported from `data/coros_exports/COROS_export_2026-06-08/run.fit`.",
                "  - FIT summary: start `2026-06-08 06:00:00-04:00`, avg HR `145`, max HR `162`, ascent `30 m`.",
            ],
            manual_notes_lines=[
                "  - Felt controlled.",
                "  - Kept the effort honest.",
            ],
            sleep="7h",
            soreness="low",
            stress="normal",
            warning_signs="none",
        )

        rendered = m.render_weekly_day_entry(entry)
        parsed = m.parse_weekly_day_entry(date(2026, 6, 8), rendered.splitlines()[1:])

        self.assertEqual(parsed.planned, entry.planned)
        self.assertEqual(parsed.completed, entry.completed)
        self.assertEqual(parsed.time, entry.time)
        self.assertEqual(parsed.distance, entry.distance)
        self.assertEqual(parsed.pace, entry.pace)
        self.assertEqual(parsed.effort, entry.effort)
        self.assertEqual(parsed.notes, "Felt controlled. Kept the effort honest.")
        self.assertEqual(
            parsed.managed_notes_lines,
            m.normalize_nested_note_lines(entry.managed_notes_lines),
        )
        self.assertEqual(
            parsed.manual_notes_lines,
            m.normalize_nested_note_lines(entry.manual_notes_lines),
        )

    def test_weather_update_from_hourly_matches_hour_and_reports_missing(self) -> None:
        activity = m.weather.Activity(
            row={
                "distance_mi": "6.0",
                "duration_s": "3600",
                "source_relpath": "data/coros_exports/example.fit",
                "avg_hr": "",
                "max_hr": "",
                "ascent_m": "",
                "start_time": "2026-06-08T06:34:12-04:00",
                "weather_temp_f": "",
                "weather_observation_time": "",
            },
            local_start=datetime.fromisoformat("2026-06-08T06:34:12-04:00"),
            local_date=date(2026, 6, 8),
            timezone_name="America/New_York",
        )

        success = m.weather.weather_update_from_hourly(
            activity,
            {
                "time": ["2026-06-08T06:00", "2026-06-08T07:00"],
                "temperature_2m": [18.0, 19.5],
            },
        )
        missing = m.weather.weather_update_from_hourly(
            activity,
            {
                "time": ["2026-06-08T07:00"],
                "temperature_2m": [19.5],
            },
        )

        self.assertEqual(success["weather_temp_c"], "18.0")
        self.assertEqual(success["weather_temp_f"], "64.4")
        self.assertEqual(success["weather_source"], "open-meteo")
        self.assertEqual(success["weather_observation_time"], "2026-06-08T06:00")
        self.assertEqual(success["weather_fetch_error"], "")
        self.assertIn("missing hourly point", missing["weather_fetch_error"])

    def test_sync_records_seeds_entries_merges_legacy_and_upserts_activity(self) -> None:
        week_start = date(2026, 6, 8)
        today = date(2026, 6, 10)
        week_plan = m.WeekPlan(
            source_relpath="plans/2026-half-marathon/week_2026-06-08.md",
            week_start=week_start,
            target_mileage="40-45",
            primary_purpose="threshold",
            day_plans=[
                m.DayPlan("Mon", "Off", "Recovery", "", week_start),
                m.DayPlan("Tue", "Easy 5", "Aerobic", "", week_start.replace(day=9)),
                m.DayPlan("Wed", "Workout", "Threshold", "", week_start.replace(day=10)),
            ],
        )
        existing_entry = m.WeeklyDayEntry(
            day_date=week_start,
            planned="",
            completed="",
            managed_notes_lines=["  - "],
            manual_notes_lines=["  - "],
        )
        legacy_entry = m.WeeklyDayEntry(
            day_date=week_start,
            planned="Off",
            completed="rest day",
            effort="rest",
            manual_notes_lines=["  - Legacy note."],
        )
        activity = m.weather.Activity(
            row={
                "distance_mi": "5.0",
                "duration_s": "1800",
                "sport": "running",
                "source_relpath": "data/coros_exports/COROS_export_2026-06-08/example.fit",
                "start_time": "2026-06-09T06:00:00-04:00",
                "avg_hr": "143",
                "max_hr": "158",
                "ascent_m": "18",
                "weather_temp_f": "63.0",
                "weather_observation_time": "2026-06-09T06:00",
                "weather_source": "open-meteo",
            },
            local_start=datetime.fromisoformat("2026-06-09T06:00:00-04:00"),
            local_date=week_start.replace(day=9),
            timezone_name="America/New_York",
        )

        weekly_path = Path("/tmp/week_2026-06-08.md")
        readme_calls: list[tuple] = []
        weekly_calls: list[tuple] = []
        with patch.object(m, "load_week_plan", return_value=week_plan), patch.object(
            m, "parse_weekly_day_entries", return_value={week_start: existing_entry}
        ), patch.object(
            m,
            "parse_legacy_daily_log_entry",
            side_effect=lambda day: legacy_entry if day == week_start else None,
        ), patch.object(
            m.weather, "load_processed_activities_for_week", return_value=[activity]
        ), patch.object(
            m, "upsert_weekly_log", side_effect=lambda *args: weekly_calls.append(args) or weekly_path
        ), patch.object(
            m, "update_readme", side_effect=lambda *args: readme_calls.append(args)
        ):
            result = m.sync_records(today, update_logs=True, update_readme_flag=True)

        self.assertEqual(result["weekly_paths"], [weekly_path])
        self.assertEqual(
            result["synced_entry_dates"],
            [week_start.replace(day=9), week_start.replace(day=10)],
        )
        self.assertEqual(result["uncovered_activity_dates"], [])
        self.assertEqual(result["status"], "Tuesday run logged")
        self.assertAlmostEqual(result["total_miles"], 5.0)
        synced_entries = weekly_calls[0][4]
        self.assertEqual(synced_entries[week_start].completed, "rest day")
        self.assertEqual(synced_entries[week_start.replace(day=9)].completed, "5.0 mi run")
        self.assertEqual(synced_entries[week_start.replace(day=9)].effort, "imported")
        self.assertEqual(synced_entries[week_start.replace(day=10)].planned, "Workout")
        self.assertEqual(len(weekly_calls), 1)
        self.assertEqual(len(readme_calls), 1)

    def test_sync_records_aggregates_multiple_same_day_activities(self) -> None:
        week_start = date(2026, 6, 29)
        today = date(2026, 7, 1)
        monday = week_start
        week_plan = m.WeekPlan(
            source_relpath="plans/2026-half-marathon/01_pre_block_ramp.md",
            week_start=week_start,
            target_mileage="32-35",
            primary_purpose="base",
            day_plans=[
                m.DayPlan("Monday", "Off", "Recovery", "", monday),
            ],
        )
        first_run = m.weather.Activity(
            row={
                "distance_mi": "3.39",
                "duration_s": "2059",
                "sport": "running",
                "source_relpath": "data/coros_exports/COROS_export_2026-07-01/first.fit",
                "start_time": "2026-06-29T19:18:33-04:00",
                "avg_hr": "147",
                "max_hr": "165",
                "ascent_m": "11",
                "weather_temp_f": "82.6",
                "weather_observation_time": "2026-06-29T19:00",
                "weather_source": "open-meteo",
            },
            local_start=datetime.fromisoformat("2026-06-29T19:18:33-04:00"),
            local_date=monday,
            timezone_name="America/New_York",
        )
        second_run = m.weather.Activity(
            row={
                "distance_mi": "0.81",
                "duration_s": "597",
                "sport": "running",
                "source_relpath": "data/coros_exports/COROS_export_2026-07-01/second.fit",
                "start_time": "2026-06-29T20:11:22-04:00",
                "avg_hr": "138",
                "max_hr": "147",
                "ascent_m": "5",
                "weather_temp_f": "81.0",
                "weather_observation_time": "2026-06-29T20:00",
                "weather_source": "open-meteo",
            },
            local_start=datetime.fromisoformat("2026-06-29T20:11:22-04:00"),
            local_date=monday,
            timezone_name="America/New_York",
        )

        weekly_path = Path("/tmp/week_2026-06-29.md")
        weekly_calls: list[tuple] = []
        with patch.object(m, "load_week_plan", return_value=week_plan), patch.object(
            m, "parse_weekly_day_entries", return_value={}
        ), patch.object(
            m, "parse_legacy_daily_log_entry", return_value=None
        ), patch.object(
            m.weather, "load_processed_activities_for_week", return_value=[first_run, second_run]
        ), patch.object(
            m, "upsert_weekly_log", side_effect=lambda *args: weekly_calls.append(args) or weekly_path
        ), patch.object(
            m, "update_readme"
        ):
            result = m.sync_records(today, update_logs=True, update_readme_flag=True)

        self.assertAlmostEqual(result["total_miles"], 4.20)
        self.assertEqual(result["status"], "Monday run logged")
        synced_entry = weekly_calls[0][4][monday]
        self.assertEqual(synced_entry.completed, "4.20 mi total (2 runs)")
        self.assertEqual(synced_entry.time, "44:16")
        self.assertEqual(synced_entry.distance, "4.20 mi")
        self.assertEqual(synced_entry.pace, "10:32/mi")
        self.assertIn("first.fit", "\n".join(synced_entry.managed_notes_lines))
        self.assertIn("second.fit", "\n".join(synced_entry.managed_notes_lines))

    def test_sync_records_files_prior_week_run_imported_later(self) -> None:
        # Sunday run imported the following week: the activity belongs to the
        # 2026-07-06 week, but the import happens on Monday 2026-07-13. The run
        # must land in its own (older) week's log while README only refreshes for
        # the current clock week.
        clock_week = date(2026, 7, 13)
        activity_week = date(2026, 7, 6)
        run_day = date(2026, 7, 12)
        today = clock_week

        clock_plan = m.WeekPlan(
            source_relpath="plans/2026-half-marathon/01_pre_block_ramp.md",
            week_start=clock_week,
            target_mileage="33-36",
            primary_purpose="base",
            day_plans=[m.DayPlan("Monday", "Off", "Recovery", "", clock_week)],
        )
        activity_plan = m.WeekPlan(
            source_relpath="plans/2026-half-marathon/01_pre_block_ramp.md",
            week_start=activity_week,
            target_mileage="29-32",
            primary_purpose="absorb",
            day_plans=[m.DayPlan("Sunday", "Long run", "Aerobic", "", run_day)],
        )

        activity = m.weather.Activity(
            row={
                "distance_mi": "8.52",
                "duration_s": "5578",
                "sport": "running",
                "source_relpath": "data/coros_exports/COROS_export_2026-07-13/run.fit",
                "start_time": "2026-07-12T09:59:38-04:00",
                "avg_hr": "143",
                "max_hr": "164",
                "ascent_m": "103",
                "weather_temp_f": "75.2",
                "weather_observation_time": "2026-07-12T09:00",
                "weather_source": "open-meteo",
            },
            local_start=datetime.fromisoformat("2026-07-12T09:59:38-04:00"),
            local_date=run_day,
            timezone_name="America/New_York",
        )

        plans = {clock_week: clock_plan, activity_week: activity_plan}
        weekly_calls: list[date] = []
        readme_calls: list[date] = []
        with patch.object(
            m, "load_week_plan", side_effect=lambda ws: plans[ws]
        ), patch.object(
            m, "parse_weekly_day_entries", side_effect=lambda ws: {}
        ), patch.object(
            m, "parse_legacy_daily_log_entry", return_value=None
        ), patch.object(
            m.weather, "load_processed_activities_for_week", return_value=[]
        ), patch.object(
            m,
            "upsert_weekly_log",
            side_effect=lambda week_plan, *rest: (
                weekly_calls.append(week_plan.week_start)
                or Path(f"/tmp/week_{week_plan.week_start.isoformat()}.md")
            ),
        ), patch.object(
            m, "update_readme", side_effect=lambda week_plan, *rest: readme_calls.append(week_plan.week_start)
        ):
            result = m.sync_records(
                today,
                update_logs=True,
                update_readme_flag=True,
                recent_activities=[activity],
            )

        # Both weeks written; README refreshed for the clock week only.
        self.assertEqual(sorted(weekly_calls), [activity_week, clock_week])
        self.assertEqual(readme_calls, [clock_week])
        # The run landed on its true date and nothing was left uncovered.
        self.assertIn(run_day, result["synced_entry_dates"])
        self.assertEqual(result["uncovered_activity_dates"], [])
        self.assertEqual(
            sorted(result["weekly_paths"]),
            [
                Path(f"/tmp/week_{activity_week.isoformat()}.md"),
                Path(f"/tmp/week_{clock_week.isoformat()}.md"),
            ],
        )

    def test_main_aborts_when_parser_dependencies_are_missing(self) -> None:
        captured: list[list[Path]] = []
        fake_args = SimpleNamespace(
            date="2026-06-08",
            no_readme=False,
            no_logs=False,
            sync_only=False,
            no_weather=False,
            weather_timeout=10.0,
            require_weather=False,
            manual_note=[],
            sleep=[],
            soreness=[],
            stress=[],
            warning_signs=[],
        )
        with patch.object(m, "parse_args", return_value=fake_args), patch.object(
            m.batch,
            "find_loose_fit_files",
            return_value=[Path("run.fit")],
        ), patch.object(m.batch, "fit_parser_available", return_value=False), patch.object(
            m.batch,
            "print_fit_parser_preflight_failure",
            side_effect=lambda files: captured.append(files),
        ), patch.object(m, "sync_records") as sync_records:
            exit_code = m.main()

        self.assertEqual(exit_code, 3)
        self.assertEqual(captured, [[Path("run.fit")]])
        sync_records.assert_not_called()


class IngestCorosFitSectionHelpersTest(unittest.TestCase):
    def test_ensure_markers_replaces_existing_section(self) -> None:
        text = (
            "preamble\n"
            "<!-- current-week:start -->\n"
            "old body\n"
            "<!-- current-week:end -->\n"
            "trailer\n"
        )
        updated = m.ensure_markers(
            text,
            m.README_START,
            m.README_END,
            "Current Week",
            "new body",
        )

        self.assertIn("<!-- current-week:start -->\nnew body\n<!-- current-week:end -->", updated)
        self.assertNotIn("old body", updated)

    def test_replace_heading_section_inserts_when_missing(self) -> None:
        text = "intro\n"
        updated = m.replace_heading_section(text, m.DAILY_ENTRIES_HEADING, "## Daily Entries\n\nbody")

        self.assertIn("## Daily Entries\n\nbody", updated)


if __name__ == "__main__":
    unittest.main()
