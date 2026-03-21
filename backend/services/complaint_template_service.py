"""
services/complaint_template_service.py — HostelOps AI
=======================================================
Hardcoded complaint templates for quick-fill on the frontend (Sprint 7b).
No DB table — these are static and always available.
"""
from schemas.complaint import ComplaintTemplateRead

_TEMPLATES = [
    ComplaintTemplateRead(title="Broken fan/AC", description="The fan or air conditioner in my room is not working.", category="maintenance"),
    ComplaintTemplateRead(title="Water supply issue", description="There is no water or low water pressure in my room/bathroom.", category="maintenance"),
    ComplaintTemplateRead(title="Bathroom not cleaned", description="The common bathroom has not been cleaned and is in an unhygienic condition.", category="maintenance"),
    ComplaintTemplateRead(title="Washing machine not working", description="The washing machine is not functioning properly.", category="laundry"),
    ComplaintTemplateRead(title="Clothes missing from machine", description="My clothes are missing after a laundry session.", category="laundry"),
    ComplaintTemplateRead(title="Food quality is poor", description="The food quality served in the mess is below acceptable standards.", category="mess"),
    ComplaintTemplateRead(title="Unhygienic kitchen conditions", description="The mess kitchen or serving area is not clean and appears unhygienic.", category="mess"),
    ComplaintTemplateRead(title="Noise disturbance from neighbor", description="I am experiencing excessive noise disturbance from a neighboring room.", category="interpersonal"),
    ComplaintTemplateRead(title="Harassment or bullying", description="I am being harassed or bullied by another resident and require immediate assistance.", category="interpersonal"),
]


def get_templates() -> list[ComplaintTemplateRead]:
    """Returns the hardcoded list of complaint templates."""
    return _TEMPLATES
