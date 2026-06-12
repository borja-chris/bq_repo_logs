from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from weekly_plan import WeekPlan

REPO_ROOT = Path(__file__).resolve().parent.parent
README_PATH = REPO_ROOT / "README.md"
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
MANUAL_WEEKLY_NOTES_HEADING = "## Manual Weekly Notes"
DAILY_ENTRIES_HEADING = "## Daily Entries"
MANAGED_NOTES_FIELD = "- Managed Notes:"
MANUAL_NOTES_FIELD = "- Manual Notes:"


@dataclass
class WeeklyDayEntry:
    day_date: date
    planned: str = ""
    completed: str = ""
    time: str = ""
    distance: str = ""
    pace: str = ""
    effort: str = ""
    managed_notes_lines: list[str] = field(default_factory=list)
    manual_notes_lines: list[str] = field(default_factory=list)
    sleep: str = ""
    soreness: str = ""
    stress: str = ""
    warning_signs: str = ""

    @property
    def notes(self) -> str:
        note_parts: list[str] = []
        for raw_line in self.manual_notes_lines:
            cleaned = raw_line.strip()
            if not cleaned:
                continue
            if cleaned.startswith("-"):
                cleaned = cleaned[1:].strip()
            if cleaned:
                note_parts.append(cleaned)
        return " ".join(note_parts)

    @property
    def has_content(self) -> bool:
        return any(
            (
                self.completed,
                self.time,
                self.distance,
                self.pace,
                self.effort,
                self.notes,
                self.sleep,
                self.soreness,
                self.stress,
                self.warning_signs,
            )
        )


def weekly_log_path(week_start: date) -> Path:
    return REPO_ROOT / "logs" / "weekly" / f"week_{week_start.isoformat()}.md"


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


def ensure_weekly_log_structure(text: str) -> str:
    if "## Auto Summary" in text:
        text = text.replace("## Auto Summary", "## Weekly Summary", 1)
    if "## Manual Notes" in text:
        text = text.replace("## Manual Notes", MANUAL_WEEKLY_NOTES_HEADING, 1)
    if DAILY_ENTRIES_HEADING in text:
        return text
    trimmed = text.rstrip()
    return f"{trimmed}\n\n{DAILY_ENTRIES_HEADING}\n"


def empty_nested_note_lines() -> list[str]:
    return ["  - "]


def has_real_note_lines(lines: list[str]) -> bool:
    for line in lines:
        cleaned = line.strip()
        if cleaned and cleaned != "-":
            return True
    return False


def normalize_nested_note_lines(lines: list[str]) -> list[str]:
    cleaned = [line.rstrip() for line in lines]
    real_lines = [line for line in cleaned if line.strip() and line.strip() != "-"]
    if real_lines:
        return real_lines
    return empty_nested_note_lines()


def create_weekly_day_entry(day_date: date, planned: str = "") -> WeeklyDayEntry:
    return WeeklyDayEntry(
        day_date=day_date,
        planned=planned,
        managed_notes_lines=empty_nested_note_lines(),
        manual_notes_lines=empty_nested_note_lines(),
    )


def build_managed_notes_lines(activity: Any) -> list[str]:
    managed = [activity.import_note, activity.fit_note]
    if activity.weather_note:
        managed.append(activity.weather_note)
    return [f"  {line}" for line in managed]


def parse_weekly_day_entry(day_date: date, block_lines: list[str]) -> WeeklyDayEntry:
    entry = create_weekly_day_entry(day_date)
    current_section: str | None = None
    for raw_line in block_lines:
        if raw_line.startswith("- Planned:"):
            entry.planned = raw_line.removeprefix("- Planned:").strip()
            current_section = None
        elif raw_line.startswith("- Completed:"):
            entry.completed = raw_line.removeprefix("- Completed:").strip()
            current_section = None
        elif raw_line.startswith("- Time:"):
            entry.time = raw_line.removeprefix("- Time:").strip()
            current_section = None
        elif raw_line.startswith("- Distance:"):
            entry.distance = raw_line.removeprefix("- Distance:").strip()
            current_section = None
        elif raw_line.startswith("- Pace:"):
            entry.pace = raw_line.removeprefix("- Pace:").strip()
            current_section = None
        elif raw_line.startswith("- Effort:"):
            entry.effort = raw_line.removeprefix("- Effort:").strip()
            current_section = None
        elif raw_line == MANAGED_NOTES_FIELD:
            current_section = "managed"
        elif raw_line == MANUAL_NOTES_FIELD:
            current_section = "manual"
        elif raw_line.startswith("- Sleep:"):
            entry.sleep = raw_line.removeprefix("- Sleep:").strip()
            current_section = None
        elif raw_line.startswith("- Soreness:"):
            entry.soreness = raw_line.removeprefix("- Soreness:").strip()
            current_section = None
        elif raw_line.startswith("- Stress:"):
            entry.stress = raw_line.removeprefix("- Stress:").strip()
            current_section = None
        elif raw_line.startswith("- Warning signs:"):
            entry.warning_signs = raw_line.removeprefix("- Warning signs:").strip()
            current_section = None
        elif current_section == "managed":
            entry.managed_notes_lines.append(raw_line.rstrip())
        elif current_section == "manual":
            entry.manual_notes_lines.append(raw_line.rstrip())
    entry.managed_notes_lines = normalize_nested_note_lines(entry.managed_notes_lines)
    entry.manual_notes_lines = normalize_nested_note_lines(entry.manual_notes_lines)
    return entry


def parse_weekly_day_entries_from_text(text: str) -> dict[date, WeeklyDayEntry]:
    if DAILY_ENTRIES_HEADING not in text:
        return {}
    section_match = re.search(
        rf"(?ms)^{re.escape(DAILY_ENTRIES_HEADING)}\n(?P<body>.*?)(?=^## |\Z)",
        text,
    )
    if section_match is None:
        return {}
    body_lines = section_match.group("body").splitlines()
    entries: dict[date, WeeklyDayEntry] = {}
    current_date: date | None = None
    current_block: list[str] = []
    for raw_line in body_lines:
        if raw_line.startswith("### "):
            if current_date is not None:
                entries[current_date] = parse_weekly_day_entry(current_date, current_block)
            current_block = []
            heading_value = raw_line.removeprefix("### ").strip()
            try:
                current_date = date.fromisoformat(heading_value)
            except ValueError:
                current_date = None
            continue
        if current_date is not None:
            current_block.append(raw_line)
    if current_date is not None:
        entries[current_date] = parse_weekly_day_entry(current_date, current_block)
    return entries


def parse_weekly_day_entries(week_start: date) -> dict[date, WeeklyDayEntry]:
    path = weekly_log_path(week_start)
    if not path.exists():
        return {}
    return parse_weekly_day_entries_from_text(path.read_text())


def parse_legacy_daily_log_entry(day_date: date) -> WeeklyDayEntry | None:
    path = resolve_daily_log_path(day_date)
    if not path.exists():
        return None
    entry = create_weekly_day_entry(day_date)
    section: str | None = None
    text = ensure_daily_log_structure(path.read_text())
    for raw_line in text.splitlines():
        if raw_line.startswith("- Planned:"):
            entry.planned = raw_line.removeprefix("- Planned:").strip()
            section = None
        elif raw_line.startswith("- Completed:"):
            entry.completed = raw_line.removeprefix("- Completed:").strip()
            section = None
        elif raw_line.startswith("- Time:"):
            entry.time = raw_line.removeprefix("- Time:").strip()
            section = None
        elif raw_line.startswith("- Distance:"):
            entry.distance = raw_line.removeprefix("- Distance:").strip()
            section = None
        elif raw_line.startswith("- Pace:"):
            entry.pace = raw_line.removeprefix("- Pace:").strip()
            section = None
        elif raw_line.startswith("- Effort:"):
            entry.effort = raw_line.removeprefix("- Effort:").strip()
            section = None
        elif raw_line == MANAGED_NOTES_HEADING:
            section = "managed"
        elif raw_line == MANUAL_NOTES_HEADING:
            section = "manual"
        elif raw_line == RECOVERY_HEADING:
            section = None
        elif raw_line.startswith("- Sleep:"):
            entry.sleep = raw_line.removeprefix("- Sleep:").strip()
        elif raw_line.startswith("- Soreness:"):
            entry.soreness = raw_line.removeprefix("- Soreness:").strip()
        elif raw_line.startswith("- Stress:"):
            entry.stress = raw_line.removeprefix("- Stress:").strip()
        elif raw_line.startswith("- Warning signs:"):
            entry.warning_signs = raw_line.removeprefix("- Warning signs:").strip()
        elif section == "managed" and raw_line.startswith("- "):
            entry.managed_notes_lines.append(f"  {raw_line}")
        elif section == "manual" and raw_line.startswith("- "):
            entry.manual_notes_lines.append(f"  {raw_line}")
    entry.managed_notes_lines = normalize_nested_note_lines(entry.managed_notes_lines)
    entry.manual_notes_lines = normalize_nested_note_lines(entry.manual_notes_lines)
    return entry


def merge_legacy_entry(target: WeeklyDayEntry, legacy: WeeklyDayEntry) -> None:
    if not target.planned:
        target.planned = legacy.planned
    if not target.completed:
        target.completed = legacy.completed
    if not target.time:
        target.time = legacy.time
    if not target.distance:
        target.distance = legacy.distance
    if not target.pace:
        target.pace = legacy.pace
    if not target.effort:
        target.effort = legacy.effort
    if not has_real_note_lines(target.managed_notes_lines) and has_real_note_lines(legacy.managed_notes_lines):
        target.managed_notes_lines = legacy.managed_notes_lines
    if not has_real_note_lines(target.manual_notes_lines) and has_real_note_lines(legacy.manual_notes_lines):
        target.manual_notes_lines = legacy.manual_notes_lines
    if not target.sleep:
        target.sleep = legacy.sleep
    if not target.soreness:
        target.soreness = legacy.soreness
    if not target.stress:
        target.stress = legacy.stress
    if not target.warning_signs:
        target.warning_signs = legacy.warning_signs


def render_weekly_day_entry(entry: WeeklyDayEntry) -> str:
    lines = [
        f"### {entry.day_date.isoformat()}",
        "",
        f"- Planned: {entry.planned}",
        f"- Completed: {entry.completed}",
        f"- Time: {entry.time}",
        f"- Distance: {entry.distance}",
        f"- Pace: {entry.pace}",
        f"- Effort: {entry.effort}",
        MANAGED_NOTES_FIELD,
        *normalize_nested_note_lines(entry.managed_notes_lines),
        MANUAL_NOTES_FIELD,
        *normalize_nested_note_lines(entry.manual_notes_lines),
        f"- Sleep: {entry.sleep}",
        f"- Soreness: {entry.soreness}",
        f"- Stress: {entry.stress}",
        f"- Warning signs: {entry.warning_signs}",
    ]
    return "\n".join(lines)


def render_daily_entries_section(entries: dict[date, WeeklyDayEntry]) -> str:
    rendered = [
        render_weekly_day_entry(entry)
        for _, entry in sorted(entries.items())
    ]
    if not rendered:
        return f"{DAILY_ENTRIES_HEADING}\n"
    return f"{DAILY_ENTRIES_HEADING}\n\n" + "\n\n".join(rendered) + "\n"


def replace_heading_section(text: str, heading: str, body: str) -> str:
    section_pattern = re.compile(
        rf"(?ms)^{re.escape(heading)}\n.*?(?=^## |\Z)"
    )
    replacement = f"{body.rstrip()}\n"
    if section_pattern.search(text):
        return section_pattern.sub(replacement, text, count=1)
    trimmed = text.rstrip()
    return f"{trimmed}\n\n{replacement}"


def seed_missing_planned_day_entries(
    entries: dict[date, WeeklyDayEntry],
    week_plan: WeekPlan,
    today: date,
) -> list[date]:
    seeded_dates: list[date] = []
    for day_plan in week_plan.day_plans:
        entry = entries.get(day_plan.day_date)
        if entry is None:
            entries[day_plan.day_date] = create_weekly_day_entry(day_plan.day_date, day_plan.planned)
            seeded_dates.append(day_plan.day_date)
            entry = entries[day_plan.day_date]
        if not entry.planned:
            entry.planned = day_plan.planned
        if day_plan.day_date <= today and not entry.completed:
            planned_lower = day_plan.planned.strip().lower()
            if planned_lower == "off":
                entry.completed = "off"
                entry.effort = entry.effort or "off"
            elif planned_lower == "rest":
                entry.completed = "rest day"
                entry.effort = entry.effort or "rest"
    return seeded_dates


def upsert_activity_entry(entry: WeeklyDayEntry, activity: Any) -> None:
    entry.completed = activity.completed_label
    entry.time = activity.time_label
    entry.distance = f"{activity.row['distance_mi']} mi"
    entry.pace = activity.pace_label
    if not entry.effort or entry.effort in {"off", "rest"}:
        entry.effort = "imported"
    entry.managed_notes_lines = build_managed_notes_lines(activity)


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


def summarize_day(entry: WeeklyDayEntry) -> tuple[str, str]:
    completed = entry.completed or "x"
    note_parts: list[str] = []
    note_text = entry.notes
    if entry.time and entry.pace:
        note_parts.append(f"{entry.time} at {entry.pace}.")
    elif entry.time:
        note_parts.append(f"Time {entry.time}.")
    if note_text:
        note_parts.append(sentence(note_text))
    soreness = entry.soreness
    if soreness and soreness.lower() not in note_text.lower() and "sore" not in note_text.lower():
        note_parts.append(sentence(entry.soreness, "Soreness: "))
    if entry.warning_signs:
        note_parts.append(sentence(entry.warning_signs, "Warning signs: "))
    return completed, " ".join(part.strip() for part in note_parts if part.strip()) or "x"


def build_week_rows(
    week_plan: WeekPlan,
    day_entries: dict[date, WeeklyDayEntry],
) -> tuple[list[str], float, str]:
    rows = ["| Day | Planned | Actual | Notes |", "| --- | --- | --- | --- |"]
    total_miles = 0.0
    latest_logged: tuple[date, WeeklyDayEntry] | None = None
    for day_plan in week_plan.day_plans:
        entry = day_entries.get(day_plan.day_date)
        actual = "x"
        note = "x"
        if entry:
            actual, note = summarize_day(entry)
            total_miles += actual_miles_from_distance(entry.distance)
            if entry.has_content:
                latest_logged = (day_plan.day_date, entry)
        rows.append(f"| {day_plan.day_name} | {day_plan.planned} | {actual} | {note} |")
    if latest_logged is None:
        status = "No days logged yet"
    else:
        latest_date, latest_entry = latest_logged
        label = latest_date.strftime("%A")
        completed = latest_entry.completed.lower()
        if completed == "rest day":
            status = f"{label} rest logged"
        elif completed == "off":
            status = f"{label} off logged"
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
        "This block mirrors the active weekly log summary for the current week. Daily entries for the week live in `logs/weekly/week_YYYY-MM-DD.md`.",
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


def upsert_weekly_log(
    week_plan: WeekPlan,
    rows: list[str],
    total_miles: float,
    status: str,
    day_entries: dict[date, WeeklyDayEntry],
) -> Path:
    weekly_path = weekly_log_path(week_plan.week_start)
    body = build_weekly_log_body(week_plan, rows, total_miles, status)
    if weekly_path.exists():
        text = ensure_weekly_log_structure(weekly_path.read_text())
    else:
        template = WEEKLY_TEMPLATE.read_text().replace("YYYY-MM-DD", week_plan.week_start.isoformat())
        text = ensure_weekly_log_structure(template)
    updated = ensure_markers(text, WEEKLY_START, WEEKLY_END, "Weekly Summary", body)
    updated = replace_heading_section(updated, DAILY_ENTRIES_HEADING, render_daily_entries_section(day_entries))
    weekly_path.write_text(updated)
    return weekly_path
