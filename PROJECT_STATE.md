# HostelOps AI — Project State Document & AI Onboarding Prompt
# Version: Sprint 1 Complete
# Last Updated: February 2026
# Purpose: This file is the single source of truth for the current state of the project.
#          Paste this into ANY AI assistant (Opus, Sonnet, Gemini, or any future model)
#          to instantly onboard it to the project. Update this file at the end of every sprint.

---

## INSTRUCTIONS FOR AI READING THIS

You are being onboarded as a developer/reviewer for HostelOps AI. Read this entire document before doing or saying anything. This document tells you:

1. What this project is
2. Every decision that has been made and WHY
3. The current state of the codebase
4. What has been built, what deviates from the original plan, and what is next
5. Rules you must follow without exception

After reading, your job depends on why you were called:
- **If called for verification:** audit the codebase against this document and report exactly what matches, what deviates, and what is missing.
- **If called for development:** pick up from the current sprint and follow CONVENTIONS.md exactly.
- **If called for debugging:** fix only what is broken, do not refactor anything that is working.
- **Never** change something that is working just because you would have done it differently.

---

## SECTION 1 — WHAT IS HOSTELOPS AI

HostelOps AI is an autonomous operations management system for hostels (college-affiliated and independent PGs). It uses a multi-agent AI architecture to automate three core hostel operations:

- **Agent 1 (Orchestrator):** Receives all student complaints, classifies them using an LLM, and routes them to the correct agent or staff member. Uses confidence-gated action — acts automatically when confident, escalates to human when uncertain.
- **Agent 2 (Laundry Agent):** Manages laundry slot booking with a fairness algorithm. Handles machine breakdowns and priority requests.
- **Agent 3 (Mess Agent):** Monitors mess feedback across 5 dimensions (food quality, quantity, hygiene, variety, timing). Detects chronic dissatisfaction and sudden spikes. Alerts warden and mess manager proactively.

**The system is designed to be built entirely by an AI coding assistant.** Every convention, schema, and pattern is chosen to maximise AI coding effectiveness.

**Full product specification is in PRD.md** — always reference it for feature details.
**All coding rules are in CONVENTIONS.md** — always follow it without exception.

---

## SECTION 2 — NON-NEGOTIABLE CONSTRAINTS

These constraints were decided at the start and cannot be changed under any circumstances:

| Constraint | Detail |
|-----------|--------|
| Zero cost | No paid APIs. No paid services beyond Railway hobby ($5/month optional). |
| Open-source LLM | Groq free tier + Llama 3. Never swap to a paid model. |
| No paid infrastructure | Neon/Supabase free tier for DB, Upstash free for Redis, Railway free for hosting. |
| AI-first development | Every file, folder, and pattern is optimised for AI coding assistant use. |
| All three agents in V1 | Never reduce scope to a single agent. All three ship together. |
| LangChain for V1 | LangGraph is documented as the V2 upgrade path but not implemented in V1. |
| Async-first | Every route, DB call, and LLM call is async. No synchronous blocking code. |
| Pydantic as source of truth | Every entity has a Pydantic schema. TypeScript types mirror them exactly. |

---

## SECTION 3 — TECHNOLOGY STACK (FINAL, LOCKED)

| Layer | Technology | Notes |
|-------|-----------|-------|
| Frontend | React 18 + TypeScript + Vite + PWA + Shadcn/UI | |
| Backend | Python + FastAPI + Pydantic v2 + SQLAlchemy + Alembic | |
| Agent Orchestration | LangChain | LangGraph is V2 upgrade path |
| LLM | Groq free tier + Llama 3 (llama3-8b-8192) | Open-source model |
| Task Queue | Celery + Upstash Redis (free tier) | |
| Database | PostgreSQL via Supabase OR Neon (free tier) | See DB notes in Section 5 |
| Auth | JWT via python-jose + bcrypt (direct, NOT passlib) | passlib removed — see Section 5 |
| Hosting | Railway (free tier) | |
| Push Notifications | Web Push API (pywebpush backend) | |
| Config | python-dotenv + pydantic-settings | |

---

## SECTION 4 — PROJECT FOLDER STRUCTURE

```
/HostelOPS AI
├── PRD.md                          ← Full product spec (always reference this)
├── CONVENTIONS.md                  ← Coding rules (always follow this)
├── PROJECT_STATE.md                ← This file (update after every sprint)
├── .gitignore                      ← .env is in here
│
├── /backend
│   ├── main.py                     ← FastAPI app entry point
│   ├── config.py                   ← ALL env vars loaded here via pydantic-settings
│   ├── database.py                 ← SQLAlchemy async engine + session
│   ├── /models                     ← SQLAlchemy ORM models
│   ├── /schemas                    ← Pydantic v2 schemas (source of truth)
│   │   └── enums.py                ← All enums (UserRole, ComplaintStatus, etc.)
│   ├── /routes                     ← FastAPI APIRouter files (thin, no logic)
│   ├── /services                   ← All business logic
│   ├── /agents                     ← LangChain agent definitions
│   ├── /tools                      ← Typed agent tool callables
│   ├── /tasks                      ← Celery task definitions
│   ├── /middleware                 ← Rate limiter, prompt sanitizer
│   ├── /migrations                 ← Alembic migration files
│   ├── .env                        ← NOT committed to git
│   └── .env.example                ← Committed — all variable names, no values
│
└── /frontend
    └── /src
        ├── /types                  ← TypeScript types (mirror Pydantic schemas)
        ├── /api                    ← All API call functions
        ├── /components             ← Shadcn/UI reusable components
        ├── /pages                  ← Page-level components
        ├── /hooks                  ← Custom React hooks
        ├── /context                ← AuthContext, NotificationContext
        └── /lib                    ← rolePermissions.ts, utils.ts
```

---

## SECTION 5 — SPRINT HISTORY & DEVIATIONS

This is the most important section. Every deviation from the original plan is documented here. Any AI working on this project MUST read this section and respect these changes — never revert to the original plan.

---

### SPRINT 1 — Foundation (COMPLETE ✅)
**Completed:** February 2026
**Goal:** Project setup, auth system, all schemas, all models, database migrations.

#### What was built:
- Full backend project structure following CONVENTIONS.md
- All Pydantic schemas in `/backend/schemas/` including `enums.py`
- All SQLAlchemy models in `/backend/models/` — 10 tables total
- Alembic migrations run successfully — all 10 tables created in database
- JWT authentication system — register, login, verify, deactivate
- Role-based access control via FastAPI dependencies
- Full frontend scaffold — React + TypeScript + Vite + PWA
- All page placeholders created (StudentDashboard, WardenDashboard, etc.)
- TypeScript types in `/frontend/src/types/` mirroring all Pydantic schemas
- Auth API functions and AuthContext

#### ✅ Definition of Done — verified:
- Backend starts with `uvicorn main:app --reload` without errors ✅
- All 10 tables created in Supabase ✅
- `POST /api/auth/register` creates user with `is_verified=False` ✅
- `POST /api/auth/login` returns 401 for unverified user ✅
- `POST /api/users/{id}/verify` sets `is_verified=True` ✅
- `POST /api/auth/login` returns JWT with correct role claim after verification ✅
- Frontend runs at `http://localhost:5173` without errors ✅

#### ⚠️ DEVIATIONS FROM ORIGINAL PLAN — respect these forever:

**Deviation 1 — passlib removed, bcrypt used directly**
- **Original plan:** Use `passlib[bcrypt]` for password hashing
- **What happened:** `passlib` is unmaintained and clashes with modern `bcrypt` package, causing `ValueError: password cannot be longer than 72 bytes`
- **Fix applied:** Removed passlib entirely. Using `bcrypt` library directly in `auth_service.py`
- **Rule going forward:** NEVER import or use passlib anywhere in this project. Always use the `hash_password()` and `verify_password()` functions from `auth_service.py`
- **Current implementation:**
```python
import bcrypt

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    pwd_bytes = password.encode('utf-8')[:72]  # Safe truncation
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode('utf-8')

def verify_password(plain: str, hashed: str) -> bool:
    pwd_bytes = plain.encode('utf-8')[:72]
    hash_bytes = hashed.encode('utf-8')
    return bcrypt.checkpw(pwd_bytes, hash_bytes)
```

**Deviation 2 — Database port changed to 5432 (direct connection)**
- **Original plan:** Use Supabase pooler on port 6543
- **What happened:** pgBouncer transaction pooling on port 6543 conflicts with asyncpg prepared statement caching, causing `DuplicatePreparedStatementError`
- **Fix applied:** Changed DATABASE_URL in `.env` to use port 5432 (direct connection, bypasses pgBouncer)
- **Rule going forward:** DATABASE_URL must always use port 5432 for Supabase. Never change this back to 6543 unless explicitly handling the pgBouncer conflict with `statement_cache_size: 0`
- **Format:** `postgresql+asyncpg://postgres.PROJECT_REF:PASSWORD@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres`

**Deviation 3 — verify_warden.py debug script**
- **What happened:** A debug script `verify_warden.py` was created to manually verify the first warden account in the database
- **Fix applied:** Script deleted from codebase
- **Rule going forward:** The bootstrap problem (how does the first admin get verified?) must be solved with a proper `create_admin.py` script in Sprint 2 — Task 0. This script runs once during deployment setup, never via an API endpoint.

---

> **Next sprint will be added here once Sprint 1 has been fully verified and committed.**

---

### SPRINT 2 — Agent 1 Core (COMPLETE ✅)
**Completed:** March 2026
**Goal:** Student can file a complaint, receive immediate acknowledgement, and the complaint is classified by the LLM asynchronously via Celery and either auto-assigned or routed to the Warden approval queue — with a working fallback classifier if the LLM fails.

#### What was built:
- `backend/create_admin.py` — idempotent one-time admin bootstrap script
- `backend/celery_app.py` — Celery application instance (Upstash Redis, SSL configured)
- `backend/middleware/prompt_sanitizer.py` — injection detection, HTML stripping
- `backend/services/fallback_classifier.py` — keyword rule classifier (mess/laundry/maintenance/interpersonal)
- `backend/services/complaint_service.py` — state machine (`transition_complaint()` is the only function allowed to change complaint.status)
- `backend/agents/agent_complaint.py` — LangChain + Groq + Llama3 classification agent
- `backend/tasks/complaint_tasks.py` — full Celery pipeline (acknowledge → LLM → fallback → route)
- `backend/tasks/notification_tasks.py` — Sprint 6 push notification stub
- `backend/tools/complaint_tools.py` — 6 typed async Agent 1 tools
- `backend/routes/complaints.py` — 4 endpoints (file, get, update status, reopen)
- Updated `database.py` with sync engine (`SyncSessionLocal`) for Celery task DB access
- Updated `main.py` to register complaints router at `/api/complaints`

#### ✅ Definition of Done — verified:
- Redis ping: True (Upstash via rediss://) ✅
- Celery worker starts without errors (`--pool=solo` on Windows): "hostelops@Anishekh ready." ✅
- `POST /api/complaints/` returns immediate response with `complaint_id` + `INTAKE` status ✅
- Celery task fires classification in background ✅
- Fallback classifier: mess ✅ laundry ✅ maintenance ✅ interpersonal/high ✅
- Prompt injection detection and `flagged_input` storage ✅
- `transition_complaint()` rejects invalid transitions with `ValueError` ✅
- Audit log entry created for every state change ✅
- Sprint 1 auth system still works — untouched ✅

#### ⚠️ DEVIATIONS — respect these forever:

**Deviation 4 — Upstash Redis requires rediss:// (SSL)**
- **Original plan:** Sprint prompt showed `redis://` URLs
- **What happened:** Upstash Redis enforces TLS — plain `redis://` is rejected with "connection closed by server"
- **Fix applied:** Changed both `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND` in `.env` to `rediss://`
- **celery_app.py** uses `broker_use_ssl = {"ssl_cert_reqs": ssl.CERT_NONE}` to accept Upstash's self-signed cert
- **Rule going forward:** ALWAYS use `rediss://` for Upstash Redis. Never change back to `redis://`

**Deviation 5 — Celery on Windows requires --pool=solo**
- **What happened:** Celery's default fork-based pool raises `PermissionError: [WinError 5]` on Windows
- **Fix applied:** Run Celery with `--pool=solo` flag on Windows
- **Rule going forward:** For local development on Windows: `celery -A celery_app worker --pool=solo --loglevel=info`
- In production (Railway Linux): standard fork pool works fine, remove `--pool=solo`

**Deviation 6 — notification_service.py already existed**
- Sprint 2 Task 9 specified creating `notification_service.py`
- It was already built in Sprint 1 with `notify_user()` and `notify_all_by_role()` functions
- No changes were needed — it was reused as-is

---

## SECTION 6 — ENVIRONMENT VARIABLES

All variables live in `/backend/.env` (not committed). `/backend/.env.example` is committed with all names but no values.

```env
# Database — ALWAYS port 5432, never 6543 (see Deviation 2 above)
DATABASE_URL=postgresql+asyncpg://postgres.PROJECT_REF:PASSWORD@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres

# Auth
JWT_SECRET=<long random string>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_HOURS=24
REFRESH_TOKEN_EXPIRE_DAYS=30

# LLM — free tier, open-source model
GROQ_API_KEY=<from console.groq.com>
GROQ_MODEL_NAME=llama3-8b-8192

# Task Queue — NOT YET CONFIGURED (Sprint 2)
CELERY_BROKER_URL=
CELERY_RESULT_BACKEND=

# Push Notifications — NOT YET CONFIGURED (Sprint 6)
VAPID_PUBLIC_KEY=
VAPID_PRIVATE_KEY=
VAPID_CLAIM_EMAIL=

# Agent Thresholds
COMPLAINT_CONFIDENCE_THRESHOLD=0.85
MESS_DISSATISFACTION_THRESHOLD=2.5
MESS_SPIKE_DELTA=1.5
LAUNDRY_NOSHOW_PENALTY_HOURS=48
LAUNDRY_UNAVAILABILITY_DAYS=4
APPROVAL_QUEUE_TIMEOUT_MINUTES=30

# CORS
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
```

---

## SECTION 7 — KEY DECISIONS LOG

Every significant architectural or technical decision made during this project is logged here. Any AI must understand these before suggesting changes.

| Decision | What was decided | Why | When |
|----------|-----------------|-----|------|
| Supervisor Pattern | Agent 1 is the single orchestrator. All complaints enter through Agent 1 only. | Consistent triage, logging, and routing. Nothing bypasses the orchestrator. | Pre-Sprint 1 |
| LangChain over CrewAI | Using LangChain, not CrewAI | Agents don't collaborate in parallel — they have separate domains. CrewAI solves a collaboration problem we don't have. LangChain has more training data for AI coding tools. | Pre-Sprint 1 |
| LangChain over LangGraph (V1) | Using LangChain for V1, LangGraph documented as V2 | LangGraph has steeper learning curve. LangChain is sufficient for V1 volume. LangGraph migration is data-model-compatible. | Pre-Sprint 1 |
| Groq + Llama 3 over self-hosted LLM | Using Groq free tier | Self-hosting requires hardware and DevOps knowledge we don't have. Groq is free, fast, and uses an open-source model. | Pre-Sprint 1 |
| Three agents in V1 | All three agents ship in V1 | The three-agent system is the core value proposition. A standalone complaint classifier is not compelling. Laundry and mess agents are not complex enough to justify cutting. | Pre-Sprint 1 |
| PWA over native app | Using React PWA | No app store, no cost, works on all devices, supports push notifications. | Pre-Sprint 1 |
| Neon/Supabase PostgreSQL | Free hosted PostgreSQL | Zero DevOps setup. Free tier. Standard PostgreSQL — fully compatible with all libraries. | Pre-Sprint 1 |
| passlib removed | Using bcrypt directly | passlib is unmaintained and incompatible with modern bcrypt package. | Sprint 1 |
| Port 5432 for Supabase | Direct connection not pooler | pgBouncer pooler on 6543 conflicts with asyncpg prepared statement caching. | Sprint 1 |
| create_admin.py for bootstrap | One-time script for first admin | Debug scripts must not exist in production codebase. The first admin needs a clean, repeatable setup process. | Sprint 1 review |

---

## SECTION 8 — VERIFICATION CHECKLIST (FOR OPUS OR ANY REVIEWER AI)

If you are reading this to verify the current state of the project, check every item below against the actual codebase. Report exactly: ✅ PASS, ❌ FAIL, or ⚠️ DEVIATION (with explanation).

### Sprint 1 Verification

**Re-verification:** PASS — 4/4 failures fixed, 2/2 deviations resolved, 0 regressions

**Structure:**
- [ ] `/backend/config.py` exists and uses `BASE_DIR = Path(__file__).resolve().parent` for absolute .env path
- [ ] `/backend/database.py` exists with async SQLAlchemy engine
- [ ] `/backend/schemas/enums.py` exists with all enums defined
- [ ] All 9 schema files exist in `/backend/schemas/`
- [ ] All 10 model files exist in `/backend/models/`
- [ ] `/backend/services/auth_service.py` uses bcrypt directly — NOT passlib
- [ ] `/backend/routes/auth.py` has register and login endpoints
- [ ] `/backend/routes/users.py` has verify and deactivate endpoints
- [ ] `/backend/.env.example` is committed with all variable names
- [ ] `/backend/.env` is NOT committed (check .gitignore)
- [ ] `verify_warden.py` does NOT exist anywhere in the codebase
- [ ] All 10 tables exist in the Supabase database

**Code quality:**
- [ ] No hardcoded values anywhere — all config comes from `settings` imported from `config.py`
- [ ] No direct `os.environ` access outside `config.py`
- [ ] No passlib imports anywhere
- [ ] All route handlers use `async def`
- [ ] All DB calls use `AsyncSession`

**Frontend:**
- [ ] `/frontend/src/types/` has TypeScript types for user, complaint, laundry, mess
- [ ] `/frontend/src/api/authApi.ts` exists
- [ ] `/frontend/src/context/AuthContext.tsx` exists
- [ ] `/frontend/src/pages/Login.tsx` exists
- [ ] All 6 page placeholders exist

**Functional:**
- [ ] Backend starts without errors
- [ ] Swagger UI loads at `http://localhost:8000/docs`
- [ ] Register endpoint creates user with `is_verified=False`
- [ ] Login returns 401 for unverified user
- [ ] Verify endpoint activates account
- [ ] Login returns JWT with role claim after verification
- [ ] Protected route returns 403 with wrong role token
- [ ] Frontend starts without errors

---

## SECTION 9 — HOW TO USE THIS DOCUMENT

### Starting a new session with any AI:

```
Read PROJECT_STATE.md completely before doing anything.
Then read CONVENTIONS.md.
Then read the relevant sections of PRD.md for the current sprint.

Current sprint: [UPDATE THIS EACH SPRINT]
Your task: [DESCRIBE TASK]
```

### After completing a sprint:

Update this document:
1. Mark the sprint as COMPLETE ✅ in Section 5
2. Fill in the Definition of Done results
3. Add any new deviations to the Deviations subsection
4. Add any new decisions to Section 7
5. Update the environment variables in Section 6 if anything changed
6. **Add the NEXT sprint section only after the current one is fully complete and committed** — never document future sprints in advance
7. Commit: `git commit -m "Update PROJECT_STATE.md — Sprint X complete"`

### If switching AI models mid-sprint:

Paste this entire document into the new AI and say:
*"Read PROJECT_STATE.md. We are mid-Sprint [X]. The following tasks are complete: [list]. Continue from: [next task]. Do not change anything that is already working."*

---

## SECTION 10 — GOLDEN RULES (NEVER VIOLATE)

1. **Never change working code** just because you would do it differently. If it works and passes the Definition of Done, leave it alone.
2. **Never use passlib** anywhere in this project. Use `hash_password()` and `verify_password()` from `auth_service.py`.
3. **Never change DATABASE_URL port to 6543.** Always 5432.
4. **Never put logic in routes.** Routes call services. Services contain logic.
5. **Never call the LLM directly from a route or service.** All LLM calls go through `/agents/`.
6. **Never run slow operations synchronously.** Everything slow goes through Celery tasks.
7. **Never hardcode any value** that should come from `.env`.
8. **Never commit `.env`** under any circumstances.
9. **Always update PROJECT_STATE.md** at the end of every sprint before starting the next.
10. **Always reference PRD.md and CONVENTIONS.md** before writing any new code.