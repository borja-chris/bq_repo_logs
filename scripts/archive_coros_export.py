#!/usr/bin/env python3
"""Archive FIT files for a COROS export batch after summaries exist."""

from __future__ import annotations

import argparse
import json
import tarfile
from pathlib import Path


def repo_relpath(path: Path, repo_root: Path) -> str:
    return str(path.resolve().relative_to(repo_root.resolve()))


def update_jsonl(export_dir: Path, archive_path: Path, repo_root: Path) -> None:
    processed_name = f"{export_dir.name.lower()}_summary.jsonl"
    jsonl_path = repo_root / "data" / "processed" / processed_name
    if not jsonl_path.exists():
        return

    lines: list[str] = []
    archive_relpath = repo_relpath(archive_path, repo_root)
    with jsonl_path.open() as handle:
        for raw_line in handle:
            row = json.loads(raw_line)
            row["source_archive_relpath"] = archive_relpath
            row["source_archive_member"] = row.get("source_file", "")
            lines.append(json.dumps(row, sort_keys=True))

    with jsonl_path.open("w") as handle:
        for line in lines:
            handle.write(line)
            handle.write("\n")


def archive_batch(export_dir: Path) -> int:
    fit_files = sorted(export_dir.glob("*.fit"))
    if not fit_files:
        raise SystemExit(f"No .fit files found in {export_dir}")

    archive_path = export_dir / "fit_files.tar.gz"
    if archive_path.exists():
        raise SystemExit(f"Archive already exists: {archive_path}")

    repo_root = Path.cwd()
    with tarfile.open(archive_path, "w:gz") as archive:
        for path in fit_files:
            archive.add(path, arcname=path.name)

    with tarfile.open(archive_path, "r:gz") as archive:
        members = [member.name for member in archive.getmembers() if member.isfile()]
    expected_members = [path.name for path in fit_files]
    if members != expected_members:
        raise SystemExit("Archive verification failed: member list mismatch.")

    update_jsonl(export_dir, archive_path, repo_root)

    for path in fit_files:
        path.unlink()

    print(f"Archived {len(fit_files)} FIT files to {archive_path}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("export_dir", type=Path)
    args = parser.parse_args()
    return archive_batch(args.export_dir)


if __name__ == "__main__":
    raise SystemExit(main())
