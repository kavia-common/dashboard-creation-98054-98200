# dashboard-creation-98054-98200

CI notes:
- Linting is triggered via `.init/.linter.sh`, which delegates to `BackendAPIService/flake8`.
- The shim will attempt to install flake8 if missing and run lint non-interactively.