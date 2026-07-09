#!/usr/bin/env bash
#
# Canonical COROS ingest entry point.
#
# Always runs scripts/ingest_coros_fit.py under the repo's .venv interpreter so
# the FIT parser dependencies are guaranteed present. Running the ingest under a
# bare system python silently lacks the parser and aborts mid-run; this wrapper
# removes that footgun and fails loudly with the setup hint if the venv is not
# ready. All arguments are passed straight through to ingest_coros_fit.py.
#
# Usage:
#   scripts/ingest.sh
#   scripts/ingest.sh --manual-note "2026-07-08|Longer run, felt good"
#   scripts/ingest.sh --sync-only
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
venv_python="${repo_root}/.venv/bin/python"
ingest_script="${repo_root}/scripts/ingest_coros_fit.py"

hint() {
  echo "  Fix: run 'bash scripts/setup_fit_env.sh' to build the .venv with FIT deps." >&2
}

if [[ ! -x "${venv_python}" ]]; then
  echo "error: ${venv_python} not found or not executable." >&2
  hint
  exit 1
fi

# The interpreter existing is not enough — the failure we actually hit was a
# venv whose FIT parser deps were missing. Verify the parser is importable
# before touching any files, reusing the script's own availability check so this
# preflight never drifts from the real requirement (accepts fitparse OR fitdecode).
if ! "${venv_python}" -c "import sys; sys.path.insert(0, '${repo_root}/scripts'); import ingest_coros_fit_batch as b; sys.exit(0 if b.fit_parser_available() else 1)" >/dev/null 2>&1; then
  echo "error: FIT parser dependencies are unavailable in ${venv_python}." >&2
  hint
  exit 1
fi

exec "${venv_python}" "${ingest_script}" "$@"
