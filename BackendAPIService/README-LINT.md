# Linting in CI

Some CI environments call `flake8` directly from the repository without creating a virtualenv.
To ensure linting works reliably:

- A local shim `./flake8` is provided to proxy to a real flake8, creating one if needed.
- The `requirements.txt` already pins `flake8`, so running `pip install -r requirements.txt` will install it.

If your CI fails with `flake8: command not found`, ensure the repository root is on PATH or invoke:
```bash
./flake8
```

For local development:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
flake8
```
