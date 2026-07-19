from __future__ import annotations

# Reconciliation check: every rendered weekly log's "Actual mileage so far" should
# equal the sum of distance_mi for that week's activities in the processed data.
# Historical logs can silently drift from the source (e.g. a stale mid-week snapshot
# that was never re-rendered), and that drift is otherwise only noticed by accident
# during an unrelated full re-render. Run this to catch it deliberately.

import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parent.parent
WEEKLY_DIR = REPO_ROOT / "logs" / "weekly"
LOGGED_RE = re.compile(r"Actual mileage so far: `([\d.]+)`")


@dataclass
class Result:
    week_start: date
    logged: float | None
    expected: float

    @property
    def matches(self) -> bool:
        if self.logged is None:
            return False
        return round(self.logged, 2) == round(self.expected, 2)


def parse_logged_mileage(text: str) -> float | None:
    match = LOGGED_RE.search(text)
    return float(match.group(1)) if match else None


def reconcile_week(week_start: date, weekly_text: str, activities: Iterable[object]) -> Result:
    logged = parse_logged_mileage(weekly_text)
    expected = round(sum(float(activity.distance_mi) for activity in activities), 2)
    return Result(week_start=week_start, logged=logged, expected=expected)


def format_result(result: Result) -> str:
    logged = "missing" if result.logged is None else f"{result.logged:.2f}"
    return f"{result.week_start.isoformat()}: logged {logged} != expected {result.expected:.2f}"


def week_start_from_path(path: Path) -> date:
    return date.fromisoformat(path.stem.removeprefix("week_"))


def reconcile_all() -> list[Result]:
    # Imported here so the pure functions above stay importable without the pipeline
    # (and its parser dependencies) being loadable in the interpreter.
    import ingest_coros_fit_weather as weather

    results: list[Result] = []
    for path in sorted(WEEKLY_DIR.glob("week_*.md")):
        week_start = week_start_from_path(path)
        activities = weather.load_processed_activities_for_week(week_start)
        results.append(reconcile_week(week_start, path.read_text(), activities))
    return results


def main() -> int:
    results = reconcile_all()
    mismatches = [result for result in results if not result.matches]
    if not mismatches:
        print(f"OK: {len(results)} weekly logs reconcile with processed data.")
        return 0
    print(f"MISMATCH: {len(mismatches)} of {len(results)} weekly logs disagree with processed data:")
    for mismatch in mismatches:
        print(f"  - {format_result(mismatch)}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
