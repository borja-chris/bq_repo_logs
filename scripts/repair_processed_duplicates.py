"""Repair duplicate activity_id rows across data/processed/*.jsonl.

Historically nothing deduplicated data/processed/*.jsonl against itself, so a
re-exported COROS activity could land twice across two different files with
byte-identical fields. Downstream weekly sync sums every matching row, so a
duplicate silently doubles reported mileage/time for that day.

This script scans all data/processed/*.jsonl files in sorted-filename order.
For every activity_id that appears more than once, the first occurrence (in
that same sorted order) is kept and every later occurrence is removed. Files
with no removals are left byte-for-byte untouched.

Usage:
    .venv/bin/python scripts/repair_processed_duplicates.py            # dry-run (default)
    .venv/bin/python scripts/repair_processed_duplicates.py --dry-run  # explicit dry-run
    .venv/bin/python scripts/repair_processed_duplicates.py --apply    # rewrite files
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = REPO_ROOT / "data" / "processed"


def find_duplicate_removals(processed_dir: Path) -> list[tuple[Path, int, str, str]]:
    """Return (path, line_number, activity_id, raw_line) tuples to remove.

    `line_number` is 1-indexed within its file. The first occurrence of each
    activity_id, in sorted-filename order, is kept; every later occurrence
    (whether in the same file or a different one) is scheduled for removal.
    """
    seen: set[str] = set()
    removals: list[tuple[Path, int, str, str]] = []
    for path in sorted(processed_dir.glob("*.jsonl")):
        with path.open() as handle:
            lines = handle.readlines()
        for index, raw_line in enumerate(lines, start=1):
            stripped = raw_line.strip()
            if not stripped:
                continue
            row = json.loads(stripped)
            activity_id = row.get("activity_id", "")
            if not activity_id:
                continue
            if activity_id in seen:
                removals.append((path, index, activity_id, raw_line))
            else:
                seen.add(activity_id)
    return removals


def apply_removals(removals: list[tuple[Path, int, str, str]]) -> None:
    by_file: dict[Path, set[int]] = {}
    for path, index, _activity_id, _raw_line in removals:
        by_file.setdefault(path, set()).add(index)

    for path, line_numbers in by_file.items():
        with path.open() as handle:
            lines = handle.readlines()
        kept = [line for i, line in enumerate(lines, start=1) if i not in line_numbers]
        with path.open("w") as handle:
            handle.writelines(kept)


def repo_relpath(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def run(processed_dir: Path, apply_changes: bool) -> list[tuple[Path, int, str]]:
    """Find and (optionally) remove duplicate activity_id rows.

    Prints one line per row that would be/was removed, then returns the
    (path, line_number, activity_id) tuples for the caller to inspect.
    """
    removals = find_duplicate_removals(processed_dir)
    verb = "Removed" if apply_changes else "Would remove"
    for path, index, activity_id, _raw_line in removals:
        print(f"{verb}: {repo_relpath(path)}:{index} activity_id={activity_id}")

    if apply_changes and removals:
        apply_removals(removals)

    return [(path, index, activity_id) for path, index, activity_id, _raw_line in removals]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be removed without writing (default behavior).",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Rewrite files, actually removing duplicate rows.",
    )
    args = parser.parse_args()

    removals = run(PROCESSED_DIR, apply_changes=args.apply)

    if not removals:
        print("No duplicate activity_id rows found.")
        return 0

    files_touched = len({path for path, _index, _activity_id in removals})
    if args.apply:
        print(f"Rewrote {files_touched} file(s); removed {len(removals)} row(s).")
    else:
        print(
            f"Dry run: {len(removals)} row(s) in {files_touched} file(s) would be removed. "
            "Re-run with --apply to rewrite."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
