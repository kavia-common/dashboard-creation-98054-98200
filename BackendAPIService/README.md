# BackendAPIService

FastAPI backend providing:
- JWT authentication (`POST /login`)
- Protected CRUD endpoints for Users (`/users`) and Reports (`/reports`)
- Chart data endpoint (`GET /charts/data`)
- Dashboard overview endpoint (`GET /dashboard`)
- PostgreSQL integration via SQLAlchemy
- bcrypt password hashing
- OpenAPI docs at `/docs` and `/openapi.json`
- Production Dockerfile using Uvicorn

## Environment

Copy `.env.example` to `.env` and update values:
- DATABASE_URL (PostgreSQL URL or SQLite for local quick start)
- JWT_SECRET_KEY
- JWT_EXPIRES_MINUTES (optional)
- ADMIN_EMAIL / ADMIN_PASSWORD for seeding first admin on startup (optional)

Note: The app reads environment variables via pydantic BaseSettings. If required variables are missing (e.g. DATABASE_URL, JWT_SECRET_KEY), startup will fail.

## Run locally

Always target the correct module path `src.api.main:app`:

```bash
pip install -r requirements.txt

# Option A: direct uvicorn with explicit module path
uvicorn src.api.main:app --reload

# Option B: use the helper runner (ensures proper sys.path)
python -m src.run
```

Troubleshooting:
- Error: `ERROR: Error loading ASGI app. Could not import module "main".`
  This means the command attempted to load `main:app`. Use the full path `src.api.main:app` or `python -m src.run`.

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
- DATABASE_URL defaults to `sqlite:///./app.db` if not set (a file in container working dir).
- JWT_SECRET_KEY defaults to `insecure-dev-secret-change-me` if not set.
Always set proper values in production via env/Compose.

## OpenAPI

Generate and write to `interfaces/openapi.json`:
```bash
python -m src.api.generate_openapi
```
