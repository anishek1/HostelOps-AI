"""
agents/complaint_classifier.py — HostelOps AI
===============================================
LLM-based complaint classifier using direct Groq API (no LangChain).
Extracts structured fields from free-text complaint descriptions.
Returns ClassificationResult on success, None on failure — caller handles fallback.
"""
import json
import logging

from groq import AsyncGroq
from pydantic import BaseModel

from config import settings

logger = logging.getLogger(__name__)


class ClassificationResult(BaseModel):
    category: str        # must match ComplaintCategory enum values
    severity: str        # must match ComplaintSeverity enum values
    urgency: int         # 1 (low) to 5 (critical)
    affected_count: int  # number of students affected (default 1)
    location: str        # extracted location or "unspecified"
    safety_flag: bool    # true if health/safety risk detected
    language_detected: str  # e.g. "english", "hindi", "hinglish"


SYSTEM_PROMPT = """You are a complaint extraction system for a college hostel.
Extract structured information from student complaint text.

Categories: mess | laundry | maintenance | interpersonal | critical | uncategorised
- mess: food quality, quantity, hygiene, menu, timing, canteen
- laundry: washing machines, clothes, booking slots, laundry room
- maintenance: room repairs, electrical, plumbing, furniture, water supply
- interpersonal: conflicts, harassment, ragging, misconduct
- critical: life-threatening, severe infrastructure failure, emergency

Severity: low | medium | high

Respond ONLY with valid JSON:
{
  "category": "<category>",
  "severity": "<severity>",
  "urgency": <1-5>,
  "affected_count": <integer, default 1>,
  "location": "<extracted location or 'unspecified'>",
  "safety_flag": <true if health/safety risk, else false>,
  "language_detected": "<english|hindi|hinglish|other>"
}"""


async def classify_complaint(complaint_text: str) -> ClassificationResult | None:
    """
    Calls Groq LLM to extract structured fields from complaint text.
    Returns ClassificationResult on success, None on failure.
    Never raises — catches and logs all errors.
    """
    try:
        client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        response = await client.chat.completions.create(
            model=settings.GROQ_MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": complaint_text},
            ],
            temperature=0,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content
        data = json.loads(raw)
        return ClassificationResult(**data)
    except Exception as e:
        logger.error(f"[complaint_classifier] LLM classification failed: {e}")
        return None
