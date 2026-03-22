# HostelOPS AI — Design System (DESIGN.md)
# Use this file with the frontend-dev agent for consistent screen generation.
# Build React components directly — do not use Stitch MCP for code generation.

## Design philosophy
Warm, friendly, human-first. This is a student app — it should feel approachable, not corporate. Every screen says "we've got your back" through soft colors, generous spacing, and clear status communication.

## Color tokens

### Primary palette
- **Primary**: Indigo `#4647D3` — buttons, active nav, links, progress indicators
- **Primary light**: `#6366F1` — lighter accents, hover states
- **Primary surface**: `rgba(70, 71, 211, 0.06)` — subtle tinted backgrounds

### Semantic colors
- **Success**: Jade `#16A085` — resolved status, confirmations, completed states
- **Danger**: Vermillion `#E83B2A` — escalated status, urgent alerts, destructive actions
- **Warning/Accent**: Saffron `#FFB800` — star ratings, attention-drawing elements, accent badges
- **Info**: Blue `#3B82F6` — informational banners, secondary highlights

### Surface colors
- **Background**: Warm cream `#FFF5EE` — main app background on all screens
- **Card**: White `#FFFFFF` — card surfaces sitting on the warm background
- **Card alt**: `#F8F7F4` — secondary card surfaces, info cards
- **Input bg**: `#F5F3EF` — form input backgrounds (warm tint, not cold gray)

### Text colors
- **Primary text**: `#1A1A2E` — headings, primary content
- **Secondary text**: `#6B6B80` — descriptions, body copy
- **Muted text**: `#9B9BAF` — timestamps, hints, placeholders
- **Disabled text**: `#C4C4D4` — inactive elements

### Status badge colors
| Status | Background | Text |
|---|---|---|
| INTAKE | `#F0F0ED` | `#6B6B80` |
| CLASSIFIED | `rgba(70, 71, 211, 0.08)` | `#3C3489` |
| AWAITING_APPROVAL | `rgba(255, 184, 0, 0.10)` | `#9E7600` |
| ASSIGNED | `rgba(70, 71, 211, 0.08)` | `#3C3489` |
| IN_PROGRESS | `rgba(70, 71, 211, 0.08)` | `#3C3489` |
| RESOLVED | `rgba(22, 160, 133, 0.08)` | `#0F6E56` |
| REOPENED | `rgba(255, 184, 0, 0.10)` | `#9E7600` |
| ESCALATED | `rgba(232, 59, 42, 0.08)` | `#C12E20` |

## Typography

### Font family
- **Primary**: Plus Jakarta Sans (all text)
- **Monospace**: For hostel codes only (e.g., ICEQ-3202)

### Scale
| Element | Size | Weight | Color |
|---|---|---|---|
| Screen title | 28-32px | 800 (extra bold) | `#1A1A2E` |
| Section heading | 18-20px | 700 | `#1A1A2E` |
| Card title | 15-16px | 700 | `#1A1A2E` |
| Body text | 14-15px | 400 | `#6B6B80` |
| Label (uppercase) | 11-12px | 600, letter-spacing 0.8px | `#9B9BAF` |
| Badge text | 10-11px | 700, uppercase | varies by status |
| Timestamp | 11-12px | 500 | `#C4C4D4` |
| Nav label | 10px | 600 | `#C4C4D4` (inactive), `#4647D3` (active) |

## Layout

### Spacing
- Screen horizontal padding: 24px
- Card padding: 16-20px
- Section gap: 20-24px
- Card gap: 10-12px
- Inner element gap: 8-12px

### Border radius
- Cards: 16-20px (large, soft)
- Buttons: 12-14px
- Inputs: 12px
- Badges/pills: 999px (full round)
- Icon containers: 10-12px
- Bottom nav: 0 (flush to edges)

### Shadows
- Cards: none or very subtle — tonal layering preferred over shadows
- No drop shadows, no box shadows on buttons

### Viewport target
- 390×844px (iPhone 14 baseline) for all screens
- min-h-dvh everywhere — use dvh not vh to handle mobile browser chrome

## Scroll pattern (standard for all content-heavy screens)

Every screen with more than one screenful of content uses this fixed layout:

```
┌─────────────────────────────┐  ← fixed top bar (header / tab bar)
│  Header or page tabs        │
├─────────────────────────────┤
│                             │
│  Scrollable content area    │  ← flex-1 overflow-y-auto, padded
│  (cards, lists, forms)      │
│                             │
├─────────────────────────────┤  ← sticky button zone (primary CTA)
│  Primary action button      │    position: sticky bottom-0, white bg
├─────────────────────────────┤
│  Bottom navigation          │  ← fixed bottom nav
└─────────────────────────────┘
```

- Top bar: `position: fixed top-0`, z-index above content
- Scrollable area: `flex-1 overflow-y-auto`, padded top to clear fixed bar
- Sticky button zone: `sticky bottom-0 bg-white/95 backdrop-blur` — used when there's a single primary CTA (e.g. Submit, Book, Confirm)
- Bottom nav: `position: fixed bottom-0`, z-index above content
- Content padding-bottom must clear the bottom nav height (≈64px) + any sticky button

## Components

### Header pattern (authenticated screens)
Avatar circle + "Good morning, {name}" with wave emoji + Notification bell icon on right. Screen title large and bold below. Left-aligned. Description in muted text.

### Card style
White background on warm cream page. Border radius 16-20px. No visible border or very subtle `1px solid rgba(0,0,0,0.04)`. Padding 16-20px. Content stacked with 8-12px gaps.

### Status badges
Pill shape 999px radius. Padding 4px 12px. Font 10-11px, 700 weight, uppercase. Translucent colored background with darker text from same color family. Use the status badge color table above.

### Bottom navigation — variants

#### Student (5 tabs)
Home | Complaints | Laundry | Mess | Profile
Icons: Home, ChatBubble, WashingMachine, Fork, Person

#### Warden (5 tabs)
Dashboard | Approvals | Students | Settings | Profile
Icons: BarChart, CheckCircle, People, Gear, Person

#### Staff — Laundry Man (3 tabs)
Slots | Machines | Profile
Icons: Calendar, WashingMachine, Person

#### Staff — Mess roles (3 tabs)
Summary | Menu | Profile
Icons: ChartBar, MenuBook, Person

All nav bars: frosted glass background `bg-white/80 backdrop-blur-md`. Icons 20-22px. Labels 10px. Active: `#4647D3`. Inactive: `#C4C4D4`. Fixed to bottom, full width.

### Buttons
- **Primary**: full width, `bg-[#4647D3]` white text, 14px radius, 52px height. No shadow.
- **Secondary**: white bg, `1.5px border`, dark text, same height.
- **Danger action**: text-only `#E83B2A`, no background. Used for Reopen / destructive links.
- **FAB**: 56px square, indigo, rounded-2xl, bottom-right absolute. Used for file complaint.

### Form inputs
Height 48-52px. Warm tinted background `#F5F3EF` or white. `1.5px border border-[#E8E4DE]`. 12px radius. Left icon in muted color. Labels above in uppercase muted style (11px, 600, letter-spacing 0.8px). Error state: `border-[#E83B2A]` + red helper text below.

### Explanation banner (college-mode registration)
Indigo-tinted surface `rgba(70,71,211,0.06)`. Left `3px solid #4647D3` border. Icon + title + body text. Used to explain why optional fields (roll number) appear in college mode.

### Timeline (complaint detail)
Vertical `#16A085` line connecting status dots. Each node: colored dot + uppercase status label + description + timestamp. Most recent at top. Reopen action at bottom in red text-only button.

### Star ratings (mess feedback)
5 stars per dimension. Filled gold `#FFB800`. Empty gray `#E8E4DE`. Tap to set. 5 dimensions, each with icon + label: Food Quality, Quantity, Hygiene, Menu Variety, Timing.

### Meal tabs (mess feedback)
Horizontal pills: Breakfast / Lunch / Dinner. Active: `bg-[#4647D3] text-white`. Inactive: `border border-[#E8E4DE] text-[#6B6B80]`. Maps to MealPeriod enum: breakfast | lunch | dinner.

### Drift alert banner (warden dashboard)
Red-tinted `rgba(232,59,42,0.06)` background. Left `3px solid #E83B2A` border. Warning icon + bold title + description text. Dismiss (X) button top-right. Shown when `drift_alert === true` in DashboardMetrics.

### Metric cards (warden dashboard)
2-column grid. White card. Large number (24px, 700) + small muted label below. Optional trend badge (green up / red down). Translucent indigo icon container top-right.

### Category breakdown (warden dashboard)
Category name + count on one row. Colored progress bar below (width = count / max). Repeating list inside a card.

### Skeleton loaders
Warm shimmer animation on placeholder rectangles. Never use spinners. Background: `#F5F3EF` → `#EDE9E4` gradient sweep.

### Slot grid (laundry booking)
3-column grid of pill buttons per time slot. States: Available (indigo outline), Booked (indigo fill), Taken (gray fill disabled), Past (muted outline disabled). Label = slot_time string e.g. "08:00-09:00".

### Machine status indicator (laundry man view)
Row card per machine: machine name + floor badge + status pill (operational / under_repair / offline). Tap to update status. Status colors: operational=jade, under_repair=saffron, offline=danger.

## Screen list (23 screens)

### Auth (6 screens)
| ID | Screen | Route | Notes |
|---|---|---|---|
| S-01 | Hostel Setup | `/auth/setup` | One-time; warden creates hostel, gets hostel code |
| S-02 | Landing | `/auth/landing` | Hostel code entry; resolves to setup/login/register |
| S-03 | Login | `/auth/login` | room_number + password + hostel_code |
| S-04 | Register | `/auth/register` | name, room, password + roll_number if college mode |
| S-05 | Registration Pending | `/auth/pending` | Waiting for warden approval |
| S-06 | Registration Rejected | `/auth/rejected` | Rejection reason + re-register option |

### Onboarding (1 screen)
| ID | Screen | Route | Notes |
|---|---|---|---|
| S-07 | Onboarding | `/onboarding` | 3-step walkthrough; shown once (has_seen_onboarding=false) |

### Student (8 screens)
| ID | Screen | Route | Notes |
|---|---|---|---|
| S-08 | Student Home | `/student` | Greeting, quick actions, active complaint card, notices |
| S-09 | File Complaint | `/student/complaints/new` | Text area + anonymous toggle + AI templates |
| S-10 | Complaint Tracker | `/student/complaints` | List with status badges, search bar |
| S-11 | Complaint Detail | `/student/complaints/:id` | Timeline + category + reopen option |
| S-12 | Laundry Booking | `/student/laundry` | Date picker + slot grid per machine |
| S-13 | Mess Page | `/student/mess` | 3 tabs: Rate / History / Menu |
| S-14 | Notification Inbox | `/student/notifications` | Paginated list, unread indicator, mark-all-read |
| S-15 | Student Profile | `/student/profile` | Info, feedback_streak, theme toggle, change password |

### Warden (6 screens)
| ID | Screen | Route | Notes |
|---|---|---|---|
| S-16 | Warden Dashboard | `/warden` | Metrics, drift alert, category breakdown, pending counts |
| S-17 | Approval Queue | `/warden/approval-queue` | Pending AI decisions; approve/override with category |
| S-18 | Student Registrations | `/warden/students` | Pending registrations; verify or reject with reason |
| S-19 | Create Staff Account | `/warden/staff/new` | Form: name, room, role, password |
| S-20 | Complaint Management | `/warden/complaints` | All complaints with search + status/category filters |
| S-21 | Hostel Settings | `/warden/settings` | 16-field config editor, read and patch |

### Staff (2 screens)
| ID | Screen | Route | Notes |
|---|---|---|---|
| S-22 | Laundry Man View | `/staff/laundry` | Slot list + machine status cards; mark repairs |
| S-23 | Mess Staff View | `/staff/mess` | Feedback summary, alerts list, today's menu |

## Implementation order (Sprint F)

Build screens in this sequence — each group unblocks the next:

**Phase 1 — Foundation (auth + shell)**
S-01 → S-02 → S-03 → S-04 → S-05 → S-06

**Phase 2 — Student core**
S-07 → S-08 → S-09 → S-10 → S-11

**Phase 3 — Student features**
S-12 → S-13 → S-14 → S-15

**Phase 4 — Warden**
S-16 → S-17 → S-18 → S-19 → S-20 → S-21

**Phase 5 — Staff**
S-22 → S-23

## Dark mode (warm espresso)
- Background: `#1A1714` (warm dark, not cold gray)
- Card surface: `#252220`
- Text primary: `#F5F0EB`
- Text secondary: `#9B9590`
- Primary: `#6366F1` (slightly lighter for contrast)

## Animation
- Page transitions: subtle slide-in (200ms ease-out)
- Card tap: `scale(0.98)` press effect
- Confetti on complaint resolution
- Skeleton loaders with warm shimmer (never spinners)
- Status badge fade-in on load

## Design decisions log

| Decision | Rationale |
|---|---|
| College mode explanation banner (S-04) | Students don't know hostel mode; banner explains why roll number appears after hostel code resolves |
| Roll number placeholder: "Enter your full college roll no. here" | Avoids confusion between student ID formats |
| Room number placeholder: "e.g. 201-A (use suffix if multiple per room)" | Real rooms have A/B/C suffixes; was confusing without example |
| ERP document upload removed from Register UI | PRD Section 8 defers file upload to V2; field exists in DB but no UI in V1 |
| Scroll pattern fixed top + sticky CTA + fixed bottom nav | Avoids content hidden under nav bars; sticky CTA keeps primary action always reachable |
| Mess page uses 3 tabs (Rate / History / Menu) | Keeps feedback, history, and menu distinct without separate routes |
| Rate tab + History tab scroll; Menu tab fits without scrolling | Menu is compact; rating form is the longest content |
| Staff bottom nav has 3 tabs (not 5) | Staff have a narrow task scope; fewer tabs reduces cognitive load |
| Warden bottom nav: Dashboard / Approvals / Students / Settings / Profile | Maps directly to the 5 warden route groups |
| No codename — brand is "HostelOPS AI" | Codenames add confusion for a product already named |
| Hostel code displayed in monospace on setup success | Codes like ICEQ-3202 are copy-paste targets; monospace aids readability |
