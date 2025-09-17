#!/usr/bin/env bash
# Idempotent bootstrap to satisfy CI linter expectations:
# - Create a local virtualenv at ./venv if missing
# - Install pinned requirements (includes flake8)

set -euo pipefail

if [ ! -d "venv" ]; then
  # Prefer python3 -m venv when available
  if command -v python3 >/dev/null 2>&1; then
    python3 -m venv venv
  elif command -v python >/dev/null 2>&1; then
    python -m venv venv
  else
    echo "Error: python3/python not found for virtualenv creation." >&2
    exit 1
  fi
fi

# Activate the venv non-interactively
# shellcheck disable=SC1091
source venv/bin/activate

# Upgrade pip for reliability, but do not fail the bootstrap if upgrade has issues
python -m pip install --upgrade pip || true

# Install project requirements which include flake8
pip install -r requirements.txt

echo "Bootstrap complete: virtualenv ready and flake8 installed."
