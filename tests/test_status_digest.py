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

def test_fails_loud_on_unparseable_block(tmp_path):
    (tmp_path / "logs" / "weekly").mkdir(parents=True)
    (tmp_path / "logs" / "weekly" / "week_2026-07-20.md").write_text("# broken\n")
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--repo-root", str(tmp_path), "--today", "2026-07-23"],
        capture_output=True, text=True,
    )
    assert result.returncode != 0
