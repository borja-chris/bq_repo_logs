# 2026-07-08 Daily-Log Archive Automation Work Retro

## Label

- This is a work-session retrospective, not a training retrospective.

## Summary

- Trigger: a "what was the last entry?" question surfaced that the last daily log was `2026-06-12`, an apparent ~26-day gap to today (`2026-07-08`).
- Diagnosis: not a logging gap. From the week of `2026-06-15` the workflow deliberately moved daily entries *into* the weekly logs (`docs/repo_workflow.md`: "Do not create standalone daily log files"), so `2026-06-13`–`2026-07-08` was fully captured. The real defect was a missed Monthly Archive Rule run: June's 11 loose `logs/daily/2026-06-*.md` files were never moved into `logs/daily/2026/2026-06/`.
- Result: remediated June (`47bd771`), then — after EM feedback that this must never be manual — automated prior-month daily-log archiving into the ingest process (`b1ca4e5`), so the only manual step remains uploading `.fit` files.

## What Worked

- Refused the face-value framing. Reading `docs/repo_workflow.md` before acting reframed a "26 missing days" panic into "one un-run archive step," and prevented backfilling 26 standalone daily files — which the workflow explicitly forbids. Diagnosis before remediation avoided doing the wrong thing efficiently.
- Applied the prior session's action item. Both subagents were pinned to Sonnet (lesser model) per the Collaboration Model, so delegation actually bought token efficiency this time — closing the loop on the `2026-07-08` race-equivalency retro's action item, which flagged that delegated agents had previously inherited Opus.
- The implementation subagent caught a determinism mismatch on its own: June's manually-written `monthly_summary.md` had hand-paraphrased notes that a deterministic renderer can't reproduce. It surfaced this to the EM instead of hacking a false byte-match — good verification judgment.
- Designed for non-recurrence, not just repair. `monthly_archive.py` is idempotent and self-healing (no-op when nothing is loose), so this class of bug cannot recur rather than being patched once.
- Verified before every commit: 38 unit tests, markdown link checker, and a live `ingest_coros_fit.py` no-op smoke run proving both the wiring and the idempotent steady state.

## What Did Not Work

- Under-reached on the first proposal. After remediating June, the initial suggestion was a *guard/checker* that would flag loose files — still leaving a manual step. The EM had to redirect to "this shouldn't be manual at all; automate it into the process." The right altitude was full automation, not a smarter reminder.
- The first (manual) June archive produced paraphrased notes, which then had to be regenerated to the deterministic verbatim output and the golden test tightened to byte-equality. Had the automation existed first, this rework would not have happened — a small cost of remediating by hand before building the tool.
- Minor: the first commit's `git add` included already-moved source paths that no longer existed in the working tree and failed; re-staged with only the new file (renames were already staged). Self-corrected, one wasted call.

## Changes Made

- `47bd771` — archived June's 11 daily logs into `logs/daily/2026/2026-06/` with a generated `monthly_summary.md`.
- `b1ca4e5` — added `scripts/monthly_archive.py` (finds loose prior-month `logs/daily/*.md`, moves them, regenerates `monthly_summary.md`; idempotent); wired `run_monthly_archive(today)` into `ingest_coros_fit.py` with a `--no-archive` escape hatch; refactored `weekly_entries.py` to extract `parse_daily_log_text(day_date, text)` for reuse and testability; added `tests/test_monthly_archive.py` (move / current-month-untouched / aggregate / idempotency / byte-for-byte golden — 38 tests total); regenerated June's summary as deterministic output; documented the automation in `docs/repo_workflow.md`.

## Follow-Up

- COROS export-batch archiving (`scripts/archive_coros_export.py`) — the other half of the Monthly Archive Rule — is still a separate manual step. It is riskier to auto-run (tar creation, membership verification, JSONL rewrites), so it was left manual and marked as such in the doc. Full "only upload `.fit`" parity requires wiring it into ingest too.

## Action Item

- Owner: Claude (Tech Lead)
- Action: draft a scoped plan to wire COROS export-batch archiving into the ingest process (auto-archive completed prior-month batches, with the same idempotent/verify-before-destroy discipline as `monthly_archive.py`), and present it to the EM for approval before implementing.
- Success condition: the EM has reviewed a concrete plan covering how "completed batch" is detected, how archive membership is verified before loose `.fit` removal, and how failures are surfaced — and has either approved implementation or explicitly deferred it. Until then, no batch files are auto-deleted.
