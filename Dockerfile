# =============================================================================
# Morocco CPSV-AP 3.2.0 Administrative Portal & SHACL Validation Engine
# Multi-arch compatible (Linux x86_64, ARM64 / Apple Silicon, Windows WSL2)
# =============================================================================

FROM python:3.12-slim

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    PORT=8085

# Install system curl for container health check
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first for optimal Docker layer caching
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy dataset and application files (filtered via .dockerignore)
COPY output/ /app/output/
COPY src/ /app/src/
COPY README.md /app/README.md
COPY installation.txt /app/installation.txt

# Security: create and run as non-root user
RUN groupadd -g 10001 cpsv && \
    useradd -u 10001 -g cpsv -m -s /bin/bash cpsv && \
    chown -R cpsv:cpsv /app

USER cpsv

# Expose HTTP port for the Moroccan Administrative Portal WebUI & API
EXPOSE 8085

# Healthcheck validating the REST API status endpoint
HEALTHCHECK --interval=20s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8085/api/status || exit 1

# Launch the standalone CPSV portal server
CMD ["python3", "src/morocco_cpsv_composer/server.py", "8085"]
