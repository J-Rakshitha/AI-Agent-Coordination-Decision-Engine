"""
MCP Server — Phase D: Industry-standard tool exposure
========================================================
Exposes the same enterprise tools from TOOL_REGISTRY via Model Context Protocol,
so external AI clients (Cursor, Claude Desktop) can invoke them.

Run standalone:
    cd backend && python -m app.mcp_server

Or configure in Cursor ~/.cursor/mcp.json (see README).
"""
import json

from mcp.server.fastmcp import FastMCP

from app.core.database import AsyncSessionLocal
from app.agents.tools import tool_handlers  # noqa: F401 — populates registry
from app.agents.tools.tool_registry import list_tools_public
from app.agents.tools.tool_executor_agent import ToolExecutorAgent
from app.agents.dev_collab.github_integration_agent import GitHubIntegrationAgent
from app.agents.dev_collab.conflict_prediction_agent import ConflictPredictionAgent
from app.agents.dev_collab.code_watch_agent import CodeWatchAgent
from app.agents.aiops.server_monitor_agent import ServerMonitorAgent
from app.services.monitoring_scheduler import get_monitor_targets
from app.core.config import settings

mcp = FastMCP(
    "Development of Enterprise Workflow Platform with Decision Automation System",
    instructions=(
        "Enterprise multi-agent coordination engine for Dev-Collaboration "
        "conflict prevention and AIOps incident response. Tools mirror the "
        "REST /api/tools registry plus monitoring and GitHub sync."
    ),
)


async def _with_db(coro_factory):
    async with AsyncSessionLocal() as db:
        return await coro_factory(db)


@mcp.tool()
async def list_available_tools() -> str:
    """List all registered enterprise tools with descriptions."""
    return json.dumps(list_tools_public(), indent=2)


@mcp.tool()
async def github_issue_lookup(query: str) -> str:
    """Search GitHub's public issue tracker for reports matching an error pattern."""
    from app.agents.tools.tool_handlers import handler_github_issue_lookup
    result = await _with_db(lambda db: handler_github_issue_lookup(db, query=query))
    return json.dumps(result, default=str)


@mcp.tool()
async def create_escalation_ticket(incident_id: int, severity: str = "P2", reason: str = "") -> str:
    """Create an enterprise ITSM escalation ticket with SLA deadline."""
    from app.agents.tools.tool_handlers import handler_create_escalation_ticket
    result = await _with_db(
        lambda db: handler_create_escalation_ticket(db, incident_id=incident_id, severity=severity, reason=reason)
    )
    return json.dumps(result, default=str)


@mcp.tool()
async def query_knowledge_base(key_signature: str) -> str:
    """Look up long-term agent memory for a previously-seen pattern."""
    from app.agents.tools.tool_handlers import handler_query_knowledge_base
    result = await _with_db(lambda db: handler_query_knowledge_base(db, key_signature=key_signature))
    return json.dumps(result, default=str)


@mcp.tool()
async def restart_service(incident_id: int | None = None) -> str:
    """Restart the affected service — fixes connection pool / timeout issues."""
    from app.agents.tools.tool_handlers import handler_restart_service
    result = await _with_db(lambda db: handler_restart_service(db, incident_id=incident_id))
    return json.dumps(result, default=str)


@mcp.tool()
async def clear_cache(incident_id: int | None = None) -> str:
    """Clear the affected service cache — fixes stale-data issues."""
    from app.agents.tools.tool_handlers import handler_clear_cache
    result = await _with_db(lambda db: handler_clear_cache(db, incident_id=incident_id))
    return json.dumps(result, default=str)


@mcp.tool()
async def select_and_execute_tool(situation: str, incident_id: int | None = None) -> str:
    """Intelligently select and execute the best tool for a natural-language situation."""
    async def _run(db):
        return await ToolExecutorAgent.select_and_execute(db, situation, incident_id=incident_id)
    result = await _with_db(_run)
    return json.dumps(result, default=str)


@mcp.tool()
async def check_service_health(service_name: str | None = None) -> str:
    """Run a live HTTP health probe on monitored services (real, not simulated)."""
    targets = get_monitor_targets()
    if service_name:
        targets = [t for t in targets if t["name"] == service_name]
    results = []
    for t in targets:
        probe = await ServerMonitorAgent.probe(t["name"], t["url"])
        results.append(probe)
    return json.dumps(results, default=str)


@mcp.tool()
async def sync_github_conflicts() -> str:
    """Fetch live open PRs from the configured GitHub repo and detect real conflicts."""
    async def _sync(db):
        result = await GitHubIntegrationAgent.fetch_open_pull_requests()
        if not result["connected"]:
            return {"synced": False, "error": result["error"]}
        found = GitHubIntegrationAgent.find_real_conflicts(result["pull_requests"])
        created = 0
        for fc in found:
            dev_a = await CodeWatchAgent.get_or_create_developer(db, fc["dev_a"], avatar_color="#4F8CFF")
            dev_b = await CodeWatchAgent.get_or_create_developer(db, fc["dev_b"], avatar_color="#FF6B6B")
            await ConflictPredictionAgent.create_conflict_event(
                db,
                file_path=fc["file_path"],
                function_name=fc["function_name"],
                dev_a_id=dev_a.id,
                dev_b_id=dev_b.id,
                risk_score=fc["risk_score"],
                source="github",
                source_url=fc.get("source_url"),
            )
            created += 1
        return {"synced": True, "pull_requests_checked": len(result["pull_requests"]), "conflicts_found": created}

    result = await _with_db(_sync)
    return json.dumps(result, default=str)


@mcp.resource("config://monitor-targets")
def monitor_targets_resource() -> str:
    """Configured real-time monitoring targets (backend + external)."""
    return json.dumps({
        "monitoring_enabled": settings.MONITORING_ENABLED,
        "interval_seconds": settings.MONITOR_INTERVAL_SECONDS,
        "targets": get_monitor_targets(),
    }, indent=2)


if __name__ == "__main__":
    mcp.run(transport="stdio")
