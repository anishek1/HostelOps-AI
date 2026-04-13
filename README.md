# HostelOPS AI

> **Autonomous Operations Management for Hostels & PGs**
> AI-driven complaint triage, fair laundry scheduling, and mess quality monitoring — built on a fully open-source, zero-cost stack.

[![Backend](https://img.shields.io/badge/Backend-FastAPI%20%2B%20Python%203.11-009688?style=flat-square)](https://fastapi.tiangolo.com/)
[![Frontend](https://img.shields.io/badge/Frontend-React%2019%20%2B%20TypeScript-61DAFB?style=flat-square)](https://react.dev/)
[![LLM](https://img.shields.io/badge/LLM-Groq%20%2B%20Llama%203.3-F04F23?style=flat-square)](https://groq.com/)
[![DB](https://img.shields.io/badge/Database-PostgreSQL%20%2F%20Supabase-336791?style=flat-square)](https://supabase.com/)
[![Queue](https://img.shields.io/badge/Queue-Celery%20%2B%20Redis-DC382D?style=flat-square)](https://docs.celeryq.dev/)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

---

## Table of Contents

1. [What is HostelOPS AI?](#1-what-is-hostelops-ai)
2. [Core Features](#2-core-features)
3. [Architecture Overview](#3-architecture-overview)
4. [Technology Stack](#4-technology-stack)
5. [Project Structure](#5-project-structure)
6. [API Reference](#6-api-reference)
7. [AI Pipeline](#7-ai-pipeline)
8. [User Roles & Access Control](#8-user-roles--access-control)
9. [Multi-Tenant Architecture](#9-multi-tenant-architecture)
10. [Frontend — PWA](#10-frontend--pwa)
11. [Security](#11-security)
12. [Getting Started — Local Development](#12-getting-started--local-development)
13. [Environment Variables](#13-environment-variables)
14. [Deployment](#14-deployment)
15. [Key Engineering Decisions](#15-key-engineering-decisions)
16. [Failure Modes & Resilience](#16-failure-modes--resilience)
17. [V2 Roadmap](#17-v2-roadmap)

---

## 1. What is HostelOPS AI?

HostelOPS AI is an **autonomous operations management system** for college hostels and independent PGs. It replaces manual, reactive day-to-day management with a structured, AI-driven pipeline that is always-on, fair, and transparent.

### Problem

Hostel wardens spend a disproportionate amount of time on repetitive, low-value administrative tasks — manually triaging complaints, mediating laundry disputes, and reacting to mess dissatisfaction only after it escalates. Students lack visibility into whether their concerns are being heard.

### Solution

HostelOPS AI automates the routine, escalates the important, and gives every stakeholder a clear interface.

| Design Principle | Implementation |
|---|---|
| **Automate the routine, escalate the sensitive** | AI never makes autonomous decisions on interpersonal or safety-critical issues |
| **Confidence-gated action** | Acts automatically when confidence ≥ threshold; ambiguous decisions surface to the warden for one-tap approval |
| **Full transparency** | Every student can track their complaint in real time |
| **Fairness by design** | Laundry allocation governed by an explicit scoring algorithm, not first-come-first-serve |
| **Zero-cost infrastructure** | Open-source models and free-tier services — no paid APIs |
| **Multi-tenant** | One deployment serves multiple hostels, each isolated by hostel code |

---

## 2. Core Features

### For Students
- **Complaint Filing** — Free-text or quick-fill from 9 category templates. Anonymous option available.
- **Live Complaint Tracker** — Real-time status: `INTAKE → CLASSIFIED → ASSIGNED → IN_PROGRESS → RESOLVED`
- **Complaint Reopening** — Reopen with reason if resolution is unsatisfactory; warden is notified and priority is elevated.
- **Laundry Slot Booking** — Date picker + per-machine slot grid with fairness scoring and no-show penalties.
- **Mess Feedback** — Rate 5 dimensions per meal (food quality, hygiene, variety, quantity, timing).
- **Mess Menu** — View the current published menu at any time.
- **Notification Inbox** — In-app notifications for every complaint status change and hostel announcement.
- **Notice Board** — Warden announcements displayed on the home screen.
- **Onboarding Walkthrough** — Shown exactly once on first login.

### For Wardens
- **Registration Approval** — Review, approve, or reject student registrations with an optional reason.
- **AI Approval Queue** — One-tap approve or override on AI-uncertain complaint classifications.
- **Dashboard Analytics** — 7 evaluation metrics computed live; drift alerts surface when AI accuracy drops.
- **Student Management** — Search, filter, deactivate, and manage all students.
- **Hostel Settings** — Configure all operational thresholds from the UI without touching `.env`.
- **Staff Account Creation** — Create laundry man and mess staff accounts directly.
- **Notice Board** — Post and delete announcements to all students.

### For Staff
- **Laundry Dashboard** — View slot assignments, mark machines as under repair or repaired.
- **Mess Dashboard** — View feedback summaries, dissatisfaction alerts, and publish the mess menu.

---

## 3. Architecture Overview

### The Supervisor Pattern

HostelOPS AI uses the **Supervisor Pattern** — a multi-agent architecture where the Orchestrator is the single entry point for all student inputs.

```
Student PWA
     │
     ▼
┌─────────────────────────────────────────┐
│           Orchestrator Agent            │
│  • Receives all complaints              │
│  • LLM classification (Groq + Llama 3) │
│  • Confidence-gated routing             │
│  • Fallback rule-based classifier       │
└──────┬──────────────────────────────────┘
       │
       ├──── High confidence → Auto-assign to staff
       │
       └──── Low confidence / high severity → Warden approval queue
```

### Complaint State Machine

```
INTAKE ──────────────────────────────────────────► ESCALATED
  │                                                    ▲
  ▼                                                    │
CLASSIFIED ──────────────────────────────────────► AWAITING_APPROVAL
  │                                                    │
  ▼                                                    │
ASSIGNED ◄─────────────────────────────────────────── │
  │
  ▼
IN_PROGRESS
  │
  ▼
RESOLVED ◄── Student confirms ──► REOPENED
```

`transition_complaint()` in `complaint_service.py` is the single gatekeeper for all state transitions. Every transition is validated against `VALID_TRANSITIONS` and written to an immutable audit log.

### Async Task Architecture

```
FastAPI Route (async)
       │
       └──► Celery Task (async via Redis broker)
                  │
                  ├──► Groq LLM (classification)
                  ├──► PostgreSQL (state write)
                  └──► Notification dispatch
```

All LLM calls are async and happen in background Celery tasks — routes never block on LLM responses.

---

## 4. Technology Stack

| Layer | Technology |
|---|---|
| **Frontend** | React 19 + TypeScript + Vite + PWA |
| **Backend** | Python 3.11 + FastAPI + Pydantic v2 |
| **ORM / Migrations** | SQLAlchemy 2.0 async + Alembic |
| **LLM** | Groq free tier — `llama-3.3-70b-versatile` |
| **Task Queue** | Celery 5.4 + Upstash Redis |
| **Database** | PostgreSQL via Supabase |
| **Auth** | JWT (python-jose) + bcrypt |
| **Embeddings** | HuggingFace Inference API — `all-MiniLM-L6-v2` |
| **Vector Search** | pgvector — semantic deduplication on complaints |
| **Deployment** | Docker + Railway (API, worker, beat) + Vercel (frontend) |

### Backend Dependencies

```
fastapi==0.115.6          uvicorn[standard]==0.34.0
sqlalchemy[asyncio]==2.0.37  asyncpg==0.30.0
alembic==1.14.1           pydantic[email]==2.10.6
pydantic-settings==2.8.1  python-jose[cryptography]==3.3.0
bcrypt==4.1.2             python-dotenv==1.0.1
celery==5.4.0             redis==5.2.1
psycopg2-binary==2.9.10   groq==0.13.0
pgvector==0.3.6           httpx==0.27.0
cachetools==5.5.0
```

---

## 5. Project Structure

```
HostelOPS AI/
├── Dockerfile                    # Docker image for Railway deployment
├── .dockerignore
├── requirements.txt              # Points to backend/requirements.txt
│
├── backend/
│   ├── main.py                   # FastAPI app entry point
│   ├── config.py                 # Single source of truth for all env vars
│   ├── database.py               # AsyncSessionLocal + SyncSessionLocal
│   ├── celery_app.py             # Celery instance + beat schedule
│   ├── create_admin.py           # Seeds first warden + hostel config
│   ├── railway.toml              # Railway health check + restart policy
│   ├── Procfile                  # Process type definitions
│   ├── runtime.txt               # Python 3.11
│   │
│   ├── models/                   # SQLAlchemy ORM models
│   │   ├── user.py
│   │   ├── complaint.py
│   │   ├── hostel.py
│   │   ├── hostel_config.py
│   │   ├── laundry_slot.py
│   │   ├── machine.py
│   │   ├── mess_feedback.py
│   │   ├── notification.py
│   │   ├── audit_log.py
│   │   ├── approval_queue.py
│   │   ├── override_log.py
│   │   ├── notice.py
│   │   └── refresh_token.py
│   │
│   ├── schemas/                  # Pydantic v2 request/response models
│   │   ├── enums.py              # All enums — single source of truth
│   │   ├── user.py
│   │   ├── complaint.py
│   │   ├── hostel.py
│   │   ├── hostel_config.py
│   │   └── ...
│   │
│   ├── routes/                   # FastAPI routers (thin HTTP layer)
│   │   ├── auth.py               # /api/auth
│   │   ├── users.py              # /api/users
│   │   ├── complaints.py         # /api/complaints
│   │   ├── hostels.py            # /api/hostels
│   │   ├── laundry.py            # /api/laundry
│   │   ├── mess.py               # /api/mess
│   │   ├── notices.py            # /api/notices/
│   │   ├── notifications.py      # /api/notifications
│   │   ├── approval_queue.py     # /api/approval-queue
│   │   ├── hostel_config.py      # /api/config
│   │   └── analytics.py         # /api/analytics
│   │
│   ├── services/                 # Business logic layer
│   │   ├── auth_service.py
│   │   ├── complaint_service.py  # State machine lives here
│   │   ├── hostel_service.py
│   │   ├── mess_service.py
│   │   ├── notification_service.py
│   │   ├── embedding_service.py  # HuggingFace semantic dedup
│   │   ├── fallback_classifier.py
│   │   └── ...
│   │
│   ├── tasks/                    # Celery task definitions
│   │   ├── complaint_tasks.py    # LLM classification pipeline
│   │   ├── mess_tasks.py         # Daily feedback analysis
│   │   ├── laundry_tasks.py      # No-show penalties + reminders
│   │   ├── approval_tasks.py     # Timeout escalation
│   │   └── notification_tasks.py
│   │
│   ├── agents/                   # Groq LLM wrappers
│   │   └── complaint_agent.py    # ReAct agent with 7 tools
│   │
│   ├── tools/                    # Typed async tool callables
│   │   └── complaint_tools.py
│   │
│   ├── middleware/
│   │   └── rate_limiter.py       # Redis sliding-window rate limiter
│   │
│   └── migrations/               # Alembic migration files
│       └── versions/             # 17 migration files
│
└── frontend/
    ├── vercel.json               # SPA rewrites for Vercel
    ├── vite.config.ts
    ├── package.json
    └── src/
        ├── api/                  # Axios API call functions
        ├── context/              # AuthContext
        ├── hooks/                # useAuth, useNotifications
        ├── lib/                  # theme, rolePermissions, utilities
        ├── pages/
        │   ├── auth/             # Landing, Login, Register, HostelSetup
        │   ├── student/          # Home, Complaints, Laundry, Mess, Profile
        │   ├── warden/           # Dashboard, ApprovalQueue, Settings
        │   └── staff/            # LaundryManView, MessStaffView
        ├── components/           # AppShell, BottomNav, SkeletonCard
        └── types/                # TypeScript interfaces
```

---

## 6. API Reference

All endpoints are prefixed with `/api`. Full interactive docs available at `/docs` (Swagger UI) and `/redoc`.

### Auth — `/api/auth`

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/login` | — | Returns JWT access token + refresh token |
| `POST` | `/refresh` | — | Rotates token pair; theft detection on reuse |
| `POST` | `/logout` | Bearer | Revokes refresh token |
| `GET` | `/me` | Bearer | Current user profile |

### Hostels — `/api/hostels`

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/setup` | — | One-time hostel creation + first warden account |
| `GET` | `/{code}/info` | — | Public hostel info for student registration |

### Users — `/api/users`

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/register` | — | Student self-registration (pending approval) |
| `GET` | `/` | Warden | List all students in hostel |
| `GET` | `/{id}` | Warden | Single student profile |
| `PATCH` | `/{id}` | Warden | Update student details |
| `DELETE` | `/{id}/deactivate` | Warden | Deactivate account |

### Complaints — `/api/complaints`

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/` | Student | File a new complaint |
| `GET` | `/my` | Student | My complaints |
| `GET` | `/` | Warden | All hostel complaints |
| `GET` | `/{id}` | Any | Single complaint + full audit timeline |
| `POST` | `/{id}/confirm-resolved` | Student | Confirm resolution |
| `POST` | `/{id}/reopen` | Student | Reopen with reason |
| `PATCH` | `/{id}/status` | Warden | Force status transition |
| `POST` | `/{id}/override` | Warden | Override AI classification |
| `GET` | `/templates` | Student | 9 quick-fill complaint templates |

### Laundry — `/api/laundry`

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/slots/{date}` | Student | Available slots for a date |
| `POST` | `/slots/{id}/book` | Student | Book a slot |
| `DELETE` | `/slots/{id}/cancel` | Student | Cancel booking |
| `GET` | `/my-bookings` | Student | Upcoming bookings |
| `GET` | `/machines` | Any | Machine list + status |
| `PATCH` | `/machines/{id}` | Laundry man | Update machine status |

### Mess — `/api/mess`

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/feedback` | Student | Submit meal feedback (5 dimensions) |
| `GET` | `/my-feedback` | Student | My feedback history |
| `GET` | `/summary` | Any | Aggregated ratings for last 7 days |
| `GET` | `/menu` | Any | Current mess menu |
| `POST` | `/menu` | Mess staff | Publish new menu item |

### Notices — `/api/notices/`

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/` | Any | All active notices |
| `POST` | `/` | Warden | Post a new notice |
| `DELETE` | `/{id}` | Warden | Delete a notice |

### Other

| Prefix | Description |
|---|---|
| `/api/approval-queue` | Warden approval/rejection of AI decisions |
| `/api/notifications` | Notification inbox, mark-read, mark-all-read |
| `/api/config` | Get/update hostel operational thresholds |
| `/api/analytics` | 7 evaluation metrics for the AI pipeline |
| `/health` | Health check — `{"status": "ok"}` |

---

## 7. AI Pipeline

### Classification Flow

Every complaint goes through a 3-layer classification pipeline:

```
1. Groq LLM (primary)
   └── llama-3.3-70b-versatile via Groq free tier
   └── Extracts: category, severity, confidence, location, affected_count

2. Fallback Rule-Based Classifier
   └── Triggered if LLM fails or times out
   └── Keyword matching on 9 categories

3. Semantic Deduplication (optional)
   └── HuggingFace all-MiniLM-L6-v2 embeddings
   └── pgvector cosine similarity > 0.82 → probable duplicate flagged
```

### Categories

`plumbing` | `electrical` | `cleaning` | `pest_control` | `furniture` | `internet` | `security` | `mess` | `other`

### Confidence Gating

```python
if confidence >= COMPLAINT_CONFIDENCE_THRESHOLD (default: 0.85):
    auto_assign()           # → ASSIGNED
else:
    surface_to_warden()     # → AWAITING_APPROVAL
```

Warden approvals are logged as `OverrideLog` entries and feed back into analytics drift detection.

### Celery Beat Schedule

| Task | Interval | Purpose |
|---|---|---|
| `check_approval_timeouts` | Every 15 min | Auto-escalate stale approvals |
| `analyze_daily_mess_feedback` | Daily (~22:00) | Detect chronic dissatisfaction |
| `check_participation_alert` | Daily | Alert if mess feedback rate drops |
| `process_noshow_penalties` | Every 60 min | Apply laundry no-show penalties |
| `check_stale_complaints` | Every 2 hours | Flag complaints with no activity |
| `send_slot_reminders` | Every 30 min | Remind students of upcoming slots |
| `check_laundry_complaint_clusters` | Every 2 hours | Detect machine-linked complaint spikes |

---

## 8. User Roles & Access Control

There are exactly **4 roles** in the system:

| Role | Description | Default Route |
|---|---|---|
| `student` | Registers with hostel code; pending warden approval | `/student` |
| `laundry_man` | Created by warden; manages machines and views slot grid | `/staff/laundry` |
| `mess_staff` | Created by warden; publishes menu and views feedback | `/staff/mess` |
| `warden` | Full access; approves students, overrides AI, manages hostel | `/warden` |

### Auth Flow

1. Warden creates hostel via `/api/hostels/setup` → receives JWT immediately
2. Student registers via `/api/users/register` → `is_verified = False`
3. Warden reviews in **Student Registrations** screen → approves or rejects with reason
4. Approved student can log in

### Token Architecture

- **Access token**: JWT, stateless, 24-hour expiry
- **Refresh token**: Opaque, DB-backed (SHA256 hash stored), 30-day expiry
- **Rotation**: Each `/api/auth/refresh` revokes the old token and issues a new pair
- **Theft detection**: If a revoked refresh token is reused, all sessions for that user are invalidated

---

## 9. Multi-Tenant Architecture

One deployment serves unlimited hostels. Each hostel is identified by a unique auto-generated **hostel code** (e.g. `IGBH-4821`).

- Every database row that contains hostel-scoped data has a `hostel_id` foreign key
- Every query filters by `hostel_id` — a user from Hostel A can never see Hostel B's data
- Cross-hostel user lookups return **404** (not 403) — returning 403 would confirm the user exists elsewhere
- Hostel configuration (thresholds, mode, capacity) is stored per-hostel in `hostel_config` with a 5-minute in-memory TTL cache

### Hostel Modes

| Mode | Student Registration Requires |
|---|---|
| `college` | Roll number + ERP document upload |
| `autonomous` | Name, room number, password only |

---

## 10. Frontend — PWA

The frontend is a fully offline-capable Progressive Web App built with React 19 + Vite.

### Design System

Dark mode throughout:

| Token | Value |
|---|---|
| Background | `#0A0A0F` |
| Card / Surface | `#13121A` |
| Elevated | `#1C1B24` |
| Primary (purple) | `#7C5CFC` |
| Success (jade) | `#1A9B6C` |
| Danger (vermillion) | `#E83B2A` |
| Warning | `#D48C00` |
| Text primary | `#F0F0F5` |
| Text secondary | `#6B6B80` |

### Screens (23 total)

**Auth:** Landing · Login · Register · Registration Pending · Registration Rejected · Hostel Setup

**Student:** Home · File Complaint · Complaint Tracker · Complaint Detail · Laundry Booking · Mess Page · Notification Inbox · Profile · Onboarding

**Warden:** Dashboard · Approval Queue · Complaint Management · Student Registrations · Hostel Settings · Create Staff Account

**Staff:** Laundry Man View · Mess Staff View

### State Management

- **TanStack Query v5** for all server state (fetching, caching, invalidation)
- **AuthContext** for token storage and user session
- **React Router v7** for client-side routing with role-based guards
- Notification polling every 30 seconds via `useNotifications` hook

---

## 11. Security

| Area | Implementation |
|---|---|
| **Passwords** | `bcrypt` with cost factor 12 |
| **JWT** | `python-jose` — HS256 signed, 24h expiry |
| **Refresh tokens** | SHA256 hash stored — raw token never persists in DB |
| **Token theft detection** | Revoked token reuse → full session wipe for that user |
| **Rate limiting** | Redis sliding-window per user — configurable daily complaint limit |
| **Hostel isolation** | Every query scoped by `hostel_id` — validated in service layer |
| **Input sanitization** | Pydantic v2 strict validation on all request bodies |
| **CORS** | Explicit origin whitelist via `ALLOWED_ORIGINS` env var |
| **Audit log** | Immutable append-only log for every complaint state transition |

---

## 12. Getting Started — Local Development

### Prerequisites

- Python 3.11+
- Node.js 20+
- A PostgreSQL database (Supabase free tier works)
- A Redis instance (Upstash free tier works)
- A Groq API key (free at console.groq.com)

### Backend

```bash
cd backend

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Fill in DATABASE_URL, JWT_SECRET, GROQ_API_KEY, CELERY_BROKER_URL, CELERY_RESULT_BACKEND

# Run migrations
alembic upgrade head

# Seed first warden + hostel config
python create_admin.py

# Start API server
uvicorn main:app --reload
```

### Celery Workers (separate terminals)

```bash
# Worker (Windows)
.venv\Scripts\celery -A celery_app worker --pool=solo --loglevel=info

# Beat scheduler
.venv\Scripts\celery -A celery_app beat --loglevel=info
```

### Frontend

```bash
cd frontend

npm install

# Configure environment
cp .env.example .env
# Set VITE_API_URL=http://localhost:8000

npm run dev       # http://localhost:5173
npm run build     # Production build (TypeScript check + Vite)
npm run lint      # ESLint
```

---

## 13. Environment Variables

Copy `backend/.env.example` to `backend/.env` and fill in all values.

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | ✅ | `postgresql+asyncpg://user:pass@host:5432/db` |
| `JWT_SECRET` | ✅ | Strong random string — `openssl rand -hex 32` |
| `GROQ_API_KEY` | ✅ | From console.groq.com |
| `GROQ_MODEL_NAME` | ✅ | `llama-3.3-70b-versatile` |
| `CELERY_BROKER_URL` | ✅ | Upstash Redis `rediss://` URL |
| `CELERY_RESULT_BACKEND` | ✅ | Same as broker URL |
| `ALLOWED_ORIGINS` | ✅ | Frontend URL(s), comma-separated |
| `HF_API_KEY` | — | HuggingFace token — leave blank to disable deduplication |
| `EMBEDDING_MODEL` | — | Default: `sentence-transformers/all-MiniLM-L6-v2` |
| `COMPLAINT_CONFIDENCE_THRESHOLD` | — | Default: `0.85` |
| `MESS_ALERT_THRESHOLD` | — | Default: `2.5` |
| `LAUNDRY_NOSHOW_PENALTY_HOURS` | — | Default: `48` |

Frontend: copy `frontend/.env.example` to `frontend/.env`.

| Variable | Description |
|---|---|
| `VITE_API_URL` | Backend URL without trailing slash — e.g. `http://localhost:8000` |

---

## 14. Deployment

The production stack uses all free tiers:

| Service | Provider |
|---|---|
| Database | Supabase (free) |
| Redis | Upstash (free) |
| API + Celery | Railway (hobby) |
| Frontend | Vercel (free) |

### Docker

A `Dockerfile` at the repo root builds the Python environment. Railway uses it directly — no language auto-detection required.

```bash
# Build locally to validate before pushing
docker build -t hostelops-ai .
docker run -e PORT=8000 -e DATABASE_URL="..." hostelops-ai
```

### Railway (3 Services)

All three services use the same Docker image with different start commands:

| Service | Start Command |
|---|---|
| API | *(uses Dockerfile CMD — uvicorn)* |
| Celery Worker | `celery -A celery_app worker --loglevel=info --concurrency=1` |
| Celery Beat | `celery -A celery_app beat --loglevel=info --schedule=/tmp/celerybeat-schedule` |

Set all environment variables from the table above on each service. The API service needs `ALLOWED_ORIGINS` set to the Vercel frontend URL.

### Vercel (Frontend)

1. Import GitHub repo → set **Root Directory** to `frontend`
2. Add env var: `VITE_API_URL` = Railway API service URL
3. Deploy — `vercel.json` handles SPA routing automatically

### Migrations (run once, before first deploy)

```bash
cd backend
alembic upgrade head
python create_admin.py   # Save the printed hostel code
```

---

## 15. Key Engineering Decisions

**Two database sessions, never mixed**
`AsyncSessionLocal` (asyncpg) is used exclusively in FastAPI routes. `SyncSessionLocal` (psycopg2) is used exclusively in Celery tasks. asyncpg is async-only and cannot run inside synchronous Celery workers.

**Single state-machine function**
`transition_complaint()` in `complaint_service.py` is the only function allowed to change complaint status. All callers go through it. This prevents inconsistent state across routes, tasks, and warden overrides.

**Confidence-gated autonomy**
The system never takes irreversible action on complaints it is uncertain about. Classification confidence below the threshold always surfaces to a human — the AI is an assistant, not a decision-maker.

**Hostel config over env vars**
Operational thresholds (mess alert levels, laundry slot hours, approval timeouts) are stored in `hostel_config` per hostel and cached in memory for 5 minutes. This allows wardens to tune their hostel without a redeploy.

**Enums as a single source of truth**
All Python enums live in `schemas/enums.py`. SQLAlchemy models mirror them exactly. Every new enum value requires an Alembic migration before any code references it.

**JWT + opaque refresh token**
Access tokens are stateless JWTs (fast, no DB lookup). Refresh tokens are opaque random strings stored as SHA256 hashes (revocable, theft-detectable). The combination gives both performance and security.

---

## 16. Failure Modes & Resilience

| Failure | Detection | Recovery |
|---|---|---|
| Groq API down | Exception in classify task | Falls back to rule-based classifier; complaint enters `AWAITING_APPROVAL` |
| Celery worker crash | Task in `STARTED` state but never `SUCCESS` | `task_acks_late=True` — task is re-queued on worker restart |
| Redis connection lost | Celery broker error | Worker retries with exponential backoff |
| DB connection error | SQLAlchemy pool timeout | FastAPI returns 503; Celery task retries |
| Approval timeout | `check_approval_timeouts` beat task | Auto-escalates complaints waiting > threshold minutes |
| Duplicate complaint | pgvector cosine similarity | Flagged in UI; staff can merge or dismiss |

---

## 17. V2 Roadmap

- **LangGraph** — replace current linear classification pipeline with a stateful graph for multi-step reasoning
- **WebSockets** — replace 30-second notification polling with real-time push
- **Analytics dashboard** — visual charts for complaint trends, mess satisfaction, and laundry utilisation
- **Mobile app** — React Native or Flutter wrapper around the existing API
- **ERP integration** — auto-verify student roll numbers against college ERP on registration
- **Multi-language support** — i18n for Hindi and regional languages
