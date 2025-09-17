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
- DATABASE_URL (PostgreSQL URL)
- JWT_SECRET_KEY
- JWT_EXPIRES_MINUTES (optional)
- ADMIN_EMAIL / ADMIN_PASSWORD for seeding first admin on startup (optional)

## Run locally

```bash
pip install -r requirements.txt
uvicorn src.api.main:app --reload
```

## Docker

```bash
docker build -t backend-service .
docker run --env-file .env -p 8000:8000 backend-service
```

## OpenAPI

Generate and write to `interfaces/openapi.json`:
```bash
python -m src.api.generate_openapi
```
