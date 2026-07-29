"""
Seed demo users on first startup — Phase C
"""
import logging

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.user import User

logger = logging.getLogger("seed_users")

DEMO_USERS = [
    {"email": "priya@infosys.com", "password": "demo123", "full_name": "Priya Sharma", "role": "developer"},
    {"email": "arjun@infosys.com", "password": "demo123", "full_name": "Arjun Mehta", "role": "developer"},
    {"email": "admin@infosys.com", "password": "admin123", "full_name": "Admin User", "role": "admin"},
]


async def seed_demo_users() -> None:
    async with AsyncSessionLocal() as db:
        for spec in DEMO_USERS:
            existing = await db.execute(select(User).where(User.email == spec["email"]))
            if existing.scalars().first():
                continue
            db.add(User(
                email=spec["email"],
                hashed_password=hash_password(spec["password"]),
                full_name=spec["full_name"],
                role=spec["role"],
            ))
        await db.commit()
    logger.info("Demo users ready (priya@, arjun@, admin@infosys.com).")
