# HostelOps AI — Developer Conventions
> **READ THIS FIRST.** This file is the coding rulebook for HostelOps AI. If you are an AI coding assistant working on this project, follow every rule in this file exactly and consistently across the entire codebase. Deviating from these conventions will break consistency and reduce code quality. When in doubt, refer to `PRD.md` for full context.

---

## 1. Project Folder Structure

Follow this structure exactly. Every new file goes in the correct location — no exceptions.

```
/HostelOPS AI
├── PRD.md                        ← Full product requirements
├── CONVENTIONS.md                ← This file
├── PROJECT_STATE.md              ← Living project state (update after every sprint)
├── .gitignore
│
├── /backend
│   ├── main.py                   ← FastAPI app entry point
│   ├── config.py                 ← Reads ALL env vars. Only place to import from .env
│   ├── database.py               ← SQLAlchemy async engine + sync engine (psycopg2 for Celery)
│   ├── celery_app.py             ← Celery app + beat schedule. sys.path fix MUST stay at top.
│   ├── create_admin.py           ← Bootstrap script: admin account + machines + hostel config
│   ├── /models                   ← SQLAlchemy ORM models (one file per entity)
│   │   ├── user.py
│   │   ├── complaint.py
│   │   ├── audit_log.py
│   │   ├── approval_queue.py
│   │   ├── override_log.py
│   │   ├── notification.py
│   │   ├── machine.py            ← NOTE: named machine.py not laundry_machine.py (Sprint 4 deviation)
│   │   ├── laundry_slot.py
│   │   ├── mess_feedback.py
│   │   ├── mess_alert.py
│   │   ├── hostel_config.py
│   │   ├── refresh_token.py
│   │   └── push_subscription.py
│   ├── /schemas                  ← Pydantic v2 schemas (SINGLE SOURCE OF TRUTH)
│   │   ├── enums.py              ← All enums (UserRole, ComplaintStatus, etc.)
│   │   ├── user.py
│   │   ├── complaint.py
│   │   ├── laundry.py
│   │   ├── mess.py
│   │   ├── approval_queue.py
│   │   ├── override_log.py
│   │   ├── notification.py
│   │   ├── hostel_config.py
│   │   └── metrics.py
│   ├── /routes                   ← FastAPI APIRouter files (thin — no logic here)
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── complaints.py
│   │   ├── approval_queue.py
│   │   ├── laundry.py
│   │   ├── mess.py
│   │   ├── notifications.py
│   │   ├── push.py
│   │   ├── analytics.py
│   │   └── hostel_config.py
│   ├── /services                 ← All business logic (pure Python, no FastAPI imports)
│   │   ├── auth_service.py       ← Uses bcrypt directly. NEVER passlib.
│   │   ├── user_service.py
│   │   ├── complaint_service.py  ← VALID_TRANSITIONS lives here. Never redefine elsewhere.
│   │   ├── approval_queue_service.py
│   │   ├── override_log_service.py
│   │   ├── notification_service.py ← notify_user() calls push inside try/except always
│   │   ├── laundry_service.py
│   │   ├── mess_service.py
│   │   ├── push_service.py
│   │   ├── metrics_service.py
│   │   ├── hostel_config_service.py ← cached config, falls back to .env
│   │   └── fallback_classifier.py
│   ├── /agents                   ← LangChain agent definitions (one per agent)
│   │   ├── agent_complaint.py
│   │   ├── agent_laundry.py
│   │   └── agent_mess.py
│   ├── /tools                    ← Typed tool callables (one per tool group)
│   │   ├── complaint_tools.py
│   │   ├── laundry_tools.py
│   │   └── mess_tools.py
│   ├── /tasks                    ← Celery task definitions
│   │   ├── complaint_tasks.py
│   │   ├── approval_tasks.py
│   │   ├── laundry_tasks.py
│   │   └── mess_tasks.py
│   ├── /middleware
│   │   ├── rate_limiter.py
│   │   └── prompt_sanitizer.py
│   ├── .env                      ← NOT committed to git
│   ├── .env.example              ← Committed — all variable names, no values
│   └── /migrations               ← Alembic files (auto-generated, never edit manually)
│
└── /frontend                     ← React 18 + TypeScript + Vite + Tailwind + Shadcn/UI (Sprint F)
    ├── index.html
    ├── vite.config.ts
    ├── tailwind.config.ts
    └── /src
        ├── main.tsx
        ├── App.tsx
        ├── service-worker.ts
        ├── /types                ← TypeScript types (mirror Pydantic schemas exactly)
        │   ├── user.ts
        │   ├── complaint.ts
        │   ├── laundry.ts
        │   ├── mess.ts
        │   ├── notification.ts
        │   └── hostelConfig.ts
        ├── /api                  ← All API call functions (never use fetch/axios in components)
        │   ├── client.ts         ← Axios instance with auto refresh token interceptor
        │   ├── authApi.ts
        │   ├── complaintsApi.ts
        │   ├── laundryApi.ts
        │   ├── messApi.ts
        │   ├── notificationsApi.ts
        │   ├── pushApi.ts
        │   └── configApi.ts
        ├── /components
        │   ├── /ui               ← Shadcn/UI base components
        │   ├── StatusBadge.tsx
        │   ├── SkeletonCard.tsx
        │   ├── ConfettiOverlay.tsx
        │   ├── DriftAlertBanner.tsx
        │   └── NotificationBell.tsx
        ├── /pages
        │   ├── /auth
        │   │   ├── Landing.tsx
        │   │   ├── Login.tsx
        │   │   ├── Register.tsx
        │   │   ├── RegistrationPending.tsx
        │   │   └── RegistrationRejected.tsx
        │   ├── /student
        │   │   ├── StudentHome.tsx
        │   │   ├── Onboarding.tsx
        │   │   ├── FileComplaint.tsx
        │   │   ├── ComplaintTracker.tsx
        │   │   ├── ComplaintDetail.tsx
        │   │   ├── LaundryBooking.tsx
        │   │   ├── MessFeedback.tsx
        │   │   ├── NotificationInbox.tsx
        │   │   └── StudentProfile.tsx
        │   ├── /warden
        │   │   ├── WardenDashboard.tsx
        │   │   ├── ApprovalQueue.tsx
        │   │   ├── StudentRegistrations.tsx
        │   │   ├── CreateStaffAccount.tsx
        │   │   ├── ComplaintManagement.tsx
        │   │   └── HostelSettings.tsx
        │   └── /staff
        │       ├── LaundryManView.tsx
        │       └── MessStaffView.tsx
        ├── /hooks
        │   ├── useAuth.ts
        │   ├── useComplaints.ts
        │   ├── useLaundrySlots.ts
        │   ├── useNotifications.ts  ← polls GET /api/notifications/ every 30 seconds
        │   └── usePushSubscription.ts
        ├── /context
        │   ├── AuthContext.tsx
        │   └── ThemeContext.tsx
        └── /lib
            ├── rolePermissions.ts
            ├── tokenManager.ts
            └── utils.ts
```

---

## 2. The Golden Rule — Feature Implementation Order

When adding any new feature, ALWAYS follow this order:

1. Define/update the **Pydantic schema** in `/backend/schemas/`
2. Define/update the **SQLAlchemy model** in `/backend/models/`
3. Generate an **Alembic migration** (`alembic revision --autogenerate`)
4. Run `alembic upgrade head`
5. Write the **service function** in `/backend/services/`
6. Add the **FastAPI route** in `/backend/routes/`
7. Update the matching **TypeScript type** in `/frontend/src/types/`
8. Add the **API function** in `/frontend/src/api/`
9. Build the **component or page** in `/frontend/src/`

**Never skip or reorder these steps.**

---

## 3. Non-Negotiable Coding Rules

### Backend
- **Pydantic schemas are the single source of truth.** Every FastAPI route MUST use Pydantic schemas for both request body and `response_model`. Never use raw dicts.
- **Routes are thin.** Validate input → call service → return response. Zero business logic in routes.
- **All LLM calls go through `/agents/`.** Never call LangChain or Groq directly from a route or task.
- **All background work goes through Celery.** LLM classification, alert generation — everything slow runs in `/tasks/`.
- **Async-first is mandatory.** Every route handler uses `async def`. Every DB call uses `AsyncSession`. Never synchronous blocking code inside a route.
- **All config comes from `config.py`.** Never access `os.environ` or `.env` directly anywhere except `config.py`.
- **State transitions are centralised.** Never update `complaint.status` directly. Always call `transition_complaint()` in `complaint_service.py`.
- **Audit log on every state change.** `transition_complaint()` writes to audit log automatically. Pass `ip_address` from `request.client.host` always.
- **Always call `await db.refresh(obj)` after `await db.commit()`** when the object will be accessed afterward.
- **Always add UUID → str field_validator** to any Pydantic schema validating SQLAlchemy ORM objects.
- **Every new PostgreSQL enum value needs an Alembic migration** before it is used in code.
- **notify_user() is the single notification function.** Push is called inside it with try/except. Never create separate push/in-app variants.
- **Hostel config values come from hostel_config_service.get_config()**, not hardcoded settings. The service has a 5-minute in-memory cache.

### Frontend
- **TypeScript types must mirror Pydantic schemas exactly.** When a backend schema changes, update the matching TypeScript type immediately.
- **All API calls go through `/src/api/`.** Never use `fetch()` or `axios` directly inside a component, page, or hook.
- **`client.ts` handles token refresh automatically** via axios interceptors. On 401 → call `/api/auth/refresh` silently. If refresh fails → clear tokens → redirect to login. Never let 401 bubble to components.
- **Role-based access is enforced in `rolePermissions.ts`.** Every protected route checks `user.role` via `ProtectedRoute` wrapper. Never conditionally render based on hardcoded role strings scattered in components.
- **Skeleton loaders always, never spinners.** Use `SkeletonCard` component on all data-heavy screens.
- **Notification polling: 30 seconds.** `useNotifications` hook calls `GET /api/notifications/` every 30 seconds when app is open. This is the V1 real-time strategy — do not implement WebSockets.
- **Push subscription registered once** from `usePushSubscription` hook called in `App.tsx` after login.
- **Onboarding shown once per account.** Check `user.has_seen_onboarding` from login response. If false → show `Onboarding.tsx` → call `PATCH /api/users/me/onboarding-seen`.
- **Theme toggle in ThemeContext.** Preference stored in localStorage as `theme: "light" | "dark"`. Applied as class on `<html>` element.
- **Environment variables from `import.meta.env` only.** Never hardcode API base URLs or keys.

---

## 4. Data Models (Pydantic Schemas — Source of Truth)

### User
```python
class UserCreate(BaseModel):
    name: str
    room_number: str
    role: UserRole  # student | laundry_man | mess_secretary | mess_manager | assistant_warden | warden | chief_warden
    hostel_mode: HostelMode  # college | autonomous
    password: str
    roll_number: str | None = None  # college mode only
    hostel_code: str  # required for student registration (Sprint 7 multi-tenant)

class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    room_number: str
    role: UserRole
    hostel_mode: HostelMode
    is_verified: bool
    is_active: bool
    is_rejected: bool
    rejection_reason: str | None
    has_seen_onboarding: bool
    created_at: datetime

    @field_validator('id', mode='before')
    @classmethod
    def uuid_to_str(cls, v):
        return str(v) if v is not None else None
```

### Complaint
```python
class ComplaintCreate(BaseModel):
    text: str  # min 10 chars, max 1000 chars, sanitized before LLM
    is_anonymous: bool = False

class ComplaintRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    student_id: str
    text: str
    sanitized_text: str | None
    flagged_input: str | None
    is_anonymous: bool
    category: ComplaintCategory | None  # mess | laundry | maintenance | interpersonal | critical | uncategorised
    severity: ComplaintSeverity | None  # low | medium | high
    status: ComplaintStatus  # INTAKE | CLASSIFIED | AWAITING_APPROVAL | ASSIGNED | IN_PROGRESS | RESOLVED | REOPENED | ESCALATED
    assigned_to: str | None
    confidence_score: float | None
    ai_suggested_category: ComplaintCategory | None
    ai_suggested_assignee: str | None
    requires_approval: bool
    classified_by: str  # "llm" | "fallback" | "warden_override"
    override_reason: str | None
    resolved_confirmed_at: datetime | None
    reopen_reason: str | None
    is_priority: bool
    created_at: datetime
    updated_at: datetime

    @field_validator('id', 'student_id', 'assigned_to', 'ai_suggested_assignee', mode='before')
    @classmethod
    def uuid_to_str(cls, v):
        return str(v) if v is not None else None
```

### LaundrySlot
```python
# IMPORTANT Sprint 4 deviations:
# - booking_status field (LaundrySlotStatus enum) — not status
# - slot_date (date) and slot_time (str "09:00-10:00") — not start_time/end_time
# - Machine model is named Machine not LaundryMachine
# - Machine uses repaired_at not last_serviced_at

class LaundrySlotRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    machine_id: str
    student_id: str | None
    slot_date: date
    slot_time: str
    booking_status: LaundrySlotStatus  # available | booked | completed | cancelled | no_show
    priority_score: float | None
    booked_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
```

### MessFeedback
```python
# IMPORTANT Sprint 4 deviation:
# MessFeedback uses 5 SEPARATE columns, NOT a single rating:
# food_quality, hygiene, menu_variety, food_quantity, timing (each int 1-5)
# meal field is named 'meal' NOT 'meal_type'
# date field is named 'date' NOT 'feedback_date' (use Field(alias="date") in schema)

class MessFeedbackCreate(BaseModel):
    meal: str  # breakfast | lunch | dinner
    food_quality: int  # 1-5
    hygiene: int  # 1-5
    menu_variety: int  # 1-5
    food_quantity: int  # 1-5
    timing: int  # 1-5
    comment: str | None = None  # max 300 chars
    feedback_date: date

class MessFeedbackRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    student_id: str
    meal: str
    feedback_date: date = Field(alias="date")  # DB column is 'date'
    food_quality: int
    hygiene: int
    menu_variety: int
    food_quantity: int
    timing: int
    comment: str | None
    created_at: datetime
```

### ApprovalQueueItem
```python
class ApprovalQueueItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    complaint_id: str
    ai_suggested_category: ComplaintCategory
    ai_suggested_severity: ComplaintSeverity
    ai_suggested_assignee: str | None
    confidence_score: float
    status: str  # pending | approved | corrected | timed_out
    reviewed_by: str | None
    override_reason: str | None
    created_at: datetime
    reviewed_at: datetime | None

    @field_validator('id', 'complaint_id', 'ai_suggested_assignee', 'reviewed_by', mode='before')
    @classmethod
    def uuid_to_str(cls, v):
        return str(v) if v is not None else None
```

### LoginResponse
```python
class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserRead  # full user object — frontend does not need a second /me call
```

---

## 5. API Routes Reference (Current — Sprints 1-6)

### Auth
| Method | Endpoint | Auth | Purpose |
|--------|----------|------|---------|
| POST | `/api/auth/register` | Public | Student registers with hostel_code |
| POST | `/api/auth/login` | Public | Returns tokens + full user object |
| POST | `/api/auth/refresh` | Public | Rotate refresh token |
| POST | `/api/auth/logout` | Any auth | Revoke all refresh tokens for user |

### Users
| Method | Endpoint | Auth | Purpose |
|--------|----------|------|---------|
| GET | `/api/users/me` | Any auth | Get current user profile |
| PATCH | `/api/users/me/onboarding-seen` | Any auth | Mark onboarding complete |
| PATCH | `/api/users/me/password` | Any auth | Self-service password change |
| POST | `/api/users/{id}/verify` | Warden | Verify pending student |
| POST | `/api/users/{id}/reject` | Warden | Reject registration with reason |
| PATCH | `/api/users/{id}/reset-password` | Warden | Reset student password |
| DELETE | `/api/users/{id}/deactivate` | Warden | Deactivate account |
| GET | `/api/users` | Warden | All users with filters |
| POST | `/api/staff` | Warden | Create staff account (immediately active) |
| GET | `/api/staff` | Warden | All active staff |

### Hostels (Sprint 7)
| Method | Endpoint | Auth | Purpose |
|--------|----------|------|---------|
| POST | `/api/hostels/setup` | Public | Warden creates hostel, gets unique code |
| GET | `/api/hostels/{code}/info` | Public | Returns hostel name + mode (for landing page) |

### Complaints
| Method | Endpoint | Auth | Purpose |
|--------|----------|------|---------|
| POST | `/api/complaints/` | Student | File complaint (min 10 chars) |
| GET | `/api/complaints/my` | Student | Own complaints (paginated) |
| GET | `/api/complaints/{id}` | Student (own) / Staff | Single complaint |
| GET | `/api/complaints/{id}/timeline` | Student (own) / Staff | Audit log entries |
| PATCH | `/api/complaints/{id}/status` | Staff | Update status |
| POST | `/api/complaints/{id}/reopen` | Student | Reopen resolved complaint |
| POST | `/api/complaints/{id}/escalate` | Warden | Escalate complaint |
| GET | `/api/complaints` | Warden | All complaints with search + filter |

### Approval Queue
| Method | Endpoint | Auth | Purpose |
|--------|----------|------|---------|
| GET | `/api/approval-queue/` | Warden | Pending items (paginated) |
| POST | `/api/approval-queue/{id}/approve` | Warden | Approve AI suggestion |
| POST | `/api/approval-queue/{id}/override` | Warden | Override with corrections |

### Laundry
| Method | Endpoint | Auth | Purpose |
|--------|----------|------|---------|
| GET | `/api/laundry/slots` | Any auth | Available slots for date |
| POST | `/api/laundry/slots/book` | Student | Book a slot |
| DELETE | `/api/laundry/slots/{id}` | Student / Laundry Man | Cancel slot |
| PATCH | `/api/laundry/slots/{id}/complete` | Laundry Man | Mark slot complete |
| GET | `/api/laundry/my-bookings` | Student | Own upcoming bookings |
| GET | `/api/laundry/machines` | Any auth | All machines with status |
| POST | `/api/laundry/machines` | Warden | Create machine |
| PATCH | `/api/laundry/machines/{id}/status` | Warden / Laundry Man | Update machine status |

### Mess
| Method | Endpoint | Auth | Purpose |
|--------|----------|------|---------|
| POST | `/api/mess/feedback` | Student | Submit feedback (one per meal per day) |
| GET | `/api/mess/summary` | Any auth | Daily avg + participation |
| GET | `/api/mess/alerts` | Warden / Mess Manager | Recent alerts |
| GET | `/api/mess/my-feedback` | Student | Own feedback history |
| POST | `/api/mess/menu` | Mess Manager | Publish new menu (Sprint 7b) |
| GET | `/api/mess/menu/current` | Any auth | Current active menu (Sprint 7b) |
| GET | `/api/mess/menu/history` | Warden / Mess Manager | Past menus (Sprint 7b) |

### Notifications
| Method | Endpoint | Auth | Purpose |
|--------|----------|------|---------|
| GET | `/api/notifications/` | Any auth | Inbox (paginated, newest first) |
| PATCH | `/api/notifications/{id}/read` | Any auth | Mark single as read |
| PATCH | `/api/notifications/read-all` | Any auth | Mark all as read |

### Push
| Method | Endpoint | Auth | Purpose |
|--------|----------|------|---------|
| GET | `/api/push/vapid-public-key` | Public | VAPID key for PWA subscription |
| POST | `/api/push/subscribe` | Any auth | Save push subscription |
| DELETE | `/api/push/unsubscribe` | Any auth | Remove subscription |

### Analytics
| Method | Endpoint | Auth | Purpose |
|--------|----------|------|---------|
| GET | `/api/analytics/dashboard` | Warden | All 7 metrics + pending counts + drift_alert |
| GET | `/api/analytics/complaints` | Warden | Complaint breakdown |
| GET | `/api/analytics/mess` | Warden / Mess Manager | Per-dimension trends |
| GET | `/api/analytics/laundry` | Warden / Laundry Man | Utilization stats |
| GET | `/api/analytics/overrides` | Warden | Paginated override log |

### Config
| Method | Endpoint | Auth | Purpose |
|--------|----------|------|---------|
| GET | `/api/config` | Any auth | Current hostel config |
| PATCH | `/api/config` | Warden | Update hostel config |

### Notice Board (Sprint 7b)
| Method | Endpoint | Auth | Purpose |
|--------|----------|------|---------|
| POST | `/api/notices` | Warden | Post a notice |
| GET | `/api/notices` | Any auth | All active notices |
| DELETE | `/api/notices/{id}` | Warden | Remove a notice |

### Health
| Method | Endpoint | Auth | Purpose |
|--------|----------|------|---------|
| GET | `/health` | Public | Returns `{ "status": "ok" }` (Sprint 7b) |

---

## 6. Environment Variables

All variables read through `config.py`. Never access directly elsewhere.

```env
# Database
DATABASE_URL=postgresql+asyncpg://postgres.PROJECT_REF:PASSWORD@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres
# NOTE: Always port 5432 (direct). Never 6543 (pgBouncer conflicts with asyncpg)

# Auth
JWT_SECRET=<long-random-string>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_HOURS=24
REFRESH_TOKEN_EXPIRE_DAYS=30

# LLM — llama3-8b-8192 was DECOMMISSIONED by Groq in March 2026
GROQ_API_KEY=<from console.groq.com>
GROQ_MODEL_NAME=llama-3.3-70b-versatile

# Task Queue
CELERY_BROKER_URL=<from Upstash dashboard — rediss://... format>
CELERY_RESULT_BACKEND=<same as broker>

# Push Notifications (VAPID)
VAPID_PRIVATE_KEY=<generate with pywebpush>
VAPID_PUBLIC_KEY=<generate with pywebpush>
VAPID_CLAIM_EMAIL=admin@hostelops.ai

# Complaint Agent
COMPLAINT_CONFIDENCE_THRESHOLD=0.85

# Mess Feedback Thresholds
MESS_ALERT_THRESHOLD=2.5
MESS_CRITICAL_THRESHOLD=2.0
MESS_MIN_PARTICIPATION=0.15
MESS_MIN_RESPONSES=5

# Laundry
LAUNDRY_SLOTS_START_HOUR=8
LAUNDRY_SLOTS_END_HOUR=22
LAUNDRY_SLOT_DURATION_HOURS=1
LAUNDRY_NOSHOW_PENALTY_HOURS=48
LAUNDRY_CANCELLATION_DEADLINE_MINUTES=15

# Approval Queue
APPROVAL_QUEUE_TIMEOUT_MINUTES=30
```

---

## 7. Agent Tool Implementation Rules

Every tool in `/backend/tools/` must follow this pattern exactly:

```python
import logging
logger = logging.getLogger(__name__)

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
- Every tool has an `Input` Pydantic model and a `Result` Pydantic model.
- Every tool is `async def`.
- Tools call services — never directly access the database themselves.
- Tools never call other tools — the agent orchestrates tool calls.
- `import logging` + `logger = logging.getLogger(__name__)` at top of every tool file.

---

## 8. Fallback Classifier

Located at `/backend/services/fallback_classifier.py`. Pure function, no external dependencies.

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

    return ClassificationResult(category="uncategorised", severity="medium", requires_approval=True, classified_by="fallback")
```

Always set `classified_by="fallback"` on the complaint record.

---

## 9. Third-Party Setup Checklist

Complete in this order before writing any code:

- [ ] **Supabase** — create free project → copy `DATABASE_URL` to `.env` (port 5432, not 6543)
- [ ] **Groq** — create free account at console.groq.com → generate API key → add to `.env`
- [ ] **Upstash** — create free Redis → copy URL to `.env` as `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND`
- [ ] **VAPID Keys** — generate with pywebpush → add both keys to `.env`
- [ ] **Railway** — create account → connect GitHub repo → add all `.env` variables → deploy

---

## 10. Real-Time Strategy (V1)

**Notifications use 30-second polling — not WebSockets.**

- `useNotifications` hook in frontend calls `GET /api/notifications/` every 30 seconds when app is open.
- Push notifications (pywebpush) handle the "app is closed" case — that's already implemented.
- WebSockets are deferred to V2. Do not implement them in Sprint F.

This decision is intentional. 30-second lag on an in-app notification is acceptable for a hostel management system.

---

## 11. Golden Rules (Never Violate)

1. **Never change working code** just because you would do it differently.
2. **Never use passlib.** Use `hash_password()` and `verify_password()` from `auth_service.py`.
3. **Never change DATABASE_URL port to 6543.** Always 5432.
4. **Never put logic in routes.** Routes call services. Services contain logic.
5. **Never call the LLM directly from a route or service.** All LLM calls go through `/agents/`.
6. **Never run slow operations synchronously.** Everything slow goes through Celery tasks.
7. **Never hardcode any config value.** Read from `config.py` → `settings.*`.
8. **Never commit `.env`** under any circumstances.
9. **Always update PROJECT_STATE.md** at the end of every sprint before starting the next.
10. **Always reference PRD.md and CONVENTIONS.md** before writing any new code.
11. **VALID_TRANSITIONS defined only in `complaint_service.py`.** Import it, never redefine.
12. **Always define `logger = logging.getLogger(__name__)` at module level** in every file that uses logging.
13. **Never remove the sys.path fix from `celery_app.py`.**
14. **Never hardcode the Groq model name.** Use `settings.GROQ_MODEL_NAME`.
15. **Always restore GROQ_API_KEY after fallback testing.**
16. **Always call `await db.refresh(obj)` after `await db.commit()`** when returning the ORM object.
17. **Always add UUID → str field_validator** to Pydantic schemas validating SQLAlchemy ORM objects.
18. **Every new PostgreSQL enum value needs an Alembic migration** before it is used in code.
19. **WARDEN_ROLES always = [assistant_warden, warden, chief_warden]** — never just `warden`.
20. **Event loop closed warning in Celery on Windows is non-fatal.** Retry succeeds automatically. No workarounds.
21. **Never store raw refresh tokens.** Always store SHA256 hash. Raw token sent to client once only.
22. **notify_user() is the single notification function.** Push called inside with try/except always.
23. **Always run `alembic upgrade head` after pulling new code.**
24. **Analytics queries must handle NULL enum fields.** Always check `if field is not None` before `.value`.
25. **Check Sprint 4 deviations before querying mess/laundry models.** MessFeedback columns: food_quality, hygiene, menu_variety, food_quantity, timing. RefreshToken column: `revoked` not `is_revoked`. Machine column: `repaired_at` not `last_serviced_at`.
26. **Notification polling is 30 seconds in Sprint F.** Do not implement WebSockets.
27. **Every FastAPI route must have an explicit `response_model=` decorator.**
28. **All list endpoints must support `limit` and `offset` pagination params.**
29. **All datetime fields in API responses must include timezone info** (`Z` or `+00:00`).
30. **Complaint text minimum 10 characters.** Enforce in Pydantic schema and backend validation.

---

## 12. How to Prompt This AI Assistant Effectively

When asking the AI to build a feature, always reference the relevant sections:

```
@CONVENTIONS.md @PRD.md @PROJECT_STATE.md

Following CONVENTIONS.md Section 2 (feature order) and Section 11 (golden rules):
Implement [feature name].

- Schema: [reference Section 4]
- Route: [reference Section 5]
- Deviations to respect: [reference PROJECT_STATE.md Section 5]
- State machine (complaints): PRD.md Section 9
- Failure handling: PRD.md Section 10
```

**Be specific. Reference sections. The more context you give, the better the output.**