# Seques — Backend Dockerfile
# Python 3.9, gunicorn + uvicorn workers (no --reload)
# Build: docker build -t seques-backend ./backend
# Run:   docker run --env-file backend/.env -p 8000:8000 seques-backend

FROM python:3.9-slim

# Prevent .pyc files and enable unbuffered stdout/stderr for log capture
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system deps required by PyMuPDF (fitz) and reportlab
RUN apt-get update && apt-get install -y --no-install-recommends \
        libglib2.0-0 \
        libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (layer cached unless requirements change)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir gunicorn \
    && pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Non-root user for least-privilege execution
RUN adduser --disabled-password --gecos "" appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Liveness probe — matches GET /health in main.py
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import os,urllib.request; urllib.request.urlopen('http://localhost:'+os.environ.get('PORT','8000')+'/health')"

# Production server: gunicorn + uvicorn workers
# --timeout 120: LLM calls can take 30-90s; default 30s kills in-flight requests
# -w 2: suitable for single-core containers; raise to (2*cores+1) on larger instances
CMD gunicorn main:app \
    -k uvicorn.workers.UvicornWorker \
    -w 2 \
    --bind 0.0.0.0:${PORT:-8000} \
    --timeout 120 \
    --graceful-timeout 30 \
    --access-logfile - \
    --error-logfile -
