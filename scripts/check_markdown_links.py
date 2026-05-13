#!/usr/bin/env python3
"""Fail on GitHub-unsafe Markdown link targets in the repository."""

from __future__ import annotations

import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
MARKDOWN_GLOBS = ("*.md",)

# Match inline Markdown links while ignoring image links.
LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")


def iter_markdown_files() -> list[Path]:
    files: list[Path] = []
    for pattern in MARKDOWN_GLOBS:
        files.extend(REPO_ROOT.rglob(pattern))
    return sorted(path for path in files if path.is_file())


def classify_target(target: str) -> str | None:
    if target.startswith("/home/"):
        return "absolute local filesystem path"
    if target.startswith("file://"):
        return "file:// URL"
    if target.startswith("/") and not target.startswith("//"):
        return "root-relative path; GitHub resolves this outside the repo"
    return None


def main() -> int:
    failures: list[tuple[Path, int, str, str]] = []

    for path in iter_markdown_files():
        rel_path = path.relative_to(REPO_ROOT)
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            for match in LINK_RE.finditer(line):
                target = match.group(1)
                reason = classify_target(target)
                if reason:
                    failures.append((rel_path, line_number, target, reason))

    if not failures:
        print("OK: no GitHub-unsafe Markdown links found.")
        return 0

    print("Found GitHub-unsafe Markdown links:")
    for rel_path, line_number, target, reason in failures:
        print(f"- {rel_path}:{line_number}: {target} ({reason})")
    print("\nUse repo-relative paths like 'docs/repo_workflow.md' for in-repo links.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
