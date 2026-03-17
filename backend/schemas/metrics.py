"""
schemas/metrics.py — HostelOps AI
=====================================
Pydantic v2 schemas for the Analytics/Metrics dashboard.
Sprint 5: New file.
"""

from datetime import datetime
from typing import Dict

from pydantic import BaseModel


class DashboardMetrics(BaseModel):
    period_days: int
    misclassification_rate: float          # Overrides / AI-classified complaints
    override_rate_by_category: Dict[str, float]  # Per category override rate
    false_high_severity_rate: float        # AI high-severity later downgraded by warden
    resolution_confirmation_rate: float    # Student-confirmed resolutions / total resolved
    avg_approval_queue_latency_minutes: float  # Avg minutes from queue creation to review
    mess_participation_rate: float         # Today's mess feedback participants / total students
    laundry_noshow_rate: float             # No-shows / total bookings in period
    drift_alert: bool                      # True if misclassification_rate > 0.25
    computed_at: datetime


class ComplaintsAnalytics(BaseModel):
    period_days: int
    total: int
    by_category: Dict[str, int]
    by_status: Dict[str, int]
    by_severity: Dict[str, int]
    avg_resolution_hours: float
    computed_at: datetime
