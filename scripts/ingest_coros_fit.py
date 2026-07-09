"""Ingest loose COROS FIT files and sync repo records.

This script:
1. Moves loose root-level `.fit` files into a dated batch folder.
2. Removes matching `:Zone.Identifier` sidecars.
3. Writes `SHA256SUMS.txt` and processed CSV/JSONL summaries.
4. Creates or updates per-day entries inside the current week's weekly log.
5. Creates or updates the current week's weekly summary.
6. Refreshes the managed current-week block in `README.md`.
7. Writes a batch manifest.

It automates factual recordkeeping and can also attach explicitly supplied
subjective daily notes during import. Coaching interpretation and plan
changes remain manual.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path

import ingest_coros_fit_batch as batch
import ingest_coros_fit_weather as weather
import monthly_archive
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
    build_managed_notes_lines,
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
    upsert_weekly_log,
)
from weekly_plan import DayPlan, WeekPlan, load_week_plan

@dataclass
class SubjectiveUpdate:
    manual_notes: list[str] = field(default_factory=list)
    sleep: str | None = None
    soreness: str | None = None
    stress: str | None = None
    warning_signs: str | None = None

def parse_dated_text(raw_value: str, flag_name: str) -> tuple[date, str]:
    if "|" not in raw_value:
        raise SystemExit(f"{flag_name} must use YYYY-MM-DD|text")
    raw_date, raw_text = raw_value.split("|", 1)
    try:
        parsed_date = date.fromisoformat(raw_date.strip())
    except ValueError as exc:
        raise SystemExit(f"{flag_name} has invalid date: {raw_date.strip()}") from exc
    text = raw_text.strip()
    if not text:
        raise SystemExit(f"{flag_name} text cannot be empty")
    return parsed_date, text

def append_unique_manual_note(entry: WeeklyDayEntry, note_text: str) -> None:
    cleaned = note_text.strip()
    if not cleaned:
        return
    existing_notes = {
        raw_line.strip()[1:].strip()
        for raw_line in entry.manual_notes_lines
        if raw_line.strip() and raw_line.strip() != "-" and raw_line.strip().startswith("-")
    }
    if cleaned in existing_notes:
        return
    real_lines = [
        raw_line.rstrip()
        for raw_line in entry.manual_notes_lines
        if raw_line.strip() and raw_line.strip() != "-"
    ]
    real_lines.append(f"  - {cleaned}")
    entry.manual_notes_lines = real_lines

def collect_subjective_updates(args: argparse.Namespace) -> dict[date, SubjectiveUpdate]:
    updates: dict[date, SubjectiveUpdate] = {}

    def update_for(day_date: date) -> SubjectiveUpdate:
        return updates.setdefault(day_date, SubjectiveUpdate())

    for raw_value in args.manual_note:
        day_date, note_text = parse_dated_text(raw_value, "--manual-note")
        update_for(day_date).manual_notes.append(note_text)
    for raw_value in args.sleep:
        day_date, text = parse_dated_text(raw_value, "--sleep")
        update_for(day_date).sleep = text
    for raw_value in args.soreness:
        day_date, text = parse_dated_text(raw_value, "--soreness")
        update_for(day_date).soreness = text
    for raw_value in args.stress:
        day_date, text = parse_dated_text(raw_value, "--stress")
        update_for(day_date).stress = text
    for raw_value in args.warning_signs:
        day_date, text = parse_dated_text(raw_value, "--warning-signs")
        update_for(day_date).warning_signs = text
    return updates

def apply_subjective_updates(
    day_entries: dict[date, WeeklyDayEntry],
    subjective_updates: dict[date, SubjectiveUpdate],
) -> list[date]:
    applied_dates: list[date] = []
    for day_date, update in sorted(subjective_updates.items()):
        entry = day_entries.get(day_date)
        if entry is None:
            entry = create_weekly_day_entry(day_date)
            day_entries[day_date] = entry
        for note_text in update.manual_notes:
            append_unique_manual_note(entry, note_text)
        if update.sleep is not None:
            entry.sleep = update.sleep
        if update.soreness is not None:
            entry.soreness = update.soreness
        if update.stress is not None:
            entry.stress = update.stress
        if update.warning_signs is not None:
            entry.warning_signs = update.warning_signs
        applied_dates.append(day_date)
    return applied_dates


def total_time_label(total_seconds: int) -> str:
    hours, remainder = divmod(total_seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def aggregate_completed_label(activities: list[weather.Activity], total_distance: float) -> str:
    if len(activities) == 1:
        return activities[0].completed_label
    run_count = sum(
        1
        for activity in activities
        if (activity.row.get("sport", "").strip() or "running") == "running"
    )
    activity_noun = "runs" if run_count == len(activities) else "activities"
    return f"{total_distance:.2f} mi total ({len(activities)} {activity_noun})"


def build_managed_notes_lines_for_activities(activities: list[weather.Activity]) -> list[str]:
    managed_lines: list[str] = []
    for activity in sorted(activities, key=lambda activity: activity.local_start):
        managed_lines.extend(build_managed_notes_lines(activity))
    return managed_lines


def upsert_activity_entries(entry: WeeklyDayEntry, activities: list[weather.Activity]) -> None:
    ordered_activities = sorted(activities, key=lambda activity: activity.local_start)
    total_distance = sum(activity.distance_mi for activity in ordered_activities)
    total_duration_s = sum(activity.duration_s for activity in ordered_activities)

    entry.completed = aggregate_completed_label(ordered_activities, total_distance)
    entry.time = total_time_label(total_duration_s)
    entry.distance = f"{total_distance:.2f} mi"
    if total_distance > 0 and total_duration_s > 0:
        pace_seconds = round(total_duration_s / total_distance)
        minutes, seconds = divmod(pace_seconds, 60)
        entry.pace = f"{minutes}:{seconds:02d}/mi"
    else:
        entry.pace = ""
    if not entry.effort or entry.effort in {"off", "rest"}:
        entry.effort = "imported"
    entry.managed_notes_lines = build_managed_notes_lines_for_activities(ordered_activities)


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
    parser.add_argument(
        "--no-archive",
        action="store_true",
        help="Skip automatic month-boundary daily-log archiving.",
    )
    parser.add_argument(
        "--manual-note",
        action="append",
        default=[],
        metavar="YYYY-MM-DD|TEXT",
        help="Append a manual note to the daily entry for the given date. Repeatable.",
    )
    parser.add_argument(
        "--sleep",
        action="append",
        default=[],
        metavar="YYYY-MM-DD|TEXT",
        help="Set the sleep field for the daily entry for the given date. Repeatable.",
    )
    parser.add_argument(
        "--soreness",
        action="append",
        default=[],
        metavar="YYYY-MM-DD|TEXT",
        help="Set the soreness field for the daily entry for the given date. Repeatable.",
    )
    parser.add_argument(
        "--stress",
        action="append",
        default=[],
        metavar="YYYY-MM-DD|TEXT",
        help="Set the stress field for the daily entry for the given date. Repeatable.",
    )
    parser.add_argument(
        "--warning-signs",
        action="append",
        default=[],
        metavar="YYYY-MM-DD|TEXT",
        help="Set the warning-signs field for the daily entry for the given date. Repeatable.",
    )
    return parser.parse_args()


def monday_of(target: date) -> date:
    return target - timedelta(days=target.weekday())


def sync_records(
    today: date,
    update_logs: bool,
    update_readme_flag: bool,
    recent_activities: list[weather.Activity] | None = None,
    subjective_updates: dict[date, SubjectiveUpdate] | None = None,
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
        activities_by_date: dict[date, list[weather.Activity]] = defaultdict(list)
        for activity in activities:
            if not (week_start <= activity.local_date <= week_end):
                continue
            activities_by_date[activity.local_date].append(activity)
        for activity_date, dated_activities in sorted(activities_by_date.items()):
            entry = day_entries.get(activity_date)
            if entry is None:
                entry = create_weekly_day_entry(
                    activity_date,
                    planned=planned_by_date.get(activity_date, ""),
                )
                day_entries[activity_date] = entry
            elif has_placeholder_planned_value(entry.planned):
                entry.planned = planned_by_date.get(activity_date, "")
            upsert_activity_entries(entry, dated_activities)
            synced_entry_dates.append(activity_date)
        if subjective_updates:
            synced_entry_dates.extend(apply_subjective_updates(day_entries, subjective_updates))

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
    subjective_updates = collect_subjective_updates(args)
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
    output_jsonl = batch.processed_paths_for(today)
    manifest_path: Path | None = None
    activities: list[weather.Activity] = []

    if not args.sync_only:
        export_dir, moved_files, removed_sidecars = batch.import_loose_fit_files(today)
        if moved_files:
            output_jsonl, rows = batch.generate_summaries(export_dir)
            if weather_enabled:
                activities = weather.enrich_rows_with_weather(rows, timeout_s=args.weather_timeout)
                batch.write_processed_outputs(output_jsonl, rows)
            fit_count = batch.write_sha256s(export_dir, rows)
            if not activities:
                activities = weather.load_activities(rows)
            manifest_path = batch.write_manifest(
                export_dir,
                today,
                fit_count,
                removed_sidecars,
                output_jsonl,
                rows,
            )
        elif weather_enabled:
            output_jsonl, rows, activities = weather.re_enrich_processed_batch_weather(
                today,
                timeout_s=args.weather_timeout,
            )
    elif weather_enabled:
        output_jsonl, rows, activities = weather.re_enrich_processed_batch_weather(
            today,
            timeout_s=args.weather_timeout,
        )

    sync_result = sync_records(
        today,
        update_logs=update_logs,
        update_readme_flag=update_readme_flag,
        recent_activities=activities or None,
        subjective_updates=subjective_updates or None,
    )
    failures = weather.weather_failures(rows) if weather_enabled and rows else []

    archive_results: list[dict] = []
    if not args.no_archive:
        archive_results = monthly_archive.run_monthly_archive(today)

    print(f"Import date: {today.isoformat()}")
    print(f"Moved FIT files: {len(moved_files)}")
    if moved_files:
        for path in moved_files:
            print(f"  - {summarize.repo_relpath(path)}")
    print(f"Removed sidecars: {removed_sidecars}")
    if rows:
        print(f"Processed activities: {len(rows)}")
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
    for result in archive_results:
        print(
            f"Archived prior-month daily logs: {result['month']} "
            f"({len(result['moved'])} files) -> {summarize.repo_relpath(result['summary_path'])}"
        )
    print(
        "Manual follow-up: coaching interpretation, retros, and plan changes remain manual. "
        "Subjective daily notes can be attached during import with --manual-note, --sleep, "
        "--soreness, --stress, and --warning-signs."
    )
    if args.require_weather and failures:
        print("Import failed requirement: weather enrichment missing for one or more activities.")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
