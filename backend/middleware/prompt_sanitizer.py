"""
prompt_sanitizer.py — HostelOps AI
====================================
Sanitizes all free-text inputs before they reach the LLM.
Detects and strips prompt injection attempts.
Call sanitize_input() on ALL complaint text and feedback comments.
"""
import re
from dataclasses import dataclass

INJECTION_PATTERNS = [
    r"ignore\s+(previous|prior|above|all)\s+instructions?",
    r"disregard\s+(previous|prior|above|all)\s+instructions?",
    r"you\s+are\s+now\s+",
    r"new\s+instructions?:",
    r"system\s*:",
    r"<\s*system\s*>",
    r"\[INST\]",
    r"###\s*instruction",
    r"act\s+as\s+(if\s+you\s+are|a|an)\s+",
    r"pretend\s+(you\s+are|to\s+be)",
    r"jailbreak",
    r"do\s+anything\s+now",
    r"dan\s+mode",
]


@dataclass
class SanitizationResult:
    sanitized_text: str
    was_flagged: bool
    original_text: str


def sanitize_input(text: str, max_length: int = 1000) -> SanitizationResult:
    """
    Sanitizes free-text input before LLM processing.
    - Strips HTML tags
    - Truncates to max_length
    - Detects injection patterns
    - Returns sanitized text + flag status
    """
    if not text:
        return SanitizationResult(sanitized_text="", was_flagged=False, original_text="")

    # Strip HTML tags
    clean = re.sub(r'<[^>]+>', '', text)

    # Normalize whitespace
    clean = re.sub(r'\s+', ' ', clean).strip()

    # Truncate
    clean = clean[:max_length]

    # Check for injection patterns
    was_flagged = False
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, clean, re.IGNORECASE):
            was_flagged = True
            # Strip the injection attempt but keep the rest
            clean = re.sub(pattern, '[removed]', clean, flags=re.IGNORECASE)

    return SanitizationResult(
        sanitized_text=clean,
        was_flagged=was_flagged,
        original_text=text,
    )
