# Run once during initial deployment: python create_admin.py
"""
create_admin.py — HostelOps AI
================================
One-time setup script that creates the first verified Assistant Warden account.
Run this ONCE after initial deployment to bootstrap the admin account.
It is safe to run multiple times — it checks for existing admins first.

Usage:
    cd backend
    python create_admin.py
"""

import sys
import os
import asyncio

# Ensure imports resolve from backend/
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import select
from database import AsyncSessionLocal
from config import settings
from models.user import User
from schemas.enums import HostelMode, UserRole
from services.auth_service import hash_password
from services.hostel_config_service import seed_default_config


async def create_admin_user(db) -> None:
    # Check if any assistant_warden already exists
    result = await db.execute(
        select(User).where(
            User.role == UserRole.warden,
            User.is_active == True,
        )
    )
    existing = result.scalars().first()

    if existing:
        print(f"\n✅ Admin already exists: '{existing.name}' (Room: {existing.room_number})")
        print("   No action taken. Admin setup is already complete.")
    else:
        # Prompt for admin details
        print("\nNo admin account found. Creating the first Assistant Warden account.")
        print("(This account will be auto-verified and active immediately.)\n")

        name = input("Enter name: ").strip()
        if not name:
            print("❌ Error: Name cannot be empty.")
            sys.exit(1)

        room_number = input("Enter room number / login identifier: ").strip()
        if not room_number:
            print("❌ Error: Room number cannot be empty.")
            sys.exit(1)

        # Check if room_number is already taken
        result = await db.execute(select(User).where(User.room_number == room_number))
        dup = result.scalar_one_or_none()
        if dup:
            print(f"❌ Error: Room number '{room_number}' is already registered.")
            sys.exit(1)

        password = input("Enter password (min 8 chars): ").strip()
        if len(password) < 8:
            print("❌ Error: Password must be at least 8 characters.")
            sys.exit(1)

        # Create the admin user
        admin = User(
            name=name,
            room_number=room_number,
            role=UserRole.warden,
            hostel_mode=HostelMode.college,
            hashed_password=hash_password(password),
            is_verified=True,
            is_active=True,
        )
        db.add(admin)
        await db.commit()
        await db.refresh(admin)

        print(f"\n✅ Admin created successfully!")
        print(f"   Name:        {admin.name}")
        print(f"   Room/Login:  {admin.room_number}")
        print(f"   Role:        {admin.role.value}")
        print(f"   Verified:    {admin.is_verified}")
        print(f"   User ID:     {admin.id}")
        print("\nYou can now log in via POST /api/auth/login with these credentials.")


async def seed_laundry_machines(db) -> None:
    from models.machine import Machine
    from schemas.enums import MachineStatus

    result = await db.execute(select(Machine))
    existing = result.scalars().first()
    if existing:
        print("\n✅ Laundry machines already seeded — skipping.")
        return

    machines = [
        Machine(name="Machine A", floor=1, status=MachineStatus.operational, is_active=True),
        Machine(name="Machine B", floor=2, status=MachineStatus.operational, is_active=True),
        Machine(name="Machine C", floor=3, status=MachineStatus.operational, is_active=True),
    ]
    for m in machines:
        db.add(m)
    await db.commit()
    print(f"\n✅ Seeded {len(machines)} laundry machines (Floors 1–3).")


async def main():
    print("=" * 50)
    print("  HostelOps AI — Admin Bootstrap")
    print("=" * 50)
    
    async with AsyncSessionLocal() as db:
        await create_admin_user(db)
        await seed_laundry_machines(db)
        await seed_default_config(db)
        print("✅ Hostel config seeded (or already exists).")

if __name__ == "__main__":
    asyncio.run(main())

