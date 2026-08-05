#!/usr/bin/env python3
"""Download COROS FIT files from a Claude-supplied manifest.

Claude makes the COROS MCP calls and emits a JSON manifest; this script does
everything that touches disk. Files land at the repo root as ``<labelId>.fit``
so the existing ``scripts/ingest.sh`` pipeline picks them up exactly as it would
a manually dropped file.
"""

from __future__ import annotations

import hashlib
import json
import urllib.error
import urllib.request
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
