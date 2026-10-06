#!/usr/bin/env python3
"""One-shot: add per-lap splits to data/processed/*_summary.jsonl rows.

For each row lacking a `laps` field, locate the archived FIT at
data/coros_exports/COROS_export_<date>/<source_file> (date taken from the
JSONL filename), verify its sha256 equals the row's `source_sha256`, extract
the `lap` messages, and add ONLY the `laps` key. Every other field is
verified unchanged before the file is atomically replaced. Rows whose FIT is
missing or whose sha mismatches are left untouched and reported. Idempotent.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ingest_coros_fit as ingest
import ingest_coros_fit_weather as weather
import summarize_coros_fit as summarize
from weekly_entries import should_render_laps
from weekly_plan import load_week_plan

REPO_ROOT = Path(__file__).resolve().parent.parent


def fit_path_for(jsonl_path: Path, row: dict, exports_dir: Path) -> Path:
    batch = jsonl_path.name.removeprefix("coros_export_").removesuffix("_summary.jsonl")
    return exports_dir / f"COROS_export_{batch}" / row.get("source_file", "")


def backfill_file(path: Path, exports_dir: Path) -> tuple[int, list[str]]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    updated: list[dict] = []
    skipped: list[str] = []
    added = 0
    for row in rows:
        new = dict(row)
        if "laps" not in row:
            fit = fit_path_for(path, row, exports_dir)
            if not fit.is_file():
                skipped.append(f"{row.get('activity_id', '?')}: missing {fit}")
            elif summarize.sha256(fit) != row.get("source_sha256"):
                skipped.append(f"{row.get('activity_id', '?')}: sha256 mismatch {fit}")
            else:
                new["laps"] = summarize.extract_laps(fit)
                added += 1
        updated.append(new)
    for before, after in zip(rows, updated):
        changed = {k for k in set(before) | set(after) if before.get(k) != after.get(k)}
        if changed - {"laps"}:
            raise SystemExit(f"{path.name}: fields other than laps changed: {sorted(changed - {'laps'})}")
    if added:
        tmp = path.with_name(path.name + ".tmp")
        tmp.write_text(
            "".join(json.dumps(row, sort_keys=True) + "\n" for row in updated),
            encoding="utf-8",
        )
        tmp.replace(path)
    return added, skipped


def weeks_needing_lap_sync(processed_dir: Path) -> list[date]:
    """Mondays of weeks holding an activity whose laps would now be rendered.

    `--sync-only` only re-syncs the clock week, so older weeks must be synced
    explicitly for already-imported SOS days to pick up their laps.
    """
    weeks: set[date] = set()
    for path in sorted(processed_dir.glob("*_summary.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            start = weather.row_start_time_value(row)
            if not start or not row.get("laps"):
                continue
            day = datetime.fromisoformat(start).date()
            monday = day - timedelta(days=day.weekday())
            try:
                plan = load_week_plan(monday)
            except Exception:
                continue
            purpose = next((d.purpose for d in plan.day_plans if d.day_date == day), "")
            if should_render_laps(row["laps"], purpose):
                weeks.add(monday)
    return sorted(weeks)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--processed-dir", type=Path, default=REPO_ROOT / "data" / "processed")
    parser.add_argument("--exports-dir", type=Path, default=REPO_ROOT / "data" / "coros_exports")
    parser.add_argument("--no-sync", action="store_true",
                        help="Skip re-syncing weekly logs that gain lap lines.")
    args = parser.parse_args()
    files = sorted(args.processed_dir.glob("*_summary.jsonl"))
    if not files:
        raise SystemExit(f"no *_summary.jsonl files in {args.processed_dir}")
    for path in files:
        added, skipped = backfill_file(path, args.exports_dir)
        print(f"backfilled {path.name}: {added} rows")
        for message in skipped:
            print(f"  skipped {message}")
    if not args.no_sync:
        today = datetime.now(weather.LOCAL_TZ).date()
        for week_start in weeks_needing_lap_sync(args.processed_dir):
            ingest.sync_week(week_start, today, update_logs=True, update_readme_flag=False)
            print(f"synced weekly log for week {week_start.isoformat()}")


if __name__ == "__main__":
    main()
