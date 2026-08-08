"""Per-user GitHub repository submit and scan."""
import re
from datetime import datetime
from urllib.parse import urlparse

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.dev_collab.repository_discovery_agent import RepositoryDiscoveryAgent
from app.models.user import User
from app.models.workflow import UserRepo
from app.routers.websocket_routes import manager


def _parse_repo_url(repo_url: str) -> tuple[str, str, str]:
    url = repo_url.strip().rstrip("/")
    if url.startswith("http"):
        path = urlparse(url).path.strip("/")
    else:
        path = url
    parts = path.split("/")
    if len(parts) < 2:
        raise ValueError("Invalid repo URL — use owner/repo or https://github.com/owner/repo")
    owner, name = parts[0], parts[1].replace(".git", "")
    normalized = f"https://github.com/{owner}/{name}"
    return normalized, owner, name


async def submit_user_repo(db: AsyncSession, user: User, repo_url: str) -> dict:
    normalized, owner, name = _parse_repo_url(repo_url)

    discovery = await RepositoryDiscoveryAgent.discover(db)
    symbols = discovery.get("context", {}).get("symbols_indexed", 0)
    conflicts = discovery.get("context", {}).get("conflicts_found", 0)

    stmt = select(UserRepo).where(UserRepo.user_id == user.id)
    result = await db.execute(stmt)
    existing = result.scalars().first()
    now = datetime.utcnow()

    if existing:
        existing.repo_url = normalized
        existing.repo_owner = owner
        existing.repo_name = name
        existing.symbols_indexed = symbols
        existing.conflicts_found = conflicts
        existing.last_scanned_at = now
        repo = existing
    else:
        repo = UserRepo(
            user_id=user.id,
            repo_url=normalized,
            repo_owner=owner,
            repo_name=name,
            symbols_indexed=symbols,
            conflicts_found=conflicts,
            last_scanned_at=now,
        )
        db.add(repo)

    await db.commit()
    await db.refresh(repo)

    await manager.broadcast("repo_scanned", {
        "user_id": user.id,
        "repo_owner": owner,
        "repo_name": name,
    })

    return {
        "repo_url": normalized,
        "repo_owner": owner,
        "repo_name": name,
        "symbols_indexed": symbols,
        "conflicts_found": conflicts,
        "last_scanned_at": repo.last_scanned_at,
    }


async def get_user_repo(db: AsyncSession, user: User) -> dict:
    stmt = select(UserRepo).where(UserRepo.user_id == user.id)
    result = await db.execute(stmt)
    repo = result.scalars().first()
    if not repo:
        return {"connected": False}
    return {
        "connected": True,
        "repo_url": repo.repo_url,
        "repo_owner": repo.repo_owner,
        "repo_name": repo.repo_name,
        "symbols_indexed": repo.symbols_indexed,
        "conflicts_found": repo.conflicts_found,
        "last_scanned_at": repo.last_scanned_at,
    }


async def recheck_user_repo(db: AsyncSession, user: User) -> dict:
    stmt = select(UserRepo).where(UserRepo.user_id == user.id)
    result = await db.execute(stmt)
    repo = result.scalars().first()
    if not repo:
        raise ValueError("No repository connected for this user")
    return await submit_user_repo(db, user, repo.repo_url)
