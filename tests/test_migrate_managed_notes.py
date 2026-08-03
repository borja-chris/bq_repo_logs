import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "migrate_managed_notes.py"


def _load_migrate_module():
    scripts_dir = SCRIPT.parent
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    spec = importlib.util.spec_from_file_location("migrate_managed_notes_under_test", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


VERBOSE = """### 2026-07-20

- Planned: Off or 3 mi very easy
- Completed: 5.57 mi run
- Time: 59:46
- Distance: 5.57 mi
- Pace: 10:44/mi
- Effort: imported
- Managed Notes:
  - Imported from `data/coros_exports/COROS_export_2026-07-23/479051765975646409.fit`.
  - FIT summary: start `2026-07-20T17:25:54-04:00`, avg HR `141`, max HR `161`, ascent `66 m`.
  - Weather at start: `83.7 F` at `2026-07-20T17:00` from `open-meteo`.
  - Heat: 84°F + 49°F dew = 133 (moderate). Heat-neutral equivalent ~10:28/mi (ran 10:44/mi, ~+2.5%).
- Manual Notes:
  - Felt heavy but fine.
- Sleep: 7h
- Soreness: calves tight
- Stress: low
- Warning signs:
"""
# Real weekly logs carry a trailing space on the (blank-valued)
# '- Warning signs:' line -- confirmed by the task-11 brief fixture itself
# (byte-verified with `od -c` against the brief source) and independently by
# reading logs/weekly/week_2026-07-20.md READ-ONLY, where every blank
# '- Warning signs: ' line in the file carries the same trailing space.
# Round 1 lost this: a later full-file rewrite of this test module silently
# dropped the trailing space that an earlier fix had restored, and the
# round-1 report's claim that it had been byte-verified was therefore false
# for the *shipped* file (see the "Fix round 2" section of the task report
# for the correction). Injecting it here via .replace() rather than a
# literal trailing space at the end of a source line means an editor's
# automatic trailing-whitespace stripping cannot silently erase it again.
VERBOSE = VERBOSE.replace("- Warning signs:\n", "- Warning signs: \n")
assert VERBOSE.endswith("- Warning signs: \n")

# Real shape (constructed as a fixture -- not read from the repo file) of the
# 3-activity Managed Notes block found in logs/weekly/week_2026-07-06.md: a
# single day with three separate imported runs, each with its own
# Imported/FIT/Weather/Heat quadruple, all nested under one '- Managed Notes:'
# header. This is the exact shape that the old joined-regex-over-the-whole-
# block implementation collapsed to a single line, silently dropping the
# other two activities' provenance.
MULTI_IMPORT = """### 2026-07-11

- Planned: 3x1 mile repeats
- Completed: 12.2 mi total (3 runs)
- Time: 1:47:00
- Distance: 12.2 mi
- Pace: 8:45/mi
- Effort: imported
- Managed Notes:
  - Imported from `data/coros_exports/COROS_export_2026-07-11/478830233435275571.fit`.
  - FIT summary: start `2026-07-11T08:54:33-04:00`, avg HR `141`, max HR `164`, ascent `2 m`.
  - Weather at start: `70.9 F` at `2026-07-11T08:00` from `open-meteo`.
  - Heat: 71°F + 69°F dew = 140 (moderate). Heat-neutral equivalent ~8:57/mi (ran 9:10/mi, ~+2.5%).
  - Imported from `data/coros_exports/COROS_export_2026-07-11/478830233435275572.fit`.
  - FIT summary: start `2026-07-11T09:05:19-04:00`, avg HR `168`, max HR `188`, ascent `20 m`.
  - Weather at start: `73.8 F` at `2026-07-11T09:00` from `open-meteo`.
  - Heat: 74°F + 70°F dew = 144 (heavy). Heat-neutral equivalent ~7:50/mi (ran 8:08/mi, ~+3.8%).
  - Imported from `data/coros_exports/COROS_export_2026-07-11/478830233435275573.fit`.
  - FIT summary: start `2026-07-11T09:41:28-04:00`, avg HR `148`, max HR `154`, ascent `2 m`.
  - Weather at start: `73.8 F` at `2026-07-11T09:00` from `open-meteo`.
  - Heat: 74°F + 70°F dew = 144 (heavy). Heat-neutral equivalent ~11:38/mi (ran 12:04/mi, ~+3.8%).
- Manual Notes:
  - Planned parkrun 5k. Mon-Wed quality was front-loaded (7/7 mile repeats, 7/8 longer run) to arrive fresh; Thu-Fri kept easy.
  - Parkrun 5k result (own FIT, 478830233435275572): 3.06 mi in 24:53, 8:08/mi, avg HR 168 / max 188.
- Sleep:
- Soreness:
- Stress:
- Warning signs:
"""
# Same real-shape trailing-space fix as VERBOSE above, applied to the four
# blank manual-section fields (also confirmed against
# logs/weekly/week_2026-07-20.md read-only: blank '- Sleep: ', '- Soreness: ',
# '- Stress: ', and '- Warning signs: ' lines all carry one trailing space).
for _blank_field in ("Sleep", "Soreness", "Stress", "Warning signs"):
    MULTI_IMPORT = MULTI_IMPORT.replace(f"- {_blank_field}:\n", f"- {_blank_field}: \n")
assert MULTI_IMPORT.endswith("- Warning signs: \n")

# Dedicated fixture for the trailing-whitespace regression (fix round 2,
# Finding 2b): one real activity (so the Managed Notes block is actually
# compacted, exercising the real code path) plus every blank manual-section
# field in the real trailing-space shape confirmed above, including the
# blank '  - ' Manual Notes bullet itself.
TRAILING_WS_FIXTURE = """### 2026-07-21

- Planned: Off
- Completed: 3.1 mi run
- Time: 30:00
- Distance: 3.1 mi
- Pace: 9:40/mi
- Effort: imported
- Managed Notes:
  - Imported from `data/coros_exports/COROS_export_2026-07-23/000000000000000001.fit`.
  - FIT summary: start `2026-07-21T07:00:00-04:00`, avg HR `130`, max HR `150`, ascent `10 m`.
- Manual Notes:
  -
- Sleep:
- Soreness:
- Stress:
- Warning signs:
"""
TRAILING_WS_FIXTURE = (
    TRAILING_WS_FIXTURE
    .replace("  -\n", "  - \n")
    .replace("- Sleep:\n", "- Sleep: \n")
    .replace("- Soreness:\n", "- Soreness: \n")
    .replace("- Stress:\n", "- Stress: \n")
    .replace("- Warning signs:\n", "- Warning signs: \n")
)
assert "  - \n" in TRAILING_WS_FIXTURE
assert TRAILING_WS_FIXTURE.endswith("- Warning signs: \n")


def test_compacts_managed_notes_and_touches_nothing_else(tmp_path):
    log = tmp_path / "week_2026-07-20.md"
    log.write_text(VERBOSE, encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--weekly-dir", str(tmp_path)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    text = log.read_text(encoding="utf-8")
    assert text.count("  - Imported 479051765975646409.fit | start 17:25 | HR 141/161 | asc 66m | 84°F + 49°F dew = 133 (moderate). Heat-neutral equivalent ~10:28/mi (ran 10:44/mi, ~+2.5%)") == 1
    assert "FIT summary" not in text
    # every non-managed line byte-identical
    def strip_managed(source):
        keep, in_managed = [], False
        for line in source.splitlines():
            if line == "- Managed Notes:":
                in_managed = True
                keep.append(line)
            elif in_managed and line.startswith("  - "):
                continue
            else:
                in_managed = False
                keep.append(line)
        return keep
    assert strip_managed(VERBOSE) == strip_managed(text)


def test_idempotent(tmp_path):
    log = tmp_path / "week_2026-07-20.md"
    log.write_text(VERBOSE, encoding="utf-8")
    subprocess.run([sys.executable, str(SCRIPT), "--weekly-dir", str(tmp_path)], check=True)
    once = log.read_text(encoding="utf-8")
    subprocess.run([sys.executable, str(SCRIPT), "--weekly-dir", str(tmp_path)], check=True)
    assert log.read_text(encoding="utf-8") == once


def test_compacts_multiple_activities_in_one_block(tmp_path):
    log = tmp_path / "week_2026-07-06.md"
    log.write_text(MULTI_IMPORT, encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--weekly-dir", str(tmp_path)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    text = log.read_text(encoding="utf-8")

    original_imported_from_count = MULTI_IMPORT.count("- Imported from `")
    assert original_imported_from_count == 3

    imported_lines = [line for line in text.splitlines() if line.startswith("  - Imported ")]
    assert len(imported_lines) == 3
    assert len(imported_lines) == original_imported_from_count
    assert imported_lines == [
        "  - Imported 478830233435275571.fit | start 08:54 | HR 141/164 | asc 2m | "
        "71°F + 69°F dew = 140 (moderate). Heat-neutral equivalent ~8:57/mi (ran 9:10/mi, ~+2.5%)",
        "  - Imported 478830233435275572.fit | start 09:05 | HR 168/188 | asc 20m | "
        "74°F + 70°F dew = 144 (heavy). Heat-neutral equivalent ~7:50/mi (ran 8:08/mi, ~+3.8%)",
        "  - Imported 478830233435275573.fit | start 09:41 | HR 148/154 | asc 2m | "
        "74°F + 70°F dew = 144 (heavy). Heat-neutral equivalent ~11:38/mi (ran 12:04/mi, ~+3.8%)",
    ]
    assert "FIT summary" not in text

    # Manual Notes (and everything else outside Managed Notes) untouched.
    def strip_managed(source):
        keep, in_managed = [], False
        for line in source.splitlines():
            if line == "- Managed Notes:":
                in_managed = True
                keep.append(line)
            elif in_managed and line.startswith("  - "):
                continue
            else:
                in_managed = False
                keep.append(line)
        return keep
    assert strip_managed(MULTI_IMPORT) == strip_managed(text)


def test_multi_import_block_is_idempotent(tmp_path):
    log = tmp_path / "week_2026-07-06.md"
    log.write_text(MULTI_IMPORT, encoding="utf-8")
    subprocess.run([sys.executable, str(SCRIPT), "--weekly-dir", str(tmp_path)], check=True)
    once = log.read_text(encoding="utf-8")
    subprocess.run([sys.executable, str(SCRIPT), "--weekly-dir", str(tmp_path)], check=True)
    assert log.read_text(encoding="utf-8") == once


def test_migrate_file_aborts_on_corrupt_compaction_and_leaves_file_unchanged(tmp_path, monkeypatch):
    log = tmp_path / "week_2026-07-06.md"
    log.write_text(MULTI_IMPORT, encoding="utf-8")

    module = _load_migrate_module()

    def corrupting_compact(block):
        # Simulate exactly the bug this fix-round addresses: collapse a
        # multi-activity block down to just its first line, silently
        # dropping the rest of the activities' provenance.
        return [block[0]]

    monkeypatch.setattr(module, "compact", corrupting_compact)

    with pytest.raises(SystemExit):
        module.migrate_file(log)

    # The temp-write-verify-then-replace approach means a failed
    # verification must never touch the original file, and must never leave
    # a stray .tmp sibling behind.
    assert log.read_text(encoding="utf-8") == MULTI_IMPORT
    assert not log.with_name(log.name + ".tmp").exists()


def test_verify_migration_catches_merge_and_duplicate_with_balanced_count(tmp_path, monkeypatch):
    # Fix round 2, Finding 1 regression: a bare activity COUNT check is not
    # enough. Build a file with two Managed Notes blocks -- day A has 2
    # activities, day B has 1 -- then corrupt the compaction so day A's two
    # activities are merged into a single line (losing one) while day B's
    # one activity is duplicated into two lines (gaining one). The total
    # "- Imported " count across the file is unchanged (3 -> 3), which the
    # old count-only check would have accepted, but the ORDERED per-activity
    # identity sequence is corrupted (an activity vanished and another was
    # duplicated), which the new check must catch.
    two_block_text = """### 2026-07-13

- Planned: 2x2 mile repeats
- Completed: 8 mi total (2 runs)
- Time: 1:10:00
- Distance: 8 mi
- Pace: 8:45/mi
- Effort: imported
- Managed Notes:
  - Imported from `data/coros_exports/COROS_export_2026-07-13/500000000000000001.fit`.
  - FIT summary: start `2026-07-13T08:00:00-04:00`, avg HR `140`, max HR `160`, ascent `10 m`.
  - Imported from `data/coros_exports/COROS_export_2026-07-13/500000000000000002.fit`.
  - FIT summary: start `2026-07-13T09:00:00-04:00`, avg HR `150`, max HR `170`, ascent `15 m`.
- Manual Notes:
  -
- Sleep:
- Soreness:
- Stress:
- Warning signs:

### 2026-07-14

- Planned: 4 mi easy
- Completed: 4 mi run
- Time: 40:00
- Distance: 4 mi
- Pace: 10:00/mi
- Effort: imported
- Managed Notes:
  - Imported from `data/coros_exports/COROS_export_2026-07-14/500000000000000003.fit`.
  - FIT summary: start `2026-07-14T07:00:00-04:00`, avg HR `135`, max HR `155`, ascent `5 m`.
- Manual Notes:
  -
- Sleep:
- Soreness:
- Stress:
- Warning signs:
"""
    original_imported_from_count = two_block_text.count("- Imported from `")
    assert original_imported_from_count == 3

    log = tmp_path / "week_2026-07-13.md"
    log.write_text(two_block_text, encoding="utf-8")

    module = _load_migrate_module()
    real_compact = module.compact

    def corrupting_compact(block):
        imported_count = sum(1 for line in block if module.IMPORTED.search(line))
        if imported_count == 2:
            # Merge: only compact the FIRST of the two activities, silently
            # dropping the second.
            _preamble, segments = module._segment_block(block)
            return module._compact_segment(segments[0])
        if imported_count == 1:
            # Duplicate: emit the single activity's compact line twice.
            compacted = real_compact(block)
            return compacted + [compacted[0]]
        return real_compact(block)

    monkeypatch.setattr(module, "compact", corrupting_compact)

    # Sanity-check the premise: with this corruption, the total activity
    # COUNT in the migrated text is unchanged (one dropped + one
    # duplicated), so a count-only check would have let this through.
    migrated = module.migrate_text(two_block_text)
    new_imported_lines = [line for line in migrated.splitlines() if line.startswith("  - Imported ")]
    assert len(new_imported_lines) == original_imported_from_count == 3

    with pytest.raises(SystemExit):
        module.migrate_file(log)

    assert log.read_text(encoding="utf-8") == two_block_text
    assert not log.with_name(log.name + ".tmp").exists()


def test_trailing_whitespace_on_non_managed_lines_survives_migration(tmp_path):
    # Fix round 2, Finding 2b: real weekly logs carry a trailing space on
    # blank manual-section fields (verified read-only against
    # logs/weekly/week_2026-07-20.md). This must fail if the migration -- or
    # anything it calls -- ever adds an .rstrip() to a passthrough line.
    log = tmp_path / "week_2026-07-21.md"
    log.write_text(TRAILING_WS_FIXTURE, encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--weekly-dir", str(tmp_path)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    migrated = log.read_text(encoding="utf-8")
    assert "FIT summary" not in migrated  # confirm compaction actually ran
    for expected_line in (
        "  - \n",
        "- Sleep: \n",
        "- Soreness: \n",
        "- Stress: \n",
        "- Warning signs: \n",
    ):
        assert expected_line in migrated, f"trailing whitespace lost on: {expected_line!r}"
