# CI Linting

Some CI runners do not provision a Python virtualenv before running lint, and the default script may attempt to `source venv/bin/activate` and run `flake8`, which fails.

Use the provided non-interactive CI lint script instead:

```bash
bash BackendAPIService/scripts/ci_lint.sh
```

This script:
- Installs requirements to the user site if needed (best-effort, non-fatal),
- Uses the repo-local `./flake8` shim that will locate or bootstrap flake8 if missing,
- Runs lint against the codebase.

If your CI must call `flake8` directly, call `./flake8` from the BackendAPIService root.
