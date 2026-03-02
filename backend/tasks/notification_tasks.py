"""
notification_tasks.py — HostelOps AI
=======================================
Placeholder for background notification tasks (Sprint 6 — Push Notifications).
This file must exist because celery_app.py includes it in the task discovery list.
Push delivery via pywebpush will be implemented in Sprint 6.
"""
from celery_app import celery_app


@celery_app.task(name="tasks.notification_tasks.send_push_notification")
def send_push_notification(recipient_id: str, title: str, body: str):
    """
    Placeholder: Sprint 6 will implement push delivery via pywebpush.
    In-app notifications are always written synchronously — this is best-effort push.
    """
    pass
