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
