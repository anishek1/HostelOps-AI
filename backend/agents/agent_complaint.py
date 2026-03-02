"""
agent_complaint.py — HostelOps AI
===================================
Agent 1 — Complaint Classification Agent.
Uses LangChain + Groq + Llama 3 to classify complaints.
Returns structured ClassificationResult with confidence score.
All LLM calls go through this file — never call Groq directly from services.
"""
import logging

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel

from config import settings

logger = logging.getLogger(__name__)


class ClassificationResult(BaseModel):
    category: str          # must match ComplaintCategory enum values
    severity: str          # must match ComplaintSeverity enum values
    suggested_assignee_role: str  # role of who should handle this
    confidence: float      # 0.0 to 1.0
    reasoning: str         # one sentence explanation


CLASSIFICATION_PROMPT = """You are a complaint classification system for a college hostel.
Classify the following student complaint into exactly one category.

Categories:
- mess: food quality, quantity, hygiene, menu, timing, canteen issues
- laundry: washing machines, clothes, booking slots, laundry room
- maintenance: room repairs, electrical, plumbing, furniture, water supply, infrastructure
- interpersonal: conflicts between students, harassment, ragging, misconduct, safety concerns
- critical: life-threatening, severe infrastructure failure, emergency situations

Severity:
- low: minor inconvenience, non-urgent
- medium: needs attention within 24 hours
- high: urgent, safety-related, or sensitive interpersonal issue

Respond ONLY with valid JSON matching this exact structure:
{{
  "category": "<category>",
  "severity": "<severity>",
  "suggested_assignee_role": "<role>",
  "confidence": <float between 0.0 and 1.0>,
  "reasoning": "<one sentence>"
}}

Student complaint: {complaint_text}"""


async def classify_complaint(complaint_text: str) -> ClassificationResult | None:
    """
    Calls Groq LLM to classify a complaint.
    Returns ClassificationResult on success.
    Returns None on failure — caller handles fallback.
    Never raises exceptions — catches and logs all errors.
    """
    try:
        llm = ChatGroq(
            model=settings.GROQ_MODEL_NAME,
            api_key=settings.GROQ_API_KEY,
            temperature=0,
        )
        prompt = ChatPromptTemplate.from_template(CLASSIFICATION_PROMPT)
        parser = JsonOutputParser(pydantic_object=ClassificationResult)
        chain = prompt | llm | parser

        result = await chain.ainvoke({"complaint_text": complaint_text})
        return ClassificationResult(**result)
    except Exception as e:
        logger.error(f"[Agent 1] LLM classification failed: {e}")
        return None
