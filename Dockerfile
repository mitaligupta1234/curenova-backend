# CureNova 2.0 Backend Containerfile
# Base image: Python 3.11 slim (Debian Bookworm)
FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

# Install runtime system libraries (libgomp1 required for XGBoost OpenMP execution, curl for healthchecks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first for caching layer
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application backend, ML inference package, and initialization scripts
COPY app/ /app/app/
COPY ml/ /app/ml/
COPY scripts/ /app/scripts/

# Create non-root system user and application data directory for database mount
RUN groupadd -r curenova && useradd -r -g curenova -d /app -s /sbin/nologin curenova \
    && mkdir -p /app/data \
    && chown -R curenova:curenova /app

USER curenova

EXPOSE 8000

# Container healthcheck using native liveness probe endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Production application entrypoint
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
