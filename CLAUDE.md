# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

HostelOps AI is an autonomous hostel operations management system with an AI-powered complaint classification pipeline, laundry slot booking, mess feedback analysis, and a multi-role approval workflow. It consists of a FastAPI backend and a React/TypeScript frontend.

## Commands

### Backend (run from `backend/`)

```bash
# Start dev server
uvicorn main:app --reload

# Database migrations
alembic upgrade head
alembic revision --autogenerate -m "description"
alembic downgrade -1

# Bootstrap first admin account + seed machines + hostel config (run once after DB setup)
python create_admin.py

# Celery worker (Windows — must use --pool=solo)
.venv\Scripts\celery -A celery_app worker --pool=solo --loglevel=info

# Celery beat scheduler (separate terminal)
.venv\Scripts\celery -A celery_app beat --loglevel=info

# Install dependencies
pip install -r requirements.txt
```

### Frontend (run from `frontend/`)

```bash
npm run dev       # Vite dev server (http://localhost:5173)
npm run build     # TypeScript check + Vite production build
npm run lint      # ESLint
npm run preview   # Preview production build
```

## Architecture

### Backend stack

- **FastAPI** with async/await throughout all routes and services
- **SQLAlchemy 2.0 async** (`asyncpg` driver) for all FastAPI route handlers
- **Celery + Redis (Upstash)** for background tasks and periodic scheduling
- **psycopg2** sync driver used exclusively inside Celery tasks (asyncpg is async-only)
- **LangChain + Groq (Llama 3)** for AI agents
- **Alembic** for schema migrations

### Layer conventions

```
routes/       -> thin HTTP layer, no business logic, delegates to services/
services/     -> all business logic; called by routes and Celery tasks
agents/       -> LangChain LLM wrappers; called only from services or tasks
tools/        -> typed async tool callables used by agents; call services, never DB directly
tasks/        -> Celery task definitions; use SyncSessionLocal, not get_db
models/       -> SQLAlchemy ORM models
schemas/      -> Pydantic v2 request/response models
middleware/   -> rate limiter (Redis sliding window), prompt sanitizer
```

Every file in `tools/` must follow this pattern: typed `Input` Pydantic model + typed `Result` Pydantic model + `async def tool_fn(input: Input, db: AsyncSession) -> Result`. Tools call services — never access the DB directly. Tools never call other tools.

### Critical architectural rules

1. **`config.py` is the only file that reads from env/`.env`**. All other files import `settings` from there.
2. **Two DB engines**: `AsyncSessionLocal` + `get_db` for FastAPI routes; `SyncSessionLocal` for Celery tasks. Never mix them.
3. **Complaint state machine**: `transition_complaint()` in `complaint_service.py` is the ONLY function allowed to change `complaint.status`. All transitions are validated against `VALID_TRANSITIONS` and written to `audit_log`.
4. **LLM calls**: All Groq/LangChain calls go through `agents/`. Never call Groq directly from services or routes.
5. **Enums**: All Python enums are defined in `schemas/enums.py`. Never define enums inline in model or schema files. DB-level enums in SQLAlchemy models must mirror these exactly.
6. **Groq model**: Always use `settings.GROQ_MODEL_NAME`. The default `llama3-8b-8192` was decommissioned by Groq in March 2026 — the correct model is `llama-3.3-70b-versatile`. Never hardcode a model name.
7. **`WARDEN_ROLES`** always = `[assistant_warden, warden, chief_warden]`. Never use just `warden` for warden-level access checks.
8. **Operational thresholds** (mess alert levels, laundry slot hours, approval timeout, etc.) come from `hostel_config_service.get_config()` — not from `settings.*`. The service has a 5-minute in-memory cache and falls back to `.env` if the DB row is missing.
9. **`await db.refresh(obj)` after every `await db.commit()`** when the object is returned afterward — prevents `MissingGreenlet` errors.
10. **UUID → str `field_validator`**: every Pydantic schema that validates a SQLAlchemy ORM object must convert UUID fields to str with `mode='before'`.
11. **Every new PostgreSQL enum value needs an Alembic migration** before being used in code.
12. **Analytics queries must handle NULL enum fields** — always check `if field is not None` before calling `.value`.
13. **Login must include hostel_code.** Room numbers are not globally unique — hostel_id scoping on login is mandatory. Never allow login by room_number alone.
14. **User management endpoints return 404 (not 403) for cross-hostel users.** Returning 403 would confirm the user exists in another hostel.

### Authentication flow

- Login returns a JWT access token (stateless, 24h) + opaque DB-backed refresh token (30d).
- Refresh tokens are stored as SHA256 hashes; raw token returned once and never stored.
- Token rotation: each `/api/auth/refresh` call revokes the old token and issues a new pair.
- Theft detection: if a revoked token is reused, all sessions for that user are invalidated.
- `get_current_user` and `require_role(*roles)` are FastAPI dependencies from `auth_service.py`.

### Role hierarchy

`student` | `laundry_man` | `mess_secretary` | `mess_manager` | `assistant_warden` | `warden` | `chief_warden`

Assistant wardens approve new student registrations (or reject with reason). Students start as `is_verified=False`.

### Celery beat schedule

| Task | Interval |
|---|---|
| `check_approval_timeouts` | Every 15 min |
| `analyze_daily_mess_feedback` | Daily (~22:00) |
| `check_participation_alert` | Daily |
| `process_noshow_penalties` | Every 60 min |
| `send_slot_reminders` | Every 30 min |

### Hostel modes

`college` mode requires `roll_number` + `erp_document_url` on registration. `autonomous` mode does not.

### Current sprint & known deviations

**Current sprint: Sprint F — React PWA Frontend.** Backend is feature-complete and fully audited. Sprints 7 and 7b are done. A full production audit (2 rounds, 31 fixes) confirmed hostel_id isolation across all queries. Every DB query must filter by `hostel_id`. A user from hostel A must never see hostel B's data.

**Critical field name deviations from what you might expect** (these have caused bugs before):

| Model | Actual column | NOT |
|---|---|---|
| `RefreshToken` | `revoked` | `is_revoked` |
| `Machine` | `repaired_at` | `last_serviced_at` |
| `LaundrySlot` | `booking_status` | `status` |
| `LaundrySlot` | `slot_date` + `slot_time` | `start_time` / `end_time` |
| `MessFeedback` | `food_quality`, `hygiene`, `menu_variety`, `food_quantity`, `timing` (5 separate int columns) | a single `rating` column |
| `MessFeedback` | `meal` | `meal_type` |
| `MessFeedback` | `date` (DB column name) | `feedback_date` — use `Field(alias="date")` in schema |
| `OverrideLog` | `warden_id` | `corrected_by` |

### Feature implementation order

Always follow this sequence when adding any feature — never skip or reorder:

1. Pydantic schema (`schemas/`)
2. SQLAlchemy model (`models/`)
3. Alembic migration (`alembic revision --autogenerate`) + `alembic upgrade head`
4. Service function (`services/`)
5. FastAPI route (`routes/`)
6. TypeScript type (`frontend/src/types/`)
7. API function (`frontend/src/api/`)
8. Component or page (`frontend/src/`)

### Frontend stack

- **React 19** + **TypeScript** + **Vite 7**
- **Tailwind CSS v4** (via `@tailwindcss/vite` plugin)
- **TanStack Query v5** for server state
- **React Router v7** for routing
- **Axios** for HTTP; auth token stored and managed via `AuthContext`
- PWA-enabled via `vite-plugin-pwa`
- Design system (Sprint F): Clash Display + General Sans fonts, Indigo primary, Saffron accent, Jade success, Vermillion danger, Shadcn/UI components
- Notification polling: 30-second interval via `useNotifications` hook — WebSockets are explicitly deferred to V2

### Frontend structure

```
src/
  api/          -> Axios API call functions (one file per domain)
  context/      -> AuthContext (token storage, user state)
  hooks/        -> useAuth and other custom hooks
  lib/          -> rolePermissions, utility functions
  pages/        -> one file per route/page
  types/        -> TypeScript interfaces mirroring backend schemas
```

## Environment Setup

Copy `backend/.env.example` to `backend/.env` and fill in:

- `DATABASE_URL` — `postgresql+asyncpg://...`
- `JWT_SECRET` — any strong random string
- `GROQ_API_KEY` — from Groq console
- `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND` — Redis/Upstash URLs (use `rediss://` for TLS)
- `VAPID_PUBLIC_KEY` / `VAPID_PRIVATE_KEY` / `VAPID_CLAIM_EMAIL` — generate with `npx web-push generate-vapid-keys`

The backend reads `.env` using an absolute path, so it works regardless of working directory.
