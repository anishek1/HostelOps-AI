"""
celery_app.py — HostelOps AI
=============================
Celery application instance.
Import this in tasks to get the celery app.
Never import this in routes or services directly.
"""
from celery import Celery
from config import settings

celery_app = Celery(
    "hostelops",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["tasks.complaint_tasks", "tasks.notification_tasks"],
)

import ssl as _ssl

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,  # Only ack after task completes — prevents lost tasks on crash
    # Upstash Redis uses TLS — ssl.CERT_NONE skips cert verification (Upstash uses self-signed)
    broker_use_ssl={
        "ssl_cert_reqs": _ssl.CERT_NONE,
    },
    redis_backend_use_ssl={
        "ssl_cert_reqs": _ssl.CERT_NONE,
    },
)
