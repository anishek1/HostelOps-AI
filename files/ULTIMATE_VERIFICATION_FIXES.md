# HostelOps AI — Ultimate Verification Fix Prompt
# Paste into Cursor (Sonnet 4.6 Thinking) or Gemini 3.1 Pro
# Fix ONLY what is listed. Touch nothing else.

---

@CONVENTIONS.md @PRD.md @PROJECT_STATE.md

You are fixing failures found in the HostelOps AI ultimate verification audit. Fix exactly the 6 items below — 2 blocking failures, 2 structural deviations, 2 cosmetic deviations. Do not refactor anything else.

---

## FIX 1 — Hardcoded confidence threshold (BLOCKING)

**File:** `backend/tasks/complaint_tasks.py`
**Line:** 293
**Problem:** `threshold = 0.85` is hardcoded. Must use settings.

```python
# Before (wrong):
threshold = 0.85

# After (correct):
from config import settings
threshold = settings.COMPLAINT_CONFIDENCE_THRESHOLD
```

Make sure `settings` is already imported at the top of the file. If it is, just replace the hardcoded value. Do not import settings twice.

Verify after fix:
- [ ] `0.85` does not appear as a hardcoded value anywhere in `complaint_tasks.py`
- [ ] `settings.COMPLAINT_CONFIDENCE_THRESHOLD` is used instead

---

## FIX 2 — Business logic in routes/users.py (BLOCKING)

**File:** `backend/routes/users.py`
**Lines:** 67 and 115
**Problem:** `user.is_verified = True` and `user.is_active = False` are set directly inside route handlers. Routes must never contain business logic.

**Step 1 — Create `backend/services/user_service.py`:**

```python
"""
user_service.py — HostelOps AI
================================
Service functions for user management.
Called by routes/users.py — never contains FastAPI-specific code.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.user import User
from schemas.enums import UserRole
from fastapi import HTTPException


async def verify_user(
    user_id: str,
    verified_by: str,
    db: AsyncSession
) -> User:
    """
    Sets is_verified=True for a user.
    Called by Assistant Warden after reviewing registration.
    Raises 404 if user not found.
    Raises 400 if user is already verified.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.is_verified:
        raise HTTPException(status_code=400, detail="User is already verified")

    user.is_verified = True
    await db.commit()
    await db.refresh(user)
    return user


async def deactivate_user(
    user_id: str,
    deactivated_by: str,
    db: AsyncSession
) -> User:
    """
    Sets is_active=False for a user.
    Called by Assistant Warden when student vacates.
    Raises 404 if user not found.
    Raises 400 if user is already inactive.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="User is already inactive")

    user.is_active = False
    await db.commit()
    await db.refresh(user)
    return user


async def get_user_by_id(
    user_id: str,
    db: AsyncSession
) -> User:
    """
    Fetches a user by ID.
    Raises 404 if not found.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
```

**Step 2 — Thin out `backend/routes/users.py`:**

Replace the verify and deactivate route handlers so they call the service:

```python
# verify route — before (wrong, logic in route):
user.is_verified = True
await db.commit()

# verify route — after (correct, calls service):
from services.user_service import verify_user
user = await verify_user(user_id=user_id, verified_by=current_user.id, db=db)
return user

# deactivate route — before (wrong):
user.is_active = False
await db.commit()

# deactivate route — after (correct):
from services.user_service import deactivate_user
user = await deactivate_user(user_id=user_id, deactivated_by=current_user.id, db=db)
return user
```

Verify after fix:
- [ ] `backend/services/user_service.py` exists with `verify_user()` and `deactivate_user()`
- [ ] `routes/users.py` has zero `user.is_verified =` or `user.is_active =` assignments
- [ ] Routes are thin — 3-5 lines max per handler
- [ ] Verify and deactivate endpoints still work correctly

---

## FIX 3 — Import VALID_TRANSITIONS in complaint_tasks.py (STRUCTURAL)

**File:** `backend/tasks/complaint_tasks.py`
**Problem:** `_transition_complaint_sync()` in complaint_tasks.py duplicates the `VALID_TRANSITIONS` dict from `complaint_service.py`. If one is updated, the other drifts.

**Fix — import from the single source of truth:**

In `complaint_service.py`, make sure `VALID_TRANSITIONS` is defined at module level (not inside the function):

```python
# In complaint_service.py — at module level
VALID_TRANSITIONS = {
    ComplaintStatus.INTAKE: [ComplaintStatus.CLASSIFIED, ComplaintStatus.ESCALATED],
    ComplaintStatus.CLASSIFIED: [ComplaintStatus.ASSIGNED, ComplaintStatus.AWAITING_APPROVAL],
    ComplaintStatus.AWAITING_APPROVAL: [ComplaintStatus.ASSIGNED, ComplaintStatus.ESCALATED],
    ComplaintStatus.ASSIGNED: [ComplaintStatus.IN_PROGRESS, ComplaintStatus.ESCALATED],
    ComplaintStatus.IN_PROGRESS: [ComplaintStatus.RESOLVED],
    ComplaintStatus.RESOLVED: [ComplaintStatus.REOPENED],
    ComplaintStatus.REOPENED: [ComplaintStatus.ASSIGNED],
    ComplaintStatus.ESCALATED: [ComplaintStatus.ASSIGNED],
}
```

Then in `complaint_tasks.py`, import it instead of redefining:

```python
# In complaint_tasks.py — remove the local VALID_TRANSITIONS definition
# Add this import instead:
from services.complaint_service import VALID_TRANSITIONS
```

Verify after fix:
- [ ] `VALID_TRANSITIONS` is defined ONLY in `complaint_service.py`
- [ ] `complaint_tasks.py` imports it — no local copy

---

## FIX 4 — Remove stale localStorage comment in AuthContext.tsx (COSMETIC)

**File:** `frontend/src/context/AuthContext.tsx`
**Line:** 4
**Problem:** A comment says "Restores session from localStorage" but no localStorage code exists. Stale comment is misleading.

Simply delete the misleading comment. Do not change any code — only remove the comment.

Verify after fix:
- [ ] No mention of `localStorage` anywhere in `AuthContext.tsx` — not in comments, not in code

---

## FIX 5 — Pin langchain-core in requirements.txt (COSMETIC)

**File:** `backend/requirements.txt`
**Problem:** `langchain-core` is a transitive dependency but not explicitly pinned.

Add this line to `requirements.txt`:
```
langchain-core==0.1.53
```

Add it alongside the other langchain packages.

---

## FIX 6 — Remove INTAKE→CLASSIFIED normalization bypasses (STRUCTURAL)

**File:** `backend/services/complaint_service.py`
**Lines:** ~240 and ~300
**Problem:** `assign_complaint()` and `send_to_approval_queue()` set `complaint.status` directly as a "normalization" step before calling `transition_complaint()`. This bypasses the single-point-of-update rule.

**Fix — use transition_complaint() for the normalization step too:**

```python
# In assign_complaint() — before calling transition to ASSIGNED,
# first transition INTAKE → CLASSIFIED if needed:
if complaint.status == ComplaintStatus.INTAKE:
    await transition_complaint(
        complaint_id=complaint_id,
        from_state=ComplaintStatus.INTAKE,
        to_state=ComplaintStatus.CLASSIFIED,
        triggered_by="system",
        db=db,
        note="Auto-classified before assignment"
    )

# Then transition CLASSIFIED → ASSIGNED:
await transition_complaint(
    complaint_id=complaint_id,
    from_state=ComplaintStatus.CLASSIFIED,
    to_state=ComplaintStatus.ASSIGNED,
    triggered_by=classified_by,
    db=db
)
```

Apply the same pattern in `send_to_approval_queue()`.

Verify after fix:
- [ ] `complaint.status =` assignment appears ONLY inside `transition_complaint()` in `complaint_service.py`
- [ ] Zero direct status assignments in `assign_complaint()` or `send_to_approval_queue()`

---

## AFTER ALL FIXES

Run the backend to confirm nothing broke:
```bash
cd backend
.venv\Scripts\uvicorn main:app --reload
```

Test:
1. Register + verify a student
2. Login and file a complaint
3. Confirm Celery classifies it
4. Confirm Assistant Warden can verify a new student (via the new user_service)
5. Confirm deactivate endpoint still works

Commit:
```bash
git add .
git commit -m "Ultimate verification fixes — hardcoded threshold, thin routes, single-point status update, VALID_TRANSITIONS import"
git push origin main
```
