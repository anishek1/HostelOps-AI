"""
routes/hostels.py — HostelOps AI
====================================
Hostel management routes.
Sprint 7: Multi-tenant architecture.

POST /api/hostels/setup  — public, creates hostel + first warden account
GET  /api/hostels/{code}/info — public, returns hostel name + mode for landing page
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from schemas.hostel import HostelPublicInfo, HostelSetupRequest, HostelSetupResponse
from services.hostel_service import create_hostel_with_warden, get_hostel_by_code

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/setup", response_model=HostelSetupResponse, status_code=status.HTTP_201_CREATED)
async def setup_hostel(payload: HostelSetupRequest, db: AsyncSession = Depends(get_db)):
    """
    One-time hostel setup endpoint.
    Creates the hostel record, generates a unique hostel code, and creates the
    first assistant_warden account (immediately verified).
    Returns tokens so the warden is logged in immediately after setup.
    """
    hostel, warden, access_token, refresh_token = await create_hostel_with_warden(payload, db)

    from schemas.hostel import HostelRead
    return HostelSetupResponse(
        hostel=HostelRead.model_validate(hostel),
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.get("/{code}/info", response_model=HostelPublicInfo)
async def get_hostel_info(code: str, db: AsyncSession = Depends(get_db)):
    """
    Public endpoint — called by the student registration page to validate the
    hostel code and display the hostel name + mode before the student fills in
    their details.
    """
    hostel = await get_hostel_by_code(code, db)
    if not hostel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid hostel code. Please check with your warden.",
        )
    return HostelPublicInfo(name=hostel.name, mode=hostel.mode, code=hostel.code)
