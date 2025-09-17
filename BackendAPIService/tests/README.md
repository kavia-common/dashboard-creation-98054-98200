# BackendAPIService Tests

This directory contains pytest-based tests for the FastAPI BackendAPIService.

What is covered:
- Authentication: JWT login success and invalid flows
- Authorization: Protected endpoints require Bearer token
- Users CRUD: list, create (admin vs user role rules), update, delete (self vs admin), error cases
- Reports CRUD: create (default owner, admin override), update/delete with ownership constraints, search and paging
- Charts and Dashboard: response shape validation and auth enforcement
- Error handling: validation errors, 401/403/404/400 paths

How tests run:
- Tests override the app's `get_db` dependency to use a dedicated SQLite database file (tests/conftest.py).
- DB schema is created at session start and dropped at end. Seed data includes:
  - Admin user: admin@example.com / adminpass
  - Normal user: user@example.com / userpass
  - Two sample reports for the normal user

Run tests locally (non-interactive/CI):
```bash
cd BackendAPIService
pytest -q
# or with more output
pytest -vv
```

Notes:
- JWT secret is set to a test value via environment variables in conftest.
- If running in a container, ensure requirements are installed (`pip install -r requirements.txt`).
