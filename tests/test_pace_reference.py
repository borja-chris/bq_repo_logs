"""README Pace Reference block is generated from 03_framework.md's Pace Guide."""

import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import weekly_entries as we  # noqa: E402

FRAMEWORK = """# Framework

## Pace Guide

Intro text.

| Run Type | Pace | Basis |
| --- | --- | --- |
| Recovery | 11:00-11:45/mi | Slow |
| Easy aerobic | 10:30-11:30/mi | Band |
| Long run | 9:30-11:00/mi | Mostly easy |
| Half-marathon pace (HMP) | 8:33-8:43/mi | Anchor |
| Threshold (~1-hr effort) | 8:15-8:38/mi | Hard |
| Strength reps | 8:28-8:38/mi | HMP - 10s |
| Speed reps | 7:36-8:05/mi | 5K |

| Other | Table | Here |
| --- | --- | --- |
| x | y | z |

## Next
"""

README = """# T

## Current Week

<!-- current-week:start -->
cw
<!-- current-week:end -->

## Workflow

wf
"""


def test_parse_rows_verbatim():
    rows = we.parse_pace_table(FRAMEWORK)
    assert len(rows) == 7
    assert rows[0] == ("Recovery", "11:00-11:45/mi")
    assert rows[3] == ("Half-marathon pace (HMP)", "8:33-8:43/mi")
    assert rows[6] == ("Speed reps", "7:36-8:05/mi")


def test_build_body():
    body = we.build_pace_reference(FRAMEWORK)
    lines = body.splitlines()
    assert lines[0] == "Source: [03_framework.md](plans/2026-half-marathon/03_framework.md#pace-guide)"
    assert "| Run Type | Pace |" in lines
    assert "| --- | --- |" in lines
    assert "| Strength reps | 8:28-8:38/mi |" in lines
    assert "Basis" not in body
    assert body.endswith("Hansons tempo runs are run at HMP. Rep target times and recovery jogs: see the source.")


@pytest.mark.parametrize("text", ["# no guide\n", "## Pace Guide\n\nno table here\n\n## Next\n"])
def test_missing_table_raises(text):
    with pytest.raises(SystemExit):
        we.parse_pace_table(text)


def test_missing_framework_file_raises(tmp_path, monkeypatch):
    monkeypatch.setattr(we, "FRAMEWORK_PATH", tmp_path / "nope.md")
    monkeypatch.setattr(we, "README_PATH", tmp_path / "README.md")
    (tmp_path / "README.md").write_text(README)
    with pytest.raises(SystemExit):
        we.update_pace_reference()
    assert (tmp_path / "README.md").read_text() == README


def test_inserts_section_before_workflow_and_is_idempotent(tmp_path, monkeypatch):
    fw = tmp_path / "fw.md"
    fw.write_text(FRAMEWORK)
    readme = tmp_path / "README.md"
    readme.write_text(README)
    monkeypatch.setattr(we, "FRAMEWORK_PATH", fw)
    monkeypatch.setattr(we, "README_PATH", readme)
    we.update_pace_reference()
    first = readme.read_text()
    assert first.index("## Current Week") < first.index("## Pace Reference") < first.index("## Workflow")
    assert first.index("<!-- pace-reference:start -->") < first.index("| Recovery | 11:00-11:45/mi |")
    assert "cw\n" in first and "wf\n" in first
    we.update_pace_reference()
    assert readme.read_text() == first


def test_existing_block_replaced(tmp_path, monkeypatch):
    fw = tmp_path / "fw.md"
    fw.write_text(FRAMEWORK)
    readme = tmp_path / "README.md"
    readme.write_text(README)
    monkeypatch.setattr(we, "FRAMEWORK_PATH", fw)
    monkeypatch.setattr(we, "README_PATH", readme)
    we.update_pace_reference()
    fw.write_text(FRAMEWORK.replace("11:00-11:45/mi", "11:10-11:50/mi"))
    we.update_pace_reference()
    out = readme.read_text()
    assert "11:10-11:50/mi" in out and "11:00-11:45/mi" not in out
    assert out.count("<!-- pace-reference:start -->") == 1
