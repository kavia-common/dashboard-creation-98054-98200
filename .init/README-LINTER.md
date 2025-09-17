This directory contains CI helper scripts.

If your CI runner invokes `flake8` directly and does not preinstall it, a local shim `./flake8` is provided here to resolve to:
- System flake8 if available,
- BackendAPIService-local shim (`../BackendAPIService/venv/bin/flake8` or `../BackendAPIService/flake8`),
- Or installs flake8 in user site packages and re-invokes it.

No changes are required if your CI environment already has flake8 available.
