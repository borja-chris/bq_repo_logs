#!/usr/bin/env python3
"""One-shot: compress verbose Managed Notes blocks in logs/weekly/*.md.

A Managed Notes block may contain more than one imported activity (multiple
runs logged under a single day). Each activity is delimited by its own
'  - Imported from `...`' bullet; everything from that bullet up to (but not
including) the next such bullet belongs to that activity. Each activity
segment is compacted to its own one-line summary (Task 10's format), in
original order -- a block with N verbose activities always yields N compact
lines. Lines that precede the first Imported bullet in a block, and any line
that matches none of the four verbose patterns, pass through untouched.
Every other byte in the file passes through untouched. Idempotent:
already-compact lines (no 'Imported from' backtick form) are left alone.

Before an atomically-replaced file is written, the migration is independently
verified: every non-managed line must survive byte-identical and in order,
and the ordered sequence of per-activity identities (source filename plus
start time) must be conserved -- not just their count, so a merge in one
block masked by a duplicate elsewhere cannot slip through.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
IMPORTED = re.compile(r"- Imported from `(?P<path>[^`]+)`")
FIT = re.compile(
    r"- FIT summary: start `(?P<start>[^`]*)`, avg HR `(?P<avg>[^`]*)`, "
    r"max HR `(?P<max>[^`]*)`, ascent `(?P<ascent>[^`]*) m`"
)
WEATHER = re.compile(r"- Weather at start: `(?P<temp>[^ `]+) F`")
HEAT = re.compile(r"- Heat: (?P<body>.+?)\.?$")
# Matches the compact ("- Imported <file> | start HH:MM | ...") form so the
# verifier can extract a comparable identity from already-migrated text.
COMPACT_ACTIVITY = re.compile(
    r"^  - Imported (?P<file>\S+)(?: \| start (?P<start>\d{2}:\d{2}))?"
)


def _segment_block(block: list[str]) -> tuple[list[str], list[list[str]]]:
    """Split a Managed Notes block into (preamble, segments).

    A new segment starts at each line matching IMPORTED and runs until the
    next such line (or end of block). `preamble` holds any lines that
    precede the first Imported bullet -- normally empty, but preserved
    untouched if present. Order is preserved throughout.
    """
    preamble: list[str] = []
    segments: list[list[str]] = []
    current: list[str] | None = None
    for line in block:
        if IMPORTED.search(line):
            if current is not None:
                segments.append(current)
            current = [line]
        elif current is not None:
            current.append(line)
        else:
            preamble.append(line)
    if current is not None:
        segments.append(current)
    return preamble, segments


def _compact_segment(segment: list[str]) -> list[str]:
    joined = "\n".join(segment)
    imported = IMPORTED.search(joined)
    fit = FIT.search(joined)
    if not imported or not fit:
        return segment  # not the verbose import format; leave untouched
    parts = [f"Imported {Path(imported.group('path')).name}"]
    start = fit.group("start")
    if len(start) >= 16:
        parts.append(f"start {start[11:16]}")
    if fit.group("avg"):
        parts.append(f"HR {fit.group('avg')}/{fit.group('max') or '?'}")
    if fit.group("ascent"):
        parts.append(f"asc {fit.group('ascent')}m")
    heat = HEAT.search(joined)
    weather = WEATHER.search(joined)
    if heat:
        parts.append(heat.group("body").rstrip("."))
    elif weather:
        parts.append(f"{weather.group('temp')}°F")
    extras = [line for line in segment
              if not any(p.search(line) for p in (IMPORTED, FIT, WEATHER, HEAT))]
    return [f"  - {' | '.join(parts)}", *extras]


def compact(block: list[str]) -> list[str]:
    """Compact a Managed Notes block, one output line per activity segment."""
    preamble, segments = _segment_block(block)
    if not segments:
        return block  # nothing looks like an activity import; leave untouched
    out: list[str] = list(preamble)
    for segment in segments:
        out.extend(_compact_segment(segment))
    return out


def _iter_lines_with_managed_blocks(text: str):
    """Yield (is_block_content, line) for each line of `text`.

    A line is block content only when it is nested ('  - ' prefixed) under a
    literal '- Managed Notes:' header. The header line itself, and every
    other line in the file, is passthrough content. Shared by migrate_text
    and the verifier so both agree on exactly which bytes are eligible to
    change.
    """
    in_managed = False
    for line in text.splitlines():
        if line == "- Managed Notes:":
            in_managed = True
            yield False, line
        elif in_managed and line.startswith("  - "):
            yield True, line
        else:
            in_managed = False
            yield False, line


def split_managed(text: str) -> tuple[list[str], list[str]]:
    """Return (non_managed_lines, managed_block_lines) for `text`."""
    non_managed: list[str] = []
    managed: list[str] = []
    for is_block, line in _iter_lines_with_managed_blocks(text):
        (managed if is_block else non_managed).append(line)
    return non_managed, managed


def _is_activity_start(line: str) -> bool:
    """True if `line` begins a new activity, in either verbose or compact form."""
    if IMPORTED.search(line):
        return True
    return line.startswith("  - Imported ") and not IMPORTED.search(line)


def _activity_identity(segment: list[str]) -> tuple[str, str]:
    """Derive a (filename, start_HH:MM) identity for one activity segment.

    Works on either form: verbose (Imported-from + FIT-summary lines) or
    already-compact (single '- Imported <file> | start HH:MM | ...' line).
    The filename is the stable key; start time disambiguates same-named or
    time-less entries when present on both sides.
    """
    joined = "\n".join(segment)
    imported = IMPORTED.search(joined)
    if imported:
        filename = Path(imported.group("path")).name
        fit = FIT.search(joined)
        start = ""
        if fit and len(fit.group("start")) >= 16:
            start = fit.group("start")[11:16]
        return (filename, start)
    compact = COMPACT_ACTIVITY.search(segment[0])
    if compact:
        return (compact.group("file"), compact.group("start") or "")
    # Unrecognized shape (shouldn't normally happen -- segments only start
    # on lines _is_activity_start already classified as an activity marker).
    # Fall back to the raw first line so a mismatch here still shows up as a
    # verification failure rather than a silent false match.
    return (segment[0], "")


def _activity_sequence(managed_lines: list[str]) -> list[tuple[str, str]]:
    """Ordered list of activity identities across all Managed Notes blocks.

    Lines are grouped into segments the same way `_segment_block` groups a
    single block, except a segment here can start on either the verbose or
    the compact activity marker (so this can be applied to both the
    original and the migrated text). Non-activity block content (e.g. a
    blank '  - ' placeholder, or extra lines within a segment) does not
    start a new segment and contributes no identity of its own.
    """
    segments: list[list[str]] = []
    current: list[str] | None = None
    for line in managed_lines:
        if _is_activity_start(line):
            if current is not None:
                segments.append(current)
            current = [line]
        elif current is not None:
            current.append(line)
        # else: content before any activity marker in the flattened stream
        # (e.g. an empty placeholder block) -- not an activity.
    if current is not None:
        segments.append(current)
    return [_activity_identity(segment) for segment in segments]


def migrate_text(text: str) -> str:
    out: list[str] = []
    block: list[str] = []
    for is_block, line in _iter_lines_with_managed_blocks(text):
        if is_block:
            block.append(line)
            continue
        if block:
            out.extend(compact(block))
            block = []
        out.append(line)
    if block:
        out.extend(compact(block))
    trailing = "\n" if text.endswith("\n") else ""
    return "\n".join(out) + trailing


def verify_migration(original: str, migrated: str, name: str) -> None:
    """Abort (SystemExit) rather than let a bad migration through.

    Checks, independently of how migrate_text/compact did their work:
      (a) every line outside a Managed Notes block is byte-identical and in
          the same relative order before and after; and
      (b) the ORDERED sequence of per-activity identities (filename, plus
          start time when available) inside Managed Notes blocks is
          conserved -- catching dropped, merged, duplicated, or reordered
          activities. A bare count is not enough here: two activities
          merged into one line while a different block's activity is
          duplicated elsewhere leaves the total count unchanged but changes
          the ordered identity sequence, which this catches.
    """
    orig_non_managed, orig_block_lines = split_managed(original)
    new_non_managed, new_block_lines = split_managed(migrated)
    if orig_non_managed != new_non_managed:
        raise SystemExit(
            f"{name}: non-managed content changed during migration -- aborting"
        )
    orig_identities = _activity_sequence(orig_block_lines)
    new_identities = _activity_sequence(new_block_lines)
    if orig_identities != new_identities:
        raise SystemExit(
            f"{name}: activity identities changed during migration "
            f"({orig_identities} -> {new_identities}) -- aborting"
        )


def migrate_file(path: Path) -> bool:
    """Migrate a single weekly log file. Returns True if it was rewritten.

    Reads the original, computes the migration, verifies it independently,
    writes to a `.tmp` sibling, then atomically replaces the original. The
    original is never opened for writing; a failed verification raises
    SystemExit before any temp file is created.
    """
    original = path.read_text(encoding="utf-8")
    migrated = migrate_text(original)
    if migrated == original:
        return False
    verify_migration(original, migrated, path.name)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(migrated, encoding="utf-8")
    tmp.replace(path)
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--weekly-dir", type=Path,
                        default=REPO_ROOT / "logs" / "weekly")
    args = parser.parse_args()
    for path in sorted(args.weekly_dir.glob("week_*.md")):
        if migrate_file(path):
            print(f"compacted {path.name}")


if __name__ == "__main__":
    main()
