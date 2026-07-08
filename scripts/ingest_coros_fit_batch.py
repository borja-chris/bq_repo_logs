from __future__ import annotations

import json
import tarfile
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Iterable

import summarize_coros_fit as summarize

REPO_ROOT = Path(__file__).resolve().parent.parent


def format_int(value: int) -> str:
    return f"{value:,}"


def fit_parser_available() -> bool:
    return summarize.FITPARSE_FILE is not None or summarize.FITDECODE is not None


def print_fit_parser_preflight_failure(fit_files: list[Path]) -> None:
    print("Import aborted: FIT parser dependencies are unavailable in this interpreter.")
    print("Use `.venv/bin/python scripts/ingest_coros_fit.py` or run `bash scripts/setup_fit_env.sh`.")
    print(f"Loose FIT files left in repo root: {len(fit_files)}")
    for path in fit_files:
        print(f"  - {path.name}")


def batch_dir_for(import_date: date) -> Path:
    return REPO_ROOT / "data" / "coros_exports" / f"COROS_export_{import_date.isoformat()}"


def processed_paths_for(import_date: date) -> Path:
    stem = f"coros_export_{import_date.isoformat()}_summary"
    return REPO_ROOT / "data" / "processed" / f"{stem}.jsonl"


def find_loose_fit_files() -> list[Path]:
    return sorted(path for path in REPO_ROOT.glob("*.fit") if path.is_file())


def import_loose_fit_files(import_date: date) -> tuple[Path, list[Path], int]:
    fit_files = find_loose_fit_files()
    export_dir = batch_dir_for(import_date)
    export_dir.mkdir(parents=True, exist_ok=True)
    removed_sidecars = 0
    moved_files: list[Path] = []
    for source_path in fit_files:
        target_path = export_dir / source_path.name
        source_path.rename(target_path)
        moved_files.append(target_path)
        sidecar = REPO_ROOT / f"{source_path.name}:Zone.Identifier"
        if sidecar.exists():
            sidecar.unlink()
            removed_sidecars += 1
    return export_dir, moved_files, removed_sidecars


def write_sha256s(export_dir: Path, rows: Iterable[dict[str, str]]) -> int:
    hash_path = export_dir / "SHA256SUMS.txt"
    with hash_path.open("w") as handle:
        count = 0
        for row in rows:
            handle.write(f"{row['source_sha256']}  {row['source_relpath']}\n")
            count += 1
    return count


def generate_summaries(export_dir: Path) -> tuple[Path, list[dict[str, str]]]:
    import_date = export_dir.name.removeprefix("COROS_export_")
    output_jsonl = processed_paths_for(date.fromisoformat(import_date))
    fit_files = sorted(export_dir.glob("*.fit"))
    if fit_files:
        rows = summarize.parse_fit_files(fit_files)
    else:
        archive_path = export_dir / "fit_files.tar.gz"
        if not archive_path.exists():
            rows = []
        else:
            with TemporaryDirectory() as temp_dir_name:
                temp_dir = Path(temp_dir_name)
                with tarfile.open(archive_path, "r:gz") as archive:
                    archive.extractall(temp_dir)
                archived_fit_files = sorted(temp_dir.rglob("*.fit"))
                rows = summarize.parse_fit_files(archived_fit_files)
    summarize.write_jsonl(output_jsonl, rows)
    return output_jsonl, rows


def load_processed_rows(jsonl_path: Path) -> list[dict[str, str]]:
    if not jsonl_path.exists():
        return []
    rows: list[dict[str, str]] = []
    with jsonl_path.open() as handle:
        for raw_line in handle:
            raw_line = raw_line.strip()
            if not raw_line:
                continue
            rows.append(json.loads(raw_line))
    return rows


def write_processed_outputs(
    output_jsonl: Path,
    rows: list[dict[str, str]],
) -> None:
    summarize.write_jsonl(output_jsonl, rows)


def write_manifest(
    export_dir: Path,
    import_date: date,
    fit_count: int,
    removed_sidecars: int,
    output_jsonl: Path,
    rows: list[dict[str, str]],
) -> Path:
    fit_files = sorted(export_dir.glob("*.fit"))
    payload_bytes = sum(path.stat().st_size for path in fit_files)
    folder_bytes = sum(path.stat().st_size for path in export_dir.iterdir() if path.is_file())
    parser_names = sorted({row.get("parser", "") for row in rows if row.get("parser", "")})
    manifest = export_dir / "manifest.md"
    first_source = fit_files[0].name if fit_files else ""
    lines = [
        f"# COROS Export Manifest - {import_date.isoformat()}",
        "",
        "## Import",
        "",
        f"- Source file: `{first_source}`" if fit_count == 1 else f"- Source files: `{fit_count}` files",
        f"- Repo folder: `data/coros_exports/{export_dir.name}/`",
        f"- Imported on: {import_date.isoformat()}",
        f"- FIT files: {fit_count}",
        f"- FIT payload bytes: {format_int(payload_bytes)}",
        f"- Removed sidecars: {removed_sidecars} `*:Zone.Identifier` file" + ("" if removed_sidecars == 1 else "s"),
        "",
        "## Integrity",
        "",
        "- Hash file: `SHA256SUMS.txt`",
        f"- Hash entries: {fit_count}",
        "",
        "## Processing",
        "",
        f"- Processed JSONL: `{summarize.repo_relpath(output_jsonl)}`",
        f"- JSONL rows: {len(rows)}",
        f"- Summary row count matches FIT count: {'yes' if len(rows) == fit_count else 'no'}",
        f"- Parser used for this batch: `{', '.join(parser_names) or 'unknown'}`",
        "",
        "## Archive",
        "",
        "- Archive status: not archived yet",
        "- Reason: current-month loose FIT files stay available for repair, reparse, or enrichment",
        f"- Folder bytes with loose FIT files: {format_int(folder_bytes)}",
        "",
        "## Notes",
        "",
        "- Raw FIT files are binary training records and may contain GPS, timestamps, heart rate, and device metadata.",
        "- Processed summaries should be written to `data/processed/`.",
    ]
    manifest.write_text("\n".join(lines) + "\n")
    return manifest
