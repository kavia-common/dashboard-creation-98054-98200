# BackendAPIService

FastAPI backend providing secure JWT authentication, protected CRUD for users and reports, and chart data.

## Quick Start

1. Create environment:
   - Copy `.env.example` to `.env`
   - Set a strong `JWT_SECRET_KEY`

2. Install dependencies:
   - `pip install -r requirements.txt`

3. Run development server:
   - `uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000`

4. Docs:
   - Swagger UI: `/docs`
   - OpenAPI JSON: `/openapi.json`
   - Auth help: `/docs/auth`

## Authentication

- POST `/auth/login` with JSON `{ "email": "admin@example.com", "password": "Admin@12345" }`
- Use the returned `access_token` as a Bearer token:
  - `Authorization: Bearer <token>`

## Protected Endpoints

- Users: `GET/POST /users`, `PUT/DELETE /users/{id}`
- Reports: `GET/POST /reports`, `PUT/DELETE /reports/{id}`
- Charts: `GET /charts/data`

All require a valid Authorization header.

## Generate OpenAPI file

```
python -m src.api.generate_openapi
```

This writes `interfaces/openapi.json` for integration with other services.

## Notes

- This demo uses in-memory repositories. Replace with a database-backed repository (e.g., SQLAlchemy + PostgreSQL) for production.
- Password hashing uses bcrypt. Never store plaintext passwords.
