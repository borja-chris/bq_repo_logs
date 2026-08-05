import hashlib
import http.client
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
    assert entries[0]["date"] == "2026-08-04"
    assert entries[0]["url"] == "https://s3.coros.com/fit/452218867308052480/479396244626636805.fit"
    assert entries[0]["latitude"] == 40.811001
    assert entries[0]["longitude"] == -73.954002


def test_parse_manifest_accepts_multiple_entries():
    second = dict(VALID_ENTRY, labelId="111222333444555666")
    entries = fetch_coros.parse_manifest(json.dumps([VALID_ENTRY, second]))
    assert len(entries) == 2
    assert entries[0]["labelId"] == "479396244626636805"
    assert entries[1]["labelId"] == "111222333444555666"


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


@pytest.mark.parametrize("bad_value", [True, "abc"])
def test_parse_manifest_rejects_non_numeric_latitude(bad_value):
    entry = dict(VALID_ENTRY, latitude=bad_value)
    with pytest.raises(fetch_coros.ManifestError):
        fetch_coros.parse_manifest(json.dumps([entry]))


@pytest.mark.parametrize("bad_value", [True, "abc"])
def test_parse_manifest_rejects_non_numeric_longitude(bad_value):
    entry = dict(VALID_ENTRY, longitude=bad_value)
    with pytest.raises(fetch_coros.ManifestError):
        fetch_coros.parse_manifest(json.dumps([entry]))


@pytest.mark.parametrize("bad_value", ["abc", []])
def test_parse_manifest_rejects_non_integer_sport_type(bad_value):
    entry = dict(VALID_ENTRY, sportType=bad_value)
    with pytest.raises(fetch_coros.ManifestError):
        fetch_coros.parse_manifest(json.dumps([entry]))


def test_parse_manifest_rejects_non_dict_entry():
    with pytest.raises(fetch_coros.ManifestError):
        fetch_coros.parse_manifest(json.dumps([1, 2, 3]))


def test_load_ledger_returns_empty_dict_when_absent(tmp_path):
    assert fetch_coros.load_ledger(tmp_path / "nope.json") == {}


def test_load_ledger_reads_existing_entries(tmp_path):
    path = tmp_path / "ledger.json"
    path.write_text(json.dumps({"123": {"date": "2026-08-04"}}), encoding="utf-8")
    assert fetch_coros.load_ledger(path)["123"]["date"] == "2026-08-04"


def test_load_ledger_raises_on_corrupt_json(tmp_path):
    path = tmp_path / "ledger.json"
    path.write_text("{broken", encoding="utf-8")
    with pytest.raises(fetch_coros.LedgerError):
        fetch_coros.load_ledger(path)


def test_load_ledger_raises_on_non_object(tmp_path):
    path = tmp_path / "ledger.json"
    path.write_text(json.dumps(["not", "an", "object"]), encoding="utf-8")
    with pytest.raises(fetch_coros.LedgerError):
        fetch_coros.load_ledger(path)


def test_save_ledger_roundtrips_and_creates_parent(tmp_path):
    path = tmp_path / "nested" / "ledger.json"
    fetch_coros.save_ledger(path, {"123": {"date": "2026-08-04"}})
    assert fetch_coros.load_ledger(path) == {"123": {"date": "2026-08-04"}}
    assert path.read_text(encoding="utf-8").endswith("\n")


def _fake_fit_bytes(payload=b"body"):
    # Bytes 8-11 carry the .FIT signature; the header before it is not inspected.
    return b"\x0e\x20\xa6\x52\xcb\x53\x03\x00" + b".FIT" + payload


def test_has_fit_magic_accepts_real_signature():
    assert fetch_coros.has_fit_magic(_fake_fit_bytes())


def test_has_fit_magic_rejects_short_and_wrong_payloads():
    assert not fetch_coros.has_fit_magic(b"tiny")
    assert not fetch_coros.has_fit_magic(b"x" * 40)


def test_fetch_activity_writes_file_and_returns_sha(tmp_path, monkeypatch):
    data = _fake_fit_bytes()
    monkeypatch.setattr(fetch_coros, "download_bytes", lambda url: data)
    path, digest = fetch_coros.fetch_activity(VALID_ENTRY, tmp_path)
    assert path == tmp_path / "479396244626636805.fit"
    assert path.read_bytes() == data
    assert digest == hashlib.sha256(data).hexdigest()


def test_fetch_activity_rejects_non_fit_payload_and_leaves_no_file(tmp_path, monkeypatch):
    monkeypatch.setattr(fetch_coros, "download_bytes", lambda url: b"<html>404</html>")
    with pytest.raises(fetch_coros.DownloadError):
        fetch_coros.fetch_activity(VALID_ENTRY, tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_fetch_activity_cleans_up_when_download_raises(tmp_path, monkeypatch):
    def boom(url):
        raise OSError("connection reset")

    monkeypatch.setattr(fetch_coros, "download_bytes", boom)
    with pytest.raises(fetch_coros.DownloadError):
        fetch_coros.fetch_activity(VALID_ENTRY, tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_fetch_activity_wraps_incomplete_read_and_leaves_no_file(tmp_path, monkeypatch):
    def boom(url):
        raise http.client.IncompleteRead(b"partial")

    monkeypatch.setattr(fetch_coros, "download_bytes", boom)
    with pytest.raises(fetch_coros.DownloadError):
        fetch_coros.fetch_activity(VALID_ENTRY, tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_fetch_activity_cleans_up_when_write_fails(tmp_path, monkeypatch):
    data = _fake_fit_bytes()
    monkeypatch.setattr(fetch_coros, "download_bytes", lambda url: data)

    def boom_write(self, _data):
        raise OSError("disk full")

    monkeypatch.setattr(Path, "write_bytes", boom_write)
    with pytest.raises(fetch_coros.DownloadError):
        fetch_coros.fetch_activity(VALID_ENTRY, tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_run_skips_activities_already_in_ledger(tmp_path, monkeypatch):
    ledger_path = tmp_path / "ledger.json"
    fetch_coros.save_ledger(ledger_path, {VALID_ENTRY["labelId"]: {"date": "2026-08-04"}})

    def unexpected(url):
        raise AssertionError("must not download a ledgered activity")

    monkeypatch.setattr(fetch_coros, "download_bytes", unexpected)
    fetched, skipped, failed = fetch_coros.run([VALID_ENTRY], tmp_path, ledger_path, False)
    assert (fetched, skipped, failed) == (0, 1, 0)


def test_run_records_ledger_entry_after_success(tmp_path, monkeypatch):
    ledger_path = tmp_path / "ledger.json"
    data = _fake_fit_bytes()
    monkeypatch.setattr(fetch_coros, "download_bytes", lambda url: data)
    fetched, skipped, failed = fetch_coros.run([VALID_ENTRY], tmp_path, ledger_path, False)
    assert (fetched, skipped, failed) == (1, 0, 0)

    record = fetch_coros.load_ledger(ledger_path)[VALID_ENTRY["labelId"]]
    assert record["sha256"] == hashlib.sha256(data).hexdigest()
    assert record["date"] == "2026-08-04"
    assert record["sportType"] == 100
    assert record["latitude"] == 40.811001
    assert record["filename"] == "479396244626636805.fit"
    assert record["fetched_at"]


def test_run_skips_existing_file_without_overwriting(tmp_path, monkeypatch):
    ledger_path = tmp_path / "ledger.json"
    existing = tmp_path / "479396244626636805.fit"
    existing.write_bytes(b"original")

    def unexpected(url):
        raise AssertionError("must not download over an existing file")

    monkeypatch.setattr(fetch_coros, "download_bytes", unexpected)
    fetched, skipped, failed = fetch_coros.run([VALID_ENTRY], tmp_path, ledger_path, False)
    assert (fetched, skipped, failed) == (0, 1, 0)
    assert existing.read_bytes() == b"original"


def test_run_counts_failure_and_writes_no_ledger_entry(tmp_path, monkeypatch):
    ledger_path = tmp_path / "ledger.json"
    monkeypatch.setattr(fetch_coros, "download_bytes", lambda url: b"<html>404</html>")
    fetched, skipped, failed = fetch_coros.run([VALID_ENTRY], tmp_path, ledger_path, False)
    assert (fetched, skipped, failed) == (0, 0, 1)
    assert fetch_coros.load_ledger(ledger_path) == {}


def test_run_dry_run_touches_neither_network_nor_disk(tmp_path, monkeypatch):
    ledger_path = tmp_path / "ledger.json"

    def unexpected(url):
        raise AssertionError("dry run must not download")

    monkeypatch.setattr(fetch_coros, "download_bytes", unexpected)
    fetched, skipped, failed = fetch_coros.run([VALID_ENTRY], tmp_path, ledger_path, True)
    assert (fetched, skipped, failed) == (1, 0, 0)
    assert not ledger_path.exists()
    assert list(tmp_path.iterdir()) == []


def test_main_reads_manifest_file_and_returns_zero(tmp_path, monkeypatch):
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps([VALID_ENTRY]), encoding="utf-8")
    monkeypatch.setattr(fetch_coros, "download_bytes", lambda url: _fake_fit_bytes())
    monkeypatch.setattr(fetch_coros, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(fetch_coros, "LEDGER_PATH", tmp_path / "ledger.json")
    assert fetch_coros.main(["--manifest", str(manifest)]) == 0


def test_main_returns_one_on_malformed_manifest(tmp_path, monkeypatch):
    manifest = tmp_path / "manifest.json"
    manifest.write_text("{broken", encoding="utf-8")
    monkeypatch.setattr(fetch_coros, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(fetch_coros, "LEDGER_PATH", tmp_path / "ledger.json")
    assert fetch_coros.main(["--manifest", str(manifest)]) == 1
