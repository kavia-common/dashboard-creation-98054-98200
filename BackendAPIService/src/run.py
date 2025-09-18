"""
Utility entrypoint to run the FastAPI app with a consistent import path.

Usage:
    python -m src.run
or
    python src/run.py

This ensures Uvicorn targets the correct module path: src.api.main:app
"""
import os
import sys


def _ensure_project_root_on_path() -> None:
    """
    Ensure the project root is on sys.path so that 'src' is importable
    even if executed from different working directories.
    """
    # Resolve this file -> src/run.py -> project_root/src/run.py
    current_file = os.path.abspath(__file__)
    src_dir = os.path.dirname(current_file)
    project_root = os.path.dirname(src_dir)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

# PUBLIC_INTERFACE


def main() -> None:
    """Launch the Uvicorn server targeting src.api.main:app.

    Binds to HOST:PORT where:
    - HOST defaults to 0.0.0.0
    - PORT defaults to 3001 (to align with container/orchestrator expectations)
    Override via environment variables HOST and PORT as needed.
    """
    _ensure_project_root_on_path()
    import uvicorn  # lazy import after path adjustment

    host = os.getenv("HOST", "0.0.0.0")
    # Default to 3001 to match Dockerfile, compose and orchestrator health checks
    port = int(os.getenv("PORT", "3001"))
    print(f"Starting Uvicorn for BackendAPIService on {host}:{port} ...")
    uvicorn.run(
        "src.api.main:app",
        host=host,
        port=port,
        proxy_headers=True,
        reload=os.getenv("UVICORN_RELOAD", "false").lower() in ("1", "true", "yes"),
        workers=int(os.getenv("UVICORN_WORKERS", "1")),
        log_level=os.getenv("UVICORN_LOG_LEVEL", "info"),
    )


if __name__ == "__main__":
    main()
