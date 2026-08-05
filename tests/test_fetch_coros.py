import importlib.util
import json
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "fetch_coros.py"


def _load_fetch_module():
    scripts_dir = SCRIPT.parent
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    spec = importlib.util.spec_from_file_location("fetch_coros_under_test", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


fetch_coros = _load_fetch_module()


VALID_ENTRY = {
    "labelId": "479396244626636805",
    "sportType": 100,
    "date": "2026-08-04",
    "url": "https://s3.coros.com/fit/452218867308052480/479396244626636805.fit",
    "latitude": 40.811001,
    "longitude": -73.954002,
}


def test_parse_manifest_accepts_valid_entry():
    entries = fetch_coros.parse_manifest(json.dumps([VALID_ENTRY]))
    assert len(entries) == 1
    assert entries[0]["labelId"] == "479396244626636805"
    assert entries[0]["sportType"] == 100
    assert entries[0]["latitude"] == 40.811001


def test_parse_manifest_allows_missing_coordinates():
    entry = {k: v for k, v in VALID_ENTRY.items() if k not in ("latitude", "longitude")}
    entries = fetch_coros.parse_manifest(json.dumps([entry]))
    assert entries[0]["latitude"] is None
    assert entries[0]["longitude"] is None


def test_parse_manifest_rejects_non_list():
    with pytest.raises(fetch_coros.ManifestError):
        fetch_coros.parse_manifest(json.dumps(VALID_ENTRY))


def test_parse_manifest_rejects_invalid_json():
    with pytest.raises(fetch_coros.ManifestError):
        fetch_coros.parse_manifest("{not json")


@pytest.mark.parametrize("missing", ["labelId", "sportType", "date", "url"])
def test_parse_manifest_rejects_missing_required_field(missing):
    entry = {k: v for k, v in VALID_ENTRY.items() if k != missing}
    with pytest.raises(fetch_coros.ManifestError):
        fetch_coros.parse_manifest(json.dumps([entry]))


def test_parse_manifest_rejects_non_https_url():
    entry = dict(VALID_ENTRY, url="ftp://s3.coros.com/x.fit")
    with pytest.raises(fetch_coros.ManifestError):
        fetch_coros.parse_manifest(json.dumps([entry]))


def test_parse_manifest_rejects_label_id_with_path_separator():
    entry = dict(VALID_ENTRY, labelId="../../etc/passwd")
    with pytest.raises(fetch_coros.ManifestError):
        fetch_coros.parse_manifest(json.dumps([entry]))
