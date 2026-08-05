# COROS MCP → FIT Fetch Integration

**Date:** 2026-08-04
**Status:** Approved for implementation

## Problem

The only manual step in the ingest workflow is the operator dropping `.fit`
files at the repo root. COROS now publishes an MCP server
(`https://mcpus.coros.com/mcp`) that exposes activity records and original FIT
file download URLs. Fetching those files automatically removes the last manual
step without changing how records are written.

## Verified Findings

These were confirmed against the live service on 2026-08-04, not assumed:

- **Endpoint.** `https://mcp.coros.com/mcp` is a geo-router whose protected-resource
  metadata declares `https://mcpus.coros.com/mcp`. Registering the router URL
  fails Claude Code's RFC 9728 resource-URI check; the regional host must be
  registered directly.
- **Auth.** Dynamic client registration, PKCE-S256, and `offline_access` are all
  supported, so Claude Code completes the OAuth flow itself and holds a refresh
  token. Authentication must be done interactively (`/mcp`); a non-TTY invocation
  cannot complete it.
- **FIT URLs need no auth.** `queryActivityFitFileDownloadUrls` returns a plain
  `s3.coros.com` URL that fetches with a bare `curl` (HTTP 200, 218,075 bytes,
  valid `.FIT` magic). The download step therefore requires no credentials.
- **Downloaded FIT files are pipeline-compatible.** Passing a downloaded file
  through `summarize_coros_fit.parse_fit` yielded `sport=running`,
  `start_time=2026-08-04T17:20:35-04:00`, `distance_mi=9.01`, `duration_s=5854`,
  `avg_hr=144`, `max_hr=170`, `ascent_m=110`.
- **`max_hr` is FIT-only.** Neither `querySportRecords` nor `getActivityDetail`
  returns it, but the FIT file does. This is the decisive reason to fetch files
  rather than scrape the summary endpoints.
- **Missing lat/long is pre-existing.** The downloaded file parsed with empty
  `latitude`/`longitude`, but so does every historical row in
  `data/processed/*.jsonl`. Not a regression. `querySportRecords` does return
  start coordinates, so this path can capture data the FIT path never had.

## Architecture

Only metadata crosses the model boundary. Claude makes the MCP calls and emits a
manifest; a plain script does everything touching disk. No FIT bytes pass
through context and no auth code exists in the repo.

```
Claude:  querySportRecords ──► queryActivityFitFileDownloadUrls ──► manifest JSON
                                                                        │
Script:  scripts/fetch_coros.py ◄───────────────────────────────────────┘
                │ download → <repo_root>/<labelId>.fit
                ▼
         bash scripts/ingest.sh   (unchanged — globs *.fit at repo root)
                ▼
         data/coros_exports/ · data/processed/ · logs/weekly/ · STATUS.md
```

The seam is `find_loose_fit_files()` in `scripts/ingest_coros_fit_batch.py`,
which globs `*.fit` at the repo root. Landing bytes there is indistinguishable
from a manual drop, so the entire downstream pipeline is untouched.

## Component: `scripts/fetch_coros.py`

**Invocation**

```
.venv/bin/python scripts/fetch_coros.py --manifest -        # read stdin
.venv/bin/python scripts/fetch_coros.py --manifest FILE
.venv/bin/python scripts/fetch_coros.py --manifest - --dry-run
```

**Manifest format** — a JSON array. `labelId`, `sportType`, `date`, and `url` are
required; `latitude` and `longitude` are optional.

```json
[{"labelId": "479396244626636805", "sportType": 100, "date": "2026-08-04",
  "url": "https://s3.coros.com/fit/452218867308052480/479396244626636805.fit",
  "latitude": 40.811001, "longitude": -73.954002}]
```

**Behavior**

1. Load the ledger; fail loudly if it is corrupt.
2. Skip manifest entries whose `labelId` is already in the ledger.
3. Download each remaining URL to `<repo_root>/<labelId>.fit`.
4. Validate: non-empty and `.FIT` magic present at bytes 8–11.
5. Append a ledger entry per file that landed successfully.
6. Print a summary (fetched / skipped / failed) and the next command to run.

`--dry-run` reports the fetch/skip decision for every entry and touches neither
the network nor disk.

## Dedup Ledger

`data/coros_fetch_ledger.json`, keyed by `labelId`:

```json
{"479396244626636805": {"sportType": 100, "date": "2026-08-04",
  "sha256": "...", "fetched_at": "2026-08-04T18:02:11-04:00",
  "latitude": 40.811001, "longitude": -73.954002,
  "filename": "479396244626636805.fit"}}
```

Dedup is keyed on `labelId` rather than file hash because the skip decision must
happen *before* downloading — FIT downloads are rate-limited daily (max 10 per
call plus a daily cap), so a repeated sync must not spend quota re-fetching known
activities.

Entries are written when the file lands on disk, not after ingest completes. If
ingest fails afterward, the `.fit` remains at the repo root and the next
`ingest.sh` run sweeps it up, so the ledger never blocks recovery.

## Coordinates

Recorded in the ledger; deliberately **not** wired into
`scripts/ingest_coros_fit_weather.py`. The MCP record list is the only source for
start coordinates and storing them costs nothing, but consuming them is a
separate change with its own risk. The value of this change is that the ingest
path stays byte-identical, and bundling a weather change would forfeit that.

## Error Handling

| Condition | Behavior |
|---|---|
| HTTP failure | Delete partial file, no ledger entry, non-zero exit |
| Missing/invalid `.FIT` magic | Delete file, no ledger entry, non-zero exit |
| Target path already exists | Skip with warning; never overwrite |
| Corrupt ledger | Fail loudly; never silently reset |
| Malformed manifest entry | Fail before any download |

Every failure mode leaves a retry safe: nothing partial is recorded, so re-running
the same manifest resumes cleanly.

## Testing

`tests/test_fetch_coros.py`, following existing repo test patterns, with no
network access — the downloader is monkeypatched and a minimal FIT-magic fixture
stands in for real files. Cases:

- Ledger skip: a `labelId` already present is not downloaded.
- Magic-byte rejection: a non-FIT payload fails and leaves no ledger entry.
- Partial cleanup: a mid-download failure removes the partial file.
- Dry-run: no network calls, no disk writes, correct decisions reported.
- Malformed manifest: rejected before any download begins.
- Existing target file: skipped with a warning, not overwritten.

Full verification: `.venv/bin/python -m pytest tests/ -q &&
.venv/bin/python scripts/check_markdown_links.py &&
.venv/bin/python scripts/status_digest.py`

## Non-Goals

- No OAuth or MCP protocol code in the repo; Claude Code owns the connection.
- No cron or unattended scheduling. Sync runs when the operator asks.
- No changes to `ingest.sh`, `ingest_coros_fit.py`, or any existing script.
- No weather-enrichment wiring.

## Operating Flow

1. Operator: "sync COROS."
2. Claude calls `querySportRecords` for the range, then
   `queryActivityFitFileDownloadUrls` for activities not already in the ledger.
3. Claude pipes the manifest to `scripts/fetch_coros.py`.
4. Claude runs `bash scripts/ingest.sh`, verifies the runs landed in the correct
   `logs/weekly/week_*.md`, and commits.

The operator's manual step becomes a sentence instead of a file drop.

## First Use

Backfill the gap between the last export batch (`COROS_export_2026-07-23`,
processed through the 07-22 run) and today: runs dated 07-29, 07-31, 08-02,
08-03, and 08-04. Five activities fits inside the 10-per-call limit, so this is a
single pass.
