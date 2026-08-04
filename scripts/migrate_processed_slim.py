#!/usr/bin/env python3
"""One-shot: rewrite data/processed/*_summary.jsonl to the slim output schema.

Writes each file to a .tmp sibling, verifies that the ordered sequence of
(activity_id, source_sha256, distance_mi, duration_s) tuples is identical
before and after slimming -- catching value corruption of those four
identity fields introduced by slim_row -- then atomically replaces. The
slimming step (`slim = [slim_row(r) for r in rows]`) is a 1:1,
order-preserving list comprehension, so rows cannot be dropped, reordered,
or duplicated here; this check cannot and does not claim to catch that.
Idempotent.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from summarize_coros_fit import slim_row

REPO_ROOT = Path(__file__).resolve().parent.parent


IDENTITY_FIELDS = ["activity_id", "source_sha256", "distance_mi", "duration_s"]


def _identity_key(row: dict[str, str]) -> tuple[str, ...]:
    return tuple(row.get(field, "") for field in IDENTITY_FIELDS)


def migrate_file(path: Path) -> int:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    slim = [slim_row(row) for row in rows]
    before = [_identity_key(row) for row in rows]
    after = [_identity_key(row) for row in slim]
    if before != after:
        raise SystemExit(f"{path.name}: row identity fields changed during slimming "
                          f"(activity_id, source_sha256, distance_mi, or duration_s "
                          f"corrupted)")
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in slim),
        encoding="utf-8",
    )
    tmp.replace(path)
    return len(slim)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--processed-dir", type=Path,
                        default=REPO_ROOT / "data" / "processed")
    args = parser.parse_args()
    files = sorted(args.processed_dir.glob("*_summary.jsonl"))
    if not files:
        raise SystemExit(f"no *_summary.jsonl files in {args.processed_dir}")
    for path in files:
        count = migrate_file(path)
        print(f"migrated {path.name}: {count} rows")


if __name__ == "__main__":
    main()
