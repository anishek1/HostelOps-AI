"""
fallback_classifier.py — HostelOps AI
=======================================
Rule-based keyword classifier used when LLM is unavailable.
This is a SAFETY NET only — not a replacement for the LLM.
Always sets classified_by="fallback" on the complaint record.
Shape mirrors ClassificationResult from agents/complaint_classifier.py.
"""
from dataclasses import dataclass

from schemas.enums import ComplaintCategory, ComplaintSeverity


@dataclass
class FallbackClassification:
    category: ComplaintCategory
    severity: ComplaintSeverity
    urgency: int           # 1-5
    affected_count: int    # default 1
    location: str          # default "unspecified"
    safety_flag: bool      # default False
    language_detected: str # default "english"
    classified_by: str = "fallback"


KEYWORD_RULES = [
    {
        "keywords": [
            "food", "mess", "meal", "breakfast", "lunch", "dinner",
            "cook", "taste", "hygiene", "canteen", "thali", "sabzi", "roti",
            "khana", "bhojan",
        ],
        "category": ComplaintCategory.mess,
        "severity": ComplaintSeverity.medium,
        "urgency": 2,
    },
    {
        "keywords": [
            "laundry", "washing", "machine", "clothes", "slot",
            "dryer", "washer", "detergent", "spin",
        ],
        "category": ComplaintCategory.laundry,
        "severity": ComplaintSeverity.medium,
        "urgency": 2,
    },
    {
        "keywords": [
            "water", "electricity", "fan", "light", "ac", "furniture",
            "door", "window", "plumbing", "flush", "tap", "pipe", "switch",
            "bulb", "ceiling", "wall", "roof", "bed", "mattress", "chair",
            "table", "cupboard", "lock", "paani", "bijli",
        ],
        "category": ComplaintCategory.maintenance,
        "severity": ComplaintSeverity.medium,
        "urgency": 2,
    },
    {
        "keywords": [
            "fight", "harassment", "threat", "abuse", "unsafe", "scared",
            "uncomfortable", "bully", "ragging", "misbehave", "assault",
            "violence", "stalk",
        ],
        "category": ComplaintCategory.interpersonal,
        "severity": ComplaintSeverity.high,
        "urgency": 5,
        "safety_flag": True,
    },
    {
        "keywords": [
            "fire", "emergency", "collapse", "flood", "gas leak", "unconscious",
            "hospital", "ambulance", "critical", "life",
        ],
        "category": ComplaintCategory.critical,
        "severity": ComplaintSeverity.high,
        "urgency": 5,
        "safety_flag": True,
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
                urgency=rule.get("urgency", 2),
                affected_count=1,
                location="unspecified",
                safety_flag=rule.get("safety_flag", False),
                language_detected="unknown",
            )

    return FallbackClassification(
        category=ComplaintCategory.uncategorised,
        severity=ComplaintSeverity.medium,
        urgency=2,
        affected_count=1,
        location="unspecified",
        safety_flag=False,
        language_detected="unknown",
    )
