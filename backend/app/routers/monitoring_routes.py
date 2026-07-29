"""
Monitoring API routes — Phase B
Prefix: /api/monitoring
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.database import get_db
from app.models.monitoring import ServiceHealthSnapshot
from app.services.monitoring_scheduler import get_monitor_targets

router = APIRouter(prefix="/api/monitoring", tags=["Server Monitoring"])


@router.get("/status")
async def monitoring_status(db: AsyncSession = Depends(get_db)):
    """Latest health snapshot per monitored service (real probe data, not hardcoded)."""
    targets = get_monitor_targets()
    services = []

    for target in targets:
        result = await db.execute(
            select(ServiceHealthSnapshot)
            .where(ServiceHealthSnapshot.service_name == target["name"])
            .order_by(ServiceHealthSnapshot.checked_at.desc())
            .limit(1)
        )
        snap = result.scalars().first()
        if snap:
            services.append({
                "service_name": snap.service_name,
                "url": snap.url,
                "status_code": snap.status_code,
                "response_time_ms": snap.response_time_ms,
                "error_rate_pct": snap.error_rate_pct,
                "healthy": snap.healthy,
                "checked_at": snap.checked_at,
            })
        else:
            services.append({
                "service_name": target["name"],
                "url": target["url"],
                "status_code": None,
                "response_time_ms": None,
                "error_rate_pct": None,
                "healthy": None,
                "checked_at": None,
            })

    return {
        "monitoring_enabled": settings.MONITORING_ENABLED,
        "interval_seconds": settings.MONITOR_INTERVAL_SECONDS,
        "services": services,
    }


@router.get("/history/{service_name}")
async def monitoring_history(service_name: str, limit: int = 20, db: AsyncSession = Depends(get_db)):
    """Recent probe history for charts / debugging."""
    result = await db.execute(
        select(ServiceHealthSnapshot)
        .where(ServiceHealthSnapshot.service_name == service_name)
        .order_by(ServiceHealthSnapshot.checked_at.desc())
        .limit(min(limit, 100))
    )
    snaps = result.scalars().all()
    return [
        {
            "response_time_ms": s.response_time_ms,
            "status_code": s.status_code,
            "healthy": s.healthy,
            "checked_at": s.checked_at,
        }
        for s in snaps
    ]
