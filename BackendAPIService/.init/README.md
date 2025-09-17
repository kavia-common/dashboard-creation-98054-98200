This directory contains initialization helpers for CI and local linting.

If your CI linter expects a `venv/` and `flake8` in PATH, run:
```bash
bash ../.init_bootstrap.sh
```
This creates `./venv`, installs pinned requirements (including flake8), and lets the linter script proceed.
