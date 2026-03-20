"""
schemas/enums.py — HostelOps AI
================================
All enum definitions used across schemas and models.
Import from here — never define enums inline in schema or model files.
"""

from enum import Enum


class UserRole(str, Enum):
    student = "student"
    laundry_man = "laundry_man"
    mess_secretary = "mess_secretary"
    mess_manager = "mess_manager"
    assistant_warden = "assistant_warden"
    warden = "warden"
    chief_warden = "chief_warden"


class HostelMode(str, Enum):
    college = "college"
    autonomous = "autonomous"


class ComplaintCategory(str, Enum):
    mess = "mess"
    laundry = "laundry"
    maintenance = "maintenance"
    interpersonal = "interpersonal"
    critical = "critical"
    uncategorised = "uncategorised"


class ComplaintSeverity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class ComplaintStatus(str, Enum):
    INTAKE = "INTAKE"
    CLASSIFIED = "CLASSIFIED"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    REOPENED = "REOPENED"
    ESCALATED = "ESCALATED"


class SlotStatus(str, Enum):
    booked = "booked"
    cancelled = "cancelled"
    completed = "completed"
    no_show = "no_show"


class MealPeriod(str, Enum):
    breakfast = "breakfast"
    lunch = "lunch"
    dinner = "dinner"


class ApprovalStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    corrected = "corrected"
    timed_out = "timed_out"


class AlertType(str, Enum):
    chronic = "chronic"
    spike = "spike"


class MessDimension(str, Enum):
    food_quality = "food_quality"
    food_quantity = "food_quantity"
    hygiene = "hygiene"
    menu_variety = "menu_variety"
    timing = "timing"


class OverrideReason(str, Enum):
    wrong_category = "wrong_category"
    wrong_assignee = "wrong_assignee"
    wrong_severity = "wrong_severity"
    other = "other"


class NotificationType(str, Enum):
    complaint_assigned = "complaint_assigned"
    approval_needed = "approval_needed"
    mess_alert = "mess_alert"
    laundry_reminder = "laundry_reminder"
    machine_down = "machine_down"
    complaint_resolved = "complaint_resolved"
    registration_pending = "registration_pending"
    complaint_escalated = "complaint_escalated"
    complaint_reopened = "complaint_reopened"
    # Sprint 6: registration lifecycle + account notifications
    registration_approved = "registration_approved"
    registration_rejected = "registration_rejected"
    password_reset = "password_reset"
    account_deactivated = "account_deactivated"


class ClassifiedBy(str, Enum):
    llm = "llm"
    fallback = "fallback"
    manual = "manual"
    warden_override = "warden_override"


class LaundrySlotStatus(str, Enum):
    available = "available"
    booked = "booked"
    completed = "completed"
    cancelled = "cancelled"
    no_show = "no_show"  # Sprint 5: added for no-show penalty system


class MachineStatus(str, Enum):
    operational = "operational"
    under_repair = "under_repair"
    out_of_service = "out_of_service"


class MealType(str, Enum):
    breakfast = "breakfast"
    lunch = "lunch"
    dinner = "dinner"
    snacks = "snacks"

