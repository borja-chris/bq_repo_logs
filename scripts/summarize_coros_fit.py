#!/usr/bin/env python3
"""Summarize COROS FIT files into reviewable CSV and JSONL outputs.

Requires the optional `fitparse` package:

    python -m pip install fitparse
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import warnings
from pathlib import Path
from typing import Any


FIELDS = [
    "import_batch",
    "source_file",
    "source_relpath",
    "source_sha256",
    "activity_id",
    "start_time",
    "sport",
    "sub_sport",
    "distance_mi",
    "duration_s",
    "avg_hr",
    "max_hr",
    "ascent_m",
    "parser",
    "parse_error",
]


def field_map(message: Any) -> dict[str, Any]:
    return {field.name: field.value for field in message}


def miles(meters: Any) -> str:
    if meters in (None, ""):
        return ""
    return f"{float(meters) / 1609.344:.2f}"


def seconds(value: Any) -> str:
    if value in (None, ""):
        return ""
    return f"{float(value):.0f}"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def repo_relpath(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(Path.cwd().resolve()))
    except ValueError:
        return str(path)


def parse_fit(path: Path) -> dict[str, str]:
    try:
        from fitparse import FitFile
    except ImportError:
        FitFile = None

    row = {field: "" for field in FIELDS}
    row["import_batch"] = path.parent.name
    row["source_file"] = path.name
    row["source_relpath"] = repo_relpath(path)
    row["source_sha256"] = sha256(path)
    row["activity_id"] = path.stem

    def apply_values(values: dict[str, Any], parser_name: str) -> None:
        row["start_time"] = str(values.get("start_time", ""))
        row["sport"] = str(values.get("sport", ""))
        row["sub_sport"] = str(values.get("sub_sport", ""))
        row["distance_mi"] = miles(values.get("total_distance"))
        row["duration_s"] = seconds(values.get("total_elapsed_time"))
        row["avg_hr"] = str(values.get("avg_heart_rate", "") or "")
        row["max_hr"] = str(values.get("max_heart_rate", "") or "")
        row["ascent_m"] = str(values.get("total_ascent", "") or "")
        row["parser"] = parser_name

    fitparse_exc: Exception | None = None
    if FitFile is not None:
        try:
            fit_file = FitFile(str(path))
            for message in fit_file.get_messages():
                if message.name == "session":
                    apply_values(field_map(message), "fitparse")
                    break
        except Exception as exc:
            fitparse_exc = exc

    if not row["parser"]:
        try:
            import fitdecode
        except ImportError:
            if fitparse_exc is not None:
                row["parse_error"] = f"{type(fitparse_exc).__name__}: {fitparse_exc}"
            else:
                row["parse_error"] = "Missing optional dependencies `fitparse` and `fitdecode`."
            return row

        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                with fitdecode.FitReader(str(path)) as fit_file:
                    for frame in fit_file:
                        if (
                            frame.frame_type == fitdecode.FIT_FRAME_DATA
                            and frame.name == "session"
                        ):
                            apply_values(
                                {field.name: field.value for field in frame.fields},
                                "fitdecode",
                            )
                            break
        except Exception as fitdecode_exc:
            if fitparse_exc is not None:
                row["parse_error"] = (
                    f"fitparse {type(fitparse_exc).__name__}: {fitparse_exc}; "
                    f"fitdecode {type(fitdecode_exc).__name__}: {fitdecode_exc}"
                )
            else:
                row["parse_error"] = (
                    f"fitdecode {type(fitdecode_exc).__name__}: {fitdecode_exc}"
                )

    return row


def write_jsonl(output_path: Path, rows: list[dict[str, str]]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True))
            handle.write("\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_dir", type=Path)
    parser.add_argument("output_csv", type=Path)
    parser.add_argument(
        "--jsonl",
        type=Path,
        help="Optional newline-delimited JSON output for machine processing.",
    )
    args = parser.parse_args()

    fit_files = sorted(args.input_dir.glob("*.fit"))
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    rows = [parse_fit(path) for path in fit_files]

    with args.output_csv.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    if args.jsonl:
        write_jsonl(args.jsonl, rows)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
