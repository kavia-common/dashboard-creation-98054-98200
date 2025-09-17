"""
API package initializer.

Exposes the FastAPI application instance as `app` for external imports such as
Uvicorn or testing frameworks.

Example:
    uvicorn src.api:app --reload
"""

# PUBLIC_INTERFACE
def get_version() -> str:
    """Return the API package version."""
    return "1.0.0"

# Import at module level to expose `app` as src.api.app
from .main import app  # noqa: E402,F401  (import after definition on purpose)
