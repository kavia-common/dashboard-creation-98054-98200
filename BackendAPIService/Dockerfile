# syntax=docker/dockerfile:1

FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Install system deps (for building wheels, uvloop optional on linux)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install python deps first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src ./src
COPY interfaces ./interfaces

# Create non-root user
RUN useradd -m -u 10001 appuser
USER appuser

# Expose API port expected by the orchestrator
EXPOSE 3001

# Healthcheck: call health endpoint on port 3001
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python - <<'PY' || exit 1
import sys, urllib.request
try:
    with urllib.request.urlopen("http://127.0.0.1:3001/") as r:
        sys.exit(0 if r.status==200 else 1)
except Exception:
    sys.exit(1)
PY

# Start Uvicorn in production mode on port 3001
# NOTE: Configuration comes from environment variables (.env via docker-compose or secrets)
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "3001", "--proxy-headers", "--forwarded-allow-ips", "*", "--workers", "2"]
