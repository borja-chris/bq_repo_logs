from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import ingest_coros_fit_weather as weather  # noqa: E402
import ingest_coros_fit_batch as batch  # noqa: E402
import repair_processed_duplicates as repair  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent

DUP_ACTIVITY_ID = "478263554103869447"


def _row(activity_id: str, source_file: str, start_time: str = "2026-06-16T17:53:59-04:00") -> dict[str, str]:
    return {
        "activity_id": activity_id,
        "ascent_m": "100",
        "avg_hr": "147",
        "distance_mi": "8.37",
        "duration_s": "5515",
        "max_hr": "165",
        "parser": "fitdecode",
        "source_file": source_file,
        "source_sha256": "ea552b8819642c033359c4d3af0b108da5b9c0bf236e3fbea9b965fe8115f051",
        "sport": "running",
        "start_lat": "40.811329",
        "start_lon": "-73.954178",
        "start_time": start_time,
        "start_timezone": "America/New_York",
    }


def _write_jsonl(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")


# ---------------------------------------------------------------------------
# Task 1: read-time dedup in load_processed_activities_for_week
# ---------------------------------------------------------------------------


def test_load_processed_activities_for_week_dedups_across_files(tmp_path, monkeypatch):
    monkeypatch.setattr(weather, "REPO_ROOT", tmp_path)
    processed_dir = tmp_path / "data" / "processed"

    # Sorted-filename order: the 06-17 file (first import) sorts before the
    # 06-21 file (the re-export) — this mirrors the real repo duplicate.
    _write_jsonl(
        processed_dir / "coros_export_2026-06-17_summary.jsonl",
        [_row(DUP_ACTIVITY_ID, source_file="first.fit")],
    )
    _write_jsonl(
        processed_dir / "coros_export_2026-06-21_summary.jsonl",
        [_row(DUP_ACTIVITY_ID, source_file="second.fit")],
    )

    activities = weather.load_processed_activities_for_week(date(2026, 6, 15))

    assert len(activities) == 1
    assert activities[0].row["activity_id"] == DUP_ACTIVITY_ID
    assert activities[0].row["source_file"] == "first.fit"


def test_load_processed_activities_for_week_keeps_distinct_activities(tmp_path, monkeypatch):
    monkeypatch.setattr(weather, "REPO_ROOT", tmp_path)
    processed_dir = tmp_path / "data" / "processed"

    _write_jsonl(
        processed_dir / "coros_export_2026-06-17_summary.jsonl",
        [_row(DUP_ACTIVITY_ID, source_file="first.fit")],
    )
    _write_jsonl(
        processed_dir / "coros_export_2026-06-18_summary.jsonl",
        [_row("478999999999999999", source_file="other.fit", start_time="2026-06-17T08:00:00-04:00")],
    )

    activities = weather.load_processed_activities_for_week(date(2026, 6, 15))

    assert len(activities) == 2
    assert {a.row["activity_id"] for a in activities} == {DUP_ACTIVITY_ID, "478999999999999999"}


# ---------------------------------------------------------------------------
# Task 2: ingest-time dedup in generate_summaries
# ---------------------------------------------------------------------------


def test_generate_summaries_skips_activity_id_already_in_other_processed_file(tmp_path, monkeypatch):
    monkeypatch.setattr(batch, "REPO_ROOT", tmp_path)

    # An activity already imported into a different processed file.
    existing_path = tmp_path / "data" / "processed" / "coros_export_2026-06-17_summary.jsonl"
    _write_jsonl(existing_path, [_row(DUP_ACTIVITY_ID, source_file="dup.fit")])

    export_dir = tmp_path / "data" / "coros_exports" / "COROS_export_2026-06-21"
    export_dir.mkdir(parents=True)
    (export_dir / "dup.fit").write_bytes(b"")
    (export_dir / "new.fit").write_bytes(b"")

    canned_rows = [
        _row(DUP_ACTIVITY_ID, source_file="dup.fit"),
        _row("478111111111111111", source_file="new.fit", start_time="2026-06-21T09:00:00-04:00"),
    ]

    def fake_parse_fit_files(fit_files):
        return canned_rows

    monkeypatch.setattr(batch.summarize, "parse_fit_files", fake_parse_fit_files)

    output_jsonl, rows = batch.generate_summaries(export_dir)

    assert [row["activity_id"] for row in rows] == ["478111111111111111"]

    written = [json.loads(line) for line in output_jsonl.read_text().splitlines() if line.strip()]
    assert [row["activity_id"] for row in written] == ["478111111111111111"]


def test_generate_summaries_keeps_all_rows_when_no_duplicates(tmp_path, monkeypatch):
    monkeypatch.setattr(batch, "REPO_ROOT", tmp_path)

    export_dir = tmp_path / "data" / "coros_exports" / "COROS_export_2026-06-21"
    export_dir.mkdir(parents=True)
    (export_dir / "new.fit").write_bytes(b"")

    canned_rows = [_row("478111111111111111", source_file="new.fit", start_time="2026-06-21T09:00:00-04:00")]

    def fake_parse_fit_files(fit_files):
        return canned_rows

    monkeypatch.setattr(batch.summarize, "parse_fit_files", fake_parse_fit_files)

    output_jsonl, rows = batch.generate_summaries(export_dir)

    assert [row["activity_id"] for row in rows] == ["478111111111111111"]


# ---------------------------------------------------------------------------
# Task 3: repo-data invariant — every real activity_id appears exactly once.
# Expected to FAIL until scripts/repair_processed_duplicates.py --apply has
# been run against the real repo data (task 4).
# ---------------------------------------------------------------------------


def test_all_real_processed_activity_ids_are_unique():
    processed_dir = REPO_ROOT / "data" / "processed"
    occurrences: dict[str, list[str]] = {}
    for path in sorted(processed_dir.glob("*.jsonl")):
        with path.open() as handle:
            for index, raw_line in enumerate(handle, start=1):
                raw_line = raw_line.strip()
                if not raw_line:
                    continue
                row = json.loads(raw_line)
                activity_id = row.get("activity_id", "")
                if not activity_id:
                    continue
                occurrences.setdefault(activity_id, []).append(f"{path.name}:{index}")

    duplicates = {aid: locs for aid, locs in occurrences.items() if len(locs) > 1}
    assert duplicates == {}, f"Duplicate activity_id rows found: {duplicates}"


# ---------------------------------------------------------------------------
# Task 4: scripts/repair_processed_duplicates.py
# ---------------------------------------------------------------------------


def test_repair_dry_run_reports_without_modifying(tmp_path):
    processed_dir = tmp_path / "data" / "processed"
    first_path = processed_dir / "coros_export_2026-06-17_summary.jsonl"
    second_path = processed_dir / "coros_export_2026-06-21_summary.jsonl"
    _write_jsonl(first_path, [_row(DUP_ACTIVITY_ID, source_file="first.fit")])
    _write_jsonl(
        second_path,
        [
            _row(DUP_ACTIVITY_ID, source_file="second.fit"),
            _row("478999999999999999", source_file="unique.fit", start_time="2026-06-21T09:00:00-04:00"),
        ],
    )

    removals = repair.run(processed_dir, apply_changes=False)

    assert removals == [(second_path, 1, DUP_ACTIVITY_ID)]
    # Dry run must not touch either file.
    assert len(first_path.read_text().splitlines()) == 1
    assert len(second_path.read_text().splitlines()) == 2


def test_repair_apply_removes_duplicate_and_leaves_other_file_untouched(tmp_path):
    processed_dir = tmp_path / "data" / "processed"
    first_path = processed_dir / "coros_export_2026-06-17_summary.jsonl"
    second_path = processed_dir / "coros_export_2026-06-21_summary.jsonl"
    first_content = json.dumps(_row(DUP_ACTIVITY_ID, source_file="first.fit")) + "\n"
    second_rows = [
        _row(DUP_ACTIVITY_ID, source_file="second.fit"),
        _row("478999999999999999", source_file="unique.fit", start_time="2026-06-21T09:00:00-04:00"),
    ]
    first_path.parent.mkdir(parents=True, exist_ok=True)
    first_path.write_text(first_content)
    _write_jsonl(second_path, second_rows)

    removals = repair.run(processed_dir, apply_changes=True)

    assert removals == [(second_path, 1, DUP_ACTIVITY_ID)]
    # First file (holding the kept, first occurrence) is byte-for-byte untouched.
    assert first_path.read_text() == first_content
    remaining = [json.loads(line) for line in second_path.read_text().splitlines() if line.strip()]
    assert [row["activity_id"] for row in remaining] == ["478999999999999999"]


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
