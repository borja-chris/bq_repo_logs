import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "migrate_processed_slim.py"


def _load_migrate_module():
    scripts_dir = SCRIPT.parent
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    spec = importlib.util.spec_from_file_location("migrate_processed_slim_under_test", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module

def test_migration_slims_rows_and_preserves_identity(tmp_path):
    row = {
        "activity_id": "1", "source_file": "1.fit", "source_sha256": "sha1",
        "source_relpath": "/tmp/x/1.fit", "import_batch": "x",
        "start_time": "2026-07-20T17:25:54-04:00", "start_time_raw": "r",
        "start_time_utc": "u", "start_time_resolution": "res",
        "start_timezone": "America/New_York", "start_lat": "40.8",
        "start_lon": "-73.9", "sport": "running", "sub_sport": "",
        "distance_mi": "5.57", "duration_s": "3586", "avg_hr": "141",
        "max_hr": "161", "ascent_m": "66", "weather_temp_c": "28.7",
        "weather_temp_f": "83.7", "weather_dew_point_f": "49.0",
        "parser": "fitdecode", "parse_error": "", "weather_fetch_error": "",
    }
    src = tmp_path / "coros_export_2026-07-23_summary.jsonl"
    src.write_text(json.dumps(row) + "\n")
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--processed-dir", str(tmp_path)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    migrated = [json.loads(l) for l in src.read_text().splitlines()]
    assert len(migrated) == 1
    assert migrated[0]["source_sha256"] == "sha1"
    assert migrated[0]["distance_mi"] == "5.57"
    assert "source_relpath" not in migrated[0]
    assert "weather_temp_c" not in migrated[0]
    assert "parse_error" not in migrated[0]


def test_migrate_file_aborts_on_row_corruption_and_leaves_file_unchanged(tmp_path, monkeypatch):
    row = {
        "activity_id": "1", "source_file": "1.fit", "source_sha256": "sha1",
        "source_relpath": "/tmp/x/1.fit", "import_batch": "x",
        "start_time": "2026-07-20T17:25:54-04:00", "start_time_raw": "r",
        "start_time_utc": "u", "start_time_resolution": "res",
        "start_timezone": "America/New_York", "start_lat": "40.8",
        "start_lon": "-73.9", "sport": "running", "sub_sport": "",
        "distance_mi": "5.57", "duration_s": "3586", "avg_hr": "141",
        "max_hr": "161", "ascent_m": "66", "weather_temp_c": "28.7",
        "weather_temp_f": "83.7", "weather_dew_point_f": "49.0",
        "parser": "fitdecode", "parse_error": "", "weather_fetch_error": "",
    }
    src = tmp_path / "coros_export_2026-07-23_summary.jsonl"
    original_text = json.dumps(row) + "\n"
    src.write_text(original_text)

    module = _load_migrate_module()
    real_slim_row = module.slim_row

    def corrupting_slim_row(r):
        # Corrupt an identity field (activity_id) without touching
        # source_sha256 -- this is exactly the kind of corruption the old
        # (dead-code row-count / tautological source_sha256-set) checks
        # could never have detected, since source_sha256 is untouched and
        # the row count is unchanged.
        out = real_slim_row(r)
        out["activity_id"] = "CORRUPTED"
        return out

    monkeypatch.setattr(module, "slim_row", corrupting_slim_row)

    with pytest.raises(SystemExit):
        module.migrate_file(src)

    # The temp-file-then-replace approach means a failed verification must
    # never touch the original record.
    assert src.read_text() == original_text
    assert not src.with_name(src.name + ".tmp").exists()
