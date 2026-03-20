# HostelOps AI — Product Requirements Document
**Version:** 2.0 | **Status:** Sprints 1-6 Complete | **Constraint:** Zero-cost, open-source models, free-tier hosted services

---

## Table of Contents
1. [Product Overview](#1-product-overview)
2. [Users & Roles](#2-users--roles)
3. [System Architecture](#3-system-architecture)
4. [Warden & Staff Tools](#4-warden--staff-tools)
5. [Student Experience](#5-student-experience)
6. [Feedback Loop & Evaluation](#6-feedback-loop--evaluation)
7. [Non-Functional Requirements](#7-non-functional-requirements)
8. [Out of Scope (V1)](#8-out-of-scope-v1)
9. [Complaint State Graph](#9-complaint-state-graph)
10. [Failure Modes & Resilience](#10-failure-modes--resilience)
11. [Technology Stack](#11-technology-stack)
12. [Remaining Sprint Plan](#12-remaining-sprint-plan)

---

## 1. Product Overview

### 1.1 What is HostelOps AI?
HostelOps AI is an autonomous operations management system for hostels — both college-affiliated and independent PGs. It replaces the manual, reactive, and inconsistent day-to-day management of complaints, laundry, and mess operations with a structured, AI-driven pipeline that is always-on, fair, and transparent.

The system is built on the **Supervisor Pattern** — a multi-agent architecture where a central orchestrator (Agent 1) receives all inputs, classifies them, and routes them to the appropriate specialized agent or staff member. Human oversight is preserved at every critical decision point.

### 1.2 Problem Statement
Hostel wardens and staff spend a disproportionate amount of time on repetitive, low-value administrative tasks — manually triaging complaints, mediating laundry disputes, and reacting to mess dissatisfaction only after it has already escalated. Students, meanwhile, lack transparency into whether their concerns are being heard or acted upon.

HostelOps AI solves this by automating the routine, escalating the important, and giving every stakeholder a clear and reliable interface for hostel operations.

### 1.3 Core Design Principles
- **Automate the routine, escalate the sensitive** — the AI never makes autonomous decisions about interpersonal or safety-critical issues.
- **Confidence-gated action** — the system acts automatically only when confident. All ambiguous decisions surface to a human for one-tap approval.
- **Full transparency** — every student can track their complaint status. Every warden can see operations health at a glance.
- **Fairness by design** — resource allocation (laundry) is governed by an explicit scoring algorithm, not first-come-first-serve.
- **Zero-cost infrastructure** — open-source models, free-tier hosted services. No paid APIs. Self-hosting paths documented for every service.
- **Role-based and verified** — every user is authenticated and verified before accessing the system.

### 1.4 Hostel Modes

| Mode | Onboarding Requirements |
|------|------------------------|
| **College Hostel Mode** | Student registers with Name, Room Number, Hostel Code, and College Roll Number. Assistant Warden verifies and approves before access is granted. |
| **Autonomous Hostel / PG Mode** | Student registers with Name, Room Number, and Hostel Code only. Assistant Warden manually verifies and approves. |

> In both modes, no student account is active until a human (Assistant Warden) has reviewed and approved it. Ghost accounts must be deactivated by the Assistant Warden when a student vacates.

#### Deployment Model (Multi-tenant)
HostelOps AI is a **single deployment serving multiple hostels**. Each hostel is identified by a unique **hostel code** (e.g. `IGBH-4821`).

**Warden setup flow (first time):**
1. Warden goes to the app URL
2. Clicks "Set up my hostel" → fills hostel name, mode, floors, account details
3. System generates unique hostel code — e.g. `IGBH-4821`
4. Warden sees: "Your hostel code is **IGBH-4821** — share this with your students"
5. Warden dashboard is live

**Student registration flow:**
1. Student opens the same app URL
2. Clicks "Register" → enters name, room number, password, hostel code
3. System validates code, links student to correct hostel
4. Student sees "Registration Pending" screen
5. Warden approves → student can log in

#### Hostel Configuration
All operational thresholds are stored in the `hostel_config` table — not in `.env`. Wardens can update them from the Hostel Settings screen. Defaults are seeded by `create_admin.py`.

---

## 2. Users & Roles

### 2.1 Role Definitions

| Role | Type | Key Responsibilities |
|------|------|---------------------|
| Student | End user | File complaints, book laundry slots, submit mess feedback, track complaint status |
| Laundry Man | Operational staff | Receive laundry complaint assignments, mark slots complete, manage machine status |
| Mess Secretary | Operational staff | Receive mess complaint assignments from Agent 1 routing |
| Mess Manager | Supervisory staff | Receive mess dissatisfaction alerts from Agent 3, publish mess menu |
| Assistant Warden | Administrative staff | Verify/approve/reject student registrations, deactivate accounts, receive maintenance complaint assignments |
| Warden | Supervisory authority | Receive escalated complaints, approve AI-uncertain decisions via approval queue, receive urgent alerts |
| Chief Warden | Top authority | Receive only critical or escalated unresolved complaints — final escalation point |

### 2.2 Authentication & Access Control

**Student registration flow:**
1. Student registers with name, room number, password, hostel code (+ roll number in college mode)
2. Account is inactive until warden approves
3. Warden can reject with a reason — student sees the reason and can re-register
4. Approved students receive push + in-app notification
5. On first login: onboarding walkthrough shown once (`has_seen_onboarding` flag on user)

**Staff account creation:**
- Only wardens can create staff accounts (laundry_man, mess_secretary, mess_manager, assistant_warden)
- Created via warden dashboard → immediately active (no approval needed)
- Staff change their temporary password via `PATCH /api/users/me/password`

**Password reset:**
- Students cannot self-reset passwords (no email required in V1)
- Warden resets via `PATCH /api/users/{id}/reset-password`
- Resets password + revokes all refresh tokens + notifies student

**Account deactivation:**
- When student vacates, warden deactivates their account
- Deactivated student sees: "Your account has been deactivated. Contact your warden."
- Not the generic 401 error

**Rate limiting:**
- Complaint filing: max 5 per student per day (enforced per hostel via hostel_config)
- Wardens and staff are never rate limited on complaint endpoints

---

## 3. System Architecture

### 3.1 Architecture Overview — The Supervisor Pattern

> **KEY PRINCIPLE:** Every student interaction enters through Agent 1. Nothing bypasses the orchestrator. This ensures consistent triage, logging, and routing across the entire system.

HostelOps AI uses the Supervisor Pattern. Agent 1 is the single entry point. It orchestrates the system by classifying incoming data and routing to the correct downstream agent or staff member. Agents 2 and 3 are specialized sub-agents that also receive routed inputs from Agent 1.

### 3.2 High-Level Data Flow

1. Student submits a complaint OR books a laundry slot OR submits mess feedback via the PWA.
2. All complaints enter Agent 1 (Orchestrator). Laundry bookings go directly to Agent 2. Mess ratings go directly to Agent 3.
3. Agent 1 classifies by category and severity. Mess complaints → Agent 3. Laundry complaints → Agent 2. All others → Agent 1 assigns directly.
4. If confidence is high, Agent 1 acts automatically. If confidence is low or severity is high, it surfaces to the Warden's approval queue.
5. Student receives automatic acknowledgement immediately.
6. Assigned staff member receives an in-app notification + push notification via the PWA.
7. All warden override decisions are logged for continuous improvement.
8. Complaint status lifecycle: INTAKE → CLASSIFIED → ASSIGNED/AWAITING_APPROVAL → IN_PROGRESS → RESOLVED. Student confirms resolution.

---

### 3.3 Agent 1 — Complaint & Routing Agent (Orchestrator)

**Purpose:** Receives all student complaints. Classifies by category and severity. Routes to the right agent or staff. Acknowledges the student. Escalates to human approval when uncertain.

#### Complaint Categories & Routing

| Complaint Type | Category | Routing Target |
|---------------|----------|---------------|
| Food quality, mess hygiene, menu, timing | Mess-related | Routed to Agent 3 → Mess Manager / Mess Secretary |
| Laundry machine, missing clothes, slot issues | Laundry-related | Routed to Agent 2 → Laundry Man |
| Room maintenance, electrical, plumbing, furniture | Maintenance | Assigned to Assistant Warden |
| Student conflict, harassment, misconduct | Interpersonal / Sensitive | Escalated directly to Warden — NEVER auto-assigned |
| Critical unresolved, safety, severe infrastructure | Critical | Escalated to Chief Warden after Warden review |

#### Severity Classification

| Severity | Examples | Action |
|----------|----------|--------|
| **Low** | Fan noise, cold food, minor inconvenience | Auto-assign, acknowledge student. No warden alert. |
| **Medium** | Machine broken, bathroom unclean 2+ days | Auto-assign, acknowledge student, passive warden notification. |
| **High** | No water overnight, food poisoning, harassment | DO NOT auto-assign. Surface to Warden approval queue immediately. |

#### Confidence-Gated Action
- **High confidence + Low/Medium severity** → Act automatically. Assign, acknowledge, notify staff.
- **High confidence + High severity** → NEVER auto-assign. Always escalate to Warden approval queue.
- **Low confidence (any severity)** → Surface to Warden approval queue with best-guess pre-filled.

Confidence threshold is configurable via `hostel_config.complaint_confidence_threshold` (default: 0.85).

#### Anonymous Complaints
- All staff see `Anonymous Student` instead of the student's name.
- Wardens (warden, chief_warden, assistant_warden) retain ability to view actual identity.
- Anonymous complaints are classified and routed identically to named complaints.

#### Complaint Templates (Sprint 7b)
Common complaint types are available as quick-fill templates to reduce student friction. Examples: "Fan not working", "Water not coming", "Bathroom light fused". Students can tap a template to pre-fill the complaint text.

---

### 3.4 Agent 2 — Laundry Allocation Agent

**Purpose:** Manages laundry slot booking calendar. Enforces fairness rules. Handles machine breakdowns and priority requests. Receives laundry complaints from Agent 1.

#### Slot System Rules
- One active booking per student per day.
- No-show penalty: 48-hour priority reduction (multiplier 0.1) after a no-show without cancellation.
- Cancellation without penalty: up to `hostel_config.laundry_cancellation_deadline_minutes` (default 15 mins) before slot start.
- Late cancellation: same priority penalty as no-show.

#### Laundry Fairness Algorithm

Priority score = `min(days_since_last_booking, 30) × penalty_multiplier`
- New students start with score 1.0 (maximum)
- No-show in last 48 hours: `penalty_multiplier = 0.1`
- Otherwise: `penalty_multiplier = 1.0`
- Score is computed per-request, never stored permanently

Students with score ≥ 20 (4+ days since last wash) have first 2 slots highlighted as "Available for you" — a UI nudge, NOT a hard reservation.

#### Machine Breakdown Sequence
1. Student files laundry complaint → Agent 1 routes to Agent 2
2. Machine marked `under_repair` immediately
3. All future booked slots for affected machine cancelled
4. Affected students notified via push + in-app
5. Laundry Man notified
6. Machine resumes bookings when Laundry Man marks it repaired

---

### 3.5 Agent 3 — Mess Feedback & Dissatisfaction Monitor

**Purpose:** Collects structured mess feedback. Monitors satisfaction trends across 5 dimensions. Detects chronic dissatisfaction and sudden spikes. Alerts Warden and Mess Manager proactively.

#### Feedback Data Pipeline
Students submit feedback through a dedicated section in the PWA. Students select the meal: **Breakfast / Lunch / Dinner**. Once submitted, that meal's option shows a confirmation tick. All three options reset at midnight every day.

Feedback dimensions (1–5 each):
- Food Quality
- Food Quantity  
- Hygiene / Cleanliness
- Menu Variety
- Timing & Availability

Optional one-line comment (max 300 chars). One submission per meal per student per day enforced server-side.

#### Feedback Streak (Sprint 7b)
`feedback_streak` counter on User model. Increments when student submits any feedback for the day. Resets if they miss a day. Shown in student profile as a motivator for consistent participation.

#### Mess Menu (Sprint 7b)
Mess Manager publishes the current menu anytime (not locked to weekly schedule). Menu has a `valid_from` date — always shows the most recent menu. History kept for Agent 3 correlation. Students see today's menu in the Mess section.

#### Dissatisfaction Detection Logic

> **CHRONIC PATTERN:** Any single dimension rated below `hostel_config.mess_alert_threshold` (default 2.5/5) for 3+ consecutive meals triggers a chronic alert.

> **INCIDENT SPIKE:** Any dimension dropping by 1.5 from its 7-day rolling average in a single meal triggers an immediate alert — even if absolute score isn't critically low.

If daily participation drops below `hostel_config.mess_min_participation` (default 15%) for 3 consecutive days → Warden alerted.

#### Alert Behaviour
- Below `mess_alert_threshold` → alerts Mess Manager
- Below `mess_critical_threshold` (default 2.0) → also alerts Assistant Warden
- All alerts sent via in-app + push notifications

---

## 4. Warden & Staff Tools

### 4.1 Approval Queue
- Shows all complaints awaiting human decision
- Each item shows: complaint text, AI suggestion (category/severity/assignee), confidence score, time in queue
- Time in queue turns amber at 15 mins, red at 30 mins
- Warden can: approve as-is, or override with corrected values + reason
- Auto-escalates after `hostel_config.approval_queue_timeout_minutes` (default 30 mins) — Celery beat task

### 4.2 Notice Board (Sprint 7b)
Wardens post announcements visible to all students in the hostel. Students see notices on their home screen. Push notification sent when a new notice is published.

Examples: "Water supply cut tomorrow 8am-12pm", "Holiday on Friday", "New laundry rules"

### 4.3 Warden Dashboard Metrics
All 7 evaluation metrics computed on-demand:
1. Misclassification rate (overrides / total classified, rolling 30d)
2. Override rate by category
3. False high-severity rate
4. Student-confirmed resolution rate
5. Avg approval queue latency
6. Mess feedback participation rate
7. Laundry no-show rate

**Drift alert:** If misclassification rate > 25% in any 7-day window → banner displayed: "AI classification accuracy has dropped. Manual review recommended."

Dashboard also shows:
- `pending_registrations` count
- `pending_approval_queue` count

### 4.4 Hostel Settings
All thresholds configurable from Settings screen — no `.env` editing required:
- Hostel name, mode, total floors
- Complaint confidence threshold
- Approval queue timeout
- Mess alert/critical thresholds
- Laundry slot hours, no-show penalty, cancellation deadline

---

## 5. Student Experience

### 5.1 Complaint Filing
1. Student opens PWA → navigates to "File Complaint"
2. Optionally selects a complaint template (Sprint 7b) or types free-text (min 10 chars, max 1000 chars)
3. Optionally toggles "Submit Anonymously"
4. Submits → receives immediate acknowledgement
5. Complaint appears in personal tracker with status: Registered

### 5.2 Complaint Status Tracker

| Status | Meaning |
|--------|---------|
| **Registered** | Received by system. Awaiting classification and assignment. |
| **Assigned** | Classified and assigned to staff. Staff notified. |
| **In Progress** | Staff has acknowledged and is working on it. |
| **Resolved** | Staff marked as resolved. Student prompted to confirm. |
| **Reopened** | Student marked as unresolved. Reopened with elevated priority. |
| **Escalated** | Elevated to Warden or Chief Warden. |

When marked Resolved → student receives: "Was your issue resolved?" with Yes/No. If No → complaint reopens with elevated priority (`is_priority=True`) and Warden notified.

### 5.3 Laundry Booking
1. Student opens "Book Laundry Slot"
2. Date strip + machine tabs shown. Slots as grid (green=available, grey=taken, blue=yours, red=repair)
3. Student selects a slot → confirmation bottom sheet
4. Cancel up to `laundry_cancellation_deadline_minutes` before start — no penalty
5. Late cancellation or no-show triggers 48-hour priority penalty

### 5.4 Mess Feedback
Dedicated section, always accessible. Students select meal → rate 5 dimensions with stars → optional comment → submit. Submitted meals show green tick. All reset at midnight.

#### Feedback Streak
Student profile shows how many consecutive days they've submitted feedback. Motivates daily participation which improves Agent 3 data quality.

### 5.5 Mess Menu (Sprint 7b)
Students see the current active mess menu in the Mess section. Published by Mess Manager anytime. Shows what's being served today for breakfast, lunch, and dinner.

### 5.6 Notice Board (Sprint 7b)
Students see warden announcements on their home screen. New notices trigger push notifications. Notices remain visible until warden removes them.

### 5.7 First Login Onboarding
Shown exactly once per account after first approved login. 3-step walkthrough:
- Step 1: "File complaints — track everything from here"
- Step 2: "Book laundry slots — fair and transparent"
- Step 3: "Rate your mess — your feedback drives improvements"

`has_seen_onboarding` flag on User model. Once shown, never shown again.

---

## 6. Feedback Loop & Evaluation

### 6.1 Override Logging
Every Warden correction stored with: original complaint text, AI classification, human correction, override reason (dropdown: Wrong Category / Wrong Assignee / Wrong Severity / Other), and timestamp. Foundation for model improvement.

### 6.2 Evaluation Metrics

| Metric | Formula | Acceptable Threshold | Action if Breached |
|--------|---------|---------------------|-------------------|
| Misclassification Rate | Overrides / Total classified (rolling 30d) | < 15% | Review and refine classification prompt |
| Override Rate by Category | Overrides per category / Total in category | < 20% per category | Reclassify edge cases for that category |
| False High-Severity Rate | High-severity downgraded by Warden / Total high-severity | < 10% | Adjust severity prompt criteria |
| Student-Confirmed Resolution Rate | Yes responses / Total confirmations sent | > 80% | Investigate assignee behaviour |
| Avg Approval Queue Latency | Time from queue creation to Warden action (min) | < 20 min avg | Send escalation reminders more aggressively |
| Mess Feedback Participation Rate | Unique submitting / Total active students (daily) | > 40% daily | Adjust reminder timing |
| Laundry No-Show Rate | No-shows / Total bookings (rolling 7d) | < 10% | Review penalty communication |

> **DRIFT ALERT:** If Misclassification Rate exceeds 25% in any 7-day rolling window → dashboard displays banner: *"AI classification accuracy has dropped. Manual review recommended."*

### 6.3 Periodic Model Review
Monthly review of override log + evaluation metrics. Patterns of consistent misclassification → iterate on classification prompt. No retraining required — prompt iteration only.

---

## 7. Non-Functional Requirements

### 7.1 Technology Constraints

| Layer | Choice | Self-Host Alternative |
|-------|--------|-----------------------|
| LLM | Groq free tier + llama-3.3-70b-versatile | vLLM running Llama 3 on local hardware |
| Backend | Python + FastAPI + Pydantic v2 + SQLAlchemy + Alembic | — |
| Agent Orchestration | LangChain (V1) — LangGraph (V2 upgrade path) | — |
| Frontend | React 18 + TypeScript + Vite + PWA + Tailwind + Shadcn/UI | — |
| Database | PostgreSQL via Supabase free tier | PostgreSQL on any VPS or Docker |
| Task Queue | Celery + Upstash Redis free tier | Redis on Docker |
| Hosting | Railway free tier | Docker Compose on any Linux server |
| Auth | JWT via python-jose + bcrypt (direct, NOT passlib) | — |
| Push Notifications | Web Push API (pywebpush) | — |

> **NOTE:** passlib was removed from the project. Never use it. Use `hash_password()` and `verify_password()` from `auth_service.py` which use bcrypt directly.

> **LLM NOTE:** `llama3-8b-8192` was decommissioned by Groq in March 2026. Current model: `llama-3.3-70b-versatile`. Always use `settings.GROQ_MODEL_NAME` — never hardcode.

### 7.2 Performance Expectations
- Complaint acknowledgement to student: within 5 seconds of submission
- Classification and routing (high-confidence): within 10 seconds
- Approval queue surfacing: within 10 seconds of submission
- Push notifications for staff assignments: within 30 seconds
- Mess alert generation after threshold crossed: within 5 minutes
- In-app notification refresh: within 30 seconds (polling)

### 7.3 Security
- **Prompt Injection Detection** — pre-processing strips injection patterns. Flagged inputs logged. Original stored in `flagged_input` field.
- **Input Sanitization** — all string inputs trimmed, length-capped, HTML-escaped.
- **Rate Limiting** — per-user, configurable via hostel_config. Wardens never rate limited.
- **Audit Logs** — every state-changing action written to audit log with user ID, action, timestamp, IP address.
- **JWT Rotation** — access tokens expire after 24 hours. Refresh tokens expire after 30 days. Token rotation on every refresh. Revoked token reuse triggers all-session invalidation.
- **HTTPS Enforced** — Railway enforces HTTPS.
- **Anonymous complaint identity** — accessible only to Warden roles.
- **Password Reset** — warden-only in V1. No self-service (no email field required).
- **CORS** — locked to frontend URL only in production (Sprint D).

---

## 8. Out of Scope (V1)

**Deferred to V2:**
- ERP document upload (file upload for college mode verification — manual warden approval is sufficient for V1)
- Laundry priority exception flow (medical/unavailability requests — fairness score alone is sufficient for V1)
- Laundry no-show detection frequency improvement (currently hourly — acceptable for V1)
- Mess feedback time-window enforcement (any meal can be rated at any time in V1)
- Rate limit per-category (currently global 5/day — per-category deferred)
- WebSockets for real-time updates (30-second polling is sufficient for V1)
- Multi-hostel management dashboard (single-hostel management only per warden)
- RAG-enhanced complaint triage (Qdrant vector memory — no external dependencies in V1)
- LangGraph migration (documented upgrade path, not implemented in V1)
- Native mobile app (iOS/Android) — PWA covers all mobile use cases
- WhatsApp/SMS integration — API cost constraints
- Offline functionality — requires active internet connection
- Complaint upvoting
- Roommate info endpoint
- Lost and found board
- Visitor log
- Automated corrective action suggestions to Mess Manager

---

## 9. Complaint State Graph

### 9.1 States

| State | Definition |
|-------|-----------|
| `INTAKE` | Received and acknowledged. Classification not yet complete. |
| `CLASSIFIED` | LLM returned a classification. High-confidence non-sensitive → ASSIGNED. Others → AWAITING_APPROVAL. |
| `AWAITING_APPROVAL` | In Warden's approval queue. No assignment made. Awaiting human confirmation. |
| `ASSIGNED` | Assigned to a staff member. Staff notified. |
| `IN_PROGRESS` | Staff acknowledged and is actively working on it. |
| `RESOLVED` | Staff marked resolved. Student prompted for confirmation. |
| `REOPENED` | Student confirmed unresolved. Back in queue with elevated priority (`is_priority=True`). |
| `ESCALATED` | Elevated to Warden or Chief Warden due to severity, sensitivity, or inaction. |

### 9.2 Valid Transitions

| Transition | Trigger |
|-----------|---------|
| `INTAKE → CLASSIFIED` | LLM classification completes successfully |
| `INTAKE → ESCALATED` | LLM fails after all retries — fallback to manual |
| `CLASSIFIED → ASSIGNED` | High-confidence, non-sensitive — auto-assigned |
| `CLASSIFIED → AWAITING_APPROVAL` | Low confidence OR high severity |
| `AWAITING_APPROVAL → ASSIGNED` | Warden approves or corrects AI suggestion |
| `AWAITING_APPROVAL → ESCALATED` | Warden escalates directly OR queue item unreviewed > timeout |
| `ASSIGNED → IN_PROGRESS` | Staff acknowledges in their dashboard |
| `ASSIGNED → ESCALATED` | Sits in ASSIGNED for > 24 hours without IN_PROGRESS — auto-escalates |
| `IN_PROGRESS → RESOLVED` | Staff marks resolved |
| `RESOLVED → REOPENED` | Student taps No on resolution confirmation |
| `REOPENED → ASSIGNED` | Re-assigned with elevated priority. Warden notified. |
| `ESCALATED → ASSIGNED` | Chief Warden / Warden manually assigns |

> **IMPLEMENTATION NOTE:** `transition_complaint(complaint_id, from_state, to_state, triggered_by, db, ip_address)` in `complaint_service.py` is the ONLY place complaint.status is updated. VALID_TRANSITIONS dict is defined only here. Pass `ip_address` from `request.client.host` always.

---

## 10. Failure Modes & Resilience

### 10.1 Design Philosophy
HostelOps AI must degrade gracefully under every failure condition. The fallback chain is always: **retry → rule-based fallback → manual escalation**. The system must never fail silently.

### 10.2 Failure Scenarios & Responses

| Failure Scenario | Response | Pattern |
|-----------------|----------|---------|
| Groq API timeout or 5xx | Celery retries up to 3 times with exponential backoff. If all fail → AWAITING_APPROVAL. Warden notified. | Retry + manual fallback |
| Confidence score parsing fails | Treat as low-confidence → AWAITING_APPROVAL. Log raw response. Never crash. | Parse fallback |
| LLM hallucinates invalid category | Pydantic validation rejects. Complaint routes to AWAITING_APPROVAL. | Schema validation |
| Celery / Redis crash | Complaint written to DB as AWAITING_APPROVAL immediately. Student acknowledged. | Sync fallback |
| Prompt injection attempt | Sanitized version classified. Original stored in `flagged_input`. Warden notified passively. | Sanitize + flag + log |
| Database connection failure | SQLAlchemy retries 3 times. If unreachable > 30s → 503. | Connection pool + 503 |
| Push notification delivery failure | Caught and logged. In-app notification always written to DB regardless. | In-app inbox fallback |
| Mess feedback participation collapse | If < 15% for 3 consecutive days → Agent 3 alerts Warden. | Participation monitor |

### 10.3 Rule-Based Fallback Classifier

| Trigger Keywords | Fallback Classification |
|-----------------|------------------------|
| food, mess, meal, breakfast, lunch, dinner, cook, taste, hygiene | Category: mess \| Severity: medium |
| laundry, washing, machine, clothes, slot, dryer | Category: laundry \| Severity: medium |
| water, electricity, fan, light, AC, furniture, door, window, plumbing | Category: maintenance \| Severity: medium |
| fight, harassment, threat, abuse, unsafe, scared, uncomfortable | Category: interpersonal \| Severity: HIGH \| → AWAITING_APPROVAL always |
| No keyword match | Category: uncategorised \| Severity: medium \| → AWAITING_APPROVAL |

`classified_by="fallback"` always set on the complaint record.

---

## 11. Technology Stack

### 11.1 Complete Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| Frontend | React 18 + TypeScript + Vite + PWA + Tailwind + Shadcn/UI | Sprint F |
| Backend | Python + FastAPI + Pydantic v2 + SQLAlchemy + Alembic | Sprints 1-6 complete |
| Agent Orchestration | LangChain | LangGraph is V2 upgrade path |
| LLM | Groq free tier + llama-3.3-70b-versatile | llama3-8b-8192 decommissioned March 2026 |
| Task Queue | Celery + Upstash Redis (free tier) | Windows dev: --pool=solo |
| Database | PostgreSQL via Supabase (free tier) | Port 5432 always, never 6543 |
| Auth | JWT via python-jose + bcrypt (direct) | passlib removed |
| Hosting | Railway | Docker Compose on Sprint D |
| Push Notifications | Web Push API (pywebpush) | VAPID keys required |
| Config | python-dotenv + pydantic-settings | All secrets in .env |

> **LANGGRAPH UPGRADE PATH:** The Pydantic schemas and tool definitions are already LangGraph-compatible. When complaint volume grows — migrate Agent 1 to a LangGraph state machine. No data model changes required.

### 11.2 Deployment Modes

**Development:** uvicorn + celery --pool=solo locally. Supabase + Upstash free tier. No Docker needed.

**Production (Sprint D):** Docker Compose on Railway or any Linux server. CORS locked to frontend URL.

> **Railway free tier note:** Sleeps after inactivity. Use UptimeRobot (free) to ping every 5 minutes, or Railway hobby plan ($5/month).

---

## 12. Remaining Sprint Plan

### Sprint 7 — Multi-tenant Architecture
- `hostels` table with unique hostel code generation
- `hostel_id` added to all relevant tables (users, complaints, slots, feedback, etc.)
- Data isolation on every query — users only see their hostel's data
- `POST /api/hostels/setup` — warden creates hostel, gets code
- `GET /api/hostels/{code}/info` — public, returns hostel name + mode
- Student registration accepts `hostel_code` field
- Alembic migrations for all changes

### Sprint 7b — API Polish + New Features
**API completeness:**
- Pagination on all list endpoints (limit + offset)
- Consistent error format audit — all errors: `{ "detail": "string" }`
- `GET /api/users` for wardens with filters
- `GET /api/complaints` search + filter for wardens
- `PATCH /api/users/me/password` self-service password change
- Response model audit — every route has explicit response_model
- Past date validation on laundry booking
- Complaint minimum length (10 chars)
- Timezone fix on all datetime responses
- `GET /health` endpoint
- Document 30s polling convention in CONVENTIONS.md

**New features:**
- Mess menu (POST/GET /api/mess/menu/*)
- Notice board (POST/GET/DELETE /api/notices)
- Complaint templates (GET /api/complaints/templates)
- Feedback streak counter on User model

### Sprint F — React PWA Frontend
Full React 18 + TypeScript + Vite + Tailwind + Shadcn/UI build.
Design system: Clash Display + General Sans, Indigo primary, Saffron accent, Jade success, Vermillion danger.
All 20 screens per Stitch design brief.

### Sprint D — Docker + Deployment
- Docker + docker-compose for full stack
- Railway one-click deploy button on GitHub README
- CORS locked to frontend URL
- Environment variable documentation
- Landing/marketing page at root URL
- Production checklist

### V2 Deferrals
ERP document upload, laundry priority exceptions, mess time-window enforcement, rate limit per-category, WebSockets, multi-hostel dashboard, RAG (Qdrant), LangGraph, native mobile app, WhatsApp/SMS, complaint upvoting, roommate info, lost and found, visitor log.