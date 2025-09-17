# syntax=docker/dockerfile:1
FROM python:3.11-slim

# Security and performance best practices
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOST=0.0.0.0 \
    PORT=3001

WORKDIR /app

# System deps (psycopg requires build tools and libpq)
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential libpq-dev curl && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY src /app/src

# Expose port expected by orchestrator
EXPOSE 3001

# Health check aligned to service port
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s CMD curl -f http://localhost:3001/ || exit 1

# Run with Uvicorn on 0.0.0.0:3001
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "3001", "--proxy-headers"]
