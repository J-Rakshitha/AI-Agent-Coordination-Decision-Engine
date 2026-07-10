"""
Resolution Suggestion Agent
============================
When a conflict is detected/predicted, this agent drafts a suggestion for
how the two developers should proceed. Uses the Hybrid AI Client (LangChain
LLM + rule-based fallback) AND Memory:

  - Long-term memory: checks the Knowledge Base for this exact file+function
    pattern — if two devs have collided here before, that prior resolution
    is reused as context (and as the fallback if the LLM is unavailable).
  - Short-term memory: recent conflict-resolution activity is included as
    context.
"""
from app.agents.llm.llm_client import HybridAIClient
from app.agents.llm.fallback_rules import fallback_conflict_suggestion
from app.agents.llm.prompt_templates import CONFLICT_RESOLUTION_PROMPT
from app.agents.coordinator_agent import CoordinatorAgent
from app.agents.memory_agent import MemoryAgent


class ResolutionSuggestionAgent:

    @staticmethod
    async def suggest(db, dev_a_name: str, dev_b_name: str, file_path: str, function_name: str) -> dict:
        key_signature = f"{file_path}:{function_name}"

        past_knowledge = await MemoryAgent.recall_knowledge(db, key_signature)
        recent_context = await MemoryAgent.recall_recent(db, module="dev_collab", limit=3)

        memory_context = ""
        if past_knowledge:
            memory_context += (
                f"\nLong-term memory (this file/function has collided {past_knowledge.success_count}x before): "
                f"{past_knowledge.insight}"
            )
        if recent_context:
            memory_context += "\nShort-term memory (recent related activity):\n- " + "\n- ".join(recent_context)

        prompt = CONFLICT_RESOLUTION_PROMPT.format(
            dev_a_name=dev_a_name,
            dev_b_name=dev_b_name,
            function_name=function_name,
            file_path=file_path,
            memory_context=memory_context,
        )

        def fallback():
            if past_knowledge:
                return past_knowledge.insight
            return fallback_conflict_suggestion(dev_a_name, dev_b_name, file_path, function_name)

        result = await HybridAIClient.reason(prompt=prompt, fallback_fn=fallback)

        await CoordinatorAgent.log_decision(
            db=db,
            agent_name="Resolution Suggestion Agent",
            module="dev_collab",
            decision_summary=result.text,
            used_llm=result.used_llm,
        )

        await MemoryAgent.remember(
            db, category="conflict_pattern", key_signature=key_signature, insight=result.text
        )

        return {"suggestion": result.text, "used_llm": result.used_llm}
