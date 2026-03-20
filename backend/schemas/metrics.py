"""
schemas/metrics.py — HostelOps AI
=====================================
Pydantic v2 schemas for the Analytics/Metrics dashboard.
Sprint 5: New file.
Sprint 6: Added pending counts to DashboardMetrics. Updated ComplaintsAnalytics.
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
    # Sprint 6: pending counts for warden overview
    pending_registrations: int = 0         # Unverified, non-rejected students awaiting approval
    pending_approval_queue: int = 0        # Pending items in the approval queue
    computed_at: datetime


class ComplaintsAnalytics(BaseModel):
    period_days: int
    total_complaints: int
    by_category: Dict[str, int]
    by_status: Dict[str, int]
    by_severity: Dict[str, int]
    avg_resolution_hours: float
    classified_by_llm: int = 0
    classified_by_fallback: int = 0
    computed_at: datetime


class MessAnalytics(BaseModel):
    period_days: int
    total_feedback: int
    daily_participation: Dict[str, int]    # date_str -> count
    avg_by_dimension: Dict[str, float]     # dimension -> avg score
    overall_avg: float
    alerts_this_period: int
    computed_at: datetime


class LaundryAnalytics(BaseModel):
    period_days: int
    total_bookings: int
    total_cancellations: int
    total_noshows: int
    noshow_rate: float
    cancellation_rate: float
    computed_at: datetime
