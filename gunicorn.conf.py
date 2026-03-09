"""
Gunicorn configuration for AlphaEdge production deployment.
"""
import multiprocessing
import os

# ── Server socket ────────────────────────────────────────────────
bind = os.getenv("BIND", "0.0.0.0:8000")

# ── Worker processes ─────────────────────────────────────────────
workers = int(os.getenv("API_WORKERS", min(multiprocessing.cpu_count() * 2 + 1, 8)))
worker_class = "uvicorn.workers.UvicornWorker"
worker_tmp_dir = "/dev/shm"  # faster worker heartbeat on Linux

# ── Timeouts ─────────────────────────────────────────────────────
timeout = 120          # kill worker if no response in 120s (ML predictions can be slow)
graceful_timeout = 30  # wait 30s for in-flight requests on shutdown
keepalive = 5

# ── Logging ──────────────────────────────────────────────────────
accesslog = "-"   # stdout
errorlog = "-"    # stderr
loglevel = os.getenv("LOG_LEVEL", "info").lower()
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)sμs'

# ── Process naming ───────────────────────────────────────────────
proc_name = "alphaedge"

# ── Security ─────────────────────────────────────────────────────
limit_request_line = 8190
limit_request_fields = 100
limit_request_field_size = 8190

# ── Preload ──────────────────────────────────────────────────────
preload_app = False  # keep False so each worker inits its own model copy
