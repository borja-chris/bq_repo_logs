# Import Runbook

End-to-end procedure for "let's do another import", from an empty repo root to
a pushed commit. Written to be executable by a Sonnet-tier agent with no prior
session context: every step below is either a literal command or a rule with
its failure mode stated.

`docs/repo_workflow.md` → "Data Import Loop" describes what the ingest script
does once `.fit` files exist. This runbook covers the steps on either side of
it: finding the activities, and integrating the result.

## 0. Preconditions

- Interpreter is always `.venv/bin/python`. Bare `python` is not installed and
  system `python3` lacks the FIT deps.
- The COROS MCP server (`mcp__coros__*` tools) must be reachable. If its tools
  are unavailable, stop and report — the operator's only manual fallback is
  dropping `.fit` files in the repo root, after which you resume at step 4.

## 1. Find the gap

Read `STATUS.md` (root, regenerated on every ingest). It gives the last logged
*week* and the day of week ("Sunday run logged") — not a date. To get the date,
open that week's `logs/weekly/week_YYYY-MM-DD.md` and find the last
`### YYYY-MM-DD` block with a non-empty `Completed:` line.

Then query from **14 days before that day** through today. Not the day after it:
a `.fit` file uploaded late carries its *activity* date, which can fall before
the last logged day, so a range that starts after the last logged day misses
late arrivals completely — the single most likely way to silently lose a run.

Over-requesting is free. `querySportRecords` is not rate-limited and the fetch
ledger dedups anything already imported, so the lookback costs one tool call and
nothing else. Do not narrow the range to "what the user mentioned" either — they
routinely mention one run and have three activities on the watch.

## 2. List activities (`querySportRecords`)

Pass **only** `startDate`, `endDate`, `sportTypeCodes`, `limit`:

```json
{"startDate": "20260805", "endDate": "20260817",
 "sportTypeCodes": [100, 101, 102, 103, 104, 900], "limit": 20}
```

- The tool's schema marks every optional filter as `required`. Ignore that:
  omitting the keys works, and passing explicit `null` for any of them
  (`minDistanceKm`, `maxAveragePace`, `locationKeyword`, …) is rejected
  server-side with `Tool call anomalies detected… Initialize a new session to
  reset context`. That advice is wrong — it is not a context problem and a new
  session will not help. Omit the keys.
- Include the non-running codes `104` (hike) and `900` (walk) alongside the run
  codes `100-103`. Recovery blocks and cross-training days are exactly the ones
  worth importing, and a run-only query silently misses them.
- Output gets lossily compressed in transit past ~8 records (labels stripped).
  If you get more than 8, re-query in narrower ranges and cross-check labelIds
  before treating them as load-bearing.

Record for each activity: `LabelId`, `SportType`, date, and start coordinates.

## 3. Get FIT URLs (`queryActivityFitFileDownloadUrls`)

One call per activity, `labelId` + `sportType`:

```json
{"labelId": "479580047219392514", "sportType": 100}
```

- The **date-range form** (`startDate`/`endDate`, with or without `sportType`)
  is rejected the same way as above. It is the shape that looks efficient; it
  does not work.
- **Returned URLs count against the daily FIT quota**, same as downloads. Before
  querying, drop any labelId already present in `data/coros_fetch_ledger.json` —
  the ledger skip in `fetch_coros.py` happens *after* the quota is spent.
- URLs are `https://s3.coros.com/fit/<userId>/<labelId>.fit`.

## 4. Fetch

Write the manifest to the session scratchpad (not the repo). It is a JSON array;
`labelId`, `sportType`, `date` (`YYYY-MM-DD`), `url` are required, `latitude`
and `longitude` optional but worth carrying — they feed weather enrichment.

```json
[{"labelId": "479580047219392514", "sportType": 100, "date": "2026-08-12",
  "url": "https://s3.coros.com/fit/452218867308052480/479580047219392514.fit",
  "latitude": 40.811001, "longitude": -73.954002}]
```

```bash
.venv/bin/python scripts/fetch_coros.py --manifest <path> --dry-run
.venv/bin/python scripts/fetch_coros.py --manifest <path>
```

Expect a `N fetched, N skipped, N failed` summary and `<labelId>.fit` files in
the repo root. Any `failed` count is a stop-and-report.

## 5. Ingest, with the user's notes attached

Everything the user said about how the runs went goes in on this command — not
into a later hand edit of the weekly log.

```bash
bash scripts/ingest.sh \
  --manual-note "2026-08-12|Run cut short by shin splints; stopped early." \
  --soreness "2026-08-12|Shin splints — pain forced an early stop." \
  --manual-note "2026-08-16|Recovery-mode hike, no running."
```

All flags are repeatable and all are `"YYYY-MM-DD|text"`. Map the user's prose:
pain/tightness/niggle → `--soreness`; "didn't sleep" → `--sleep`; work/life load
→ `--stress`; anything that should trip a warning → `--warning-signs`;
everything else → `--manual-note`. Attribute each note to the date of the
activity it describes, which is often not today.

Then confirm the run landed where you expect by reading
`logs/weekly/week_YYYY-MM-DD.md` for the **activity's** Monday-dated week. Import
date ≠ activity date; files arrive days or months late.

## 6. Verify

```bash
.venv/bin/python -m pytest tests/ -q \
  && .venv/bin/python scripts/check_markdown_links.py \
  && .venv/bin/python scripts/status_digest.py
```

Once, after ingest. Read the touched weekly log once and check the day blocks
against the `querySportRecords` output you already have — distance, duration,
pace, date.

## 7. Commit and push

Stage explicit paths. Never `git add -A` / `git add .` — untracked local tooling
(`CLAUDE.local.md`, `.codex`, `.tokensave/`) sits at root and would be swept in.
A typical import touches:

```text
README.md STATUS.md data/coros_fetch_ledger.json
data/coros_exports/COROS_export_YYYY-MM-DD
data/processed/coros_export_YYYY-MM-DD_summary.jsonl
logs/weekly/week_YYYY-MM-DD.md
```

Work goes straight to `main`; commit, then push. A sub-agent running this
runbook stops at step 6 and hands the dispatcher the file list — sub-agents
never commit.

## Known reporting quirk

The weekly auto-summary's "Actual mileage" sums **all** imported activities,
including hikes and walks. A recovery week with a 6.89 mi hike reports 8.62 mi
against a running target of 31. Flag the split in your summary to the user
(running miles vs. total); do not hand-edit the generated block to hide it.
