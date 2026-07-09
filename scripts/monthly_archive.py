"""Automatic monthly archiving of loose prior-month daily logs.

Daily entries live in weekly logs going forward, so loose root-level
``logs/daily/YYYY-MM-DD.md`` files are only expected to exist for a short
window before being folded into weekly logs. This module is a self-healing
safety net: if any loose *prior-month* daily logs are still sitting in
``logs/daily/``, move them into ``logs/daily/YYYY/YYYY-MM/`` and (re)generate
that month's ``monthly_summary.md``. If nothing loose is found, it is a
no-op.

All path-computing functions accept an injectable ``daily_root`` so this
module is unit-testable against a temporary directory. They intentionally do
not depend on the REPO_ROOT-hardcoded helpers in ``weekly_entries`` for their
parameterized logic.
"""

from __future__ import annotations

import calendar
import re
import shutil
from datetime import date
from pathlib import Path

import weekly_entries
from weekly_entries import WeeklyDayEntry, actual_miles_from_distance

DEFAULT_DAILY_ROOT = weekly_entries.REPO_ROOT / "logs" / "daily"

_LOOSE_DAILY_NAME_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})\.md$")
_NO_SIGNAL_VALUES = {"none", "off", "n/a", "-"}
_REST_COMPLETED_VALUES = {"off", "rest", "rest day", "rest day."}


def _root_daily_path(daily_root: Path, d: date) -> Path:
    return daily_root / f"{d.isoformat()}.md"


def _archive_dir(daily_root: Path, d: date) -> Path:
    return daily_root / str(d.year) / d.strftime("%Y-%m")


def _archived_path(daily_root: Path, d: date) -> Path:
    return _archive_dir(daily_root, d) / f"{d.isoformat()}.md"


def loose_root_daily_dates(daily_root: Path) -> list[date]:
    dates: list[date] = []
    if not daily_root.exists():
        return dates
    for path in daily_root.glob("*.md"):
        match = _LOOSE_DAILY_NAME_RE.match(path.name)
        if not match:
            continue
        try:
            dates.append(date.fromisoformat(path.stem))
        except ValueError:
            continue
    return dates


def loose_prior_month_dates(today: date, daily_root: Path) -> list[date]:
    dates = [
        d
        for d in loose_root_daily_dates(daily_root)
        if (d.year, d.month) < (today.year, today.month)
    ]
    return sorted(dates)


def _parse_seconds(text: str) -> int | None:
    cleaned = text.strip()
    if not cleaned:
        return None
    parts = cleaned.split(":")
    if len(parts) not in (2, 3):
        return None
    try:
        numbers = [int(part) for part in parts]
    except ValueError:
        return None
    if len(numbers) == 3:
        hours, minutes, seconds = numbers
    else:
        hours = 0
        minutes, seconds = numbers
    return hours * 3600 + minutes * 60 + seconds


def _fmt_hms(total_seconds: int) -> str:
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours}:{minutes:02d}:{seconds:02d}"


def _fmt_pace(total_seconds: int, total_miles: float) -> str:
    if total_miles <= 0:
        return "x"
    pace_seconds = round(total_seconds / total_miles)
    minutes = pace_seconds // 60
    seconds = pace_seconds % 60
    return f"{minutes}:{seconds:02d}/mi"


def archived_month_entries(daily_root: Path, any_date_in_month: date) -> list[WeeklyDayEntry]:
    month_dir = _archive_dir(daily_root, any_date_in_month)
    entries: list[WeeklyDayEntry] = []
    if not month_dir.exists():
        return entries
    for path in month_dir.glob("*.md"):
        match = _LOOSE_DAILY_NAME_RE.match(path.name)
        if not match:
            continue
        try:
            entry_date = date.fromisoformat(path.stem)
        except ValueError:
            continue
        entries.append(weekly_entries.parse_daily_log_text(entry_date, path.read_text()))
    entries.sort(key=lambda entry: entry.day_date)
    return entries


def _has_signal(value: str) -> bool:
    cleaned = value.strip().lower()
    return bool(cleaned) and cleaned not in _NO_SIGNAL_VALUES


def render_monthly_summary(month_key: str, entries: list[WeeklyDayEntry]) -> str:
    year, month = (int(part) for part in month_key.split("-"))
    last_day = calendar.monthrange(year, month)[1]

    run_miles_by_entry = {
        entry.day_date: actual_miles_from_distance(entry.distance) for entry in entries
    }
    logged_run_entries = [entry for entry in entries if run_miles_by_entry[entry.day_date] > 0]

    total_miles = sum(run_miles_by_entry[entry.day_date] for entry in logged_run_entries)
    total_seconds = 0
    for entry in logged_run_entries:
        seconds = _parse_seconds(entry.time)
        if seconds is not None:
            total_seconds += seconds

    logged_run_days = len(logged_run_entries)
    avg_pace = _fmt_pace(total_seconds, total_miles)
    avg_distance = (total_miles / logged_run_days) if logged_run_days else 0.0

    if logged_run_entries:
        longest_entry = min(
            logged_run_entries,
            key=lambda entry: (-run_miles_by_entry[entry.day_date], entry.day_date),
        )
        longest_miles = run_miles_by_entry[longest_entry.day_date]
        longest_date = longest_entry.day_date.isoformat()
    else:
        longest_miles = 0.0
        longest_date = "x"

    manual_notes_count = sum(1 for entry in entries if entry.notes.strip())
    soreness_count = sum(1 for entry in entries if _has_signal(entry.soreness))
    warning_count = sum(1 for entry in entries if _has_signal(entry.warning_signs))

    lines = [
        f"# {month_key} Daily Log Summary",
        "",
        f"- Month: `{month_key}`",
        f"- Date span: `{month_key}-01` to `{month_key}-{last_day:02d}`",
        f"- Daily logs archived: `{len(entries)}`",
        f"- Logged run days: `{logged_run_days}`",
        f"- Total mileage: `{total_miles:.2f} mi`",
        f"- Total logged time: `{_fmt_hms(total_seconds)}`",
        f"- Average pace across logged miles: `{avg_pace}`",
        f"- Average distance per logged run: `{avg_distance:.2f} mi`",
        f"- Longest logged run: `{longest_miles:.2f} mi` on `{longest_date}`",
        f"- Days with manual notes: `{manual_notes_count}`",
        f"- Days with soreness notes: `{soreness_count}`",
        f"- Days with warning-sign notes: `{warning_count}`",
        "",
        "## Daily Index",
        "",
        "| Date | Planned | Completed | Distance | Effort | Notes |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for entry in entries:
        run_miles = run_miles_by_entry[entry.day_date]
        planned = entry.planned or "x"
        if run_miles > 0:
            completed = f"{run_miles:.2f} mi run"
        elif entry.completed.strip().lower() in _REST_COMPLETED_VALUES:
            completed = "Rest day"
        else:
            completed = "x"
        distance = f"{run_miles:.2f} mi" if run_miles > 0 else "x"
        effort = entry.effort or "x"
        notes = entry.notes or "x"
        lines.append(
            f"| {entry.day_date.isoformat()} | {planned} | {completed} | {distance} | "
            f"{effort} | {notes} |"
        )

    return "\n".join(lines) + "\n"


def archive_month(daily_root: Path, month_first_date: date) -> dict:
    month_key = month_first_date.strftime("%Y-%m")
    year, month = month_first_date.year, month_first_date.month
    archive_dir = _archive_dir(daily_root, month_first_date)
    archive_dir.mkdir(parents=True, exist_ok=True)

    moved: list[date] = []
    for d in loose_root_daily_dates(daily_root):
        if (d.year, d.month) != (year, month):
            continue
        source = _root_daily_path(daily_root, d)
        target = _archived_path(daily_root, d)
        if not target.exists():
            shutil.move(str(source), str(target))
        else:
            source.unlink()
        moved.append(d)

    entries = archived_month_entries(daily_root, month_first_date)
    summary_text = render_monthly_summary(month_key, entries)
    summary_path = archive_dir / "monthly_summary.md"
    summary_path.write_text(summary_text)

    return {"month": month_key, "moved": sorted(moved), "summary_path": summary_path}


def run_monthly_archive(today: date, daily_root: Path = DEFAULT_DAILY_ROOT) -> list[dict]:
    loose_dates = loose_prior_month_dates(today, daily_root)
    if not loose_dates:
        return []

    months: dict[tuple[int, int], date] = {}
    for d in loose_dates:
        key = (d.year, d.month)
        months.setdefault(key, date(d.year, d.month, 1))

    results = []
    for (year, month), month_first_date in sorted(months.items()):
        results.append(archive_month(daily_root, month_first_date))
    return results
