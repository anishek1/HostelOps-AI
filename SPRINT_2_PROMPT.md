# HostelOps AI — Sprint 2 Prompt
# Agent 1 Core — Complaint Filing + LLM Classification Pipeline
# Paste into Cursor (Sonnet 4.6 Thinking) with @CONVENTIONS.md @PRD.md @PROJECT_STATE.md

---

@CONVENTIONS.md @PRD.md @PROJECT_STATE.md

You are the lead developer for HostelOps AI. Sprint 1 is complete and fully verified. You are now building Sprint 2.

**Read PROJECT_STATE.md completely before writing a single line of code.** Pay special attention to Section 5 (deviations) and Section 10 (golden rules). Everything in Sprint 1 that is working must remain untouched.

**Current Sprint:** Sprint 2 — Agent 1 Core
**Goal:** By the end of this sprint, a student can file a complaint, receive an immediate acknowledgement, and the complaint is classified by the LLM asynchronously via Celery and either auto-assigned or routed to the Warden approval queue — with a working fallback classifier if the LLM fails.

---

## Before You Write Any Code

1. Read CONVENTIONS.md Section 2 (feature implementation order) and Section 3 (golden rules)
2. Read PRD.md Section 3.3 (Agent 1 in full), Section 9 (complaint state graph), Section 10 (failure modes)
3. Tell me which files you will create and which you will modify before writing anything
4. Confirm you will NOT touch any file from Sprint 1 unless explicitly listed in this prompt

---

## Sprint 2 Task List — Complete in This Exact Order

---

### Task 0 — Bootstrap Admin Script (create_admin.py)

This task was identified in Sprint 1 as a required fix. The `verify_warden.py` debug script was deleted. A proper replacement is needed.

Create `backend/create_admin.py` — a one-time setup script that runs during initial deployment to create the first verified Assistant Warden account.

Rules for this script:
- It is a standalone Python script, NOT a FastAPI route or endpoint
- It reads config from `config.py` (never hardcodes values)
- It creates one user with `role=assistant_warden`, `is_verified=True`, `is_active=True`
- It checks if an admin already exists before creating — never creates duplicates
- It prints clear success/failure messages to the terminal
- It is safe to run multiple times (idempotent)
- Add a comment at the top: `# Run once during initial deployment: python create_admin.py`

Usage will be:
```bash
cd backend
python create_admin.py
# Enter name: 
# Enter email/identifier:
# Enter password:
# Admin created successfully.
```

---

### Task 1 — Celery + Redis Setup

**1a. Install dependencies** (add to requirements.txt):
```
celery==5.3.6
redis==5.0.1
kombu==5.3.4
```

**1b. Create `backend/celery_app.py`:**
```python
"""
celery_app.py — HostelOps AI
=============================
Celery application instance.
Import this in tasks to get the celery app.
Never import this in routes or services directly.
"""
from celery import Celery
from config import settings

celery_app = Celery(
    "hostelops",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["tasks.complaint_tasks", "tasks.notification_tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,  # Only ack after task completes — prevents lost tasks on crash
)
```

**1c. Verify Upstash Redis connection:**
- Make sure `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND` are filled in `.env`
- Go to upstash.com, create a free Redis database, copy the Redis URL
- Format: `redis://default:PASSWORD@HOST:PORT`
- Test connection:
```bash
python -c "import redis; r = redis.from_url('YOUR_REDIS_URL'); r.ping(); print('Redis connected')"
```

---

### Task 2 — Prompt Sanitizer Middleware

Before ANY text reaches the LLM it must be sanitized. Create `backend/middleware/prompt_sanitizer.py`:

```python
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
        original_text=text
    )
```

---

### Task 3 — Fallback Classifier

Create `backend/services/fallback_classifier.py` — pure function, no external dependencies, no async:

```python
"""
fallback_classifier.py — HostelOps AI
=======================================
Rule-based keyword classifier used when LLM is unavailable.
This is a SAFETY NET only — not a replacement for the LLM.
Always sets classified_by="fallback" on the complaint record.
The Warden dashboard must display this distinction clearly.
"""
from schemas.enums import ComplaintCategory, ComplaintSeverity
from dataclasses import dataclass

@dataclass
class FallbackClassification:
    category: ComplaintCategory
    severity: ComplaintSeverity
    requires_approval: bool
    classified_by: str = "fallback"
    note: str = ""

KEYWORD_RULES = [
    {
        "keywords": ["food", "mess", "meal", "breakfast", "lunch", "dinner", "cook", "taste", "hygiene", "canteen", "thali", "sabzi", "roti"],
        "category": ComplaintCategory.mess,
        "severity": ComplaintSeverity.medium,
        "requires_approval": False,
    },
    {
        "keywords": ["laundry", "washing", "machine", "clothes", "slot", "dryer", "washer", "detergent", "spin"],
        "category": ComplaintCategory.laundry,
        "severity": ComplaintSeverity.medium,
        "requires_approval": False,
    },
    {
        "keywords": ["water", "electricity", "fan", "light", "ac", "furniture", "door", "window", "plumbing", "flush", "tap", "pipe", "switch", "bulb", "ceiling", "wall", "roof", "bed", "mattress", "chair", "table", "cupboard", "lock"],
        "category": ComplaintCategory.maintenance,
        "severity": ComplaintSeverity.medium,
        "requires_approval": False,
    },
    {
        "keywords": ["fight", "harassment", "threat", "abuse", "unsafe", "scared", "uncomfortable", "bully", "ragging", "misbehave", "assault", "violence", "stalk"],
        "category": ComplaintCategory.interpersonal,
        "severity": ComplaintSeverity.high,
        "requires_approval": True,
    },
]

def classify_with_fallback(text: str) -> FallbackClassification:
    """
    Classifies complaint text using keyword matching.
    Called when LLM is unavailable after all retries.
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
```

---

### Task 4 — Agent 1 Tools

Create `backend/tools/complaint_tools.py` — all 6 Agent 1 tools with typed Pydantic input/output schemas:

```python
"""
complaint_tools.py — HostelOps AI
===================================
Agent 1 typed tool definitions.
Each tool has a strict Pydantic input schema and typed output.
Tools call services — they never access the DB directly.
All tools are async.
"""
```

Implement these 6 tools exactly as defined in PRD.md Section 3.3:

| Tool | Input Schema | Output Schema |
|------|-------------|--------------|
| `assign_complaint_tool` | `complaint_id, assignee_id, severity, category` | `AssignmentResult(success, notified, assigned_at)` |
| `escalate_complaint_tool` | `complaint_id, escalation_target, reason` | `EscalationResult(success, queue_item_id)` |
| `request_human_approval_tool` | `complaint_id, ai_category, ai_severity, ai_assignee_id, confidence` | `ApprovalRequest(queue_item_id, created_at)` |
| `acknowledge_student_tool` | `complaint_id, student_id, is_anonymous` | `AcknowledgementResult(success, message)` |
| `route_to_agent_tool` | `complaint_id, target_agent, complaint_text, category` | `RoutingResult(success, agent_received)` |
| `log_override_tool` | `complaint_id, warden_id, original, corrected, reason` | `LogResult(log_id)` |

Rules:
- Every tool input and output is a Pydantic BaseModel
- Every tool is `async def`
- Tools call service functions — never direct DB access
- `acknowledge_student_tool` must ALWAYS succeed — never raise an exception (catch and log instead)

---

### Task 5 — Complaint Service (State Machine)

Create `backend/services/complaint_service.py`.

This is the most critical file in the entire project. Every complaint state change goes through here.

**5a. Implement the state transition function:**

```python
async def transition_complaint(
    complaint_id: str,
    from_state: ComplaintStatus,
    to_state: ComplaintStatus,
    triggered_by: str,  # user_id or "system"
    db: AsyncSession,
    note: str | None = None
) -> Complaint:
    """
    The ONLY function allowed to change complaint.status.
    Validates the transition is legal before applying it.
    Writes to audit log automatically.
    Raises ValueError for invalid transitions.
    """
```

Valid transitions (from PRD.md Section 9.2 — implement exactly these, reject all others):
```python
VALID_TRANSITIONS = {
    ComplaintStatus.INTAKE: [ComplaintStatus.CLASSIFIED, ComplaintStatus.ESCALATED],
    ComplaintStatus.CLASSIFIED: [ComplaintStatus.ASSIGNED, ComplaintStatus.AWAITING_APPROVAL],
    ComplaintStatus.AWAITING_APPROVAL: [ComplaintStatus.ASSIGNED, ComplaintStatus.ESCALATED],
    ComplaintStatus.ASSIGNED: [ComplaintStatus.IN_PROGRESS, ComplaintStatus.ESCALATED],
    ComplaintStatus.IN_PROGRESS: [ComplaintStatus.RESOLVED],
    ComplaintStatus.RESOLVED: [ComplaintStatus.REOPENED],
    ComplaintStatus.REOPENED: [ComplaintStatus.ASSIGNED],
    ComplaintStatus.ESCALATED: [ComplaintStatus.ASSIGNED],
}
```

**5b. Implement these service functions:**

```python
async def create_complaint(
    student_id: str,
    data: ComplaintCreate,
    db: AsyncSession
) -> Complaint:
    """
    Creates complaint in INTAKE state.
    Sanitizes text via prompt_sanitizer.
    Stores both original and sanitized text.
    Stores flagged_input if injection was detected.
    Does NOT classify — that happens in Celery task.
    """

async def get_complaint(
    complaint_id: str,
    requesting_user_id: str,
    requesting_user_role: UserRole,
    db: AsyncSession
) -> Complaint:
    """
    Students can only get their own complaints.
    Staff and wardens can get any complaint.
    Raises 404 if not found, 403 if not authorized.
    """

async def assign_complaint(
    complaint_id: str,
    assignee_id: str,
    category: ComplaintCategory,
    severity: ComplaintSeverity,
    classified_by: str,  # "llm" or "fallback"
    db: AsyncSession
) -> Complaint:
    """
    Assigns complaint to staff.
    Calls transition_complaint() INTAKE/CLASSIFIED → ASSIGNED.
    Never called directly for high-severity complaints.
    """

async def send_to_approval_queue(
    complaint_id: str,
    ai_category: ComplaintCategory,
    ai_severity: ComplaintSeverity,
    ai_assignee_id: str,
    confidence: float,
    db: AsyncSession
) -> ApprovalQueueItem:
    """
    Creates approval queue item.
    Calls transition_complaint() → AWAITING_APPROVAL.
    """
```

---

### Task 6 — LangChain + Groq Agent Setup

Create `backend/agents/agent_complaint.py`:

```python
"""
agent_complaint.py — HostelOps AI
===================================
Agent 1 — Complaint Classification Agent.
Uses LangChain + Groq + Llama 3 to classify complaints.
Returns structured ClassificationResult with confidence score.
All LLM calls go through this file — never call Groq directly from services.
"""
```

**6a. Install additional dependencies** (add to requirements.txt):
```
langchain==0.1.20
langchain-groq==0.1.6
langchain-core==0.1.53
```

**6b. Implement the classification function:**

```python
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel
from config import settings

class ClassificationResult(BaseModel):
    category: str  # must match ComplaintCategory enum values
    severity: str  # must match ComplaintSeverity enum values
    suggested_assignee_role: str  # role of who should handle this
    confidence: float  # 0.0 to 1.0
    reasoning: str  # one sentence explanation

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
        # Log the error but never crash
        print(f"[Agent 1] LLM classification failed: {e}")
        return None
```

---

### Task 7 — Celery Classification Task

Create `backend/tasks/complaint_tasks.py`:

```python
"""
complaint_tasks.py — HostelOps AI
===================================
Background tasks for complaint processing.
All LLM classification runs here — never synchronously in routes.
Implements full retry policy and fallback chain from PRD.md Section 10.
"""
```

Implement `classify_and_route_complaint` task with the full retry + fallback chain from PRD.md Section 10.2:

```python
@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=2,  # 2s, then 4s, then 8s (exponential)
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def classify_and_route_complaint(self, complaint_id: str):
    """
    Full classification pipeline for a single complaint.
    
    Flow:
    1. Fetch complaint from DB
    2. Try LLM classification (up to 3 retries with backoff)
    3. If LLM fails → use fallback classifier
    4. If confidence >= threshold AND severity != high → auto-assign
    5. If confidence < threshold OR severity == high → approval queue
    6. If Celery itself crashes → complaint stays in AWAITING_APPROVAL (set on creation)
    
    Always:
    - Sends student acknowledgement FIRST before any classification
    - Logs classified_by ("llm" or "fallback") on the complaint record
    - If injection was flagged → sends passive alert to Warden
    """
```

Key rules for this task:
- Student acknowledgement (`acknowledge_student_tool`) is called FIRST — before LLM runs
- LLM is called with `await classify_complaint()` from `agent_complaint.py`
- If LLM returns `None` → use `classify_with_fallback()` from `fallback_classifier.py`
- Confidence threshold from `settings.COMPLAINT_CONFIDENCE_THRESHOLD` (default 0.85)
- High severity ALWAYS goes to approval queue regardless of confidence
- All DB operations inside the task use a new sync session (Celery doesn't support async sessions natively — use `sessionmaker` with sync engine for task DB access)
- Set `classified_by = "llm"` or `classified_by = "fallback"` on the complaint record

**Important — Celery + Async DB:**
Celery tasks cannot use the async SQLAlchemy session. Create a separate sync engine in `database.py` for use in Celery tasks only:

```python
# In database.py — add alongside the async engine
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Sync engine for Celery tasks only
sync_engine = create_engine(
    settings.DATABASE_URL.replace("postgresql+asyncpg", "postgresql+psycopg2"),
    pool_pre_ping=True,
)
SyncSessionLocal = sessionmaker(bind=sync_engine)
```

Add `psycopg2-binary` to requirements.txt.

---

### Task 8 — Complaint Routes

Create `backend/routes/complaints.py`:

All routes are thin — they validate input and call services only.

```python
# POST /api/complaints/
# - Requires student role
# - Sanitizes input via prompt_sanitizer
# - Creates complaint in INTAKE state via complaint_service.create_complaint()
# - Fires classify_and_route_complaint.delay(complaint_id) — async, non-blocking
# - Returns immediate response: complaint_id + status INTAKE + acknowledgement message
# - Total response time must be under 2 seconds (LLM runs in background)

# GET /api/complaints/{id}
# - Students: can only see own complaints
# - Staff/Wardens: can see all complaints
# - Returns full complaint with current status

# PATCH /api/complaints/{id}/status
# - Staff only (laundry_man, mess_secretary, assistant_warden, warden, chief_warden)
# - Allowed transitions for staff: ASSIGNED → IN_PROGRESS, IN_PROGRESS → RESOLVED
# - Calls transition_complaint() — never updates status directly

# POST /api/complaints/{id}/reopen
# - Student only, on their own complaint
# - Only allowed when complaint status is RESOLVED
# - Calls transition_complaint() RESOLVED → REOPENED
# - Elevates priority, notifies Warden
```

Register the router in `main.py`.

---

### Task 9 — Notification Service (Basic)

Create `backend/services/notification_service.py` — basic in-app notification only (push notifications come in Sprint 6):

```python
async def create_notification(
    recipient_id: str,
    title: str,
    body: str,
    notification_type: NotificationType,
    db: AsyncSession
) -> Notification:
    """
    Creates an in-app notification record.
    Sprint 6 will add push delivery on top of this.
    This function is always called — even if push fails later,
    the notification is always in the DB inbox.
    """
```

This is called by the tools (acknowledge_student_tool, assign_complaint_tool, etc.) to create notification records.

---

## Definition of Done — Sprint 2

Before calling Sprint 2 complete, verify ALL of the following:

**Setup:**
- [ ] `backend/create_admin.py` exists and runs successfully — creates verified admin
- [ ] Celery worker starts without errors: `.venv\Scripts\celery -A celery_app worker --loglevel=info`
- [ ] Redis connection confirmed via ping test

**Agent 1 Pipeline:**
- [ ] `POST /api/complaints/` returns immediate response (under 2 seconds) with complaint_id and INTAKE status
- [ ] Student receives acknowledgement notification in DB immediately
- [ ] Celery worker logs show classification task picked up and running
- [ ] After ~10 seconds, complaint status changes from INTAKE to either ASSIGNED or AWAITING_APPROVAL
- [ ] `classified_by` field is set to "llm" or "fallback" on the complaint record

**LLM Classification:**
- [ ] High-confidence + low/medium severity complaint → auto-assigned, status = ASSIGNED
- [ ] High-severity complaint → always goes to AWAITING_APPROVAL regardless of confidence
- [ ] Low-confidence complaint → goes to AWAITING_APPROVAL

**Fallback:**
- [ ] Temporarily set an invalid GROQ_API_KEY in .env
- [ ] File a complaint — after retries, fallback classifier runs
- [ ] Complaint is classified with `classified_by="fallback"` and goes to AWAITING_APPROVAL
- [ ] Restore valid GROQ_API_KEY

**State Machine:**
- [ ] `transition_complaint()` rejects invalid transitions with ValueError
- [ ] Audit log entry created for every state change

**Fallback Classifier:**
- [ ] Test with "the food in the mess was very bad today" → category: mess
- [ ] Test with "washing machine is broken" → category: laundry
- [ ] Test with "fan in my room is not working" → category: maintenance
- [ ] Test with "my roommate threatened me" → category: interpersonal, severity: high, requires_approval: True

**Security:**
- [ ] Complaint text with injection attempt ("ignore previous instructions") gets flagged
- [ ] `flagged_input` field stores the original text
- [ ] `sanitized_text` field stores the cleaned version
- [ ] Warden receives passive notification about flagged input

**Routes:**
- [ ] `GET /api/complaints/{id}` returns 403 if student tries to access another student's complaint
- [ ] `PATCH /api/complaints/{id}/status` with invalid transition returns 400
- [ ] `POST /api/complaints/{id}/reopen` only works when status is RESOLVED

**No regressions:**
- [ ] Sprint 1 auth system still works — register, verify, login, role checks all pass
- [ ] All 10 database tables still intact

---

## After Completing Sprint 2

Report back with:
1. Confirmation of every Definition of Done checkbox
2. Any deviations from this spec with explanation
3. Any new decisions made that differ from PRD.md
4. Full list of files created or modified
5. Updated PROJECT_STATE.md with Sprint 2 section added

**Do not begin Sprint 3 until Sprint 2 Definition of Done is fully met and verified.**
