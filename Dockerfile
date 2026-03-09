# ── Build stage ──────────────────────────────────────────────────
FROM python:3.10-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

COPY . .
RUN pip install --no-cache-dir --prefix=/install -e .

# ── Runtime stage ────────────────────────────────────────────────
FROM python:3.10-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local
COPY --from=builder /build /app

# Non-root user for security
RUN groupadd -r alphaedge && useradd -r -g alphaedge -d /app alphaedge && \
    mkdir -p /app/data /app/models /app/logs /app/.cache && \
    chown -R alphaedge:alphaedge /app

USER alphaedge

EXPOSE 8000 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()" || exit 1

# Production: gunicorn with uvicorn workers
CMD ["gunicorn", "alphaedge.api.main:app", \
     "--config", "gunicorn.conf.py", \
     "--bind", "0.0.0.0:8000"]
