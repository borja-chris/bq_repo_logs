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
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterable
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
MANAGED_NOTES_HEADING = "## Managed Notes"
MANUAL_NOTES_HEADING = "## Manual Notes"
RECOVERY_HEADING = "## Recovery Signals"


@dataclass
class Activity:
    row: dict[str, str]
    local_start: datetime
    local_date: date

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
        return (
            f"- FIT summary: start `{self.row['start_time']}`, avg HR "
            f"`{self.row['avg_hr'] or ''}`, max HR `{self.row['max_hr'] or ''}`, "
            f"ascent `{self.row['ascent_m'] or ''} m`."
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
    return parser.parse_args()


def format_int(value: int) -> str:
    return f"{value:,}"


def monday_of(target: date) -> date:
    return target - timedelta(days=target.weekday())


def parse_start_time(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(LOCAL_TZ)


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
    rows = summarize.parse_fit_files(fit_files)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=summarize.FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    summarize.write_jsonl(output_jsonl, rows)
    return output_csv, output_jsonl, rows


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


def replace_managed_notes(lines: list[str], activity: Activity) -> list[str]:
    note_start = lines.index(MANAGED_NOTES_HEADING) + 1
    manual_index = lines.index(MANUAL_NOTES_HEADING)
    managed = [activity.import_note, activity.fit_note]
    new_notes = [""] + managed + [""]
    return lines[:note_start] + new_notes + lines[manual_index:]


def create_daily_log_stub(day_date: date, planned: str) -> Path:
    log_path = REPO_ROOT / "logs" / "daily" / f"{day_date.isoformat()}.md"
    if log_path.exists():
        return log_path
    text = load_template(DAILY_TEMPLATE).replace("YYYY-MM-DD", day_date.isoformat())
    text = ensure_daily_log_structure(text)
    lines = text.splitlines()
    set_field(lines, "Planned", planned)
    log_path.write_text("\n".join(lines) + "\n")
    return log_path


def upsert_daily_log(activity: Activity) -> Path:
    log_path = REPO_ROOT / "logs" / "daily" / f"{activity.local_date.isoformat()}.md"
    if log_path.exists():
        text = ensure_daily_log_structure(log_path.read_text())
    else:
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
        path = REPO_ROOT / "logs" / "daily" / f"{day_date.isoformat()}.md"
        if not path.exists():
            continue
        fields = {
            "completed": "",
            "time": "",
            "distance": "",
            "pace": "",
            "effort": "",
            "notes": "",
            "soreness": "",
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
            if raw_line.startswith("- Completed:"):
                fields["completed"] = raw_line.removeprefix("- Completed:").strip()
            elif raw_line.startswith("- Time:"):
                fields["time"] = raw_line.removeprefix("- Time:").strip()
            elif raw_line.startswith("- Distance:"):
                fields["distance"] = raw_line.removeprefix("- Distance:").strip()
            elif raw_line.startswith("- Pace:"):
                fields["pace"] = raw_line.removeprefix("- Pace:").strip()
            elif raw_line.startswith("- Effort:"):
                fields["effort"] = raw_line.removeprefix("- Effort:").strip()
            elif raw_line.startswith("- Soreness:"):
                fields["soreness"] = raw_line.removeprefix("- Soreness:").strip()
            elif raw_line.startswith("- Warning signs:"):
                fields["warning_signs"] = raw_line.removeprefix("- Warning signs:").strip()
            elif manual_notes_started and raw_line.startswith("- "):
                notes_lines.append(raw_line)
            elif recovery_started:
                continue
        filtered_notes = [line.removeprefix("- ").strip() for line in notes_lines]
        fields["notes"] = " ".join(note for note in filtered_notes if note and note != "")
        result[day_date] = fields
    return result


def seed_missing_planned_day_logs(week_plan: WeekPlan, today: date) -> list[Path]:
    created_paths: list[Path] = []
    for day_plan in week_plan.day_plans:
        if day_plan.day_date > today:
            continue
        if day_plan.planned.strip().lower() in {"rest", "off"}:
            continue
        log_path = REPO_ROOT / "logs" / "daily" / f"{day_plan.day_date.isoformat()}.md"
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
        if not row.get("start_time"):
            continue
        local_start = parse_start_time(row["start_time"])
        activities.append(
            Activity(
                row=row,
                local_start=local_start,
                local_date=local_start.date(),
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
                if not row.get("start_time"):
                    continue
                local_start = parse_start_time(row["start_time"])
                local_date = local_start.date()
                if week_start <= local_date <= week_end:
                    activities.append(
                        Activity(
                            row=row,
                            local_start=local_start,
                            local_date=local_date,
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

    moved_files: list[Path] = []
    removed_sidecars = 0
    rows: list[dict[str, str]] = []
    export_dir = batch_dir_for(today)
    output_csv, output_jsonl = processed_paths_for(today)
    manifest_path: Path | None = None
    daily_paths: list[Path] = []
    activities: list[Activity] = []

    if not args.sync_only:
        export_dir, moved_files, removed_sidecars = import_loose_fit_files(today)
        if moved_files:
            output_csv, output_jsonl, rows = generate_summaries(export_dir)
            fit_count = write_sha256s(export_dir, rows)
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
