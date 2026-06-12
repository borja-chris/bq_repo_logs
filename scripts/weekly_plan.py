from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLAN_DIR = REPO_ROOT / "plans" / "2026-half-marathon"
PRE_BLOCK_PLAN_PATH = PLAN_DIR / "01_pre_block_ramp.md"


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


def parse_pre_block_week(target_week: date) -> WeekPlan | None:
    text = PRE_BLOCK_PLAN_PATH.read_text()
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
    week_path = PLAN_DIR / f"week_{target_week.isoformat()}.md"
    if not week_path.exists():
        candidates = sorted(PLAN_DIR.glob("week_*_*.md"))
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
