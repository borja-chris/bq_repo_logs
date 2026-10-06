import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

import backfill_laps  # noqa: E402
import ingest_coros_fit as ingest  # noqa: E402
import summarize_coros_fit as summarize  # noqa: E402
from ingest_coros_fit_weather import Activity  # noqa: E402
from weekly_entries import (  # noqa: E402
    create_weekly_day_entry,
    parse_weekly_day_entry,
    render_weekly_day_entry,
)

FIT_1001 = REPO / "data/coros_exports/COROS_export_2026-10-01/480741589981888812.fit"


def lap(distance, duration, avg="150", mx="160"):
    return {"distance_mi": f"{distance:.3f}", "duration_s": str(duration),
            "avg_hr": avg, "max_hr": mx}


def make_activity(laps):
    row = {
        "source_file": "1.fit", "start_time": "2026-10-01T17:00:00-04:00",
        "distance_mi": "7.25", "duration_s": "3600", "sport": "running",
        "avg_hr": "156", "max_hr": "190", "ascent_m": "74",
    }
    if laps is not None:
        row["laps"] = laps
    start = datetime(2026, 10, 1, 17, 0, tzinfo=ZoneInfo("America/New_York"))
    return Activity(row=row, local_start=start, local_date=start.date(),
                    timezone_name="America/New_York")


WORKOUT = [lap(3.07, 1978, "138", "162"), lap(1.0, 491, "163", "174"),
           lap(1.0, 492, "172", "180"), lap(0.16, 90, "120", "130")]
AUTO = [lap(1.0, 600), lap(1.0, 600), lap(1.0, 600), lap(0.5, 300)]


@pytest.mark.skipif(not FIT_1001.exists(), reason="archived FIT absent")
def test_extract_laps_from_real_workout_fit():
    laps = summarize.extract_laps(FIT_1001)
    assert len(laps) == 6
    assert float(laps[0]["distance_mi"]) == pytest.approx(3.07, abs=0.01)
    assert float(laps[-1]["distance_mi"]) == pytest.approx(0.16, abs=0.01)
    reps = laps[1:5]
    for rep in reps:
        assert float(rep["distance_mi"]) == pytest.approx(1.0, abs=0.02)
    paces = [round(int(r["duration_s"]) / float(r["distance_mi"])) for r in reps]
    for got, want in zip(paces, [491, 492, 476, 448]):
        assert abs(got - want) <= 4
    assert [(r["avg_hr"], r["max_hr"]) for r in reps] == [
        ("163", "174"), ("172", "180"), ("177", "182"), ("184", "193")]


@pytest.mark.skipif(not FIT_1001.exists(), reason="archived FIT absent")
def test_parse_fit_keeps_laps_through_slim_row():
    row = summarize.parse_fit(FIT_1001)
    assert len(row["laps"]) == 6
    assert len(summarize.slim_row(row)["laps"]) == 6


def test_slim_row_does_not_invent_laps_key():
    assert "laps" not in summarize.slim_row({"activity_id": "1"})


def render(laps, purpose, manual=None):
    entry = create_weekly_day_entry(datetime(2026, 10, 1).date(), "x")
    if manual:
        entry.manual_notes_lines = [manual]
    ingest.upsert_activity_entries(entry, [make_activity(laps)], purpose)
    return entry


def test_sos_day_renders_laps():
    text = render_weekly_day_entry(render(WORKOUT, "SOS - HMP reps"))
    assert "  - Laps:" in text
    assert "    1. 3.07 mi | 32:58 | 10:44/mi | HR 138/162" in text
    assert "    2. 1.00 mi | 8:11 | 8:11/mi | HR 163/174" in text


def test_non_sos_auto_mile_laps_not_rendered():
    assert "Laps:" not in render_weekly_day_entry(render(AUTO, "Easy aerobic"))
    assert "Laps:" not in render_weekly_day_entry(render([lap(3.0, 1800)], "Easy"))


def test_non_sos_manual_laps_rendered():
    text = render_weekly_day_entry(render(WORKOUT, "Easy aerobic"))
    assert "Laps:" in text


def test_no_laps_field_renders_nothing_even_on_sos():
    assert "Laps:" not in render_weekly_day_entry(render(None, "SOS - strength"))


def test_rerender_idempotent_and_manual_notes_preserved():
    entry = render(WORKOUT, "SOS - HMP", manual="  - felt strong")
    first = render_weekly_day_entry(entry)
    parsed = parse_weekly_day_entry(entry.day_date, first.splitlines())
    ingest.upsert_activity_entries(parsed, [make_activity(WORKOUT)], "SOS - HMP")
    second = render_weekly_day_entry(parsed)
    assert second == first
    assert first.count("Laps:") == 1
    assert "  - felt strong" in second


def _write_rows(tmp_path, rows, name="coros_export_2026-10-01_summary.jsonl"):
    p = tmp_path / "processed"
    p.mkdir(exist_ok=True)
    f = p / name
    f.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows))
    return p, f


@pytest.mark.skipif(not FIT_1001.exists(), reason="archived FIT absent")
def test_backfill_adds_only_laps_and_is_idempotent(tmp_path):
    exports = tmp_path / "exports" / "COROS_export_2026-10-01"
    exports.mkdir(parents=True)
    fit = exports / FIT_1001.name
    fit.write_bytes(FIT_1001.read_bytes())
    sha = hashlib.sha256(fit.read_bytes()).hexdigest()
    rows = [
        {"activity_id": "a", "source_file": fit.name, "source_sha256": sha,
         "distance_mi": "7.25", "avg_hr": "156"},
        {"activity_id": "b", "source_file": "missing.fit", "source_sha256": "zz",
         "distance_mi": "1.00"},
        {"activity_id": "c", "source_file": fit.name, "source_sha256": "badsha"},
    ]
    pdir, f = _write_rows(tmp_path, rows)
    added, skipped = backfill_laps.backfill_file(f, tmp_path / "exports")
    assert added == 1 and len(skipped) == 2
    after = [json.loads(line) for line in f.read_text().splitlines()]
    assert len(after[0].pop("laps")) == 6
    assert after == rows  # every other field of every row unchanged
    snapshot = f.read_text()
    assert backfill_laps.backfill_file(f, tmp_path / "exports")[0] == 0
    assert f.read_text() == snapshot


def test_backfill_never_overwrites_existing_laps(tmp_path):
    rows = [{"activity_id": "a", "source_file": "1.fit", "source_sha256": "s",
             "laps": [{"distance_mi": "1.000"}]}]
    _, f = _write_rows(tmp_path, rows)
    snapshot = f.read_text()
    assert backfill_laps.backfill_file(f, tmp_path / "exports") == (0, [])
    assert f.read_text() == snapshot
