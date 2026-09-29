# Week of 2026-09-28 Work-Session Retro

## Label

- This is a work-session retrospective, not a training retrospective.

## Summary

- Imported six COROS activities (2026-09-21 through 2026-09-28), closing out week 8 (28.27/36 mi actual) and opening week 9.
- Reopened the SOS-reintroduction gate one week early (originally deferred to 2026-10-05) based on Sunday's fast long run (9:37/mi) and unlogged strides feeling great, recorded as an addendum to `decisions/2026-08-17_shin_splint_return_to_run_ramp.md`.
- Trimmed week 9's mileage from the original 44 mi grid target to ~35 mi at the runner's request (a 44 target was +16/56% over week 8's actual, judged too large a jump in the same week SOS returns), while keeping both SOS days and preserving Thursday > Tuesday ordering.
- Added the Tuesday strength workout's pace (8:28/mi) and rest-break detail (400m jog, ~2:50) to the plan and README, through three incremental edits.

## What Did Not Work

- Surfacing the Tuesday pace/rest-break detail into README took three separate round trips instead of one, because the generated-file mapping wasn't obvious going in: README's "Planned" column pulls from the plan file's **Run** cell (not its Notes cell, and not the weekly log's own `- Planned:` line), and README's "Notes" column only populates from the actual log entry post-run — so plan-file Notes/Purpose content never reaches README at all. First attempt edited the wrong field (the log's Planned line), which doesn't feed README; had to be diagnosed by reading `scripts/weekly_plan.py` mid-conversation.
- Also missed regenerating README's current-week block after an earlier plan edit (running `block_overview.py`/`status_digest.py` but not `ingest.sh --sync-only`), caught by the user asking "why is the README not updated?" — a second avoidable round trip in the same session.
- Both gaps are now captured as durable memory notes, but the underlying friction — an import/update routine spread across a shell script plus two standalone Python scripts, with a non-obvious source-to-generated-view mapping — is a repo-level rough edge, not just a one-off knowledge gap.

## Follow-Up

- Design question to resolve before implementation: what should a packaged "import routine" skill actually cover — fetch-only, fetch+ingest, or fetch+ingest+full regen+verify — and should pace/workout-detail edits to plan files be a documented part of that same routine (since they hit the same regeneration gaps)?

## Action Item

- Owner: Claude (Tech Lead)
- Action: Plan out packaging the import routine as an easily callable skill covering COROS fetch, ingest, all three derived-file regenerations (README sync via `ingest.sh --sync-only`, `block_overview.py`, `status_digest.py`), and verification (pytest + `check_markdown_links.py`) as one invocable unit. Decide where it should live (project `.claude/skills/`, a wrapper shell script, or a slash command) and how it interacts with the existing `importer-sonnet` subagent.
- Success condition: A written plan exists (not yet implemented) describing the skill's trigger name, scope, inputs/flags, and file location, ready for review and approval before building it.
- Status: Open.
