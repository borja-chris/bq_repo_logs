# Scripts

This directory is reserved for repeatable repo operations.

Near-term candidates:

- Weekly rollover helper: create the weekly log summary, daily-entry scaffolding, and weekly retro from templates.
- Decision gate helper: collect recent weekly retros before mileage or workout changes.

## FIT Summaries

The expected operator flow is:

1. Drop new `.fit` files in the repo root.
2. Run `ingest_coros_fit.py` to move them into a dated batch folder under `data/coros_exports/`, produce processed summaries, and sync the repo records.
3. Archive completed prior-month batches later with `archive_coros_export.py`.

Primary command:

```bash
.venv/bin/python scripts/ingest_coros_fit.py
```

Recommended setup for fresh environments:

```bash
bash scripts/setup_fit_env.sh
.venv/bin/python scripts/ingest_coros_fit.py
```

Optional flags:

```bash
.venv/bin/python scripts/ingest_coros_fit.py --sync-only
.venv/bin/python scripts/ingest_coros_fit.py --date 2026-05-14
.venv/bin/python scripts/ingest_coros_fit.py --no-readme
.venv/bin/python scripts/ingest_coros_fit.py --no-logs
.venv/bin/python scripts/ingest_coros_fit.py --require-weather
.venv/bin/python scripts/ingest_coros_fit.py --manual-note "2026-06-16|Legs felt fatigued but not injured."
.venv/bin/python scripts/ingest_coros_fit.py --manual-note "2026-06-16|Felt heavy by the end." --soreness "2026-06-16|Legs felt tired but structurally fine."
```

`--sync-only` also re-attempts weather enrichment for that import date's processed batch
when weather is enabled, which makes it the repair path after a transient API or DNS
failure during the original import.

When the user gives subjective context in the same turn as a FIT ingest request, pass
that context through the ingest command instead of relying on a separate manual edit
later. `--manual-note` appends bullet notes under `- Manual Notes:`. `--sleep`,
`--soreness`, `--stress`, and `--warning-signs` set the matching recovery fields for
that day.

For normal imports going forward, prefer `--require-weather` so the command fails
instead of silently leaving weather fields blank.

`ingest_coros_fit.py` is the operator-facing entry point. It handles:

- moving loose root-level `.fit` files into the dated batch folder
- removing `:Zone.Identifier` sidecars
- writing `SHA256SUMS.txt`
- generating JSONL processed summaries
- upserting matching daily-entry blocks inside the active weekly log from objective FIT fields while preserving manual notes
- attaching explicitly supplied same-turn subjective notes to the matching daily entry during ingest
- creating daily-entry stubs for past skipped planned run days so manual context has a place to live
- refreshing `logs/weekly/`
- refreshing the managed current-week block in `README.md`
- writing the batch manifest

`summarize_coros_fit.py` reads FIT files from an import directory and writes a newline-delimited JSON (`.jsonl`) summary to `data/processed/` with stable machine-oriented fields such as the import batch, repo-relative source path, FIT activity ID, and SHA-256 hash.

Example:

```bash
.venv/bin/python scripts/summarize_coros_fit.py \
  data/coros_exports/COROS_export_2026-05-09 \
  data/processed/coros_export_2026-05-09_summary.jsonl
```

It requires FIT parser dependencies from `requirements-fit.txt`. `fitdecode` is the practical default for COROS files, with `fitparse` available alongside it.

Current repo note:

- Prior successful COROS imports in this repo used `fitdecode`.
- Fresh environments should be bootstrapped with `bash scripts/setup_fit_env.sh` before FIT ingestion.

The ingest script automates objective recordkeeping and can persist explicitly supplied
subjective daily notes during import. Coaching interpretation, retros, and plan changes
remain manual.

Weekly logs use a mixed-source model:

- The top weekly summary is owned by the ingest script for objective context.
- Manual weekly notes and follow-up items stay in the same top summary section.
- `## Daily Entries` contains per-day blocks where objective fields are updated and manual notes stay attached to that day.

## FIT Archiving

`archive_coros_export.py` packs the loose FIT files in one export batch into `fit_files.tar.gz`, updates the matching processed JSONL sidecar with archive metadata, verifies archive membership, and then removes the loose `.fit` files.

Archive policy:

- Keep current-month FIT files loose after import.
- On the first maintenance pass of a new month, archive completed batches from the previous month.
- Do not archive a batch until its processed summaries already exist.

Example:

```bash
.venv/bin/python scripts/archive_coros_export.py data/coros_exports/COROS_export_2026-05-09
```

Keep scripts small and reviewable. The Markdown files remain the system of record.

## Markdown Link Check

`check_markdown_links.py` scans Markdown files for GitHub-unsafe link targets such as:

- absolute local filesystem paths like `/home/...`
- `file://...` links
- root-relative paths like `/docs/...` that GitHub resolves outside the repo

Example:

```bash
.venv/bin/python scripts/check_markdown_links.py
```

## Weekly Mileage Reconciliation

`reconcile_weekly_mileage.py` checks that every rendered weekly log's
`Actual mileage so far` equals the sum of `distance_mi` for that week's
activities in `data/processed/*.jsonl`. Historical logs can silently drift from
the source data (for example a stale mid-week snapshot that was never
re-rendered); this surfaces that drift deliberately instead of by accident during
an unrelated full re-render. Exits `0` when everything reconciles and `1` with an
expected-vs-actual line per mismatch.

Example:

```bash
.venv/bin/python scripts/reconcile_weekly_mileage.py
```

## Race Equivalency & Training Paces

`race_equivalency.py` converts a recent race result into (a) equivalent race
times across the standard distances and (b) Hansons training paces, so plan
paces can be anchored to a measured race instead of a top-down goal time. It is
a repo reimplementation of the Luke Humphrey Running (Hansons) Race Equivalency
Calculator, verified to within about 1 second of that calculator from 5k up.

Method: it uses Pete Riegel's endurance model, `T2 = T1 * (D2/D1)^k`, with
`k=1.06` for distances at or above 5k (exact against LHR) and `k=1.08` below 5k
(approximate, within about 5s). Training paces are fixed offsets from the
equivalent race paces: Easy = Marathon pace +1:30..+2:30/mi; Half tempo =
Half-marathon pace; Threshold = 10k..HM pace; Speed = 5k..10k; VO2max = 3k..5k;
Strength = Marathon pace -10s; Strides = mile pace -30s..mile pace.

Examples:

```bash
.venv/bin/python scripts/race_equivalency.py 5k 25:30
# reverse a goal time into the fitness/paces it requires
.venv/bin/python scripts/race_equivalency.py half 1:33:00
# custom distance in meters
.venv/bin/python scripts/race_equivalency.py --distance-m 5021 25:32
```

Accepted distance aliases: `mile`, `3k`, `5k`, `8k`, `10k`, `12k`, `15k`,
`10mile`, `20k`, `half`, `25k`, `30k`, `marathon` (or `--distance-m` for a
custom distance in meters). Time accepts `H:MM:SS`, `MM:SS`, or plain seconds.

Trimmed output for `race_equivalency.py 5k 25:30`:

```
Input: 5k  25:30  (8:12/mi)

Equivalent race performances (Riegel k=1.06):
  Distance              Time   Pace/mi
  1 Mile                7:30      7:30
  5k                   25:30      8:12
  10k                  53:10      8:33
  Half Marathon      1:57:18      8:57
  Marathon           4:04:34      9:20

Training paces (Hansons offsets from equivalent race pace):
  Easy                        10:50 - 11:50/mi
  Speed (5k-10k)                8:12 - 8:33/mi
  VO2max (3k-5k)                7:53 - 8:12/mi
  Lactate threshold (10k-HM)    8:33 - 8:57/mi
  Strength (MP-10s)                    9:10/mi
  Half tempo / HMP                     8:57/mi
  Strides                       7:00 - 7:30/mi
```
