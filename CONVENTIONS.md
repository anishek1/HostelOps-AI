# HostelOps AI — Developer Conventions
> **READ THIS FIRST.** This file is the coding rulebook for HostelOps AI. If you are an AI coding assistant working on this project, follow every rule in this file exactly and consistently across the entire codebase. Deviating from these conventions will break consistency and reduce code quality. When in doubt, refer to `PRD.md` for full context.

---

## 1. Project Folder Structure

Follow this structure exactly. Every new file goes in the correct location — no exceptions.

```
/hostelops-ai
├── PRD.md                        ← Full product requirements
├── CONVENTIONS.md                ← This file
├── .env                          ← All secrets (never commit)
├── .env.example                  ← Template with all keys, no values
├── docker-compose.yml            ← Full stack local/production setup
│
├── /backend
│   ├── main.py                   ← FastAPI app entry point
│   ├── config.py                 ← Reads ALL env vars. Only place to import from .env
│   ├── database.py               ← SQLAlchemy engine, AsyncSession, Base
│   ├── /models                   ← SQLAlchemy ORM models (one file per entity)
│   │   ├── user.py
│   │   ├── complaint.py
│   │   ├── laundry_slot.py
│   │   ├── machine.py
│   │   ├── mess_feedback.py
│   │   ├── mess_alert.py
│   │   ├── approval_queue.py
│   │   ├── override_log.py
│   │   └── notification.py
│   ├── /schemas                  ← Pydantic v2 schemas (SINGLE SOURCE OF TRUTH)
│   │   ├── user.py
│   │   ├── complaint.py
│   │   ├── laundry_slot.py
│   │   ├── machine.py
│   │   ├── mess_feedback.py
│   │   ├── mess_alert.py
│   │   ├── approval_queue.py
│   │   ├── override_log.py
│   │   └── notification.py
│   ├── /routes                   ← FastAPI APIRouter files (thin — no logic here)
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── complaints.py
│   │   ├── laundry.py
│   │   ├── mess.py
│   │   └── notifications.py
│   ├── /services                 ← All business logic (pure Python, no FastAPI imports)
│   │   ├── complaint_service.py
│   │   ├── laundry_service.py
│   │   ├── mess_service.py
│   │   ├── notification_service.py
│   │   ├── auth_service.py
│   │   └── fallback_classifier.py
│   ├── /agents                   ← LangChain agent definitions (one per agent)
│   │   ├── agent_complaint.py
│   │   ├── agent_laundry.py
│   │   └── agent_mess.py
│   ├── /tools                    ← Typed tool callables (one per tool)
│   │   ├── complaint_tools.py
│   │   ├── laundry_tools.py
│   │   └── mess_tools.py
│   ├── /tasks                    ← Celery task definitions
│   │   ├── complaint_tasks.py
│   │   └── notification_tasks.py
│   ├── /middleware
│   │   ├── rate_limiter.py
│   │   └── prompt_sanitizer.py
│   └── /migrations               ← Alembic files (auto-generated, never edit manually)
│
└── /frontend
    └── /src
        ├── /types                ← TypeScript types (mirror Pydantic schemas exactly)
        │   ├── complaint.ts
        │   ├── user.ts
        │   ├── laundry.ts
        │   └── mess.ts
        ├── /api                  ← All API call functions (never use fetch directly in components)
        │   ├── complaintsApi.ts
        │   ├── laundryApi.ts
        │   ├── messApi.ts
        │   ├── authApi.ts
        │   └── notificationsApi.ts
        ├── /components           ← Reusable Shadcn/UI components
        ├── /pages                ← Page-level components
        │   ├── StudentDashboard.tsx
        │   ├── LaundryBooking.tsx
        │   ├── MessFeedback.tsx
        │   ├── WardenDashboard.tsx
        │   ├── ApprovalQueue.tsx
        │   └── Login.tsx
        ├── /hooks                ← Custom React hooks
        │   ├── useAuth.ts
        │   ├── useComplaints.ts
        │   ├── useLaundrySlots.ts
        │   └── useNotifications.ts
        ├── /context
        │   ├── AuthContext.tsx
        │   └── NotificationContext.tsx
        └── /lib
            ├── rolePermissions.ts
            └── utils.ts
```

---

## 2. The Golden Rule — Feature Implementation Order

When adding any new feature, ALWAYS follow this order:

1. Define/update the **Pydantic schema** in `/backend/schemas/`
2. Define/update the **SQLAlchemy model** in `/backend/models/`
3. Generate an **Alembic migration** (`alembic revision --autogenerate`)
4. Write the **service function** in `/backend/services/`
5. Add the **FastAPI route** in `/backend/routes/`
6. Update the matching **TypeScript type** in `/frontend/src/types/`
7. Add the **API function** in `/frontend/src/api/`
8. Build the **component or page** in `/frontend/src/`

**Never skip or reorder these steps.**

---

## 3. Non-Negotiable Coding Rules

### Backend
- **Pydantic schemas are the single source of truth.** Define or check the schema before writing any route, service, or agent code. Every FastAPI route MUST use Pydantic schemas for both request body and response model. Never use raw dicts in route signatures.
- **Routes are thin.** A route handler does exactly three things: validate input (via Pydantic), call a service function, return the response. Zero business logic in routes.
- **All LLM calls go through `/agents/`.** Services call agent functions. Never call LangChain or Groq directly from a route or task.
- **All background work goes through Celery.** LLM classification, push notifications, alert generation — everything slow runs in `/tasks/`. Never run slow operations synchronously inside a route.
- **Async-first is mandatory.** Every route handler uses `async def`. Every DB call uses `AsyncSession`. Every LangChain/LLM call uses the async interface. Never use synchronous blocking calls inside a FastAPI route — this blocks the event loop.
- **All config comes from `config.py`.** Never access `os.environ` or `.env` directly anywhere except `config.py`. Import config values from there.
- **State transitions are centralised.** Never update `complaint.status` directly from a route or task. Always call `transition_complaint()` in `complaint_service.py`.
- **Audit log on every state change.** The `transition_complaint()` function writes to the audit log automatically. Do not add separate audit logging elsewhere.

### Frontend
- **TypeScript types must mirror Pydantic schemas exactly.** When a backend schema changes, update the matching TypeScript type immediately.
- **All API calls go through `/src/api/`.** Never use `fetch()` or `axios` directly inside a component, page, or hook.
- **Role-based access is enforced in `rolePermissions.ts`.** Every protected route checks `user.role` before rendering. Never conditionally render based on hardcoded role strings scattered across components.
- **Environment variables from `import.meta.env` only.** Never hardcode API base URLs or keys.

---

## 4. Data Models (Pydantic Schemas — Source of Truth)

### User
```python
class UserBase(BaseModel):
    name: str
    room_number: str
    role: UserRole  # enum: student | laundry_man | mess_secretary | mess_manager | assistant_warden | warden | chief_warden
    hostel_mode: HostelMode  # enum: college | autonomous

class UserCreate(UserBase):
    password: str
    roll_number: str | None = None
    erp_document_url: str | None = None  # college mode only

class UserRead(UserBase):
    id: str
    is_verified: bool
    is_active: bool
    created_at: datetime
```

### Complaint
```python
class ComplaintCreate(BaseModel):
    text: str  # max 1000 chars, sanitized before LLM
    is_anonymous: bool = False

class ComplaintRead(BaseModel):
    id: str
    student_id: str
    text: str
    is_anonymous: bool
    category: ComplaintCategory | None  # enum: mess | laundry | maintenance | interpersonal | critical
    severity: ComplaintSeverity | None  # enum: low | medium | high
    status: ComplaintStatus  # enum: INTAKE | CLASSIFIED | AWAITING_APPROVAL | ASSIGNED | IN_PROGRESS | RESOLVED | REOPENED | ESCALATED
    assigned_to: str | None
    confidence_score: float | None
    ai_suggested_category: ComplaintCategory | None
    ai_suggested_assignee: str | None
    requires_approval: bool
    classified_by: str  # "llm" | "fallback" | "manual"
    override_reason: str | None
    created_at: datetime
    updated_at: datetime
```

### LaundrySlot
```python
class LaundrySlotCreate(BaseModel):
    machine_id: str
    date: date
    start_time: time
    end_time: time

class LaundrySlotRead(BaseModel):
    id: str
    machine_id: str
    student_id: str
    date: date
    start_time: time
    end_time: time
    status: SlotStatus  # enum: booked | cancelled | completed | no_show
    is_priority: bool
    priority_reason: str | None
    priority_approved_by: str | None
    created_at: datetime
```

### MessFeedback
```python
class MessRatings(BaseModel):
    food_quality: int  # 1-5
    food_quantity: int  # 1-5
    hygiene: int  # 1-5
    menu_variety: int  # 1-5
    timing: int  # 1-5

class MessFeedbackCreate(BaseModel):
    meal: MealPeriod  # enum: breakfast | lunch | dinner
    date: date
    ratings: MessRatings
    comment: str | None = None  # max 300 chars

class MessFeedbackRead(MessFeedbackCreate):
    id: str
    student_id: str
    created_at: datetime
```

### ApprovalQueueItem
```python
class ApprovalQueueItemRead(BaseModel):
    id: str
    complaint_id: str
    ai_suggested_category: ComplaintCategory
    ai_suggested_severity: ComplaintSeverity
    ai_suggested_assignee: str
    confidence_score: float
    status: ApprovalStatus  # enum: pending | approved | corrected
    reviewed_by: str | None
    override_reason: str | None
    created_at: datetime
    reviewed_at: datetime | None
```

---

## 5. API Routes Reference

| Method | Endpoint | Auth | Purpose |
|--------|----------|------|---------|
| POST | `/api/auth/register` | Public | Student registers. Triggers verification workflow. |
| POST | `/api/auth/login` | Public | Returns JWT token with role claim. |
| POST | `/api/users/{id}/verify` | Assistant Warden | Activates pending student account. |
| DELETE | `/api/users/{id}/deactivate` | Assistant Warden | Deactivates vacated student account. |
| POST | `/api/complaints/` | Student | File a new complaint. Returns complaint ID + acknowledgement. |
| GET | `/api/complaints/{id}` | Student (own) / Staff (all) | Get single complaint with full status. |
| PATCH | `/api/complaints/{id}/status` | Staff | Update status (in_progress, resolved). |
| POST | `/api/complaints/{id}/reopen` | Student | Mark resolved complaint as unresolved. |
| GET | `/api/approval-queue/` | Warden | Get all pending approval queue items. |
| POST | `/api/approval-queue/{id}/approve` | Warden | Approve AI suggestion as-is. |
| POST | `/api/approval-queue/{id}/correct` | Warden | Correct AI suggestion. Logs override. |
| GET | `/api/laundry/slots/` | Student | Available slots for a date. Query: `?date=YYYY-MM-DD` |
| POST | `/api/laundry/slots/book` | Student | Book a slot. Agent 2 enforces fairness rules. |
| DELETE | `/api/laundry/slots/{id}` | Student | Cancel a booking. |
| POST | `/api/laundry/machines/{id}/repair` | Laundry Man | Mark machine repaired. Resumes bookings. |
| POST | `/api/mess/feedback/` | Student | Submit meal feedback. One per meal per day enforced. |
| GET | `/api/mess/analytics/` | Warden / Mess Manager | Trend data. Query: `?days=7` or `?days=30` |
| GET | `/api/notifications/` | Any auth user | Get user's notification inbox. |
| PATCH | `/api/notifications/{id}/read` | Any auth user | Mark notification as read. |

---

## 6. Environment Variables

All variables read through `config.py`. Never access directly elsewhere.

```env
# Database
DATABASE_URL=postgresql+asyncpg://...  # from Supabase dashboard

# Auth
JWT_SECRET=<long-random-string>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_HOURS=24
REFRESH_TOKEN_EXPIRE_DAYS=30

# LLM
GROQ_API_KEY=<from console.groq.com>
GROQ_MODEL_NAME=llama3-8b-8192

# Task Queue
CELERY_BROKER_URL=<from Upstash dashboard>
CELERY_RESULT_BACKEND=<same as broker>

# Push Notifications
VAPID_PUBLIC_KEY=<generated with: npx web-push generate-vapid-keys>
VAPID_PRIVATE_KEY=<generated with above command>
VAPID_CLAIM_EMAIL=<contact email>

# Agent Thresholds (tune these over time)
COMPLAINT_CONFIDENCE_THRESHOLD=0.85
MESS_DISSATISFACTION_THRESHOLD=2.5
MESS_SPIKE_DELTA=1.5
LAUNDRY_NOSHOW_PENALTY_HOURS=48
LAUNDRY_UNAVAILABILITY_DAYS=4
APPROVAL_QUEUE_TIMEOUT_MINUTES=30
```

---

## 7. Agent Tool Implementation Rules

Every tool in `/backend/tools/` must follow this pattern exactly:

```python
# Example: assign_complaint_tool
from pydantic import BaseModel
from datetime import datetime

class AssignComplaintInput(BaseModel):
    complaint_id: str
    assignee_id: str
    severity: ComplaintSeverity
    category: ComplaintCategory

class AssignmentResult(BaseModel):
    success: bool
    notified: bool
    assigned_at: datetime

async def assign_complaint_tool(input: AssignComplaintInput, db: AsyncSession) -> AssignmentResult:
    # 1. Call transition_complaint() — never update status directly
    # 2. Call notification_service to notify assignee
    # 3. Return typed result
    ...
```

Rules:
- Every tool has a `Input` Pydantic model and a `Result` Pydantic model.
- Every tool is an `async def` function.
- Tools call services — never directly access the database themselves.
- Tools never call other tools directly — the agent orchestrates tool calls.
- All 16 tools are defined and callable before any agent is wired up.

---

## 8. Fallback Classifier

Implement in `/backend/services/fallback_classifier.py`. Pure function, no external dependencies, no async needed.

```python
def classify_with_fallback(text: str) -> ClassificationResult:
    text_lower = text.lower()
    
    if any(kw in text_lower for kw in ["food", "mess", "meal", "breakfast", "lunch", "dinner", "cook", "taste", "hygiene"]):
        return ClassificationResult(category="mess", severity="medium", classified_by="fallback")
    
    if any(kw in text_lower for kw in ["laundry", "washing", "machine", "clothes", "slot", "dryer"]):
        return ClassificationResult(category="laundry", severity="medium", classified_by="fallback")
    
    if any(kw in text_lower for kw in ["water", "electricity", "fan", "light", "ac", "furniture", "door", "window", "plumbing"]):
        return ClassificationResult(category="maintenance", severity="medium", classified_by="fallback")
    
    if any(kw in text_lower for kw in ["fight", "harassment", "threat", "abuse", "unsafe", "scared", "uncomfortable"]):
        return ClassificationResult(category="interpersonal", severity="high", requires_approval=True, classified_by="fallback")
    
    # No match — send to manual review
    return ClassificationResult(category="uncategorised", severity="medium", requires_approval=True, classified_by="fallback", note="Fallback classifier — no keyword match found")
```

**Always set `classified_by="fallback"` on the complaint record.** This must be visible on the Warden dashboard.

---

## 9. Third-Party Setup Checklist

Complete in this order before writing any code:

- [ ] **Supabase** — create free project at supabase.com → copy `DATABASE_URL` to `.env`
- [ ] **Groq** — create free account at console.groq.com → generate API key → add `GROQ_API_KEY` to `.env`
- [ ] **Upstash** — create free Redis database at upstash.com → copy Redis URL to `.env` as both `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND`
- [ ] **VAPID Keys** — run `npx web-push generate-vapid-keys` → add both keys to `.env`
- [ ] **Railway** — create free account at railway.app → connect GitHub repo → add all `.env` variables in Railway environment panel → deploy

---

## 10. How to Prompt This AI Assistant Effectively

When asking the AI to build a feature, always reference the relevant sections:

```
@CONVENTIONS.md @PRD.md

Following CONVENTIONS.md Section 2 (feature order) and Section 3 (coding rules):
Implement the complaint filing route.

- Schema: ComplaintCreate is already defined in CONVENTIONS.md Section 4
- Route: POST /api/complaints/ (see Section 5)
- The route must call classify_complaint() from complaint_service.py asynchronously via Celery
- Agent 1 tool definitions are in PRD.md Section 3.3
- State machine: complaint starts in INTAKE state (PRD.md Section 9)
- Failure handling: if Groq fails, follow PRD.md Section 10.2 retry policy
```

**Be specific. Reference sections. The more context you give, the better the output.**
