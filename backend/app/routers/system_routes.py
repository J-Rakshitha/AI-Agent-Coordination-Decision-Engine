"""
System / Demo Control routes.
Prefix: /api/system
Includes the health check, aggregate stats, and the "Simulate API Failure"
toggle used to PROVE the hybrid fallback works live during the demo.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.models.incident import AgentDecisionLog, Incident
from app.models.dev_collab import FileEditSession, ConflictEvent
from app.agents.llm.llm_client import set_simulated_failure, get_simulated_failure
from app.agents.memory_agent import MemoryAgent
from app.core.config import settings

router = APIRouter(prefix="/api/system", tags=["System"])


@router.get("/health")
async def health_check():
    return {"status": "ok", "app": settings.APP_NAME, "env": settings.ENV}


@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Aggregate counts for the Overview dashboard's stat cards."""
    active_sessions = await db.scalar(
        select(func.count()).select_from(FileEditSession).where(FileEditSession.is_active == True)  # noqa: E712
    )
    conflicts_predicted = await db.scalar(select(func.count()).select_from(ConflictEvent))
    open_incidents = await db.scalar(
        select(func.count()).select_from(Incident).where(Incident.status.in_(["open", "escalated"]))
    )
    linked_incidents = await db.scalar(
        select(func.count()).select_from(Incident).where(Incident.linked_commit_id.isnot(None))
    )
    return {
        "active_edit_sessions": active_sessions or 0,
        "conflicts_predicted": conflicts_predicted or 0,
        "open_incidents": open_incidents or 0,
        "linked_incidents": linked_incidents or 0,
    }


@router.get("/knowledge-base")
async def get_knowledge_base(db: AsyncSession = Depends(get_db)):
    """
    Shared Knowledge & Memory Management (long-term memory) — the persistent
    insights agents have built up over time. Exposed as a REST endpoint so
    other enterprise tools/dashboards could also consume this institutional
    knowledge (this is the 'Tool & System Integration' surface).
    """
    entries = await MemoryAgent.list_recent_knowledge(db)
    return [
        {
            "id": e.id, "category": e.category, "key_signature": e.key_signature,
            "insight": e.insight, "success_count": e.success_count,
            "last_used_at": e.last_used_at,
        }
        for e in entries
    ]


@router.post("/toggle-llm-failure")
async def toggle_llm_failure(enabled: bool):
    """
    Demo control: force every agent to use the rule-based fallback,
    to prove live on stage that the system never crashes even if the
    LLM API is down.
    """
    set_simulated_failure(enabled)
    return {"simulated_llm_failure": enabled}


@router.get("/llm-failure-status")
async def llm_failure_status():
    """Lets the frontend toggle switch reflect the current state on page load."""
    return {"simulated_llm_failure": get_simulated_failure()}


@router.get("/decision-log")
async def get_decision_log(db: AsyncSession = Depends(get_db)):
    """Explainable-AI trail: every decision any agent has made, across both modules."""
    result = await db.execute(select(AgentDecisionLog).order_by(AgentDecisionLog.created_at.desc()).limit(50))
    logs = result.scalars().all()
    return [
        {
            "id": l.id, "agent_name": l.agent_name, "module": l.module,
            "decision_summary": l.decision_summary, "used_llm": l.used_llm,
            "created_at": l.created_at,
        }
        for l in logs
    ]
