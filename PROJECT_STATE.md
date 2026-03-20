# HostelOps AI — Project State Document & AI Onboarding Prompt
# Version: Sprint 6 Complete — Sprint 7 Starting
# Last Updated: March 2026
# Purpose: Single source of truth for the current project state.
#          Paste into ANY AI assistant to instantly onboard it.
#          Update at the end of every sprint.

---

## INSTRUCTIONS FOR AI READING THIS

You are being onboarded as a developer/reviewer for HostelOps AI. Read this entire document before doing or saying anything. This document tells you:

1. What this project is
2. Every decision that has been made and WHY
3. The current state of the codebase
4. What has been built, what deviates from the original plan, and what is next
5. Rules you must follow without exception

After reading:
- **If called for verification:** audit the codebase against this document and report what matches, what deviates, and what is missing.
- **If called for development:** pick up from the current sprint and follow CONVENTIONS.md exactly.
- **If called for debugging:** fix only what is broken, do not refactor anything that is working.
- **Never** change something that is working just because you would have done it differently.

---

## SECTION 1 — WHAT IS HOSTELOPS AI

HostelOps AI is an autonomous operations management system for hostels (college-affiliated and independent PGs). It uses a multi-agent AI architecture to automate three core hostel operations:

- **Agent 1 (Orchestrator):** Receives all student complaints, classifies them using an LLM, and routes them to the correct agent or staff member. Uses confidence-gated action — acts automatically when confident, escalates to human when uncertain.
- **Agent 2 (Laundry Agent):** Manages laundry slot booking with a fairness algorithm. Handles machine breakdowns and priority requests.
- **Agent 3 (Mess Agent):** Monitors mess feedback across 5 dimensions. Detects chronic dissatisfaction and sudden spikes. Alerts warden and mess manager proactively.

**Deployment model:** Multi-tenant. One deployment serves multiple hostels. Each hostel has a unique hostel code (e.g. `IGBH-4821`) that students enter during registration.

**Full product specification is in PRD.md** — always reference it for feature details.
**All coding rules are in CONVENTIONS.md** — always follow it without exception.

---

## SECTION 2 — NON-NEGOTIABLE CONSTRAINTS

| Constraint | Detail |
|-----------|--------|
| Zero cost | No paid APIs. No paid services beyond Railway hobby ($5/month optional). |
| Open-source LLM | Groq free tier + llama-3.3-70b-versatile. Never swap to a paid model. |
| No paid infrastructure | Supabase free for DB, Upstash free for Redis, Railway free for hosting. |
| AI-first development | Every file, folder, and pattern is optimised for AI coding assistant use. |
| All three agents in V1 | Never reduce scope to a single agent. All three ship together. |
| LangChain for V1 | LangGraph is documented as the V2 upgrade path but not implemented in V1. |
| Async-first | Every route, DB call, and LLM call is async. No synchronous blocking code. |
| Pydantic as source of truth | Every entity has a Pydantic schema. TypeScript types mirror them exactly. |
| Multi-tenant from Sprint 7 | Every query must filter by hostel_id after Sprint 7. |

---

## SECTION 3 — TECHNOLOGY STACK (FINAL, LOCKED)

| Layer | Technology | Notes |
|-------|-----------|-------|
| Frontend | React 18 + TypeScript + Vite + PWA + Tailwind + Shadcn/UI | Sprint F |
| Backend | Python + FastAPI + Pydantic v2 + SQLAlchemy + Alembic | Sprints 1-6 complete |
| Agent Orchestration | LangChain | LangGraph is V2 upgrade path |
| LLM | Groq free tier + llama-3.3-70b-versatile | llama3-8b-8192 DECOMMISSIONED March 2026 |
| Task Queue | Celery + Upstash Redis (free tier) | Windows dev: --pool=solo |
| Database | PostgreSQL via Supabase (free tier) | Port 5432 always, NEVER 6543 |
| Auth | JWT via python-jose + bcrypt (direct, NOT passlib) | passlib permanently removed |
| Hosting | Railway | Sprint D: Docker Compose |
| Push Notifications | Web Push API (pywebpush) | VAPID keys in .env |
| Config | python-dotenv + pydantic-settings | All secrets in .env |

---

## SECTION 4 — PROJECT FOLDER STRUCTURE

```
/HostelOPS AI
├── PRD.md
├── CONVENTIONS.md
├── PROJECT_STATE.md
├── .gitignore
│
├── /backend
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── celery_app.py             ← sys.path fix MUST stay at very top
│   ├── create_admin.py           ← seeds admin + machines + hostel config
│   ├── /models
│   │   ├── user.py               ← has is_rejected, rejection_reason, has_seen_onboarding
│   │   ├── complaint.py          ← has resolved_confirmed_at, reopen_reason, is_priority
│   │   ├── audit_log.py          ← has ip_address column
│   │   ├── approval_queue.py
│   │   ├── override_log.py       ← warden_id field (not corrected_by)
│   │   ├── notification.py
│   │   ├── machine.py            ← named machine.py (Sprint 4 deviation)
│   │   ├── laundry_slot.py       ← booking_status + slot_date + slot_time
│   │   ├── mess_feedback.py      ← 5 separate columns: food_quality, hygiene, menu_variety, food_quantity, timing
│   │   ├── mess_alert.py
│   │   ├── hostel_config.py      ← single row per hostel, cached 5 mins
│   │   ├── refresh_token.py      ← revoked column (not is_revoked)
│   │   └── push_subscription.py
│   ├── /schemas
│   │   ├── enums.py
│   │   ├── user.py               ← StaffCreate + StaffRead added Sprint 6
│   │   ├── complaint.py
│   │   ├── laundry.py
│   │   ├── mess.py
│   │   ├── approval_queue.py
│   │   ├── override_log.py
│   │   ├── notification.py
│   │   ├── hostel_config.py
│   │   └── metrics.py            ← DashboardMetrics with all 7 metrics + pending counts
│   ├── /routes
│   │   ├── auth.py               ← login returns full user object
│   │   ├── users.py              ← reject, reset-password, staff CRUD, /me, onboarding
│   │   ├── complaints.py
│   │   ├── approval_queue.py
│   │   ├── laundry.py
│   │   ├── mess.py
│   │   ├── notifications.py
│   │   ├── push.py
│   │   ├── analytics.py          ← all 3 stubs replaced with real data in Sprint 6
│   │   └── hostel_config.py
│   ├── /services
│   │   ├── auth_service.py       ← bcrypt ONLY, no passlib
│   │   ├── user_service.py       ← reject_user, warden_reset_password, create_staff_account
│   │   ├── complaint_service.py  ← VALID_TRANSITIONS single source of truth
│   │   ├── approval_queue_service.py
│   │   ├── override_log_service.py
│   │   ├── notification_service.py ← notify_user() calls push inside try/except
│   │   ├── laundry_service.py
│   │   ├── mess_service.py
│   │   ├── push_service.py
│   │   ├── metrics_service.py    ← all 7 metrics + complaints/mess/laundry analytics
│   │   ├── hostel_config_service.py ← cached config, falls back to .env
│   │   └── fallback_classifier.py
│   ├── /agents
│   │   ├── agent_complaint.py
│   │   ├── agent_laundry.py
│   │   └── agent_mess.py
│   ├── /tools
│   │   ├── complaint_tools.py
│   │   ├── laundry_tools.py
│   │   └── mess_tools.py
│   ├── /tasks
│   │   ├── complaint_tasks.py    ← route_to_laundry_agent + route_to_mess_agent
│   │   ├── approval_tasks.py     ← check_approval_timeouts (every 15 mins)
│   │   ├── laundry_tasks.py      ← process_noshow_penalties (hourly) + send_slot_reminders (30 mins)
│   │   └── mess_tasks.py         ← analyze_daily_mess_feedback (10pm) + check_participation_alert (8am)
│   ├── /middleware
│   │   ├── rate_limiter.py
│   │   └── prompt_sanitizer.py
│   └── /migrations
│
└── /frontend                     ← Not started — Sprint F
```

---

## SECTION 5 — SPRINT HISTORY & DEVIATIONS

This is the most important section. Every deviation from the original plan is documented here. Any AI working on this project MUST read this section and respect these changes — never revert to the original plan.

---

### SPRINT 1 — Foundation (COMPLETE ✅)
**Goal:** Project setup, auth system, all schemas, all models, database migrations.

**What was built:** Full backend structure, all Pydantic schemas, all SQLAlchemy models (10 tables), Alembic migrations, JWT auth system, role-based access control, React+TypeScript frontend scaffold, TypeScript types, AuthContext, Login page.

**Key deviations:**
- passlib removed — bcrypt used directly in auth_service.py with [:72] truncation. NEVER use passlib.
- DATABASE_URL uses port 5432 (direct), never 6543 (pgBouncer conflicts with asyncpg)
- Business logic moved out of routes into services (user_service.py created)
- .env.example lives in backend/ not project root

---

### SPRINT 2 — Agent 1 + Celery Pipeline (COMPLETE ✅)
**Goal:** Complaint filing, LLM classification, Celery pipeline, fallback classifier.

**What was built:** celery_app.py, prompt_sanitizer.py, fallback_classifier.py, complaint_service.py, notification_service.py, override_log_service.py, user_service.py, agent_complaint.py, complaint_tasks.py, complaint_tools.py (6 tools), routes/complaints.py.

**Key deviations:**
- Windows Celery requires --pool=solo (dev only, NOT production/Railway)
- run_async() wrapper in complaint_tasks.py for calling async tools from Celery
- psycopg2-binary added for sync engine (Celery needs sync DB)
- VALID_TRANSITIONS imported from complaint_service.py — never redefined elsewhere
- complaint.status assignment ONLY inside transition_complaint()

**Post-sprint fixes:**
- Hardcoded 0.85 threshold replaced with settings.COMPLAINT_CONFIDENCE_THRESHOLD
- GROQ model llama3-8b-8192 decommissioned → updated to llama-3.3-70b-versatile
- logger not defined in complaint_tasks.py → added import logging + getLogger
- Celery sys.path fix added to celery_app.py

---

### SPRINT 3 — Agent 1 Complete (COMPLETE ✅)
**Goal:** Approval queue, override logging, rate limiting, resolution flow, anonymous complaints, timeline.

**What was built:** approval_queue_service.py, routes/approval_queue.py, approval_tasks.py, notification routes, resolution flow in complaint_service.py, serialize_complaint() helper, ComplaintReadAnonymous schema.

**Key deviations:**
- escalate route is in routes/complaints.py not routes/approval_queue.py (URL prefix reason)
- MissingGreenlet after db.commit() → always await db.refresh(obj) before returning
- UUID fields need field_validator mode='before' for UUID→str conversion
- warden_override added to classifiedby enum (SQL + migration)
- complaint_escalated, complaint_reopened added to notificationtype enum
- WARDEN_ROLES = [assistant_warden, warden, chief_warden] — must include all three
- reopen endpoint body field is named 'reason' not 'reopen_reason'

---

### SPRINT 4 — Agent 2 (Laundry) + Agent 3 (Mess) (COMPLETE ✅)
**Goal:** Laundry slot booking with fairness algorithm, mess feedback collection and analysis, agent routing.

**What was built:** agent_laundry.py, agent_mess.py, laundry_tools.py, mess_tools.py, laundry_service.py, mess_service.py, routes/laundry.py, routes/mess.py, mess_tasks.py, complaint_tasks.py updated with routing tasks.

**⚠️ CRITICAL Sprint 4 deviations — MUST READ before querying these models:**
- Machine model is named `machine.py` / `Machine` (not LaundryMachine). Columns: `repaired_at` not `last_serviced_at`
- MessFeedback stores 5 SEPARATE columns: `food_quality`, `hygiene`, `menu_variety`, `food_quantity`, `timing` — NOT a single rating column
- MessFeedback date column is named `date` not `feedback_date` — use `Field(alias="date")` in schema
- MessFeedback meal field is named `meal` not `meal_type`
- LaundrySlot uses `booking_status` (LaundrySlotStatus) not `status` (to avoid collision with legacy column)
- LaundrySlot uses `slot_date` (date) and `slot_time` (string "09:00-10:00") not start_time/end_time

---

### SPRINT 5 — Push Notifications + Analytics + JWT Refresh + Laundry No-Show + Hostel Config (COMPLETE ✅)
**Goal:** Backend production-ready with push notifications, evaluation metrics, JWT refresh, no-show penalties, hostel config in DB.

**What was built:** hostel_config.py model+service+route, refresh_token.py model, push_subscription.py model, push_service.py, metrics_service.py (all 7 metrics), auth_service.py updated (refresh + rotation + theft detection), notification_service.py updated (push in notify_user), laundry_tasks.py (noshow + reminders), mess_tasks.py (daily analysis + participation check).

**Key deviations:**
- logout revokes ALL user tokens (more secure than spec)
- override_log uses warden_id not corrected_by
- no_show value added to laundryslostatus enum (SQL + migration)
- RefreshToken column is `revoked` not `is_revoked`
- 3 analytics endpoints (complaints, mess, laundry) were stubs — completed in Sprint 6

---

### SPRINT 6 — Backend Completions + Flow Fixes (COMPLETE ✅)
**Goal:** Close all backend gaps before React frontend is built.

**What was built:**
- User model: is_rejected, rejection_reason, has_seen_onboarding
- user_service.py: reject_user(), warden_reset_password(), create_staff_account()
- auth_service.py: login intercepts rejected accounts with 403 + reason
- login response: now includes full user object (access_token + refresh_token + user)
- routes/users.py: /reject, /reset-password, /staff CRUD, /me, /onboarding-seen
- metrics_service.py: all 3 analytics stubs replaced with real SQLAlchemy queries
- DashboardMetrics: pending_registrations + pending_approval_queue counts added

**Key deviations:**
- PATCH /api/users/me/onboarding-seen returns full UserRead not `{ has_seen_onboarding: true }`
- analytics queries initially used wrong field names (taste_score etc.) → fixed to actual columns
- complaint analytics initially crashed on NULL category/severity → added None checks
- password reset initially used is_revoked → fixed to revoked

---

## SECTION 6 — ENVIRONMENT VARIABLES

```env
# Database — ALWAYS port 5432, never 6543
DATABASE_URL=postgresql+asyncpg://postgres.PROJECT_REF:PASSWORD@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres

# Auth
JWT_SECRET=<long-random-string>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_HOURS=24
REFRESH_TOKEN_EXPIRE_DAYS=30

# LLM — llama3-8b-8192 was DECOMMISSIONED March 2026
GROQ_API_KEY=<from console.groq.com>
GROQ_MODEL_NAME=llama-3.3-70b-versatile

# Task Queue
CELERY_BROKER_URL=<from Upstash dashboard>
CELERY_RESULT_BACKEND=<same as broker>

# Push Notifications
VAPID_PRIVATE_KEY=<generate with pywebpush>
VAPID_PUBLIC_KEY=<generate with pywebpush>
VAPID_CLAIM_EMAIL=admin@hostelops.ai

# Complaint Agent
COMPLAINT_CONFIDENCE_THRESHOLD=0.85

# Mess Thresholds (also in hostel_config table — DB takes precedence)
MESS_ALERT_THRESHOLD=2.5
MESS_CRITICAL_THRESHOLD=2.0
MESS_MIN_PARTICIPATION=0.15
MESS_MIN_RESPONSES=5

# Laundry (also in hostel_config table — DB takes precedence)
LAUNDRY_SLOTS_START_HOUR=8
LAUNDRY_SLOTS_END_HOUR=22
LAUNDRY_SLOT_DURATION_HOURS=1
LAUNDRY_NOSHOW_PENALTY_HOURS=48
LAUNDRY_CANCELLATION_DEADLINE_MINUTES=15

# Approval Queue (also in hostel_config table)
APPROVAL_QUEUE_TIMEOUT_MINUTES=30
```

---

## SECTION 7 — KEY DECISIONS LOG

| Decision | What | Why | Sprint |
|----------|------|-----|--------|
| Supervisor pattern | Agent 1 is single orchestrator | Consistent triage | Planning |
| LangChain not CrewAI | Agents have separate domains | No parallel collaboration needed | Planning |
| Groq + Llama 3 | Free tier LLM | Zero cost constraint | Planning |
| passlib removed | bcrypt direct | passlib unmaintained | Sprint 1 |
| Port 5432 | Direct Supabase connection | pgBouncer conflicts asyncpg | Sprint 1 |
| run_async() wrapper | Bridge async tools in Celery | Celery is synchronous | Sprint 2 |
| VALID_TRANSITIONS single source | complaint_service.py only | Prevent drift | Sprint 2 |
| psycopg2 for Celery | Sync engine | asyncpg incompatible with sync | Sprint 2 |
| Windows --pool=solo | Dev only | Windows no fork pool | Sprint 2 |
| WARDEN_ROLES = 3 roles | assistant_warden + warden + chief_warden | assistant_warden is the primary operative | Sprint 3 |
| db.refresh() after commit | Always refresh before return | Prevent MissingGreenlet errors | Sprint 3 |
| UUID→str field_validator | mode='before' on all schemas | SQLAlchemy returns UUID objects | Sprint 3 |
| Machine model not LaundryMachine | Existing model reused | Sprint 1 already created it | Sprint 4 |
| MessFeedback 5 columns | food_quality, hygiene, etc. | More granular than single rating | Sprint 4 |
| booking_status not status | New column to avoid collision | Legacy status column existed | Sprint 4 |
| hostel_config in DB | Not hardcoded in .env | Wardens need to configure from UI | Sprint 5 |
| Refresh token rotation | Old token revoked on use | Theft detection | Sprint 5 |
| notify_user() unified | Push inside with try/except | Single notification function | Sprint 5 |
| 30-second polling | Not WebSockets | Sufficient for V1, lower complexity | Decision |
| Multi-tenant architecture | hostel_id on all tables | One deployment serves all hostels | Sprint 7 |
| Hostel code registration | Student enters code from warden | Clean UX, no subdomain complexity | Sprint 7 |
| Mess menu flexible | valid_from date, publish anytime | Hostels don't follow weekly schedules | Sprint 7b |
| Notice board | Warden → all students | Replace WhatsApp group announcements | Sprint 7b |
| Complaint templates | Quick pre-fill | Most complaints are repetitive | Sprint 7b |
| Feedback streak | Counter on User model | Incentivises daily participation | Sprint 7b |
| ERP upload deferred | Manual warden approval V1 | Complexity vs benefit | V2 |
| Laundry priority exception deferred | Fairness score sufficient V1 | Complexity vs benefit | V2 |
| RAG deferred | No external DB in V1 | Zero dependency constraint | V2 |

---

## SECTION 8 — VERIFICATION HISTORY

### Sprint 1+2 Human Checks — 9/9 PASS (March 5, 2026)
git log .env, 10 tables in DB, JWT role claim, Celery starts, injection detection, invalid transition rejected, cross-student access blocked, high severity routing, fallback classifier.

### Sprint 3 — 9/9 PASS (March 13, 2026)
Approval flow, override flow, rate limiting, resolution flow, anonymous complaints, timeline, my complaints, notifications, Celery beat.

### Sprint 4 — 11/11 PASS (March 16, 2026)
Machines seeded, available slots, book slot, one slot per day, my bookings, machine status, submit feedback, duplicate blocked, mess summary, laundry routing, mess routing.

### Sprint 5 — 9/12 (March 17, 2026)
PASS: hostel config, JWT refresh, token rotation, logout, VAPID key, push subscribe, dashboard metrics, override analytics, Celery beat.
PARTIAL (stubs — fixed in Sprint 6): complaints analytics, mess analytics, laundry analytics.

### Sprint 6 — 9/9 PASS (March 20, 2026)
Login has user object, GET /users/me, reject registration, rejected login blocked, create staff account, onboarding flag, dashboard pending counts, analytics real data, password reset.

Issues found and fixed in Sprint 6 manual checks:
1. complaints analytics crashed on NULL category → added None checks
2. mess analytics used wrong field names (taste_score) → fixed to food_quality etc.
3. password reset used is_revoked → fixed to revoked

---

## SECTION 9 — CURRENT STATE & NEXT STEPS

```
Current sprint: Sprint 7 — Multi-tenant Architecture
Sprint 1: ✅ Foundation + Auth
Sprint 2: ✅ Agent 1 + Celery Pipeline
Sprint 3: ✅ Agent 1 Complete (approval queue, resolution flow)
Sprint 4: ✅ Agent 2 (Laundry) + Agent 3 (Mess)
Sprint 5: ✅ Push Notifications + Analytics + JWT Refresh + Hostel Config
Sprint 6: ✅ Backend Completions + Flow Fixes — backend feature-complete
Sprint 7: 🔄 Multi-tenant (hostel_id + hostel codes) — STARTING NOW
Sprint 7b: ⏳ API Polish + Mess Menu + Notice Board + Templates + Streak
Sprint F: ⏳ React PWA Frontend (after Sprint 7b complete)
Sprint D: ⏳ Docker + Railway deployment (after Sprint F)
```

### When starting a new session with any AI:

```
Read PROJECT_STATE.md completely before doing anything.
Then read CONVENTIONS.md.
Then read the relevant sections of PRD.md for the current sprint.

Current sprint: Sprint 7 — Multi-tenant Architecture

Your task: [DESCRIBE TASK]
```

### After completing a sprint:
1. Mark the sprint COMPLETE ✅ in Section 5
2. Add deviations discovered
3. Add decisions to Section 7
4. Update environment variables in Section 6 if changed
5. Update Section 9 current state
6. Commit: `git commit -m "Update PROJECT_STATE.md — Sprint X complete"`

---

## SECTION 10 — GOLDEN RULES (NEVER VIOLATE)

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
20. **Event loop closed warning in Celery on Windows is non-fatal.** Retry succeeds. No workarounds.
21. **Never store raw refresh tokens.** Always store SHA256 hash. Raw token sent to client once only.
22. **notify_user() is the single notification function.** Push called inside with try/except always.
23. **Always run `alembic upgrade head` after pulling new code.**
24. **Analytics queries must handle NULL enum fields.** Check `if field is not None` before `.value`.
25. **Check Sprint 4 deviations before querying mess/laundry models.** MessFeedback columns: food_quality, hygiene, menu_variety, food_quantity, timing. Machine: repaired_at. RefreshToken: revoked (not is_revoked). LaundrySlot: booking_status (not status).
26. **Notification polling is 30 seconds in Sprint F.** Do not implement WebSockets in V1.
27. **Every FastAPI route must have an explicit `response_model=` decorator.**
28. **All list endpoints must support `limit` and `offset` pagination params** (Sprint 7b).
29. **All datetime fields in API responses must include timezone info** (`Z` or `+00:00`) (Sprint 7b).
30. **Complaint text minimum 10 characters.** Enforce in schema and backend (Sprint 7b).
31. **After Sprint 7: every query must filter by hostel_id.** Data isolation is mandatory. A user from hostel A must never see hostel B's data.

---

## SECTION 11 — V2 DEFERRALS (DO NOT IMPLEMENT IN V1)

These were explicitly decided as V2 scope. Do not implement them unless explicitly instructed:

- ERP document upload for college mode verification
- Laundry priority exception flow (medical/unavailability requests)
- Laundry no-show detection more frequent than hourly
- Mess feedback time-window enforcement (only show breakfast during morning etc.)
- Rate limit per-category instead of global daily limit
- WebSockets for real-time updates (30-second polling is V1 strategy)
- Multi-hostel management dashboard
- RAG-enhanced complaint triage (Qdrant)
- LangGraph migration for Agent 1
- Native mobile app (iOS/Android)
- WhatsApp/SMS integration
- Complaint upvoting
- Roommate info endpoint
- Lost and found board
- Visitor log
- Automated corrective action suggestions to Mess Manager