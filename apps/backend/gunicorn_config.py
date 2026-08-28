"""Gunicorn configuration for production deployment."""

import os

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
# MVP model strategy: one inference worker keeps activation state consistent.
try:
    workers = int(os.getenv("WORKERS", "1"))
except ValueError as exc:
    raise RuntimeError("WORKERS must be an integer") from exc
if workers != 1:
    raise RuntimeError(
        "Model hot-swap requires WORKERS=1; use an external coordinator for replicas"
    )
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
timeout = 60
keepalive = 2

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Process naming
proc_name = "sapikenal-backend"

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (if needed, configure in production)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"

# Application
raw_env = ["PYTHONUNBUFFERED=1"]


# Hooks
def on_starting(server):
    print("Gunicorn server starting...")


def on_exit(server):
    print("Gunicorn server exiting...")
