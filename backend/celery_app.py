"""
celery_app.py — HostelOps AI
=============================
Celery application instance.
Import this in tasks to get the celery app.
Never import this in routes or services directly.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from celery import Celery
from config import settings

celery_app = Celery(
    "hostelops",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "tasks.complaint_tasks",
        "tasks.notification_tasks",
        "tasks.approval_tasks",
        "tasks.mess_tasks",
        "tasks.laundry_tasks",
    ],
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
    # Beat schedule for periodic tasks
    beat_schedule={
        "check-approval-timeouts": {
            "task": "tasks.approval_tasks.check_approval_timeouts",
            "schedule": 900.0,  # Every 15 minutes (900 seconds)
        },
        "analyze-daily-mess-feedback": {
            "task": "tasks.mess_tasks.analyze_daily_mess_feedback",
            "schedule": 79200.0,  # Daily at ~22:00 (22 hours in seconds from start)
        },
        "check-participation-alert": {
            "task": "tasks.mess_tasks.check_participation_alert",
            "schedule": 86400.0,  # Daily (every 24 hours)
        },
        "process-noshow-penalties": {
            "task": "tasks.laundry_tasks.process_noshow_penalties",
            "schedule": 3600.0,  # Every 60 minutes
        },
        # Phase 4: Proactive monitoring
        "check-stale-complaints": {
            "task": "tasks.complaint_tasks.check_stale_complaints",
            "schedule": 7200.0,  # Every 2 hours
        },
        "send-slot-reminders": {
            "task": "tasks.laundry_tasks.send_slot_reminders",
            "schedule": 1800.0,  # Every 30 minutes
        },
        "check-laundry-complaint-clusters": {
            "task": "tasks.laundry_tasks.check_laundry_complaint_clusters",
            "schedule": 7200.0,  # Every 2 hours
        },
    },
)

