#!/usr/bin/env bash
# Non-interactive CI lint runner for BackendAPIService.
# Uses the local flake8 shim to avoid dependency on a pre-created virtualenv.

set -euo pipefail
cd "$(dirname "$0")/.."

# Prefer requirements install if pip is available and no flake8 found.
if ! command -v flake8 >/dev/null 2>&1; then
  if [ -f "requirements.txt" ] && command -v python3 >/dev/null 2>&1; then
    python3 -m pip install --user -r requirements.txt >/dev/null 2>&1 || true
  fi
fi

# Run lint using the repo-local shim (falls back to user/system installs)
./flake8
