Security Overview

Authentication
- JWT-based authentication using HS256.
- Token includes `sub` with `id`, `email`, and `role`, and an `exp` claim.
- All protected endpoints require `Authorization: Bearer <token>`.

Password Management
- Passwords are hashed with bcrypt (12 rounds).
- Plaintext passwords are never stored.
- On login errors, responses do not reveal whether the email or password was incorrect.

Environment and Secrets
- Set JWT_SECRET_KEY to a strong, secret value in production.
- Use a managed PostgreSQL and set DATABASE_URL via environment variables or secrets.
- Avoid using the default SQLite and dev secret in production.

CORS
- Defaults are permissive for development. Lock down origins, methods, and headers in production.

Logging and Error Handling
- Logs avoid sensitive information.
- Generic 500 error responses do not leak stack traces or internals.

Admin Seeding
- ADMIN_EMAIL and ADMIN_PASSWORD seed an initial admin only when no users exist.
- Rotate admin credentials after initial deployment.

Transport Security
- Deploy behind HTTPS (e.g., reverse proxy or load balancer).
- Proxy headers enabled in Uvicorn command to support upstream proxies.

Dependency Management
- Dependencies are pinned in requirements.txt.
- Update and review regularly for security patches.
