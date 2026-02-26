# HostelOps AI — Product Requirements Document
**Version:** 1.1 | **Status:** Build Ready | **Constraint:** Zero-cost, open-source models, free-tier hosted services

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
12. [Open Decisions — Next Phase](#12-open-decisions--next-phase)

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
| **College Hostel Mode** | Student registers with Name, Room Number, College Roll Number, and uploads their ERP sheet. Assistant Warden verifies and approves before access is granted. |
| **Autonomous Hostel / PG Mode** | Student registers with Name and Room Number only. Assistant Warden manually verifies and approves. No document upload required. |

> In both modes, no student account is active until a human (Assistant Warden) has reviewed and approved it. Ghost accounts must be deactivated by the Assistant Warden when a student vacates.

---

## 2. Users & Roles

### 2.1 Role Definitions

| Role | Type | Key Responsibilities |
|------|------|---------------------|
| Student | End user | File complaints, book laundry slots, submit mess feedback, track complaint status |
| Laundry Man | Operational staff | Receive laundry complaint assignments, mark machines as repaired |
| Mess Secretary | Operational staff | Receive mess complaint assignments from Agent 1 routing |
| Mess Manager | Supervisory staff | Receive mess dissatisfaction alerts from Agent 3 |
| Assistant Warden | Administrative staff | Verify/approve student registrations, deactivate accounts, receive maintenance complaint assignments |
| Warden | Supervisory authority | Receive escalated complaints, approve AI-uncertain decisions via approval queue, receive urgent alerts |
| Chief Warden | Top authority | Receive only critical or escalated unresolved complaints — final escalation point |

### 2.2 Authentication & Access Control
- Students must be registered and verified before accessing any feature.
- Staff accounts are created by the system administrator during hostel setup.
- A student account is activated only after the Assistant Warden reviews and approves the registration.
- When a student vacates, the Assistant Warden deactivates their account.
- Rate limiting enforced at account level: one complaint per category per day per student.

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
6. Assigned staff member receives an in-app notification via the PWA.
7. All warden override decisions are logged for continuous improvement.
8. Complaint status lifecycle: Registered → Assigned → In Progress → Resolved. Student confirms resolution.

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
- **High confidence + High severity** → NEVER auto-assign. Always escalate to Warden approval queue regardless of confidence.
- **Low confidence (any severity)** → Surface to Warden approval queue with best-guess pre-filled. Warden approves or corrects with one tap.

Confidence threshold is configurable via `COMPLAINT_CONFIDENCE_THRESHOLD` env variable. Recommended starting value: `0.85`.

#### Agent 1 Tools — Typed Action Definitions

| Tool Name | Pydantic Signature | Purpose |
|-----------|-------------------|---------|
| `assign_complaint_tool` | Input: `complaint_id (str), assignee_id (str), severity (enum), category (enum)` → Output: `AssignmentResult(success: bool, notified: bool, assigned_at: datetime)` | Assigns complaint to staff, triggers notification, updates status. |
| `escalate_complaint_tool` | Input: `complaint_id (str), escalation_target (enum: warden/chief_warden), reason (str)` → Output: `EscalationResult(success: bool, queue_item_id: str)` | Moves complaint to approval queue or Chief Warden. |
| `request_human_approval_tool` | Input: `complaint_id (str), ai_category (enum), ai_severity (enum), ai_assignee_id (str), confidence (float)` → Output: `ApprovalRequest(queue_item_id: str, created_at: datetime)` | Creates approval queue item for Warden. |
| `acknowledge_student_tool` | Input: `complaint_id (str), student_id (str), is_anonymous (bool)` → Output: `AcknowledgementResult(success: bool, message: str)` | Sends immediate acknowledgement. ALWAYS called first regardless of classification. |
| `route_to_agent_tool` | Input: `complaint_id (str), target_agent (enum: laundry/mess), complaint_text (str), category (enum)` → Output: `RoutingResult(success: bool, agent_received: bool)` | Hands off to Agent 2 or Agent 3. |
| `log_override_tool` | Input: `complaint_id (str), warden_id (str), original (ClassificationSnapshot), corrected (ClassificationSnapshot), reason (enum)` → Output: `LogResult(log_id: str)` | Records every warden correction. |

#### Anonymous Complaints
- All staff see `Anonymous Student` instead of the student's name.
- The Warden retains ability to view actual identity for sensitive/critical complaints.
- Anonymous complaints are classified and routed identically to named complaints.

#### Abuse Prevention
- Maximum one complaint per category per day per student.
- Suspicious patterns (repeated high-severity in short windows) are flagged to the Warden passively.

#### Override Logging
Every Warden correction is stored with: original complaint text, AI classification, human correction, override reason (dropdown: Wrong Category / Wrong Assignee / Wrong Severity / Other), and timestamp.

---

### 3.4 Agent 2 — Laundry Allocation Agent

**Purpose:** Manages laundry slot booking calendar. Enforces fairness rules. Handles no-shows, machine breakdowns, and priority exceptions. Receives laundry complaints from Agent 1.

#### Slot System Rules (enforced invisibly)
- One active booking per student at any time.
- Maximum one slot per student per day.
- No-show penalty: 48-hour priority reduction after a no-show without cancellation.
- Cancellation without penalty: up to 15 minutes before slot start.

#### Laundry Fairness Algorithm — Explicit Implementation

> **IMPLEMENTATION NOTE:** The fairness score is computed per-request, NEVER stored. Implement as a pure function: `calculate_fairness_score(student_id: str, db: AsyncSession) -> float` in `/backend/services/laundry_service.py`

1. Retrieve student's `last_laundry_date` from `LaundrySlot` table (most recent completed slot).
2. Calculate `days_since_last_wash = today - last_laundry_date`. If no history, treat as 30 (maximum weight).
3. Calculate `noshow_penalty`: if student has a no-show in last 48 hours → `penalty_multiplier = 0.1`. Otherwise `penalty_multiplier = 1.0`.
4. Calculate `fairness_score = min(days_since_last_wash, 30) * penalty_multiplier`. Range: 0–30.
5. Display available slots sorted by time ascending (standard for all students).
6. Students with `fairness_score >= 20` (4+ days since last wash) have first 2 available slots highlighted as "Available for you" — a UI nudge, NOT a hard reservation.
7. Students with priority approval bypass fairness score entirely — all slots highlighted until priority booking completes.

#### Priority Exception Handling
Two valid triggers only:
- **Medical necessity** — verified by Warden via one-tap approval.
- **Extended unavailability** — student hasn't booked in 4+ consecutive days due to full capacity. System detects automatically and flags to Warden.

Priority is NEVER self-granted. Every request requires a short reason (entered in app) + explicit Warden approval.

#### Machine Breakdown Sequence (auto-triggered when laundry complaint received from Agent 1)
1. Pause all new bookings for affected machine immediately.
2. Notify all students with upcoming bookings via PWA push — offer rebooking on available machine(s).
3. Notify Laundry Man via in-app notification.
4. Resume bookings automatically once Laundry Man marks machine repaired.

#### Agent 2 Tools — Typed Action Definitions

| Tool Name | Pydantic Signature | Purpose |
|-----------|-------------------|---------|
| `book_slot_tool` | Input: `student_id (str), machine_id (str), date (date), start_time (time), end_time (time)` → Output: `BookingResult(success: bool, slot_id: str, confirmation_sent: bool)` | Books slot after fairness check. Enforces one-per-day and one-active-booking rules. |
| `cancel_slot_tool` | Input: `slot_id (str), student_id (str), cancelled_at (datetime)` → Output: `CancellationResult(success: bool, penalty_applied: bool)` | Cancels booking. Applies no-show penalty if within 15 min or post-slot. |
| `pause_machine_tool` | Input: `machine_id (str), reason (str), reported_by (str)` → Output: `PauseResult(success: bool, affected_bookings: list[str])` | Pauses bookings for a machine. Returns affected booking IDs. |
| `resume_machine_tool` | Input: `machine_id (str), repaired_by (str)` → Output: `ResumeResult(success: bool, bookings_resumed: int)` | Marks machine repaired and reopens for bookings. |
| `flag_priority_request_tool` | Input: `student_id (str), reason (str), trigger (enum: medical/unavailability)` → Output: `PriorityRequest(queue_item_id: str, created_at: datetime)` | Sends priority request to Warden approval queue. |

---

### 3.5 Agent 3 — Mess Feedback & Dissatisfaction Monitor

**Purpose:** Collects structured mess feedback. Monitors satisfaction trends across 5 dimensions. Detects chronic dissatisfaction and sudden spikes. Alerts Warden and Mess Manager proactively. Ingests mess complaints from Agent 1 as additional signal.

#### Feedback Data Pipeline
Students submit feedback through a dedicated section in the PWA (always accessible, not just notification-triggered). Students first select the meal: **Breakfast / Lunch / Dinner**. Each option is active only during/after its meal period. Once submitted, that meal's option is greyed out with a confirmation tick. **All three options reset at midnight every day.**

Feedback dimensions (1–5 stars each):
- Food Quality
- Food Quantity
- Hygiene / Cleanliness
- Menu Variety
- Timing & Availability

Optional one-line free-text comment. One submission per meal per student per day enforced server-side.

#### Dissatisfaction Detection Logic

> **CHRONIC PATTERN:** Any single dimension rated below `MESS_DISSATISFACTION_THRESHOLD` (default: 2.5/5) for 3+ consecutive meals triggers a chronic alert. Alert includes: dimension, average score, response count, top complaints.

> **INCIDENT SPIKE:** Any dimension dropping by `MESS_SPIKE_DELTA` (default: 1.5) from its 7-day rolling average in a single meal triggers an immediate alert — even if absolute score isn't critically low.

If daily participation drops below 15% for 3 consecutive days, Agent 3 alerts the Warden: *"Feedback participation critically low — data may be insufficient."*

#### Alert Behaviour
- All alerts sent to both Warden and Mess Manager simultaneously via in-app notification.
- Alerts include: scores, participation count, trend data, related complaints from Agent 1.
- Agent does NOT prescribe corrective action — data only, Mess Manager decides.

#### Agent 3 Tools — Typed Action Definitions

| Tool Name | Pydantic Signature | Purpose |
|-----------|-------------------|---------|
| `ingest_feedback_tool` | Input: `student_id (str), meal (enum), date (date), ratings (MessRatings), comment (str\|None)` → Output: `FeedbackResult(success: bool, feedback_id: str)` | Stores rating and triggers dissatisfaction check. |
| `check_dissatisfaction_tool` | Input: `meal (enum), date (date), dimension (enum\|None)` → Output: `DissatisfactionCheck(chronic_triggered: bool, spike_triggered: bool, alert_data: AlertPayload\|None)` | Runs detection logic against last N meals. |
| `create_mess_alert_tool` | Input: `alert_type (enum: chronic/spike), dimension (enum), meal (enum), average_score (float), participation_count (int), related_complaint_ids (list[str])` → Output: `AlertResult(alert_id: str, notified_warden: bool, notified_mess_manager: bool)` | Creates MessAlert and sends notifications. |
| `ingest_complaint_signal_tool` | Input: `complaint_id (str), category (enum), text (str), date (date), meal_period (enum\|None)` → Output: `SignalResult(absorbed: bool)` | Folds Agent 1 mess complaints into dissatisfaction scoring. |

---

## 4. Warden & Staff Tools

### 4.1 Approval Queue
The Warden's approval queue is the primary human-in-the-loop interface. Every uncertain decision and every High-severity complaint surfaces here. Each queue item displays:
- Original complaint text
- AI's best-guess classification (category, severity, proposed assignee) — pre-filled
- AI's confidence level
- One-tap **Approve** button
- **Edit** option to correct before approving
- Override reason dropdown (auto-saved to improvement log)

> If a High-severity complaint is not reviewed within `APPROVAL_QUEUE_TIMEOUT_MINUTES` (default: 30 min), the system sends an escalation notification to the Warden.

### 4.2 Operations Dashboard
Real-time and historical view across all three agents:
- Complaint volume by category and severity (7-day and 30-day)
- Average complaint resolution time by category and assignee
- Student-confirmed resolution rate
- Laundry utilization rate and no-show frequency
- Mess satisfaction trends across 5 dimensions (7-day and 30-day charts)
- Mess feedback participation rate
- Evaluation metrics (see Section 6.2) — including drift alert banner if misclassification rate > 25%
- Pending approval queue count (always visible as a badge)

Daily digest notification sent each morning summarising the previous day's operations.

### 4.3 Staff Notification Types

| Role | Trigger | Content |
|------|---------|---------|
| Laundry Man | Complaint assigned / machine breakdown | Repair needed on machine X — bookings paused |
| Mess Secretary | Mess complaint assigned from Agent 1 | Complaint routed to you for action |
| Mess Manager | Dissatisfaction alert from Agent 3 | Chronic or spike alert with full context and scores |
| Assistant Warden | New registration pending / maintenance complaint | Verify student account / complaint assigned |
| Warden | Approval queue item / urgent alert / queue timeout | Pending approval / high-severity complaint / escalation |
| Chief Warden | Critical escalation from Warden | Unresolved escalation requiring top-level action |

---

## 5. Student Experience

### 5.1 Complaint Filing
1. Student opens PWA → navigates to "File Complaint"
2. Enters free-text description
3. Optionally toggles "Submit Anonymously"
4. Submits → receives immediate acknowledgement: *"Your complaint has been registered. Track its status below."*
5. Complaint appears in personal tracker with status: Registered

### 5.2 Complaint Status Tracker

| Status | Meaning |
|--------|---------|
| **Registered** | Received by system. Awaiting classification and assignment. |
| **Assigned** | Classified and assigned to staff. Staff notified. |
| **In Progress** | Staff has acknowledged and is working on it. |
| **Resolved** | Staff marked as resolved. Student prompted to confirm. |
| **Reopened** | Student marked as unresolved. Reopened with elevated priority. |

When marked Resolved, student receives: *"Your complaint has been marked resolved. Was your issue addressed?"* with Yes/No. If No → complaint reopens with elevated priority and Warden is notified.

### 5.3 Laundry Booking
1. Student opens "Book Laundry Slot" on PWA
2. Available time slots for both machines displayed. Full slots greyed out.
3. Student selects a slot and confirms. Confirmation sent via push notification.
4. Reminder sent 30 minutes before the slot.
5. Cancel up to 15 minutes before slot start — no penalty.
6. Cancellation after 15 min or no-show triggers 48-hour priority penalty.

### 5.4 Mess Feedback
The mess feedback area is a dedicated, always-accessible section on the PWA — separate from complaint filing. Students select which meal they are rating: **Breakfast / Lunch / Dinner**.

- Each option is active only during and after its meal period.
- Once submitted, that meal option shows a confirmation tick and is greyed out.
- **All three options reset at midnight every day.**
- Push notifications after each meal period serve as reminders — but the section is always open independently.
- Students rate across 5 dimensions with 1–5 stars and an optional one-line comment.

---

## 6. Feedback Loop & Evaluation

### 6.1 Override Logging
Every Warden correction stored with: original complaint text, AI classification, human correction, override reason, timestamp. Foundation for model improvement.

### 6.2 Evaluation Metrics

These metrics must be tracked and surfaced on the Warden dashboard. They are the objective health check for the AI system.

| Metric | Formula | Acceptable Threshold | Action if Breached |
|--------|---------|---------------------|-------------------|
| Misclassification Rate | Overrides / Total classified (rolling 30d) | < 15% | Review and refine classification prompt |
| Override Rate by Category | Overrides per category / Total in category | < 20% per category | Reclassify edge cases for that category |
| False High-Severity Rate | High-severity downgraded by Warden / Total high-severity | < 10% | Adjust severity prompt criteria |
| Student-Confirmed Resolution Rate | Yes responses / Total confirmations sent | > 80% | Investigate assignee behaviour |
| Avg Approval Queue Latency | Time from queue creation to Warden action (min) | < 20 min avg | Send escalation reminders more aggressively |
| Mess Feedback Participation Rate | Unique submitting / Total active students (daily) | > 40% daily | Adjust reminder timing |
| Laundry No-Show Rate | No-shows / Total bookings (rolling 7d) | < 10% | Review penalty communication |

> **DRIFT ALERT:** If Misclassification Rate exceeds 25% in any 7-day rolling window, the dashboard must display a banner: *"AI classification accuracy has dropped. Manual review recommended."*

### 6.3 Periodic Model Review
Monthly review of override log + evaluation metrics dashboard. Patterns of consistent misclassification → iterate on classification prompt and category definitions. No retraining required — prompt iteration only.

### 6.4 Student-Confirmed Resolution
Low resolution confirmation rates for a specific assignee or category flag a structural problem. Surfaced explicitly on the Warden dashboard.

---

## 7. Non-Functional Requirements

### 7.1 Technology Constraints

> **CONSTRAINT:** Zero-cost infrastructure — open-source models, free-tier hosted services. No paid APIs. No recurring licensing costs. Every service has a documented self-hosting alternative.

| Layer | Choice | Self-Host Alternative |
|-------|--------|-----------------------|
| LLM | Groq free tier + Llama 3 (open-source) | vLLM running Llama 3 on local hardware |
| Backend | Python + FastAPI + Pydantic v2 + SQLAlchemy + Alembic | — |
| Agent Orchestration | LangChain (V1) — LangGraph (V2 upgrade path) | — |
| Frontend | React 18 + TypeScript + Vite + PWA + Shadcn/UI | — |
| Database | PostgreSQL via Supabase free tier | PostgreSQL on any VPS or Docker |
| Task Queue | Celery + Upstash Redis free tier | Redis on Docker |
| Hosting | Railway free tier | Docker Compose on any Linux server |
| Push Notifications | Web Push API (pywebpush) | — fully free, no alternative needed |

### 7.2 Performance Expectations
- Complaint acknowledgement to student: within 5 seconds of submission
- Classification and routing (high-confidence): within 10 seconds
- Approval queue surfacing: within 10 seconds of submission
- Push notifications for staff assignments: within 30 seconds
- Mess alert generation after threshold crossed: within 5 minutes

### 7.3 Security Hardening
- **Prompt Injection Detection** — pre-processing strips injection patterns from all free-text fields before LLM. Flagged inputs logged and surfaced to Warden passively.
- **Input Sanitization** — all string inputs trimmed, length-capped (complaint text: max 1000 chars, comments: max 300 chars), HTML-escaped before storage or LLM processing.
- **Rate Limiting** — per-IP: 30 requests/minute to any endpoint. Per-account: 1 complaint/category/day, 1 laundry booking/day, 3 feedback submissions/day.
- **Audit Logs** — every state-changing action written to immutable audit log with user ID, action, timestamp, IP address.
- **JWT Rotation** — access tokens expire after 24 hours. Refresh tokens expire after 30 days. Token invalidated immediately on suspicious activity.
- **HTTPS Enforced** — Railway enforces HTTPS. PWA service worker registered only over HTTPS.
- **Anonymous complaint identity** — stored in separate encrypted field accessible only to Warden role.
- **ERP documents** — stored securely, accessible only to Assistant Warden.

---

## 8. Out of Scope (V1)
- WhatsApp / SMS integration — API cost constraints
- Offline functionality — requires active internet connection
- Automated corrective action suggestions to Mess Manager — alerts with data only
- Native mobile app (iOS/Android) — PWA covers all mobile use cases
- Attendance or financial management — outside operational scope
- Multi-hostel management from a single dashboard — single-hostel deployment only
- Vector memory / RAG-enhanced triage (Qdrant) — deferred to V2
- Automated drift monitoring alerts — V1 uses dashboard metrics only
- LangGraph migration — documented upgrade path, not V1 implementation

---

## 9. Complaint State Graph

### 9.1 States

Every complaint exists in exactly one state at any time. State transitions must be validated at the service layer — invalid transitions throw an error, never silently succeed.

| State | Definition |
|-------|-----------|
| `INTAKE` | Received and acknowledged. Classification not yet complete. |
| `CLASSIFIED` | LLM returned a classification. High-confidence non-sensitive → ASSIGNED. Others → AWAITING_APPROVAL. |
| `AWAITING_APPROVAL` | In Warden's approval queue. No assignment made. Awaiting human confirmation. |
| `ASSIGNED` | Assigned to a staff member. Staff notified. |
| `IN_PROGRESS` | Staff acknowledged and is actively working on it. |
| `RESOLVED` | Staff marked resolved. Student prompted for confirmation. |
| `REOPENED` | Student confirmed unresolved. Back in queue with elevated priority. |
| `ESCALATED` | Elevated to Warden or Chief Warden due to severity, sensitivity, or inaction. |

### 9.2 Valid Transitions

| Transition | Trigger |
|-----------|---------|
| `INTAKE → CLASSIFIED` | LLM classification completes successfully |
| `INTAKE → ESCALATED` | LLM fails after all retries — fallback to manual |
| `CLASSIFIED → ASSIGNED` | High-confidence, non-sensitive — auto-assigned |
| `CLASSIFIED → AWAITING_APPROVAL` | Low confidence OR high severity |
| `AWAITING_APPROVAL → ASSIGNED` | Warden approves or corrects AI suggestion |
| `AWAITING_APPROVAL → ESCALATED` | Warden escalates directly to Chief Warden |
| `AWAITING_APPROVAL → ESCALATED` | Queue item unreviewed for > `APPROVAL_QUEUE_TIMEOUT_MINUTES` |
| `ASSIGNED → IN_PROGRESS` | Staff acknowledges in their dashboard |
| `ASSIGNED → ESCALATED` | Sits in ASSIGNED for > 24 hours without IN_PROGRESS — auto-escalates |
| `IN_PROGRESS → RESOLVED` | Staff marks resolved |
| `RESOLVED → REOPENED` | Student taps No on resolution confirmation |
| `REOPENED → ASSIGNED` | Re-assigned with elevated priority. Warden notified. |
| `ESCALATED → ASSIGNED` | Chief Warden / Warden manually assigns from escalation view |

> **IMPLEMENTATION NOTE:** Implement state transitions as a single dedicated function: `transition_complaint(complaint_id, from_state, to_state, triggered_by, db)` in `/backend/services/complaint_service.py`. This function validates the transition against the allowed list, updates the DB, triggers the appropriate tool, and writes to the audit log. **Never update complaint status directly from a route.**

---

## 10. Failure Modes & Resilience

### 10.1 Design Philosophy
HostelOps AI must degrade gracefully under every failure condition. No failure should leave a student complaint silently lost or a warden unaware. The fallback chain is always: **retry → rule-based fallback → manual escalation**. The system must never fail silently.

### 10.2 Failure Scenarios & Responses

| Failure Scenario | Response | Pattern |
|-----------------|----------|---------|
| Groq API timeout or 5xx | Celery retries up to 3 times with exponential backoff (2s, 4s, 8s). If all fail → transition to `AWAITING_APPROVAL` with note: *"AI classification unavailable — manual review required."* Warden notified immediately. | Retry + manual fallback |
| Confidence score parsing fails | If LLM response can't be parsed into valid `ClassificationResult`, treat as low-confidence → route to `AWAITING_APPROVAL`. Log raw response. Never crash the request. | Parse fallback |
| LLM hallucinates invalid category | Pydantic validation rejects any category not in the defined enum. Invalid output caught, logged, complaint routes to `AWAITING_APPROVAL`. Warden sees: *"AI returned unrecognised category."* | Schema validation |
| Celery / Redis crash | FastAPI detects Celery unavailability on submission. Complaint written to DB as `AWAITING_APPROVAL` immediately. Student acknowledged. Cron job checks for complaints stuck in `INTAKE` or `AWAITING_APPROVAL` > 5 minutes and alerts Warden. | Sync fallback + cron monitor |
| Prompt injection attempt | Pre-processing detects injection patterns before text reaches LLM. Sanitized version is classified. Original stored in `flagged_input` field. Passive notification sent to Warden: *"Possible prompt injection detected in complaint [ID]."* | Sanitize + flag + log |
| Database connection failure | SQLAlchemy connection pool retries 3 times. If DB unreachable > 30 seconds → FastAPI returns 503 with: *"System temporarily unavailable. Your complaint has not been lost — please try again."* | Connection pool + 503 |
| Push notification delivery failure | pywebpush failures caught and logged. In-app notification inbox is the fallback — all notifications written to DB regardless of push delivery success. | In-app inbox fallback |
| Mess feedback participation collapse | If daily participation < 15% for 3 consecutive days → Agent 3 alerts Warden: *"Mess feedback participation critically low — data may be insufficient for reliable detection."* | Participation monitor |

### 10.3 Rule-Based Fallback Classifier

When LLM is unavailable, a deterministic keyword-based classifier serves as last resort. Implement as a pure function with no external dependencies in `/backend/services/fallback_classifier.py`.

> **IMPORTANT:** The fallback classifier must always add a system note to the complaint record: `classified_by: "fallback"`. The Warden dashboard must display this distinction clearly — wardens must always know which complaints were AI-classified vs fallback-classified.

| Trigger Keywords | Fallback Classification |
|-----------------|------------------------|
| food, mess, meal, breakfast, lunch, dinner, cook, taste, hygiene | Category: mess \| Severity: medium \| Assignee: Mess Manager |
| laundry, washing, machine, clothes, slot, dryer | Category: laundry \| Severity: medium \| Assignee: Laundry Man |
| water, electricity, fan, light, AC, furniture, door, window, plumbing | Category: maintenance \| Severity: medium \| Assignee: Assistant Warden |
| fight, harassment, threat, abuse, unsafe, scared, uncomfortable | Category: interpersonal \| Severity: HIGH \| → AWAITING_APPROVAL always |
| No keyword match | Category: uncategorised \| Severity: medium \| → AWAITING_APPROVAL with note: *"Fallback classifier — no match found"* |

---

## 11. Technology Stack

> **LANGGRAPH UPGRADE PATH:** LangChain handles V1's linear chains well. When complexity grows — particularly around reopen → escalate → reassign cycles — migrate Agent 1 to a LangGraph state machine where each node maps to a complaint state (Section 9) and edges map to valid transitions. The Pydantic schemas and tool definitions in this PRD are already LangGraph-compatible. No data model changes required for migration.

### 11.1 Complete Stack

| Layer | Technology | Notes & Self-Host Alternative |
|-------|-----------|-------------------------------|
| Frontend | React 18 + TypeScript + Vite + PWA + Shadcn/UI | TypeScript gives AI full type context. Shadcn for pre-built components. |
| Backend | Python + FastAPI + Pydantic v2 + SQLAlchemy + Alembic | Pydantic is the single source of truth for all data shapes. |
| Agent Orchestration | LangChain (V1) | LangGraph is V2 upgrade path. |
| LLM | Groq free tier + Llama 3 | Self-host: vLLM + Llama 3 on local hardware. |
| Task Queue | Celery + Upstash Redis (free tier) | Self-host: Redis on Docker. |
| Database | PostgreSQL via Supabase (free tier) | Self-host: PostgreSQL on Docker. |
| Authentication | JWT via python-jose + passlib | Role-based access via JWT claims. |
| Hosting | Railway (free tier) | Self-host: Docker Compose on any Linux server. |
| Push Notifications | Web Push API (pywebpush backend) | Fully free. Built into PWA standard. |
| Config | python-dotenv + .env file | All secrets in .env. Never hardcoded. |

### 11.2 Deployment Modes

**Development / Demo Mode** — Vercel (frontend) + Railway (backend) + Supabase + Upstash + Groq. Everything hosted, zero setup. Cost: $0–$5/month (Railway hobby plan for always-on backend recommended).

**Production / Hostel Mode** — Docker Compose on a college server. Everything self-hosted except LLM (Groq) and optionally frontend (Vercel). Cost: $0 ongoing.

> **Railway free tier note:** The free tier sleeps the backend after inactivity. For a always-on hostel system, the Railway hobby plan ($5/month) is strongly recommended. Free workaround: use UptimeRobot (free) to ping the backend every 5 minutes.

---

## 12. Open Decisions — Next Phase

### Design Discussion
1. UI/UX design for student complaint and laundry booking flows
2. Warden approval queue interface design
3. Dashboard layout and data visualisation approach
4. Mess feedback widget design to maximise participation rate
5. Mobile-first vs desktop-first layout priority
