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

# Ensure imports resolve from backend/
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from config import settings
from models.user import User
from schemas.enums import HostelMode, UserRole
from services.auth_service import hash_password


def get_sync_engine():
    """Create a synchronous engine for this standalone script."""
    sync_url = settings.DATABASE_URL.replace("postgresql+asyncpg", "postgresql+psycopg2")
    return create_engine(sync_url, pool_pre_ping=True)


def create_admin() -> None:
    print("=" * 50)
    print("  HostelOps AI — Admin Bootstrap")
    print("=" * 50)

    engine = get_sync_engine()
    Session = sessionmaker(bind=engine)

    with Session() as session:
        # Check if any assistant_warden already exists
        result = session.execute(
            select(User).where(
                User.role == UserRole.assistant_warden,
                User.is_active == True,
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            print(f"\n✅ Admin already exists: '{existing.name}' (Room: {existing.room_number})")
            print("   No action taken. Admin setup is already complete.")
            return

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
        dup = session.execute(
            select(User).where(User.room_number == room_number)
        ).scalar_one_or_none()
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
            role=UserRole.assistant_warden,
            hostel_mode=HostelMode.college,
            hashed_password=hash_password(password),
            is_verified=True,
            is_active=True,
        )
        session.add(admin)
        session.commit()
        session.refresh(admin)

        print(f"\n✅ Admin created successfully!")
        print(f"   Name:        {admin.name}")
        print(f"   Room/Login:  {admin.room_number}")
        print(f"   Role:        {admin.role.value}")
        print(f"   Verified:    {admin.is_verified}")
        print(f"   User ID:     {admin.id}")
        print("\nYou can now log in via POST /api/auth/login with these credentials.")


if __name__ == "__main__":
    create_admin()
