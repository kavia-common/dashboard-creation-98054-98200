#!/usr/bin/env bash
# CI linter bootstrap for dashboard-creation-98054-98200.
# Avoids reliance on a pre-created virtualenv and ensures flake8 is available.

set -euo pipefail

# Work from the BackendAPIService directory where the shim and requirements live.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
SERVICE_DIR="$REPO_ROOT/BackendAPIService"

cd "$SERVICE_DIR"

# Best-effort install of dependencies if flake8 isn't present.
if ! command -v flake8 >/dev/null 2>&1; then
  if command -v python3 >/dev/null 2>&1; then
    python3 -m pip install --user -r requirements.txt >/dev/null 2>&1 || true
  elif command -v python >/dev/null 2>&1; then
    python -m pip install --user -r requirements.txt >/dev/null 2>&1 || true
  fi
fi

# Use the repo-local flake8 shim which will locate or bootstrap flake8.
exec ./flake8
