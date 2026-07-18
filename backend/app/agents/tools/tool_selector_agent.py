"""
Tool Selector Agent — Milestone 2: "Implement intelligent tool selection mechanisms"
========================================================================================
Given a natural-language description of the current situation, chooses the
single best tool from the registry. Hybrid strategy, consistent with the
rest of the system:

  - LLM-based selection (LangChain ChatPromptTemplate + Gemini) when available.
  - Deterministic keyword-overlap scoring as the rule-based fallback — this
    guarantees a tool is ALWAYS selected, even with zero network/API access.

The LLM's answer is validated against the real registry before being
trusted — if it hallucinates a tool name that doesn't exist, we silently
fall back to the rule-based selector rather than failing the request.
"""
from app.agents.llm.llm_client import HybridAIClient
from app.agents.llm.prompt_templates import TOOL_SELECTION_PROMPT
from app.agents.tools.tool_registry import list_tools
from app.agents.coordinator_agent import CoordinatorAgent


class ToolSelectorAgent:

    @staticmethod
    def rule_based_select(situation: str) -> str:
        """Deterministic keyword-overlap scoring — always returns a valid tool name."""
        situation_lower = situation.lower()
        tools = list_tools()
        best_tool, best_score = tools[0], -1
        for tool in tools:
            score = sum(1 for kw in tool.keywords if kw in situation_lower)
            if score > best_score:
                best_score, best_tool = score, tool
        return best_tool.name

    @staticmethod
    async def select_tool(db, situation: str) -> dict:
        tools = list_tools()
        tool_descriptions = "\n".join(f"- {t.name}: {t.description}" for t in tools)
        prompt = TOOL_SELECTION_PROMPT.format(situation=situation, tool_descriptions=tool_descriptions)

        def fallback():
            return ToolSelectorAgent.rule_based_select(situation)

        result = await HybridAIClient.reason(prompt=prompt, fallback_fn=fallback)

        valid_names = {t.name for t in tools}
        chosen_name = result.text.strip().strip(".").lower().replace(" ", "_")
        used_llm = result.used_llm

        if chosen_name not in valid_names:
            # LLM (or a malformed fallback) didn't return a real tool name —
            # never let that break the pipeline; fall back deterministically.
            chosen_name = ToolSelectorAgent.rule_based_select(situation)
            used_llm = False

        await CoordinatorAgent.log_decision(
            db=db,
            agent_name="Tool Selector Agent",
            module="aiops",
            decision_summary=f"Selected tool '{chosen_name}' for situation: {situation}",
            used_llm=used_llm,
        )

        return {"tool_name": chosen_name, "used_llm": used_llm}
