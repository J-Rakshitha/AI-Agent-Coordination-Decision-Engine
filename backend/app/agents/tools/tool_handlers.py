"""
Tool Handlers — the actual API connectors registered into the Tool Registry.

Each handler is an async function with signature `(db, **kwargs) -> dict`
returning at minimum `{"success": bool, "output": ...}`. Handlers must
never raise for "expected" failure modes (they should catch and return
success=False) — the Tool Executor also wraps every call in a try/except
as a second safety net, so a badly-behaved handler still can't crash a
pipeline or a live demo.
"""
from app.agents.aiops.external_lookup_agent import ExternalLookupAgent
from app.agents.aiops.escalation_agent import EscalationAgent
from app.agents.aiops.remediation_agent import RemediationAgent, ACTION_LABELS
from app.agents.memory_agent import MemoryAgent
from app.agents.tools.tool_registry import Tool, register_tool


async def handler_github_issue_lookup(db, query: str = "", **kwargs) -> dict:
    """Real external API connector: GitHub public Issue Search."""
    results = await ExternalLookupAgent.find_related_issues(query or "incident")
    return {"success": True, "output": results}


async def handler_create_escalation_ticket(db, incident_id: int = 0, severity: str = "P2",
                                            reason: str = "", **kwargs) -> dict:
    """Enterprise ITSM-style connector: creates an escalation ticket with an SLA."""
    ticket = EscalationAgent.build_escalation(incident_id, severity, reason)
    return {"success": True, "output": ticket}


async def handler_query_knowledge_base(db, key_signature: str = "", **kwargs) -> dict:
    """Internal enterprise data source connector: the long-term memory store."""
    entry = await MemoryAgent.recall_knowledge(db, key_signature)
    if entry:
        return {"success": True, "output": entry.insight}
    return {"success": False, "output": "No matching knowledge base entry found."}


async def handler_restart_service(db, incident_id: int | None = None, **kwargs) -> dict:
    """Runbook-automation connector: restarts the affected service."""
    if incident_id:
        action = await RemediationAgent.perform_action(db, incident_id, "restart_service")
        return {"success": action.success, "output": action.notes}
    return {"success": True, "output": ACTION_LABELS["restart_service"] + " (simulated, no incident attached)"}


async def handler_clear_cache(db, incident_id: int | None = None, **kwargs) -> dict:
    """Runbook-automation connector: clears the affected service's cache."""
    if incident_id:
        action = await RemediationAgent.perform_action(db, incident_id, "clear_cache")
        return {"success": action.success, "output": action.notes}
    return {"success": True, "output": ACTION_LABELS["clear_cache"] + " (simulated, no incident attached)"}


def register_all_tools() -> None:
    register_tool(Tool(
        name="github_issue_lookup",
        description="Search GitHub's public issue tracker for reports matching an error pattern.",
        keywords=["github", "issue", "public", "report", "search", "lookup", "external", "known issue"],
        handler=handler_github_issue_lookup,
    ))
    register_tool(Tool(
        name="create_escalation_ticket",
        description="Create an enterprise ITSM escalation ticket with an SLA deadline for a human team.",
        keywords=["escalate", "ticket", "sla", "human", "team", "critical", "p1", "unresolved"],
        handler=handler_create_escalation_ticket,
    ))
    register_tool(Tool(
        name="query_knowledge_base",
        description="Look up this system's own long-term memory for a previously-seen pattern.",
        keywords=["memory", "knowledge", "past", "history", "seen before", "learned"],
        handler=handler_query_knowledge_base,
    ))
    register_tool(Tool(
        name="restart_service",
        description="Restart the affected service — fixes transient issues like connection pool exhaustion.",
        keywords=["restart", "connection pool", "timeout", "hang", "unresponsive"],
        handler=handler_restart_service,
    ))
    register_tool(Tool(
        name="clear_cache",
        description="Clear the affected service's cache — fixes stale-data or memory-growth issues.",
        keywords=["cache", "memory leak", "stale", "growing memory"],
        handler=handler_clear_cache,
    ))


# Populate the registry as soon as this module is imported.
register_all_tools()
