# COROS MCP FIT Fetch Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: `superpowers:subagent-driven-development`
> (recommended) or `superpowers:executing-plans` to implement this plan task-by-task.
> Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `scripts/fetch_coros.py`, which downloads COROS FIT files from a
Claude-supplied manifest to the repo root so the existing `scripts/ingest.sh`
pipeline can consume them, eliminating the manual `.fit` drop.

**Architecture:** Claude makes the MCP calls and emits a JSON manifest. This
script does everything touching disk: dedup against a `labelId` ledger, download,
validate FIT magic bytes, record the ledger. No MCP or OAuth code lives in the
repo. No existing script is modified — the script simply lands `*.fit` files at
the repo root, which `find_loose_fit_files()` in
`scripts/ingest_coros_fit_batch.py` already globs.

**Tech Stack:** Python 3 standard library only (`argparse`, `json`, `hashlib`,
`urllib.request`, `pathlib`, `datetime`). Tests use `pytest`.

**Spec:** `docs/superpowers/specs/2026-08-04-coros-mcp-fit-fetch-design.md`

## Global Constraints

- Python interpreter is **always** `.venv/bin/python`. Bare `python` is not
  installed (exit 127) and system `python3` lacks repo deps.
- Test command: `.venv/bin/python -m pytest tests/ -q`
- **Standard library only.** Do not add dependencies. Use `urllib.request`, not
  `requests`.
- **No network access in tests.** The download function is the monkeypatch point.
- **Do not modify any existing script.** Specifically not `ingest.sh`,
  `ingest_coros_fit.py`, `ingest_coros_fit_batch.py`, `summarize_coros_fit.py`,
  or `ingest_coros_fit_weather.py`.
- **Never `git add -A` or `git add .`** — untracked local tooling at root would be
  swept in. Stage explicit paths only.
- **Do NOT commit.** Each task ends with a report to the Tech Lead, who commits
  centrally. Sub-agents never run `git commit` or `git push`.
- FIT magic: bytes 8–11 of the file equal `b".FIT"`.
- Ledger path: `data/coros_fetch_ledger.json`.
- Downloaded filename: `<labelId>.fit`.

## File Structure

| File | Responsibility |
|---|---|
| `scripts/fetch_coros.py` (create) | Manifest parsing, ledger I/O, download, validation, CLI |
| `tests/test_fetch_coros.py` (create) | Full unit coverage, no network |
| `scripts/README.md` (modify) | Document the new script |

One script file is correct here: the units are small, share the same error
vocabulary, and are only ever used together. Splitting across modules would add
import ceremony without improving testability, and it would break the repo's
established one-script-per-task pattern.

---

### Task 1: Manifest parsing and validation

**Files:**
- Create: `scripts/fetch_coros.py`
- Create: `tests/test_fetch_coros.py`

**Interfaces:**
- Consumes: nothing (first task)
- Produces:
  - `class ManifestError(Exception)`
  - `parse_manifest(text: str) -> list[dict]` — returns validated entries with
    keys `labelId` (str), `sportType` (int), `date` (str), `url` (str), and
    optional `latitude`/`longitude` (float or None). Raises `ManifestError` on
    any malformed entry.

- [ ] **Step 1: Write failing tests**

Create `tests/test_fetch_coros.py`:

```python
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
```

- [ ] **Step 2: Run tests and verify they fail**

Run: `.venv/bin/python -m pytest tests/test_fetch_coros.py -q`
Expected: FAIL — `scripts/fetch_coros.py` does not exist yet, collection error.

- [ ] **Step 3: Write minimal implementation**

Create `scripts/fetch_coros.py`:

```python
#!/usr/bin/env python3
"""Download COROS FIT files from a Claude-supplied manifest.

Claude makes the COROS MCP calls and emits a JSON manifest; this script does
everything that touches disk. Files land at the repo root as ``<labelId>.fit``
so the existing ``scripts/ingest.sh`` pipeline picks them up exactly as it would
a manually dropped file.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
LEDGER_PATH = REPO_ROOT / "data" / "coros_fetch_ledger.json"

REQUIRED_FIELDS = ("labelId", "sportType", "date", "url")


class ManifestError(Exception):
    """Raised when the supplied manifest is malformed."""


def _coordinate(value: Any, field: str, index: int) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ManifestError(f"entry {index}: {field} must be a number or omitted")
    return float(value)


def parse_manifest(text: str) -> list[dict]:
    """Parse and validate a manifest, returning normalized entries."""
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ManifestError(f"manifest is not valid JSON: {exc}") from exc

    if not isinstance(payload, list):
        raise ManifestError("manifest must be a JSON array of activity entries")

    entries: list[dict] = []
    for index, raw in enumerate(payload):
        if not isinstance(raw, dict):
            raise ManifestError(f"entry {index}: must be a JSON object")

        for field in REQUIRED_FIELDS:
            if raw.get(field) in (None, ""):
                raise ManifestError(f"entry {index}: missing required field {field!r}")

        label_id = str(raw["labelId"])
        if "/" in label_id or "\\" in label_id or label_id in (".", ".."):
            raise ManifestError(f"entry {index}: labelId {label_id!r} is not a safe filename")

        url = str(raw["url"])
        if not url.startswith("https://"):
            raise ManifestError(f"entry {index}: url must be https, got {url!r}")

        try:
            sport_type = int(raw["sportType"])
        except (TypeError, ValueError) as exc:
            raise ManifestError(f"entry {index}: sportType must be an integer") from exc

        entries.append(
            {
                "labelId": label_id,
                "sportType": sport_type,
                "date": str(raw["date"]),
                "url": url,
                "latitude": _coordinate(raw.get("latitude"), "latitude", index),
                "longitude": _coordinate(raw.get("longitude"), "longitude", index),
            }
        )
    return entries
```

- [ ] **Step 4: Run tests and verify they pass**

Run: `.venv/bin/python -m pytest tests/test_fetch_coros.py -q`
Expected: PASS (10 tests, counting the four parametrized missing-field cases).

- [ ] **Step 5: Report to Tech Lead — do NOT commit**

Report the files created and the passing test count. The Tech Lead commits.

---

### Task 2: Ledger load and save

**Files:**
- Modify: `scripts/fetch_coros.py`
- Modify: `tests/test_fetch_coros.py`

**Interfaces:**
- Consumes: `ManifestError` and module conventions from Task 1.
- Produces:
  - `class LedgerError(Exception)`
  - `load_ledger(path: Path) -> dict` — returns `{}` when the file is absent;
    raises `LedgerError` on corrupt or non-object content.
  - `save_ledger(path: Path, ledger: dict) -> None` — creates parent directories,
    writes sorted, indented JSON with a trailing newline.

- [ ] **Step 1: Write failing tests**

Append to `tests/test_fetch_coros.py`:

```python
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
```

- [ ] **Step 2: Run tests and verify they fail**

Run: `.venv/bin/python -m pytest tests/test_fetch_coros.py -q`
Expected: FAIL — `AttributeError: module has no attribute 'LedgerError'`.

- [ ] **Step 3: Write minimal implementation**

Add to `scripts/fetch_coros.py`:

```python
class LedgerError(Exception):
    """Raised when the fetch ledger cannot be read."""


def load_ledger(path: Path) -> dict:
    """Load the fetch ledger, or an empty dict when it does not exist yet."""
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        # Fail loudly: silently resetting would re-download every activity and
        # burn the daily COROS FIT download quota.
        raise LedgerError(f"ledger at {path} is corrupt: {exc}") from exc
    if not isinstance(payload, dict):
        raise LedgerError(f"ledger at {path} must contain a JSON object")
    return payload


def save_ledger(path: Path, ledger: dict) -> None:
    """Write the ledger as sorted, indented JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n", encoding="utf-8")
```

- [ ] **Step 4: Run tests and verify they pass**

Run: `.venv/bin/python -m pytest tests/test_fetch_coros.py -q`
Expected: PASS.

- [ ] **Step 5: Report to Tech Lead — do NOT commit**

---

### Task 3: Download with FIT validation and partial cleanup

**Files:**
- Modify: `scripts/fetch_coros.py`
- Modify: `tests/test_fetch_coros.py`

**Interfaces:**
- Consumes: `ManifestError`, `LedgerError` from Tasks 1–2.
- Produces:
  - `class DownloadError(Exception)`
  - `FIT_MAGIC = b".FIT"`
  - `has_fit_magic(data: bytes) -> bool` — True when `data[8:12] == FIT_MAGIC`.
  - `download_bytes(url: str) -> bytes` — the sole network call and the
    monkeypatch point for tests.
  - `fetch_activity(entry: dict, dest_dir: Path) -> tuple[Path, str]` — downloads,
    validates, writes, and returns `(path, sha256_hex)`. Raises `DownloadError`
    and leaves no partial file behind on any failure.

- [ ] **Step 1: Write failing tests**

Append to `tests/test_fetch_coros.py`:

```python
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
```

Add `import hashlib` to the test file's imports.

- [ ] **Step 2: Run tests and verify they fail**

Run: `.venv/bin/python -m pytest tests/test_fetch_coros.py -q`
Expected: FAIL — `AttributeError: module has no attribute 'DownloadError'`.

- [ ] **Step 3: Write minimal implementation**

Add to `scripts/fetch_coros.py` (and add `import hashlib` plus
`import urllib.error` and `import urllib.request` to the imports):

```python
FIT_MAGIC = b".FIT"
DOWNLOAD_TIMEOUT_S = 60


class DownloadError(Exception):
    """Raised when an activity file cannot be downloaded or is not a FIT file."""


def has_fit_magic(data: bytes) -> bool:
    """True when the payload carries the FIT signature at bytes 8-11."""
    return len(data) >= 12 and data[8:12] == FIT_MAGIC


def download_bytes(url: str) -> bytes:
    """Fetch a URL and return its body. Sole network call; monkeypatched in tests."""
    with urllib.request.urlopen(url, timeout=DOWNLOAD_TIMEOUT_S) as response:
        return response.read()


def fetch_activity(entry: dict, dest_dir: Path) -> tuple[Path, str]:
    """Download one activity to dest_dir, returning (path, sha256_hex).

    Nothing is written unless the payload validates as a FIT file, so a failed
    run is always safe to retry.
    """
    destination = dest_dir / f"{entry['labelId']}.fit"
    try:
        data = download_bytes(entry["url"])
    except (urllib.error.URLError, OSError) as exc:
        raise DownloadError(f"{entry['labelId']}: download failed: {exc}") from exc

    if not has_fit_magic(data):
        raise DownloadError(
            f"{entry['labelId']}: response is not a FIT file "
            f"({len(data)} bytes, missing .FIT signature)"
        )

    dest_dir.mkdir(parents=True, exist_ok=True)
    try:
        destination.write_bytes(data)
    except OSError as exc:
        destination.unlink(missing_ok=True)
        raise DownloadError(f"{entry['labelId']}: could not write file: {exc}") from exc

    return destination, hashlib.sha256(data).hexdigest()
```

- [ ] **Step 4: Run tests and verify they pass**

Run: `.venv/bin/python -m pytest tests/test_fetch_coros.py -q`
Expected: PASS.

- [ ] **Step 5: Report to Tech Lead — do NOT commit**

---

### Task 4: CLI orchestration, dedup, and dry-run

**Files:**
- Modify: `scripts/fetch_coros.py`
- Modify: `tests/test_fetch_coros.py`

**Interfaces:**
- Consumes: `parse_manifest`, `load_ledger`, `save_ledger`, `fetch_activity`,
  `DownloadError`, `ManifestError`, `LedgerError` from Tasks 1–3.
- Produces:
  - `run(entries: list[dict], dest_dir: Path, ledger_path: Path, dry_run: bool) -> tuple[int, int, int]`
    returning `(fetched, skipped, failed)`.
  - `main(argv: list[str] | None = None) -> int` — exit 0 on success, 1 on any
    failure or bad input.

- [ ] **Step 1: Write failing tests**

Append to `tests/test_fetch_coros.py`:

```python
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
```

- [ ] **Step 2: Run tests and verify they fail**

Run: `.venv/bin/python -m pytest tests/test_fetch_coros.py -q`
Expected: FAIL — `AttributeError: module has no attribute 'run'`.

- [ ] **Step 3: Write minimal implementation**

Add to `scripts/fetch_coros.py` (add `import argparse` and `import sys`, plus
`from datetime import datetime`):

```python
def run(
    entries: list[dict],
    dest_dir: Path,
    ledger_path: Path,
    dry_run: bool,
) -> tuple[int, int, int]:
    """Fetch every entry not already known. Returns (fetched, skipped, failed)."""
    ledger = load_ledger(ledger_path)
    fetched = skipped = failed = 0

    for entry in entries:
        label_id = entry["labelId"]
        destination = dest_dir / f"{label_id}.fit"

        if label_id in ledger:
            print(f"skip  {label_id} ({entry['date']}) — already in ledger")
            skipped += 1
            continue

        if destination.exists():
            print(f"skip  {label_id} ({entry['date']}) — {destination.name} already on disk")
            skipped += 1
            continue

        if dry_run:
            print(f"fetch {label_id} ({entry['date']}) — would download {entry['url']}")
            fetched += 1
            continue

        try:
            path, digest = fetch_activity(entry, dest_dir)
        except DownloadError as exc:
            print(f"FAIL  {exc}", file=sys.stderr)
            failed += 1
            continue

        ledger[label_id] = {
            "sportType": entry["sportType"],
            "date": entry["date"],
            "sha256": digest,
            "fetched_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "latitude": entry["latitude"],
            "longitude": entry["longitude"],
            "filename": path.name,
        }
        save_ledger(ledger_path, ledger)
        print(f"fetch {label_id} ({entry['date']}) — {path.name}")
        fetched += 1

    return fetched, skipped, failed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Download COROS FIT files from a Claude-supplied manifest."
    )
    parser.add_argument(
        "--manifest",
        required=True,
        help="Path to a JSON manifest, or '-' to read it from stdin.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report fetch/skip decisions without touching the network or disk.",
    )
    args = parser.parse_args(argv)

    try:
        text = sys.stdin.read() if args.manifest == "-" else Path(args.manifest).read_text(
            encoding="utf-8"
        )
    except OSError as exc:
        print(f"error: cannot read manifest: {exc}", file=sys.stderr)
        return 1

    try:
        entries = parse_manifest(text)
        fetched, skipped, failed = run(entries, REPO_ROOT, LEDGER_PATH, args.dry_run)
    except (ManifestError, LedgerError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"\n{fetched} fetched, {skipped} skipped, {failed} failed")
    if failed:
        return 1
    if fetched and not args.dry_run:
        print("Next: bash scripts/ingest.sh")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run the full suite and verify it passes**

Run: `.venv/bin/python -m pytest tests/ -q`
Expected: PASS — the new tests plus every pre-existing test.

- [ ] **Step 5: Verify the CLI end to end without network**

Run:

```bash
printf '[{"labelId":"1","sportType":100,"date":"2026-08-04","url":"https://example.invalid/1.fit"}]' \
  | .venv/bin/python scripts/fetch_coros.py --manifest - --dry-run
```

Expected: prints a `fetch 1 (2026-08-04) — would download …` line and
`1 fetched, 0 skipped, 0 failed`, exits 0, and creates no
`data/coros_fetch_ledger.json` and no `1.fit`. Confirm with
`git status --short` that the working tree shows only the intended new files.

- [ ] **Step 6: Report to Tech Lead — do NOT commit**

---

### Task 5: Document the script

**Files:**
- Modify: `scripts/README.md`

**Interfaces:**
- Consumes: the finished CLI from Task 4.
- Produces: no code.

- [ ] **Step 1: Read the existing README and match its entry format**

Run: `hcat scripts/README.md`

Note the heading level, ordering, and phrasing used by neighboring script
entries — particularly how `ingest.sh` is described — and follow it exactly
rather than inventing a new format.

- [ ] **Step 2: Add the `fetch_coros.py` entry**

Write one entry in the established format covering:

- Purpose: downloads COROS FIT files from a Claude-supplied manifest to the repo
  root so `ingest.sh` consumes them like a manual drop.
- Usage: `.venv/bin/python scripts/fetch_coros.py --manifest -` (stdin),
  `--manifest FILE`, and `--dry-run`.
- Manifest shape: JSON array with `labelId`, `sportType`, `date`, `url`, and
  optional `latitude`/`longitude`.
- Ledger: `data/coros_fetch_ledger.json`, keyed by `labelId`, prevents
  re-downloading and protects the daily COROS quota.
- Note that Claude supplies the manifest via the COROS MCP server; the script
  itself has no MCP or auth code.
- Follow-up command: `bash scripts/ingest.sh`.

Compose the full entry and apply it in a single edit.

- [ ] **Step 3: Verify links and the full suite**

Run:

```bash
.venv/bin/python -m pytest tests/ -q && \
.venv/bin/python scripts/check_markdown_links.py && \
.venv/bin/python scripts/status_digest.py
```

Expected: tests pass, no unsafe Markdown links, digest regenerates cleanly.

- [ ] **Step 4: Report to Tech Lead — do NOT commit**

---

## Definition of Done

- `scripts/fetch_coros.py` exists and passes every test in
  `tests/test_fetch_coros.py`.
- `.venv/bin/python -m pytest tests/ -q` passes, including all pre-existing tests.
- `.venv/bin/python scripts/check_markdown_links.py` reports no unsafe links.
- No existing script was modified.
- `scripts/README.md` documents the new script.
- A dry run against a fake manifest exits 0 and writes nothing.

## Out of Scope

Do not implement these; they are explicit non-goals in the spec:

- MCP protocol or OAuth code in the repo.
- Cron or unattended scheduling.
- Wiring ledger coordinates into `scripts/ingest_coros_fit_weather.py`.
- Any change to `ingest.sh` or other existing scripts.
