"""
ASGI shim module to support uvicorn 'main:app' import style.

This module simply imports and re-exports the FastAPI application instance
from the canonical location src.api.main:app.

Preferred startup commands:
- uvicorn src.api.main:app --host 0.0.0.0 --port 3001 --proxy-headers
- python -m src.run

This shim enables compatibility with environments that are hardcoded to use 'main:app'.
"""


# PUBLIC_INTERFACE
def get_asgi_app():
    """Return the FastAPI app instance from the canonical module path."""
    # Local import inside function to avoid global redefinition issues during linting
    from src.api.main import app as _app
    return _app


# Re-export for ASGI servers like Uvicorn: uvicorn main:app
from src.api.main import app as app  # noqa: E402,F401
