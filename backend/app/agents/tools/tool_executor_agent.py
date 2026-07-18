"""
Tool Executor Agent — Milestone 2: "Test tool invocation workflows and
exception handling" + "Validate action execution accuracy"
========================================================================
Selects (via ToolSelectorAgent) and invokes a tool, with a hard safety net:
ANY exception raised by a tool handler is caught here so a single bad tool
call can never crash the pipeline or the live demo. Every invocation —
success or failure — is recorded to ToolExecutionLog, which is what
/api/tools/accuracy uses to report real, measured success-rate statistics
rather than an assumed one.
"""
from sqlalchemy import select, func, Integer

from app.agents.tools.tool_registry import get_tool
from app.agents.tools.tool_selector_agent import ToolSelectorAgent
from app.models.tool_execution import ToolExecutionLog


class ToolExecutorAgent:

    @staticmethod
    async def select_and_execute(db, situation: str, **kwargs) -> dict:
        selection = await ToolSelectorAgent.select_tool(db, situation)
        tool_name = selection["tool_name"]
        tool = get_tool(tool_name)

        if tool is None:
            # Should be unreachable (selector only returns registry names),
            # but handled explicitly so this can never 500.
            success, output, error = False, None, f"Unknown tool '{tool_name}'"
        else:
            try:
                result = await tool.handler(db, **kwargs)
                success = bool(result.get("success", False))
                output = result.get("output")
                error = None
            except Exception as exc:
                success = False
                output = None
                error = str(exc)

        log = ToolExecutionLog(
            tool_name=tool_name,
            situation=situation,
            used_llm_selection=selection["used_llm"],
            success=success,
            output=str(output)[:1000] if output is not None else None,
            error=error,
        )
        db.add(log)
        await db.commit()
        await db.refresh(log)

        return {
            "tool_name": tool_name,
            "used_llm_selection": selection["used_llm"],
            "success": success,
            "output": output,
            "error": error,
        }

    @staticmethod
    async def get_accuracy_stats(db) -> dict:
        """Validate action execution accuracy — real measured stats, not an assumption."""
        total = await db.scalar(select(func.count()).select_from(ToolExecutionLog))
        successful = await db.scalar(
            select(func.count()).select_from(ToolExecutionLog).where(ToolExecutionLog.success == True)  # noqa: E712
        )
        total = total or 0
        successful = successful or 0
        accuracy_pct = round((successful / total) * 100, 1) if total > 0 else None

        stmt = select(
            ToolExecutionLog.tool_name,
            func.count().label("total"),
            func.sum(ToolExecutionLog.success.cast(Integer)).label("successes"),
        ).group_by(ToolExecutionLog.tool_name)
        result = await db.execute(stmt)
        per_tool = [
            {
                "tool_name": row.tool_name,
                "total": row.total,
                "successes": row.successes or 0,
                "accuracy_pct": round(((row.successes or 0) / row.total) * 100, 1) if row.total else 0,
            }
            for row in result.all()
        ]

        return {
            "total_executions": total,
            "successful_executions": successful,
            "overall_accuracy_pct": accuracy_pct,
            "per_tool": per_tool,
        }
