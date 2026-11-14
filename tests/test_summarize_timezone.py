import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from summarize_coros_fit import infer_timezone_name, normalize_start_time


def test_japan_gps_resolves_to_tokyo():
    assert infer_timezone_name("34.697163", "135.487130") == ("Asia/Tokyo", "gps_inferred")
    assert infer_timezone_name("35.711609", "139.808748") == ("Asia/Tokyo", "gps_inferred")


def test_osaka_sunday_morning_is_not_saturday_local_date():
    # 2026-10-31 21:27:06 UTC is 2026-11-01 06:27 JST, not 17:27 ET on 10-31.
    local_iso, _, _, tz_name, _ = normalize_start_time(
        "2026-10-31T21:27:06", "34.697163", "135.487130"
    )
    assert tz_name == "Asia/Tokyo"
    assert local_iso.startswith("2026-11-01T06:27:06")
