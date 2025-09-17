# Contributing

## Environment Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

## Linting
Project uses flake8 with config in `.flake8`.

```bash
flake8
```

If your environment lacks flake8, install dependencies with:
```bash
pip install -r requirements.txt
```

In CI or minimal environments where `venv` or `flake8` isn't available, use the repo-local shim:
```bash
./flake8
```

## Running
```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 3001 --proxy-headers
# or
python -m src.run
```

## OpenAPI export
```bash
python -m src.api.generate_openapi
```
