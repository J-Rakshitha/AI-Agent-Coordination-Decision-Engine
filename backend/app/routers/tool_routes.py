"""
Tool & System Integration API routes (Milestone 2).
Prefix: /api/tools
"""
from pydantic import BaseModel
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.agents.tools.tool_registry import list_tools_public
from app.agents.tools.tool_executor_agent import ToolExecutorAgent
# Importing this module populates the tool registry as a side effect.
from app.agents.tools import tool_handlers  # noqa: F401

router = APIRouter(prefix="/api/tools", tags=["Tool Integration"])


class SelectAndExecuteRequest(BaseModel):
    situation: str
    incident_id: int | None = None
    query: str | None = None
    key_signature: str | None = None
    severity: str | None = "P2"
    reason: str | None = ""


@router.get("/")
async def list_tools_endpoint(user: User = Depends(get_current_user)):
    """The custom enterprise tools/API connectors this system can invoke."""
    return list_tools_public()


@router.post("/select-and-execute")
async def select_and_execute(
    payload: SelectAndExecuteRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Given a natural-language situation, intelligently selects and invokes
    the best matching tool, with full exception handling — this call can
    never fail with a raw 500 from a bad tool call.
    """
    kwargs = {
        k: v for k, v in {
            "incident_id": payload.incident_id,
            "query": payload.query,
            "key_signature": payload.key_signature,
            "severity": payload.severity,
            "reason": payload.reason,
        }.items() if v is not None
    }
    return await ToolExecutorAgent.select_and_execute(db, payload.situation, **kwargs)


@router.get("/accuracy")
async def tool_accuracy(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Validate action execution accuracy — measured success rate, overall and per-tool."""
    return await ToolExecutorAgent.get_accuracy_stats(db)
