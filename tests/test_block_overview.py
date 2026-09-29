import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import weekly_plan  # noqa: E402
import block_overview  # noqa: E402

WEEK_1 = """# Week 1 - 2026-09-14

- Target mileage: about 30
- Primary purpose: build a stable platform

| Day | Run | Purpose | Notes |
| --- | --- | --- | --- |
| Monday | 4 mi easy | Recovery | Keep breathing easy. |
| Tuesday | 5 mi easy | Easy aerobic | Aerobic support. |
| Wednesday | Off | Recovery | Normal break. |
| Thursday | 5 mi easy | Easy aerobic | Aerobic support. |
| Friday | 4 mi easy | Easy aerobic | Aerobic support. |
| Saturday | 4 mi easy | Easy aerobic | Comfortable. |
| Sunday | 8 mi | Long run | Steady, not hard. |
"""

WEEK_2 = """# Week 2 - 2026-09-21

- Target mileage: about 35
- Primary purpose: reintroduce SOS work with moderated mileage ramp

| Day | Run | Purpose | Notes |
| --- | --- | --- | --- |
| Monday | 4 mi easy | Recovery | Keep breathing easy. |
| Tuesday | 6 mi total 3 x 1 mi strength @ 8:28/mi, 400m jog recovery (~2:50) between reps | SOS - strength | Easy miles @ 10:30-11:30/mi. |
| Wednesday | Off | Recovery | Normal Hanson-style break. |
| Thursday | 7 mi total 4 mi near HMP | SOS - HMP | Smooth, even, no sprint finish. |
| Friday | 5 mi easy | Easy aerobic | Aerobic support. |
| Saturday | 4 mi easy | Easy aerobic | Comfortable. |
| Sunday | 9 mi last 2 mi steady | Long run | Steady, not hard. |
"""


def _write_weeks(tmp_path, monkeypatch, files):
    # Repoint BOTH modules' WEEKS_DIR bindings -- block_overview.iter_week_starts
    # reads its own binding, weekly_plan.parse_week_file reads its own. Both
    # must point at tmp_path or the test would silently read/write the real repo.
    weeks_dir = tmp_path / "weeks"
    weeks_dir.mkdir(parents=True)
    for name, text in files.items():
        (weeks_dir / name).write_text(text)
    monkeypatch.setattr(weekly_plan, "WEEKS_DIR", weeks_dir)
    monkeypatch.setattr(block_overview, "WEEKS_DIR", weeks_dir)
    monkeypatch.setattr(block_overview, "OVERVIEW_PATH", tmp_path / "BLOCK_OVERVIEW.md")
    return weeks_dir


def test_normal_render_lists_both_weeks_with_grid_and_arc_sections(tmp_path, monkeypatch):
    _write_weeks(
        tmp_path,
        monkeypatch,
        {
            "week_2026-09-14.md": WEEK_1,
            "week_2026-09-21.md": WEEK_2,
        },
    )
    output = block_overview.build()
    assert block_overview.GENERATED_BANNER in output
    assert "## Week Grid" in output
    assert "## Block Arc" in output
    # Both weeks should appear as numbered rows with their week-start dates.
    assert "| 1 | 2026-09-14 |" in output
    assert "| 2 | 2026-09-21 |" in output
    # Targets render (boilerplate "about"/"before" trimmed by clean_target).
    assert "| 30 |" in output
    assert "| 35 |" in output


def test_build_is_idempotent(tmp_path, monkeypatch):
    # Load-bearing: this is what makes it safe to chain block_overview.py
    # into every scripts/ingest.sh run -- re-running it from identical
    # source week files must never produce a diff-worthy change.
    _write_weeks(
        tmp_path,
        monkeypatch,
        {
            "week_2026-09-14.md": WEEK_1,
            "week_2026-09-21.md": WEEK_2,
        },
    )
    first = block_overview.build()
    second = block_overview.build()
    assert first == second


def test_main_writes_overview_file_only_under_tmp_path(tmp_path, monkeypatch):
    _write_weeks(tmp_path, monkeypatch, {"week_2026-09-14.md": WEEK_1})
    block_overview.main()
    overview_path = tmp_path / "BLOCK_OVERVIEW.md"
    assert overview_path.exists()
    assert block_overview.GENERATED_BANNER in overview_path.read_text()


def test_no_week_files_raises_system_exit(tmp_path, monkeypatch):
    # An empty weeks dir must fail loud rather than write an empty overview.
    _write_weeks(tmp_path, monkeypatch, {})
    with pytest.raises(SystemExit, match="No week files found"):
        block_overview.build()


def test_sos_day_is_bolded_and_long_run_cell_uses_purpose_tag(tmp_path, monkeypatch):
    _write_weeks(tmp_path, monkeypatch, {"week_2026-09-21.md": WEEK_2})
    output = block_overview.build()
    # Tuesday is "SOS - strength" -> short_tag "str", wrapped in ** by short_run.
    assert "**6 str**" in output
    # Sunday is the long run day; Block Arc's long-run column strips bold markers.
    assert "9 LR" in output
