"""Gunicorn configuration for the Molecular Analysis Dashboard API."""

import multiprocessing
import os

BIND = "0.0.0.0:8000"
WORKERS = int(os.environ.get("WEB_CONCURRENCY", max(1, multiprocessing.cpu_count())))
WORKER_CLASS = "uvicorn.workers.UvicornWorker"
THREADS = 1
KEEPALIVE = 30
TIMEOUT = 120
ACCESSLOG = "-"
ERRORLOG = "-"
LOGLEVEL = os.environ.get("LOG_LEVEL", "info")
