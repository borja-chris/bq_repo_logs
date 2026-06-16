"""Ingest loose COROS FIT files and sync repo records.

This script:
1. Moves loose root-level `.fit` files into a dated batch folder.
2. Removes matching `:Zone.Identifier` sidecars.
3. Writes `SHA256SUMS.txt` and processed CSV/JSONL summaries.
4. Creates or updates per-day entries inside the current week's weekly log.
5. Creates or updates the current week's weekly summary.
6. Refreshes the managed current-week block in `README.md`.
7. Writes a batch manifest.

It intentionally automates factual recordkeeping only. Subjective recovery
signals, coaching interpretation, and plan changes remain manual.
"""

from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta
from pathlib import Path

import ingest_coros_fit_batch as batch
import ingest_coros_fit_weather as weather
import summarize_coros_fit as summarize
from weekly_entries import (
    DAILY_ENTRIES_HEADING,
    MANAGED_NOTES_FIELD,
    MANUAL_NOTES_FIELD,
    README_END,
    README_START,
    README_PATH,
    RECOVERY_HEADING,
    WEEKLY_END,
    WEEKLY_START,
    WeeklyDayEntry,
    build_week_rows,
    create_weekly_day_entry,
    ensure_markers,
    merge_legacy_entry,
    normalize_nested_note_lines,
    parse_legacy_daily_log_entry,
    parse_weekly_day_entry,
    parse_weekly_day_entries,
    render_weekly_day_entry,
    replace_heading_section,
    seed_missing_planned_day_entries,
    has_placeholder_planned_value,
    update_readme,
    upsert_activity_entry,
    upsert_weekly_log,
)
from weekly_plan import DayPlan, WeekPlan, load_week_plan


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
        help="Skip weekly log updates.",
    )
    parser.add_argument(
        "--sync-only",
        action="store_true",
        help="Do not import loose FIT files. Refresh weekly logs/README from existing data.",
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
    parser.add_argument(
        "--require-weather",
        action="store_true",
        help="Fail with a non-zero exit code if any activity is missing weather after enrichment.",
    )
    return parser.parse_args()


def monday_of(target: date) -> date:
    return target - timedelta(days=target.weekday())


def sync_records(
    today: date,
    update_logs: bool,
    update_readme_flag: bool,
    recent_activities: list[weather.Activity] | None = None,
) -> dict[str, object]:
    week_start = monday_of(today)
    week_end = week_start + timedelta(days=6)
    week_plan = load_week_plan(week_start)
    day_entries = parse_weekly_day_entries(week_start)
    for day_plan in week_plan.day_plans:
        legacy_entry = parse_legacy_daily_log_entry(day_plan.day_date)
        if legacy_entry is None:
            continue
        current_entry = day_entries.get(day_plan.day_date)
        if current_entry is None:
            day_entries[day_plan.day_date] = legacy_entry
        else:
            merge_legacy_entry(current_entry, legacy_entry)

    synced_entry_dates: list[date] = []
    if update_logs:
        synced_entry_dates.extend(seed_missing_planned_day_entries(day_entries, week_plan, today))
        activities = recent_activities
        if activities is None:
            activities = weather.load_processed_activities_for_week(week_start)
        planned_by_date = {day_plan.day_date: day_plan.planned for day_plan in week_plan.day_plans}
        for activity in activities:
            if not (week_start <= activity.local_date <= week_end):
                continue
            entry = day_entries.get(activity.local_date)
            if entry is None:
                entry = create_weekly_day_entry(
                    activity.local_date,
                    planned=planned_by_date.get(activity.local_date, ""),
                )
                day_entries[activity.local_date] = entry
            elif has_placeholder_planned_value(entry.planned):
                entry.planned = planned_by_date.get(activity.local_date, "")
            upsert_activity_entry(entry, activity)
            synced_entry_dates.append(activity.local_date)

    rows, total_miles, status = build_week_rows(week_plan, day_entries)
    weekly_path: Path | None = None
    if update_logs:
        weekly_path = upsert_weekly_log(week_plan, rows, total_miles, status, day_entries)
    if update_readme_flag:
        update_readme(week_plan, rows, total_miles, status)
    return {
        "week_plan": week_plan,
        "weekly_path": weekly_path,
        "synced_entry_dates": sorted(set(synced_entry_dates)),
        "total_miles": total_miles,
        "status": status,
    }


def main() -> int:
    args = parse_args()
    today = date.fromisoformat(args.date) if args.date else datetime.now(weather.LOCAL_TZ).date()
    update_logs = not args.no_logs
    update_readme_flag = not args.no_readme
    weather_enabled = not args.no_weather
    loose_fit_files = [] if args.sync_only else batch.find_loose_fit_files()

    if loose_fit_files and not batch.fit_parser_available():
        batch.print_fit_parser_preflight_failure(loose_fit_files)
        return 3

    moved_files: list[Path] = []
    removed_sidecars = 0
    rows: list[dict[str, str]] = []
    export_dir = batch.batch_dir_for(today)
    output_csv, output_jsonl = batch.processed_paths_for(today)
    manifest_path: Path | None = None
    activities: list[weather.Activity] = []

    if not args.sync_only:
        export_dir, moved_files, removed_sidecars = batch.import_loose_fit_files(today)
        if moved_files:
            output_csv, output_jsonl, rows = batch.generate_summaries(export_dir)
            if weather_enabled:
                activities = weather.enrich_rows_with_weather(rows, timeout_s=args.weather_timeout)
                batch.write_processed_outputs(output_csv, output_jsonl, rows)
            fit_count = batch.write_sha256s(export_dir, rows)
            if not activities:
                activities = weather.load_activities(rows)
            manifest_path = batch.write_manifest(
                export_dir,
                today,
                fit_count,
                removed_sidecars,
                output_csv,
                output_jsonl,
                rows,
            )
        elif weather_enabled:
            output_csv, output_jsonl, rows, activities = weather.re_enrich_processed_batch_weather(
                today,
                timeout_s=args.weather_timeout,
            )
    elif weather_enabled:
        output_csv, output_jsonl, rows, activities = weather.re_enrich_processed_batch_weather(
            today,
            timeout_s=args.weather_timeout,
        )

    sync_result = sync_records(
        today,
        update_logs=update_logs,
        update_readme_flag=update_readme_flag,
        recent_activities=activities or None,
    )
    failures = weather.weather_failures(rows) if weather_enabled and rows else []

    print(f"Import date: {today.isoformat()}")
    print(f"Moved FIT files: {len(moved_files)}")
    if moved_files:
        for path in moved_files:
            print(f"  - {summarize.repo_relpath(path)}")
    print(f"Removed sidecars: {removed_sidecars}")
    if rows:
        print(f"Processed activities: {len(rows)}")
        print(f"CSV summary: {summarize.repo_relpath(output_csv)}")
        print(f"JSONL summary: {summarize.repo_relpath(output_jsonl)}")
        if weather_enabled:
            print(f"Weather enriched: {len(rows) - len(failures)}/{len(rows)}")
            if failures:
                print(f"Weather missing: {len(failures)}")
                for row in failures:
                    activity_id = row.get("activity_id", "") or row.get("source_file", "unknown")
                    error = row.get("weather_fetch_error", "").strip() or "missing weather fields"
                    print(f"  - {activity_id}: {error}")
    synced_entry_dates = sync_result["synced_entry_dates"]
    if isinstance(synced_entry_dates, list) and synced_entry_dates:
        print(f"Current-week daily entries synced: {len(synced_entry_dates)}")
        for day_date in synced_entry_dates:
            print(f"  - {day_date.isoformat()}")
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
    if args.require_weather and failures:
        print("Import failed requirement: weather enrichment missing for one or more activities.")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
