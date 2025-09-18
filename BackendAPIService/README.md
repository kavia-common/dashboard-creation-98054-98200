# BackendAPIService

FastAPI backend providing:
- JWT authentication (`POST /login`)
- Protected CRUD endpoints for Users (`/users`) and Reports (`/reports`)
- Chart data endpoint (`GET /charts/data`)
- Dashboard overview endpoint (`GET /dashboard`)
- PostgreSQL (or SQLite dev) via SQLAlchemy ORM
- bcrypt password hashing
- OpenAPI docs at `/docs` and `/openapi.json`
- Production Dockerfile using Uvicorn

## Environment

Copy `.env.example` to `.env` and update values:
- DATABASE_URL (PostgreSQL URL recommended; SQLite is allowed for local quick start)
- JWT_SECRET_KEY (REQUIRED in production)
- JWT_EXPIRES_MINUTES (optional; default 60)
- ADMIN_EMAIL / ADMIN_PASSWORD for seeding first admin on startup (optional)
- CORS_* values as needed

Note: The app reads environment variables via Pydantic BaseSettings. Safe defaults are applied for dev usage so the app can start even if some envs are missing.

CORS configuration
- CORS_ALLOW_ORIGINS supports:
  - Single origin string: http://localhost:3000
  - Comma-separated string: http://localhost:3000,http://127.0.0.1:3000
  - JSON list string: ["http://localhost:3000","http://127.0.0.1:3000"]
  - Unset or empty defaults to ["*"] in development
- CORS_ALLOW_METHODS and CORS_ALLOW_HEADERS accept "*", comma-separated strings, or JSON list strings.
- CORS_ALLOW_CREDENTIALS is a boolean ("true"/"false").

If parsing fails, the app raises a clear validation error indicating which CORS_ variable has an invalid format. Use .env.example as a reference.

## Run locally

Always target the correct module path `src.api.main:app`:

```bash
pip install -r requirements.txt

# Option A: direct uvicorn with explicit module path
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 3001

# Option B: use the helper runner (ensures proper sys.path)
python -m src.run
```

Troubleshooting:
- Error: `ERROR: Error loading ASGI app. Could not import module "main".`
  This means the command attempted to load `main:app`. Use the full path `src.api.main:app` or `python -m src.run`.
  Note: A compatibility shim `main.py` is included to support environments that insist on `uvicorn main:app`. Prefer the canonical path `src.api.main:app`.
- Error: SettingsError / ValidationError for CORS_ALLOW_ORIGINS, CORS_ALLOW_METHODS, or CORS_ALLOW_HEADERS:
  Ensure the environment variable value is one of:
  - Single origin: http://localhost:3000
  - Comma-separated: http://localhost:3000,http://127.0.0.1:3000
  - JSON list string: ["http://localhost:3000","http://127.0.0.1:3000]
  For development, you may leave it unset or empty to default to ["*"]. See .env.example.

## Docker

Service listens on port 3001 inside the container.

```bash
docker build -t backend-service .
docker run --env-file .env -p 3001:3001 backend-service
```

The Dockerfile runs:
```
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "3001", "--proxy-headers"]
```
which ensures the correct import path and port inside the container.

Healthcheck hits `http://localhost:3001/`.

Environment variable defaults for local/dev:
- DATABASE_URL defaults to `sqlite:///./app.db` (file in container working dir).
- JWT_SECRET_KEY defaults to `insecure-dev-secret-change-me`.
Always set proper values in production via env/Compose/Secrets.

### Database readiness and port 3001 not ready

If the backend is not reported as ready on port 3001, verify:

1) Correct DATABASE_URL:
- For PostgreSQL (RelationalDatabase), use:
  `postgresql+psycopg2://<user>:<password>@<host>:<port>/<db>`
  In Docker Compose, <host> is usually the service name (e.g., `relationaldatabase`).

2) Database availability at startup:
- The service implements a retry/backoff on startup to wait for the DB to accept connections.
- You can tune with env:
  - DB_CONNECT_MAX_ATTEMPTS (default 20)
  - DB_CONNECT_BASE_DELAY (default 0.5s)
  - DB_CONNECT_MAX_DELAY (default 5.0s)

3) Logs:
- Startup logs include the database dialect and connectivity attempts.
- Look for "Database connectivity verified" or "Database not ready ... Retrying".

4) Health endpoint:
- `/` returns a simple JSON health. The API will still come up even if DB is temporarily unavailable; DB-dependent endpoints will return errors until the DB is reachable.

See `.env.example` for full configuration.

## API Overview

- POST `/login` — returns JWT token. Body: `{ "email": "...", "password": "..." }`
- GET `/users` — list users (auth required)
- POST `/users` — create user (auth required; only admin can set role)
- PUT `/users/{user_id}` — update user (auth required; admin for role changes)
- DELETE `/users/{user_id}` — delete user (auth required; admin or self)
- GET `/reports` — list reports (auth required)
- POST `/reports` — create report (auth required)
- PUT `/reports/{report_id}` — update report (auth required; owner or admin)
- DELETE `/reports/{report_id}` — delete report (auth required; owner or admin)
- GET `/charts/data` — chart datasets (auth required)
- GET `/dashboard` — dashboard aggregates (auth required)

All protected endpoints require `Authorization: Bearer <token>` header.

## OpenAPI

Generate and write to `interfaces/openapi.json`:
```bash
python -m src.api.generate_openapi
```
