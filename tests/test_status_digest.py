import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "status_digest.py"

WEEK = """# Week of 2026-07-20 Weekly Log

## Weekly Summary

<!-- auto-summary:start -->
- Source plan: `plans/2026-half-marathon/01_pre_block_ramp.md`
- Target mileage: `about 34-37`
- Actual mileage so far: `11.19`
- Primary purpose: build a stable platform
- Status: `Wednesday run logged`
- Days: Mon 5.57mi @10:44/mi | Wed 5.62mi @11:00/mi ⚠
- Warnings: Wed: Right calf: slight sharp pain, watch closely
<!-- auto-summary:end -->
"""

def run(tmp_path, today):
    (tmp_path / "logs" / "weekly").mkdir(parents=True)
    (tmp_path / "logs" / "weekly" / "week_2026-07-20.md").write_text(WEEK)
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--repo-root", str(tmp_path), "--today", today],
        capture_output=True, text=True,
    )

def test_writes_status_md_for_current_week(tmp_path):
    result = run(tmp_path, "2026-07-23")
    assert result.returncode == 0, result.stderr
    status = (tmp_path / "STATUS.md").read_text()
    assert "week of 2026-07-20" in status
    assert "`about 34-37`" in status and "`11.19`" in status
    assert "Right calf" in status

def test_tolerates_missing_auto_summary_block(tmp_path):
    # F6: a weekly log with no auto-summary block at all (e.g. freshly
    # scaffolded, not yet filled in) must not hard-fail the whole digest --
    # it is omitted rather than raised on. Ingest already wrote real data by
    # this point, and the operator's only manual step is dropping .fit
    # files, so a crash here would strand that data with no digest.
    (tmp_path / "logs" / "weekly").mkdir(parents=True)
    (tmp_path / "logs" / "weekly" / "week_2026-07-20.md").write_text("# broken\n")
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--repo-root", str(tmp_path), "--today", "2026-07-23"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    status = (tmp_path / "STATUS.md").read_text()
    assert "No weekly log yet for this week." in status


def test_tolerates_unparseable_week_filename_date(tmp_path):
    # F6: a week_*.md file whose stem isn't an ISO date must be skipped, not
    # crash the whole digest -- the current week's real file should still be
    # picked up and reported normally.
    (tmp_path / "logs" / "weekly").mkdir(parents=True)
    (tmp_path / "logs" / "weekly" / "week_2026-07-20.md").write_text(WEEK)
    (tmp_path / "logs" / "weekly" / "week_not-a-date.md").write_text("# not a real week file\n")
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--repo-root", str(tmp_path), "--today", "2026-07-23"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    status = (tmp_path / "STATUS.md").read_text()
    assert "week of 2026-07-20" in status
    assert "`11.19`" in status


def test_still_fails_loud_on_present_but_malformed_auto_summary_block(tmp_path):
    # F6 preserves this: an auto-summary block that IS present but missing a
    # required field is real corruption, not an absent block, and must
    # still abort loudly rather than silently omit or guess.
    broken_week = WEEK.replace("- Status: `Wednesday run logged`\n", "")
    assert broken_week != WEEK
    (tmp_path / "logs" / "weekly").mkdir(parents=True)
    (tmp_path / "logs" / "weekly" / "week_2026-07-20.md").write_text(broken_week)
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--repo-root", str(tmp_path), "--today", "2026-07-23"],
        capture_output=True, text=True,
    )
    assert result.returncode != 0
    assert "auto-summary missing" in result.stderr
