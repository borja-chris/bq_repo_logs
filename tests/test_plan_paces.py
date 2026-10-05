"""Every run in a not-yet-finished plan week must carry a numeric pace.

The README current-week block is rendered from the week files' Run cells and
is the operator's in-week landing page, so labels like "easy" or "near HMP"
without a /mi pace are not enough.
"""

import sys
from datetime import date, timedelta
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import weekly_plan  # noqa: E402


def test_open_weeks_have_numeric_paces():
    current_monday = date.today() - timedelta(days=date.today().weekday())
    missing = []
    for path in sorted(weekly_plan.WEEKS_DIR.glob("week_*.md")):
        week_start = date.fromisoformat(path.stem.removeprefix("week_"))
        if week_start < current_monday:
            continue
        plan = weekly_plan.parse_week_file(week_start)
        for day in plan.day_plans:
            if day.planned.strip().lower() == "off":
                continue
            if "/mi" not in day.planned:
                missing.append(f"{path.name} {day.day_name}: {day.planned}")
    assert not missing, "Run cells without a numeric pace:\n" + "\n".join(missing)
