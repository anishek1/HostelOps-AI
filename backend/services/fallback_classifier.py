"""
fallback_classifier.py — HostelOps AI
=======================================
Rule-based keyword classifier used when LLM is unavailable.
This is a SAFETY NET only — not a replacement for the LLM.
Always sets classified_by="fallback" on the complaint record.
The Warden dashboard must display this distinction clearly.
"""
from dataclasses import dataclass, field

from schemas.enums import ComplaintCategory, ComplaintSeverity


@dataclass
class FallbackClassification:
    category: ComplaintCategory
    severity: ComplaintSeverity
    requires_approval: bool
    classified_by: str = "fallback"
    note: str = ""


KEYWORD_RULES = [
    {
        "keywords": [
            "food", "mess", "meal", "breakfast", "lunch", "dinner",
            "cook", "taste", "hygiene", "canteen", "thali", "sabzi", "roti",
        ],
        "category": ComplaintCategory.mess,
        "severity": ComplaintSeverity.medium,
        "requires_approval": False,
    },
    {
        "keywords": [
            "laundry", "washing", "machine", "clothes", "slot",
            "dryer", "washer", "detergent", "spin",
        ],
        "category": ComplaintCategory.laundry,
        "severity": ComplaintSeverity.medium,
        "requires_approval": False,
    },
    {
        "keywords": [
            "water", "electricity", "fan", "light", "ac", "furniture",
            "door", "window", "plumbing", "flush", "tap", "pipe", "switch",
            "bulb", "ceiling", "wall", "roof", "bed", "mattress", "chair",
            "table", "cupboard", "lock",
        ],
        "category": ComplaintCategory.maintenance,
        "severity": ComplaintSeverity.medium,
        "requires_approval": False,
    },
    {
        "keywords": [
            "fight", "harassment", "threat", "abuse", "unsafe", "scared",
            "uncomfortable", "bully", "ragging", "misbehave", "assault",
            "violence", "stalk",
        ],
        "category": ComplaintCategory.interpersonal,
        "severity": ComplaintSeverity.high,
        "requires_approval": True,
    },
]


def classify_with_fallback(text: str) -> FallbackClassification:
    """
    Classifies complaint text using keyword matching.
    Called when LLM is unavailable after all retries.
    Returns a FallbackClassification — never raises.
    """
    text_lower = text.lower()

    for rule in KEYWORD_RULES:
        if any(kw in text_lower for kw in rule["keywords"]):
            return FallbackClassification(
                category=rule["category"],
                severity=rule["severity"],
                requires_approval=rule["requires_approval"],
                note=f"Fallback classifier — matched keywords for {rule['category'].value}",
            )

    # No keyword match — send to manual review
    return FallbackClassification(
        category=ComplaintCategory.uncategorised,
        severity=ComplaintSeverity.medium,
        requires_approval=True,
        note="Fallback classifier — no keyword match found. Manual review required.",
    )
