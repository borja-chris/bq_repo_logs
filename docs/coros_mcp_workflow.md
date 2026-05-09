# COROS MCP Workflow

## Setup

The COROS MCP server is installed outside this repository at:

```text
/home/blk_h/.codex/mcp/coros-mcp
```

Codex is configured to start it with:

```toml
[mcp_servers.coros]
command = "/home/blk_h/.codex/mcp/coros-mcp/.venv/bin/coros-mcp"
args = ["serve"]
```

The shell command `coros-mcp` is available through:

```text
/home/blk_h/.local/bin/coros-mcp
```

## Authentication

Run this once in a normal terminal:

```bash
coros-mcp auth
```

The server stores tokens locally after authentication. It should not require a
fresh login before every Codex session unless the token storage is cleared,
invalidated, or cannot refresh.

## Useful Commands

```bash
coros-mcp auth-status
coros-mcp cache-status
coros-mcp sync --from YYYYMMDD --to YYYYMMDD
```

Within Codex, use the COROS MCP tools for:

- recent activities
- activity detail
- daily metrics
- sleep data
- planned workouts
- structured workout creation

## First Sample Learning

The first sample pull on 2026-05-09 returned two same-day run activities close
together:

- 0.94 mi, 13:48, average HR 123, training load 12
- 3.15 mi, 26:47, average HR 173, training load 176

Interpretation: same-day adjacent activities should usually be reviewed as one
session when the earlier segment has warmup-like heart rate and load. Preserve
the underlying COROS activity IDs in any durable log so the raw data remains
traceable.

For weekly summaries, combine these only as a coaching interpretation. Do not
rewrite or hide the original COROS records.
