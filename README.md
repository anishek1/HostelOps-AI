# HostelOPS AI

> **Autonomous Operations Management for Hostels & PGs**  
> AI-driven complaint triage, fair laundry scheduling, and mess quality monitoring — all in one zero-cost, open-source stack.

[![Backend](https://img.shields.io/badge/Backend-FastAPI%20%2B%20Python-009688?style=flat-square)](https://fastapi.tiangolo.com/)
[![Frontend](https://img.shields.io/badge/Frontend-React%2018%20%2B%20TypeScript-61DAFB?style=flat-square)](https://react.dev/)
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
6. [Database Schema](#6-database-schema)
7. [API Reference](#7-api-reference)
8. [AI Agents](#8-ai-agents)
9. [User Roles & Access Control](#9-user-roles--access-control)
10. [Multi-Tenant Architecture](#10-multi-tenant-architecture)
11. [Frontend (Sprint F — PWA)](#11-frontend-sprint-f--pwa)
12. [Security](#12-security)
13. [Getting Started — Development Setup](#13-getting-started--development-setup)
14. [Environment Variables](#14-environment-variables)
15. [Running the Application](#15-running-the-application)
16. [Sprint History](#16-sprint-history)
17. [Key Engineering Decisions](#17-key-engineering-decisions)
18. [API Evaluation Metrics](#18-api-evaluation-metrics)
19. [Failure Modes & Resilience](#19-failure-modes--resilience)
20. [V2 Roadmap](#20-v2-roadmap)

---

## 1. What is HostelOPS AI?

HostelOPS AI is an **autonomous operations management system** for college hostels and independent PGs. It replaces the manual, reactive, inconsistent day-to-day management of complaints, laundry, and mess operations with a structured, AI-driven pipeline that is always-on, fair, and transparent.

### Problem Statement

Hostel wardens spend a disproportionate amount of time on repetitive, low-value administrative tasks — manually triaging complaints, mediating laundry disputes, and reacting to mess dissatisfaction only after it escalates. Students lack transparency into whether their concerns are being heard.

### Solution

HostelOPS AI automates the routine, escalates the important, and gives every stakeholder a clear and reliable interface.

| Design Principle | Implementation |
|---|---|
| **Automate the routine, escalate the sensitive** | AI never makes autonomous decisions on interpersonal or safety-critical issues |
| **Confidence-gated action** | Acts automatically only when confidence ≥ threshold; ambiguous decisions surface to a human for one-tap approval |
| **Full transparency** | Every student tracks complaint status. Every warden sees operations health at a glance |
| **Fairness by design** | Laundry allocation governed by an explicit scoring algorithm, not first-come-first-serve |
| **Zero-cost infrastructure** | Open-source models, free-tier services — no paid APIs |
| **Multi-tenant** | One deployment serves multiple hostels, each isolated by hostel code |

---

## 2. Core Features

### For Students
- 📝 **Complaint Filing** — Free-text or from 9 quick-fill templates (min 10 chars). Anonymous option available.
- 📊 **Complaint Status Tracker** — Real-time status: INTAKE → CLASSIFIED → ASSIGNED → IN_PROGRESS → RESOLVED
- 🔄 **Complaint Reopening** — If resolution is unsatisfactory, reopen with elevated priority. Warden notified.
- 👕 **Laundry Slot Booking** — Date picker + per-machine slot grid. Fairness algorithm, no-show penalties.
- 🍽️ **Mess Feedback** — Rate 5 dimensions per meal (Breakfast/Lunch/Dinner). One-click from home screen.
- 📅 **Mess Menu** — View the current published menu anytime.
- 🔔 **Notification Inbox** — Push + in-app notifications for all status changes.
- 🏠 **Notice Board** — Warden announcements on home screen.
- 🔥 **Feedback Streak** — Consecutive-day participation counter. Motivates daily mess ratings.
- 🎓 **Onboarding Walkthrough** — Shown exactly once on first login.

### For Wardens (Assistant / Warden / Chief Warden)
- ✅ **Registration Approval** — Review, approve, or reject student registrations with reason.
- 🧠 **AI Approval Queue** — Review AI-uncertain complaint decisions; approve or override with one tap.
- 📈 **Dashboard Analytics** — 7 evaluation metrics computed on-demand; drift alerts when accuracy drops.
- 👥 **Student Management** — Search/filter all students; deactivate, reject, reset passwords.
- 🔧 **Hostel Settings** — Configure all operational thresholds from the UI (no `.env` editing needed).
- 👔 **Staff Account Creation** — Create laundry, mess, and assistant warden accounts directly.
- 📢 **Notice Board** — Post and delete announcements to all students.

### For Staff (Laundry Man / Mess Secretary / Mess Manager)
- 🔧 **Laundry Dashboard** — View slot assignments, mark machines under repair / repaired.
- 🥗 **Mess Dashboard** — View feedback summary, dissatisfaction alerts, publish mess menu.

---

## 3. Architecture Overview

### The Supervisor Pattern

HostelOPS AI uses the **Supervisor Pattern** — a multi-agent architecture where Agent 1 (the Orchestrator) is the single entry point for all student inputs.

```
Student PWA
     │
     ▼
┌─────────────────────────────────────────┐
│          Agent 1 — Orchestrator         │
│  • Receives all complaints              │
│  • LLM classification (Groq + Llama 3) │
│  • Confidence-gated routing            │
│  • Fallback classifier (rule-based)    │
└──────┬──────────────┬───────────────────┘
       │              │
       ▼              ▼
┌──────────────┐  ┌──────────────────────┐
│   Agent 2   │  │       Agent 3        │
│   Laundry   │  │  Mess Feedback &     │
│  Allocation │  │  Dissatisfaction     │
│   Agent     │  │  Monitor             │
└──────────────┘  └──────────────────────┘
```

### High-Level Data Flow

1. Student submits complaint → enters **Agent 1** (Celery async task)
2. Agent 1 classifies by category + severity using Groq LLM
3. **High confidence + Non-sensitive** → auto-assigns to correct staff  
4. **Low confidence OR High severity** → surfaces to Warden's approval queue
5. Student receives immediate acknowledgement (in-app + push)
6. Assigned staff member notified
7. Warden override decisions logged for continuous improvement
8. Laundry bookings → **Agent 2** directly  
9. Mess feedback → **Agent 3** directly

### Complaint State Machine

```
INTAKE ──────────────────────────────────────────► ESCALATED
  │                                                    ▲
  ▼                                                    │
CLASSIFIED ──────────────────────────────────────► AWAITING_APPROVAL
  │                                                    │
  ▼                                                    │
ASSIGNED ◄──────────────────────────────────────────  │
  │                                                    │
  ▼                                                    │
IN_PROGRESS ──────────────────────────────────────►  │
  │                                                    │
  ▼                                                    │
RESOLVED ◄── Student confirms ──► REOPENED ──────────►│
```

---

## 4. Technology Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| **Frontend** | React 18 + TypeScript + Vite + PWA | Sprint F — all screens built |
| **UI** | Tailwind CSS + Shadcn/UI | Plus Jakarta Sans typography |
| **Backend** | Python + FastAPI + Pydantic v2 | Async-first throughout |
| **ORM** | SQLAlchemy 2.0 (async) + Alembic | All migrations tracked |
| **Agent Orchestration** | LangChain | LangGraph is V2 upgrade path |
| **LLM** | Groq free tier + `llama-3.3-70b-versatile` | `llama3-8b-8192` decommissioned March 2026 |
| **Task Queue** | Celery 5.4 + Upstash Redis (free tier) | Windows dev: `--pool=solo` |
| **Database** | PostgreSQL via Supabase (free tier) | Port **5432** always, never 6543 |
| **Auth** | JWT via `python-jose` + `bcrypt` (direct) | `passlib` permanently removed |
| **Push Notifications** | Web Push API (`pywebpush`) + VAPID | |
| **Hosting** | Railway | Docker Compose for Sprint D |
| **Config** | `python-dotenv` + `pydantic-settings` | All secrets in `.env` |
| **Cache** | `cachetools` TTL cache (hostel config) | Per-hostel, maxsize=100 |

### Backend Dependencies (`requirements.txt`)

```
fastapi==0.115.6
uvicorn[standard]==0.34.0
sqlalchemy[asyncio]==2.0.37
asyncpg==0.30.0
alembic==1.14.1
pydantic[email]==2.10.6
pydantic-settings==2.8.1
python-jose[cryptography]==3.3.0
bcrypt==4.1.2
python-dotenv==1.0.1
celery==5.4.0
redis==5.2.1
kombu==5.3.4
psycopg2-binary==2.9.10      # Sync driver for Celery
langchain==0.3.18
langchain-core==0.3.35
langchain-groq==0.2.4
pywebpush==2.0.0
cachetools==5.5.0
```

---

## 5. Project Structure

```
HostelOPS AI/
├── PRD.md                        # Full product requirements document
├── CONVENTIONS.md                # All coding rules (must read before any code)
├── PROJECT_STATE.md              # Living sprint state — AI onboarding prompt
├── DESIGN.md                    # Design system spec (colors, typography, components)
│
├── backend/
│   ├── main.py                   # FastAPI app + CORS + router registration
│   ├── config.py                 # pydantic-settings — all env vars typed
│   ├── database.py               # Async SQLAlchemy engine + session factory
│   ├── celery_app.py             # Celery + beat schedule (sys.path fix at top)
│   ├── create_admin.py           # Seeds admin, machines, hostel config
│   ├── requirements.txt
│   │
│   ├── models/                   # SQLAlchemy ORM models (16 tables)
│   │   ├── user.py               # is_rejected, rejection_reason, has_seen_onboarding, feedback_streak
│   │   ├── hostel.py             # Multi-tenant: id, name, code, mode
│   │   ├── complaint.py          # resolved_confirmed_at, reopen_reason, is_priority
│   │   ├── audit_log.py          # ip_address column
│   │   ├── approval_queue.py
│   │   ├── override_log.py       # warden_id (not corrected_by)
│   │   ├── notification.py
│   │   ├── machine.py            # repaired_at (not last_serviced_at)
│   │   ├── laundry_slot.py       # booking_status + slot_date + slot_time
│   │   ├── mess_feedback.py      # 5 columns: food_quality, hygiene, menu_variety, food_quantity, timing
│   │   ├── mess_alert.py
│   │   ├── mess_menu.py          # valid_from date, day_of_week as int (1=Mon, 7=Sun)
│   │   ├── notice.py             # Hostel-scoped warden announcements
│   │   ├── hostel_config.py      # UUID PK, single row per hostel
│   │   ├── refresh_token.py      # SHA256-hashed; revoked column (not is_revoked)
│   │   └── push_subscription.py
│   │
│   ├── schemas/                  # Pydantic v2 schemas (source of truth)
│   │   ├── enums.py
│   │   ├── user.py               # StaffCreate + StaffRead (Sprint 6)
│   │   ├── complaint.py
│   │   ├── laundry.py
│   │   ├── mess.py
│   │   ├── hostel.py             # HostelSetupRequest, HostelRead, HostelPublicInfo
│   │   ├── approval_queue.py
│   │   ├── override_log.py
│   │   ├── notification.py
│   │   ├── hostel_config.py
│   │   └── metrics.py            # DashboardMetrics with all 7 metrics + pending counts
│   │
│   ├── routes/                   # FastAPI routers (thin — call services only)
│   │   ├── auth.py               # Login returns full user object
│   │   ├── users.py              # reject, reset-password, staff CRUD, /me, onboarding
│   │   ├── hostels.py            # POST /setup, GET /{code}/info
│   │   ├── complaints.py         # File, list, detail, reopen, resolve, escalate, templates
│   │   ├── approval_queue.py
│   │   ├── laundry.py
│   │   ├── mess.py               # Feedback + menu
│   │   ├── notices.py
│   │   ├── notifications.py
│   │   ├── push.py
│   │   ├── analytics.py          # Dashboard + complaints/mess/laundry analytics
│   │   └── hostel_config.py
│   │
│   ├── services/                 # All business logic lives here
│   │   ├── auth_service.py       # bcrypt ONLY (hash_password, verify_password)
│   │   ├── user_service.py       # reject_user, warden_reset_password, create_staff_account
│   │   ├── complaint_service.py  # VALID_TRANSITIONS single source of truth
│   │   ├── approval_queue_service.py
│   │   ├── override_log_service.py
│   │   ├── notification_service.py  # notify_user() — push inside try/except
│   │   ├── laundry_service.py
│   │   ├── mess_service.py
│   │   ├── mess_menu_service.py
│   │   ├── notice_service.py
│   │   ├── complaint_template_service.py  # 9 hardcoded templates (no DB table)
│   │   ├── push_service.py
│   │   ├── metrics_service.py    # All 7 metrics + analytics queries
│   │   ├── hostel_service.py     # generate_unique_hostel_code, create_hostel_with_warden
│   │   ├── hostel_config_service.py  # Cached per hostel_id
│   │   └── fallback_classifier.py    # Rule-based fallback when LLM fails
│   │
│   ├── agents/                   # LangChain agents
│   │   ├── agent_complaint.py    # Agent 1 — Orchestrator
│   │   ├── agent_laundry.py      # Agent 2 — Laundry Allocation
│   │   └── agent_mess.py         # Agent 3 — Mess Dissatisfaction Monitor
│   │
│   ├── tools/                    # LangChain tools used by agents
│   │   ├── complaint_tools.py    # 6 tools
│   │   ├── laundry_tools.py
│   │   └── mess_tools.py
│   │
│   ├── tasks/                    # Celery async tasks
│   │   ├── complaint_tasks.py    # route_to_laundry_agent + route_to_mess_agent
│   │   ├── approval_tasks.py     # check_approval_timeouts (every 15 mins)
│   │   ├── laundry_tasks.py      # process_noshow_penalties (hourly) + send_slot_reminders (30 mins)
│   │   └── mess_tasks.py         # analyze_daily_mess_feedback (10pm) + check_participation_alert (8am)
│   │
│   ├── middleware/
│   │   ├── rate_limiter.py       # Per-user, per hostel_config limit (wardens exempt)
│   │   └── prompt_sanitizer.py   # Strips injection patterns, logs flagged inputs
│   │
│   └── migrations/               # Alembic migration history
│       └── versions/
│           ├── sprint1_initial_schema
│           ├── sprint2_complaint_pipeline
│           ├── sprint3_approval_queue
│           ├── sprint4_laundry_mess
│           ├── sprint5_notifications_config
│           ├── sprint6_completions
│           ├── a1b2c3d4e5f6_sprint7_multi_tenant
│           ├── ec3264ca7257_hostel_config_uuid_pk
│           └── c57d21acb8ed_sprint7b_api_polish_and_features
│
└── frontend/                     # React 18 + TypeScript + Vite PWA
    ├── index.html
    ├── vite.config.ts
    ├── package.json
    └── src/
        ├── App.tsx               # Router + auth guards
        ├── api/                  # Typed API client modules
        ├── components/           # Shared UI components (AppShell, Nav bars, etc.)
        ├── context/              # AuthContext
        ├── hooks/                # Custom React hooks
        ├── pages/
        │   ├── auth/             # Landing, Login, Register, Pending, Rejected, HostelSetup
        │   ├── student/          # Home, Complaints, Laundry, Mess, Notifications, Profile
        │   └── warden/           # Dashboard, ApprovalQueue, Students, Staff, Settings
        └── types/                # TypeScript types mirroring Pydantic schemas
```

---

## 6. Database Schema

**16 tables** across the system. All tables scoped by `hostel_id` after Sprint 7.

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `hostels` | Multi-tenant hostel registry | `id`, `name`, `code` (XXXX-0000), `mode` |
| `users` | Students, staff, wardens | `role`, `hostel_id`, `is_verified`, `is_rejected`, `has_seen_onboarding`, `feedback_streak` |
| `complaints` | All student complaints | `status`, `category`, `severity`, `classified_by`, `assignee_id`, `is_priority`, `is_anonymous` |
| `audit_logs` | Every state change | `user_id`, `action`, `ip_address`, `timestamp` |
| `approval_queue` | AI-uncertain decisions pending warden review | `complaint_id`, `ai_suggestion`, `confidence_score` |
| `override_logs` | Warden corrections to AI decisions | `warden_id`, `original_category`, `corrected_category`, `override_reason` |
| `notifications` | In-app notification inbox | `user_id`, `type`, `is_read`, `hostel_id` |
| `push_subscriptions` | Web Push subscription endpoints | `user_id`, `endpoint`, `keys` |
| `machines` | Laundry machines | `name`, `floor`, `status`, `hostel_id`, `repaired_at` |
| `laundry_slots` | Time-based slot bookings | `slot_date`, `slot_time`, `booking_status`, `student_id`, `machine_id` |
| `mess_feedback` | Per-meal student ratings | `food_quality`, `hygiene`, `menu_variety`, `food_quantity`, `timing` (each 1-5) |
| `mess_alerts` | Auto-detected dissatisfaction alerts | `dimension`, `alert_type`, `avg_score`, `hostel_id` |
| `mess_menu` | Published weekly menus | `day_of_week` (int 1-7), `meal`, `items`, `valid_from` |
| `notices` | Warden announcements | `title`, `body`, `hostel_id`, `created_by` |
| `hostel_config` | Per-hostel operational thresholds | UUID PK, complaint confidence threshold, laundry hours, mess alert thresholds |
| `refresh_tokens` | JWT refresh token store | `token_hash` (SHA256), `revoked`, `user_id` |

### Critical Model Deviations (read before querying)

> ⚠️ These differ from what you might expect — document source of truth.

- `Machine` model is `models/machine.py` (not `LaundryMachine`). Column is `repaired_at` (not `last_serviced_at`)
- `MessFeedback` has **5 separate columns**: `food_quality`, `hygiene`, `menu_variety`, `food_quantity`, `timing` — NOT a single `rating` column
- `MessFeedback.date` (not `feedback_date`). `MessFeedback.meal` (not `meal_type`)
- `LaundrySlot` uses `booking_status` (not `status`) to avoid column collision
- `LaundrySlot` uses `slot_date` (date type) and `slot_time` (string e.g. `"09:00-10:00"`)
- `RefreshToken.revoked` (not `is_revoked`)
- `OverrideLog.warden_id` (not `corrected_by`)

---

## 7. API Reference

### Base URL
- **Development:** `http://localhost:8000`
- **Production:** Railway URL

### Authentication

All protected routes require `Authorization: Bearer <access_token>` header.

Login returns:
```json
{
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "bearer",
  "user": { /* full UserRead object */ }
}
```

> ⚠️ **Login requires `hostel_code`** — room numbers are not globally unique.

### Auth Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/api/auth/register` | None | Register student (requires hostel_code) |
| `POST` | `/api/auth/login` | None | Login (requires hostel_code) |
| `POST` | `/api/auth/refresh` | Refresh token | Get new access token |
| `POST` | `/api/auth/logout` | JWT | Revoke all user refresh tokens |

### Hostel Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/api/hostels/setup` | None | Create hostel + warden account → returns hostel code |
| `GET` | `/api/hostels/{code}/info` | None | Public hostel name + mode lookup |

### User Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/api/users/me` | JWT | Current user profile |
| `PATCH` | `/api/users/me/password` | JWT | Self-service password change |
| `PATCH` | `/api/users/me/onboarding-seen` | JWT | Mark onboarding complete |
| `GET` | `/api/users` | Warden | List students with filters (role, is_verified, search) |
| `POST` | `/api/users/{id}/verify` | Warden | Approve student registration |
| `POST` | `/api/users/{id}/reject` | Warden | Reject with reason |
| `POST` | `/api/users/{id}/deactivate` | Warden | Deactivate account |
| `PATCH` | `/api/users/{id}/reset-password` | Warden | Force reset student password |
| `POST` | `/api/users/staff` | Warden | Create staff account |
| `DELETE` | `/api/users/staff/{id}` | Warden | Deactivate staff account |

### Complaint Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/api/complaints/` | Student | File complaint (min 10 chars) |
| `GET` | `/api/complaints/my` | Student | My complaints (paginated) |
| `GET` | `/api/complaints/templates` | Any | 9 quick-fill templates |
| `GET` | `/api/complaints/` | Warden | All complaints (filters: status, category, severity, search) |
| `GET` | `/api/complaints/{id}` | Auth | Complaint detail + timeline |
| `POST` | `/api/complaints/{id}/resolve` | Staff | Mark resolved |
| `POST` | `/api/complaints/{id}/confirm-resolution` | Student | Confirm Yes/No |
| `POST` | `/api/complaints/{id}/reopen` | Student | Reopen with reason |
| `POST` | `/api/complaints/{id}/escalate` | Warden | Escalate to higher authority |
| `PATCH` | `/api/complaints/{id}/progress` | Staff | Mark in-progress |

### Approval Queue Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/api/approval-queue/` | Warden | All pending queue items (paginated) |
| `POST` | `/api/approval-queue/{id}/approve` | Warden | Approve AI suggestion |
| `POST` | `/api/approval-queue/{id}/override` | Warden | Override with correction + reason |
| `POST` | `/api/approval-queue/{id}/escalate` | Warden | Escalate directly |

### Laundry Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/api/laundry/machines` | Auth | All machines + status |
| `PATCH` | `/api/laundry/machines/{id}/status` | Laundry Man | Update machine status |
| `GET` | `/api/laundry/slots` | Auth | Available slots for date + machine |
| `POST` | `/api/laundry/slots/book` | Student | Book a slot |
| `POST` | `/api/laundry/slots/{id}/cancel` | Student | Cancel booking |
| `GET` | `/api/laundry/my-bookings` | Student | My bookings (paginated) |

### Mess Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/api/mess/feedback` | Student | Submit meal feedback (5 dimensions) |
| `GET` | `/api/mess/my-feedback` | Student | My feedback history (paginated) |
| `GET` | `/api/mess/summary` | Warden | Aggregated mess analytics |
| `GET` | `/api/mess/alerts` | Warden | Dissatisfaction alerts (paginated) |
| `POST` | `/api/mess/menu` | Mess Manager / Warden | Publish menu |
| `GET` | `/api/mess/menu` | Auth | Get current active menu |

### Notices Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/api/notices` | Warden | Create announcement |
| `GET` | `/api/notices` | Auth | All notices for hostel |
| `DELETE` | `/api/notices/{id}` | Warden | Delete (returns 204) |

### Analytics Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/api/analytics/dashboard` | Warden | All 7 metrics + pending counts |
| `GET` | `/api/analytics/complaints` | Warden | Complaint breakdown by category/severity |
| `GET` | `/api/analytics/mess` | Warden | Mess satisfaction trends |
| `GET` | `/api/analytics/laundry` | Warden | Laundry no-show + utilization rates |

### System Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/health` | None | `{ "status": "ok", "version": "1.0.0" }` |

### Pagination

All list endpoints support `?limit=20&offset=0` query params.

---

## 8. AI Agents

### Agent 1 — Complaint Orchestrator (`agent_complaint.py`)

**Input:** Raw complaint text  
**LLM:** Groq + `llama-3.3-70b-versatile` (via `settings.GROQ_MODEL_NAME`)  
**Framework:** LangChain

**Routing logic:**

| Category | Routing Target |
|----------|---------------|
| Mess-related (food, hygiene, timing) | → Agent 3 → Mess Manager / Mess Secretary |
| Laundry-related (machines, clothes, slots) | → Agent 2 → Laundry Man |
| Maintenance (room, electrical, plumbing) | → Assistant Warden |
| Interpersonal / Sensitive (conflict, harassment) | → Warden approval queue (NEVER auto-assigned) |
| Critical / Safety | → Chief Warden (after Warden review) |

**Severity → Action:**

| Severity | Action |
|----------|--------|
| Low / Medium + High confidence | Auto-assign |
| High severity (any confidence) | Approval queue ALWAYS |
| Low confidence (any severity) | Approval queue |

**Fallback chain:** LLM fails → Celery retries (3× exponential backoff) → rule-based keyword classifier → `AWAITING_APPROVAL`

**Confidence threshold:** Configurable via `hostel_config.complaint_confidence_threshold` (default: 0.85)

### Agent 2 — Laundry Allocation (`agent_laundry.py`)

**Fairness Algorithm:**

```
Priority Score = min(days_since_last_booking, 30) × penalty_multiplier
  where penalty_multiplier = 0.1 if no-show in last 48h, else 1.0
```

- Score computed on request, never stored
- Students with score ≥ 20 (4+ days since last wash) see UI nudge on first 2 available slots
- One booking per student per day enforced server-side

**No-show penalty:** 48-hour penalty applied by `process_noshow_penalties` Celery task (hourly)  
**Reminder:** `send_slot_reminders` task runs every 30 minutes

### Agent 3 — Mess Dissatisfaction Monitor (`agent_mess.py`)

**Alert triggers:**

- **Chronic pattern:** Any single dimension < `mess_alert_threshold` (default 2.5/5) for 3+ consecutive meals
- **Incident spike:** Any dimension drops 1.5 from its 7-day rolling average in one meal
- **Participation collapse:** < `mess_min_participation` (15%) for 3 consecutive days

**Alert routing:**

- Score < alert threshold → **Mess Manager** notified
- Score < critical threshold (2.0) → **Assistant Warden** also notified

**Scheduled tasks:**  
- `analyze_daily_mess_feedback` — runs at 10pm daily  
- `check_participation_alert` — runs at 8am daily

---

## 9. User Roles & Access Control

| Role | Level | Key Capabilities |
|------|-------|-----------------|
| `student` | End user | File complaints, book laundry, submit mess feedback |
| `laundry_man` | Operational staff | Manage slot completion, update machine status |
| `mess_secretary` | Operational staff | Receive mess complaint assignments |
| `mess_manager` | Supervisory staff | Receive mess alerts, publish menu |
| `assistant_warden` | Administrative | Approve/reject registrations, receive maintenance assignments |
| `warden` | Supervisory | Approval queue, escalations, dashboard |
| `chief_warden` | Top authority | Final escalation point only |

**`WARDEN_ROLES = [assistant_warden, warden, chief_warden]`** — always all three. Never just `warden`.

### Registration Flow

```
Student registers (with hostel_code)
        │
        ▼
Account inactive (is_verified=False)
        │
        ▼
Warden reviews → Approve ──► Student notified → First login → Onboarding walkthrough
              ↘ Reject (with reason) ──► Student sees rejection reason + can re-register
```

### Key Auth Rules

- **Login requires `hostel_code`** — room numbers are not globally unique (multi-tenant)
- **Rejected accounts** receive 403 with rejection reason on login attempt
- **Deactivated accounts** receive 403 with deactivation message (not generic 401)
- **Password reset** is warden-only in V1 (no email, no self-service)
- **Rate limiting** — max 5 complaints/student/day (configurable). Wardens never rate-limited.

---

## 10. Multi-Tenant Architecture

**Implemented in Sprint 7.** One deployment serves multiple hostels. Every query is scoped by `hostel_id`.

### Hostel Setup Flow

```
Warden visits app → "Set up my hostel" → fills name, mode, floors, account details
      │
      ▼
POST /api/hostels/setup
      │
      ▼
System generates unique hostel code (e.g. IGBH-4821)
      │
      ▼
Warden sees: "Your hostel code is IGBH-4821 — share this with your students"
      │
      ▼
Warden dashboard is live. Default hostel_config seeded.
```

### Student Registration with Hostel Code

```
Student opens app → "Register" → enters name, room, password, hostel_code
      │
      ▼
System validates code → links student to hostel
      │
      ▼
"Registration Pending" — warden approves
```

### Isolation Rules

- Every DB query filters by `hostel_id` after Sprint 7
- Cross-hostel operations return **404** (not 403) — prevents confirming user existence
- Login validates hostel_code — wrong code = 401
- Notifications never cross hostel boundaries
- `hostel_config` cache keyed by `hostel_id` (not a global cache)

### Hostel Config Table

All operational thresholds live in the DB — wardens configure from the UI:

| Config Key | Default | Description |
|-----------|---------|-------------|
| `complaint_confidence_threshold` | 0.85 | LLM confidence required for auto-assignment |
| `approval_queue_timeout_minutes` | 30 | Auto-escalate after N minutes |
| `mess_alert_threshold` | 2.5 | Score below this triggers Mess Manager alert |
| `mess_critical_threshold` | 2.0 | Score below this also alerts Assistant Warden |
| `mess_min_participation` | 15% | Minimum daily feedback rate before alert |
| `laundry_slots_start_hour` | 8 | First laundry slot start (24h) |
| `laundry_slots_end_hour` | 22 | Last slot end (24h) |
| `laundry_noshow_penalty_hours` | 48 | No-show priority penalty duration |
| `laundry_cancellation_deadline_minutes` | 15 | Penalty-free cancellation window |

---

## 11. Frontend (Sprint F — PWA)

### Design System

From `DESIGN.md`:

| Token | Value | Use |
|-------|-------|-----|
| Primary | Indigo `#4647D3` | Buttons, active nav, links |
| Success | Jade `#16A085` | Resolved status, confirmations |
| Danger | Vermillion `#E83B2A` | Escalated, urgent alerts |
| Accent | Saffron `#FFB800` | Star ratings, badges |
| Background | Warm cream `#FFF5EE` | Main app background |
| Card | White `#FFFFFF` | Card surfaces |
| Font | Plus Jakarta Sans | All text |

### 23 Screens

**Auth (6 screens):**
| ID | Screen | Route |
|----|--------|-------|
| S-01 | Hostel Setup | `/auth/setup` |
| S-02 | Landing | `/auth/landing` |
| S-03 | Login | `/auth/login` |
| S-04 | Register | `/auth/register` |
| S-05 | Registration Pending | `/auth/pending` |
| S-06 | Registration Rejected | `/auth/rejected` |

**Student (9 screens):**
| ID | Screen | Route |
|----|--------|-------|
| S-07 | Onboarding | `/onboarding` |
| S-08 | Student Home | `/student` |
| S-09 | File Complaint | `/student/complaints/new` |
| S-10 | Complaint Tracker | `/student/complaints` |
| S-11 | Complaint Detail | `/student/complaints/:id` |
| S-12 | Laundry Booking | `/student/laundry` |
| S-13 | Mess Page | `/student/mess` |
| S-14 | Notification Inbox | `/student/notifications` |
| S-15 | Student Profile | `/student/profile` |

**Warden (6 screens):**
| ID | Screen | Route |
|----|--------|-------|
| S-16 | Warden Dashboard | `/warden` |
| S-17 | Approval Queue | `/warden/approval-queue` |
| S-18 | Student Registrations | `/warden/students` |
| S-19 | Create Staff Account | `/warden/staff/new` |
| S-20 | Complaint Management | `/warden/complaints` |
| S-21 | Hostel Settings | `/warden/settings` |

**Staff (2 screens):**
| ID | Screen | Route |
|----|--------|-------|
| S-22 | Laundry Man View | `/staff/laundry` |
| S-23 | Mess Staff View | `/staff/mess` |

### Navigation

- **Student** — 5-tab bottom nav: Home / Complaints / Laundry / Mess / Profile
- **Warden** — 5-tab bottom nav: Dashboard / Approvals / Students / Settings / Profile
- **Laundry Staff** — 3-tab bottom nav: Slots / Machines / Profile
- **Mess Staff** — 3-tab bottom nav: Summary / Menu / Profile

### Implementation Notes

- Inline styles throughout (color constants as `const C = {...}` per page)
- `window.location.replace` for logout (clears history stack)
- 30-second polling for notifications (no WebSockets in V1)
- PWA with push notification support

---

## 12. Security

| Layer | Implementation |
|-------|---------------|
| **Prompt Injection** | `middleware/prompt_sanitizer.py` strips patterns pre-LLM. Flagged inputs logged to `complaints.flagged_input`. |
| **Input Sanitization** | All strings trimmed, length-capped, HTML-escaped |
| **Rate Limiting** | Per-user, configurable via `hostel_config`. Wardens always exempt. |
| **Audit Logs** | Every state-changing action written with user ID, action, timestamp, IP address |
| **JWT** | Access: 24h. Refresh: 30 days. Token rotation on every refresh. Reuse of revoked token → all-session invalidation. |
| **Password Hashing** | `bcrypt` directly (4.1.2). `passlib` permanently removed. 72-byte truncation applied. |
| **Refresh Token Storage** | SHA256 hash stored in DB. Raw token sent to client once only. |
| **Anonymous Complaints** | Identity visible only to `WARDEN_ROLES`. All staff see `Anonymous Student`. |
| **Cross-Hostel Access** | Returns 404 (not 403) — privacy by design. Never confirms cross-hostel user existence. |
| **CORS** | Locked to frontend URL in production (Sprint D). |
| **HTTPS** | enforced by Railway in production. |

---

## 13. Getting Started — Development Setup

### Prerequisites

- Python 3.10+ (tested on 3.11, 3.13)
- Node.js 18+
- Git
- A [Supabase](https://supabase.com/) project (free tier)
- A [Groq](https://console.groq.com/) API key (free tier)
- An [Upstash](https://upstash.com/) Redis instance (free tier)

### 1. Clone the Repository

```bash
git clone <repository-url>
cd "HostelOPS AI"
```

### 2. Backend Setup

```bash
cd backend

# Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate         # Windows
# source .venv/bin/activate    # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables

```bash
cp .env.example .env
# Edit .env with your actual values (see Section 14)
```

### 4. Run Database Migrations

```bash
alembic upgrade head
```

### 5. Seed Initial Admin Data

```bash
python create_admin.py
```

This seeds the first hostel, admin user, laundry machines, and default `hostel_config`.

### 6. Frontend Setup

```bash
cd ../frontend
npm install
```

---

## 14. Environment Variables

Create `backend/.env` (never commit this file):

```env
# Database — ALWAYS port 5432, NEVER 6543
DATABASE_URL=postgresql+asyncpg://postgres.PROJECT_REF:PASSWORD@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres

# Auth
JWT_SECRET=<long-random-string-min-32-chars>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_HOURS=24
REFRESH_TOKEN_EXPIRE_DAYS=30

# LLM — llama3-8b-8192 DECOMMISSIONED March 2026
GROQ_API_KEY=<from console.groq.com>
GROQ_MODEL_NAME=llama-3.3-70b-versatile

# Task Queue (Upstash Redis)
CELERY_BROKER_URL=rediss://:PASSWORD@ENDPOINT:6380/0
CELERY_RESULT_BACKEND=rediss://:PASSWORD@ENDPOINT:6380/0

# Push Notifications (generate with pywebpush)
VAPID_PRIVATE_KEY=<generated>
VAPID_PUBLIC_KEY=<generated>
VAPID_CLAIM_EMAIL=admin@hostelops.ai

# Complaint Agent
COMPLAINT_CONFIDENCE_THRESHOLD=0.85

# Mess Thresholds (DB hostel_config takes precedence at runtime)
MESS_ALERT_THRESHOLD=2.5
MESS_CRITICAL_THRESHOLD=2.0
MESS_MIN_PARTICIPATION=0.15
MESS_MIN_RESPONSES=5

# Laundry (DB hostel_config takes precedence at runtime)
LAUNDRY_SLOTS_START_HOUR=8
LAUNDRY_SLOTS_END_HOUR=22
LAUNDRY_SLOT_DURATION_HOURS=1
LAUNDRY_NOSHOW_PENALTY_HOURS=48
LAUNDRY_CANCELLATION_DEADLINE_MINUTES=15

# Approval Queue (DB hostel_config takes precedence at runtime)
APPROVAL_QUEUE_TIMEOUT_MINUTES=30
```

### Generating VAPID Keys

```bash
python -c "from pywebpush import generate_vapid_key; print(generate_vapid_key())"
```

---

## 15. Running the Application

### Backend

**Terminal 1 — FastAPI Server:**

```bash
cd backend
.venv\Scripts\activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 — Celery Worker:**

```bash
cd backend
.venv\Scripts\activate
# Windows:
celery -A celery_app worker --pool=solo --loglevel=info
# Linux/macOS:
celery -A celery_app worker --loglevel=info
```

**Terminal 3 — Celery Beat (Scheduled Tasks):**

```bash
cd backend
.venv\Scripts\activate
celery -A celery_app beat --loglevel=info
```

> **Windows Note:** `--pool=solo` is required for Windows (no fork support). Do NOT use `--pool=solo` in production on Railway.

> **Windows Note:** The "event loop closed" warning in Celery on Windows is non-fatal. Retry succeeds.

### Frontend

```bash
cd frontend
npm run dev
# Opens at http://localhost:5173
```

### API Documentation

FastAPI auto-generates interactive docs:
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

---

## 16. Sprint History

| Sprint | Status | What was Built |
|--------|--------|---------------|
| **Sprint 1** | ✅ Complete | Foundation — FastAPI setup, all models (10 tables), all Pydantic schemas, Alembic migrations, JWT auth + RBAC, React+TypeScript scaffold |
| **Sprint 2** | ✅ Complete | Agent 1 + Celery pipeline — complaint filing, LLM classification, Celery task queue, fallback classifier, prompt sanitizer |
| **Sprint 3** | ✅ Complete | Agent 1 complete — approval queue, override logging, rate limiting, resolution flow, anonymous complaints, complaint timeline |
| **Sprint 4** | ✅ Complete | Agent 2 (Laundry) + Agent 3 (Mess) — slot booking, fairness algorithm, mess feedback (5 dimensions), agent routing |
| **Sprint 5** | ✅ Complete | Push notifications, JWT refresh + rotation, no-show penalties, hostel config in DB, all 7 evaluation metrics |
| **Sprint 6** | ✅ Complete | Backend completions — rejection flow, staff account creation, real analytics queries, onboarding flag, pending counts |
| **Sprint 7** | ✅ Complete | Multi-tenant architecture — hostel setup, hostel codes, `hostel_id` on all tables, full data isolation |
| **Sprint 7b** | ✅ Complete | API polish — pagination, search/filter, self-service password change, notice board, mess menu, complaint templates, feedback streak |
| **Production Audit** | ✅ Complete | 2 rounds, 31 fixes — hostel_id isolation, security gaps, cross-hostel access blocked, 8 manual checks passed |
| **Sprint F** | 🔄 In Progress | React PWA frontend — all 23 screens built and wired; live testing + bug fixes in progress |
| **Sprint D** | ⏳ Pending | Docker + Railway deployment |

### Key Bug Fixes Across Sprints

- `passlib` removed — bcrypt used directly (Sprint 1)
- Celery `run_async()` wrapper for async tools in sync Celery context (Sprint 2)
- `GROQ_MODEL_NAME` env var — hardcoded model decommissioned (Sprint 2)
- `db.refresh(obj)` always after `db.commit()` — MissingGreenlet fix (Sprint 3)
- UUID → str `field_validator(mode='before')` on all Pydantic schemas (Sprint 3)
- `hostel_config.created_at` — Python-side default (not `server_default`) for existing column (Sprint F)
- Cross-hostel user management returns 404 (privacy by design) (Audit Round 2)
- `hostel_config` cache keyed by `hostel_id` (Audit Round 1)

---

## 17. Key Engineering Decisions

| Decision | Rationale | Sprint |
|----------|-----------|--------|
| Supervisor Pattern (single Agent 1 entry point) | Consistent triage, logging, and routing across entire system | Planning |
| LangChain over CrewAI | Agents have separate domains; no parallel collaboration needed | Planning |
| Groq + Llama 3 (free tier) | Zero-cost constraint | Planning |
| `passlib` removed; `bcrypt` direct | `passlib` unmaintained; bcrypt 4.x API is clean and direct | Sprint 1 |
| Port 5432 (not 6543) | pgBouncer conflicts with `asyncpg` on async connections | Sprint 1 |
| `run_async()` wrapper in Celery tasks | Celery is synchronous; async tools need bridge | Sprint 2 |
| `VALID_TRANSITIONS` single source of truth | Defined only in `complaint_service.py`; never redefined | Sprint 2 |
| `psycopg2-binary` for Celery | `asyncpg` is async-only; Celery needs sync DB driver | Sprint 2 |
| `db.refresh(obj)` after every `db.commit()` | Prevents SQLAlchemy `MissingGreenlet` errors | Sprint 3 |
| MessFeedback 5 separate columns | More granular than single rating; enables per-dimension trend analysis | Sprint 4 |
| `booking_status` (not `status`) on LaundrySlot | Avoids collision with legacy `status` column | Sprint 4 |
| `hostel_config` in DB (not `.env`) | Wardens must configure thresholds from UI without server access | Sprint 5 |
| Refresh token rotation + theft detection | Revoked token reuse triggers all-session invalidation | Sprint 5 |
| Multi-tenant from Sprint 7 | Single deployment for all hostels; lower infrastructure cost | Sprint 7 |
| Login requires `hostel_code` | Room numbers not globally unique in multi-tenant system | Sprint 7 |
| 404 (not 403) for cross-hostel operations | Privacy by design — 403 would confirm user existence across hostels | Audit |
| 30-second polling (not WebSockets) | Sufficient for V1; significantly lower complexity | V1 Decision |
| Complaint templates hardcoded (no DB table) | Static content; no admin overhead; avoids over-engineering | Sprint 7b |
| Feedback streak on User model | Incentivises daily mess feedback; improves Agent 3 data quality | Sprint 7b |

---

## 18. API Evaluation Metrics

All 7 metrics computed on-demand via `GET /api/analytics/dashboard`.

| Metric | Formula | Acceptable Threshold | Breach Action |
|--------|---------|---------------------|---------------|
| **Misclassification Rate** | Overrides / Total classified (30d rolling) | < 15% | Review classification prompt |
| **Override Rate by Category** | Overrides per category / Total in category | < 20% per category | Reclassify edge cases |
| **False High-Severity Rate** | High-severity downgraded by Warden / Total high-severity | < 10% | Adjust severity prompt criteria |
| **Student-Confirmed Resolution Rate** | Yes confirmations / Total confirmations sent | > 80% | Investigate assignee behaviour |
| **Avg Approval Queue Latency** | Time from queue creation to Warden action (min) | < 20 min avg | Escalate reminders more aggressively |
| **Mess Feedback Participation Rate** | Unique submitters / Total active students (daily) | > 40% | Adjust reminder timing |
| **Laundry No-Show Rate** | No-shows / Total bookings (7d rolling) | < 10% | Review penalty communication |

> **Drift Alert:** If Misclassification Rate > 25% in any 7-day window → dashboard displays: _"AI classification accuracy has dropped. Manual review recommended."_

---

## 19. Failure Modes & Resilience

| Failure | Response | Pattern |
|---------|----------|---------|
| Groq API timeout / 5xx | Celery retries 3× with exponential backoff → `AWAITING_APPROVAL` if all fail | Retry + manual fallback |
| Confidence score parsing fails | Treat as low-confidence → `AWAITING_APPROVAL`. Log raw response. | Parse fallback |
| LLM hallucinates invalid category | Pydantic validation rejects → `AWAITING_APPROVAL` | Schema validation |
| Celery / Redis crash | Complaint written to DB as `AWAITING_APPROVAL` immediately. Student acknowledged. | Sync fallback |
| Prompt injection attempt | Sanitized version classified. Original stored in `flagged_input`. Warden notified. | Sanitize + flag + log |
| Database connection failure | SQLAlchemy retries 3×. If unreachable > 30s → 503. | Connection pool + 503 |
| Push notification failure | Caught and logged. In-app notification always written to DB regardless. | In-app inbox fallback |
| Mess participation collapse | < 15% for 3 consecutive days → Agent 3 alerts Warden. | Participation monitor |

### Rule-Based Fallback Classifier

When LLM fails after all retries, keyword matching classifies the complaint:

| Trigger Keywords | Fallback Classification |
|-----------------|------------------------|
| food, mess, meal, breakfast, lunch, dinner, taste, hygiene | Category: `mess` \| Severity: `medium` |
| laundry, washing, machine, clothes, slot, dryer | Category: `laundry` \| Severity: `medium` |
| water, electricity, fan, light, AC, furniture, door, plumbing | Category: `maintenance` \| Severity: `medium` |
| fight, harassment, threat, abuse, unsafe, scared | Category: `interpersonal` \| Severity: `HIGH` → always `AWAITING_APPROVAL` |
| No match | Category: `uncategorised` \| → `AWAITING_APPROVAL` |

`classified_by="fallback"` set on all fallback-classified complaints.

---

## 20. V2 Roadmap

Explicitly deferred from V1. Do not implement until explicitly instructed.

| Feature | Reason Deferred |
|---------|----------------|
| ERP document upload (college mode verification) | Manual warden approval sufficient for V1 |
| Laundry priority exception flow (medical/unavailability) | Fairness score algorithm sufficient |
| Mess feedback time-window enforcement | Any meal can be rated at any time in V1 |
| Rate limit per-category (vs. global daily limit) | Global 5/day sufficient |
| WebSockets (real-time updates) | 30-second polling sufficient for V1 |
| Multi-hostel management dashboard | Per-hostel management only |
| RAG-enhanced complaint triage (Qdrant) | No external vector DB dependencies in V1 |
| LangGraph migration for Agent 1 | V2 upgrade path documented; schemas already compatible |
| Native iOS/Android app | PWA covers all mobile use cases |
| WhatsApp/SMS integration | API cost constraints |
| Complaint upvoting | Not needed for V1 |
| Roommate info endpoint | Not needed for V1 |
| Lost and found board | Out of scope |
| Visitor log | Out of scope |
| Automated corrective suggestions to Mess Manager | Out of scope |

> **LangGraph upgrade note:** Pydantic schemas and LangChain tool definitions are already LangGraph-compatible. Migrate Agent 1 to a LangGraph state machine when complaint volume grows. No data model changes required.

---

## Golden Rules (For All Contributors & AI Assistants)

1. **Never change working code** just because you would do it differently
2. **Never use `passlib`** — use `hash_password()` and `verify_password()` from `auth_service.py`
3. **DATABASE_URL port is always 5432** — never 6543
4. **Never put logic in routes** — routes call services, services contain logic
5. **Never call the LLM directly from a route or service** — all LLM calls go through `/agents/`
6. **Nothing slow runs synchronously** — everything slow goes through Celery tasks
7. **Never hardcode any config value** — read from `config.py → settings.*`
8. **Never commit `.env`**
9. **Always update `PROJECT_STATE.md`** at the end of every sprint
10. **`VALID_TRANSITIONS` is defined only in `complaint_service.py`** — import, never redefine
11. **Always `await db.refresh(obj)` after `await db.commit()`** before returning ORM objects
12. **Always add UUID → str `field_validator(mode='before')`** to Pydantic schemas
13. **Every new PostgreSQL enum value needs an Alembic migration** before it is used in code
14. **`WARDEN_ROLES = [assistant_warden, warden, chief_warden]`** — all three, always
15. **After Sprint 7: every query must filter by `hostel_id`** — data isolation is mandatory
16. **Login must include `hostel_code`** — room numbers are not globally unique
17. **Notification polling is 30 seconds** — do not implement WebSockets in V1
18. **All list endpoints must support `limit` and `offset`** pagination params

---

*For full product specification: see [PRD.md](PRD.md)*  
*For coding conventions: see [CONVENTIONS.md](CONVENTIONS.md)*  
*For current sprint state: see [PROJECT_STATE.md](PROJECT_STATE.md)*  
*For design system: see [DESIGN.md](DESIGN.md)*
