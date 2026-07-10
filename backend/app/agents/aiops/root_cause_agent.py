"""
Root-Cause Analysis Agent
==========================
Given an anomaly, explains WHY it likely happened. Uses Hybrid AI
(LangChain-wrapped LLM, with rule-based fallback) AND Memory:

  - Long-term memory: checks the Knowledge Base first for this exact
    service+error pattern. If seen before, that prior insight is fed to the
    LLM as context (and used directly as the fallback if the LLM is down).
  - Short-term memory: recent related decisions are included as context so
    the agent reasons with situational awareness, not in isolation.
"""
from app.agents.llm.llm_client import HybridAIClient
from app.agents.llm.fallback_rules import fallback_root_cause
from app.agents.llm.prompt_templates import ROOT_CAUSE_PROMPT
from app.agents.coordinator_agent import CoordinatorAgent
from app.agents.memory_agent import MemoryAgent


class RootCauseAgent:

    @staticmethod
    async def analyze(db, service_name: str, error_signature: str, raw_metrics: dict) -> dict:
        key_signature = f"{service_name}:{error_signature}"

        # Long-term memory lookup — have we seen this exact pattern before?
        past_knowledge = await MemoryAgent.recall_knowledge(db, key_signature)
        # Short-term memory — what has this module been doing recently?
        recent_context = await MemoryAgent.recall_recent(db, module="aiops", limit=3)

        memory_context = ""
        if past_knowledge:
            memory_context += (
                f"\nLong-term memory (seen {past_knowledge.success_count}x before): "
                f"{past_knowledge.insight}"
            )
        if recent_context:
            memory_context += "\nShort-term memory (recent related activity):\n- " + "\n- ".join(recent_context)

        prompt = ROOT_CAUSE_PROMPT.format(
            service_name=service_name,
            raw_metrics=raw_metrics,
            error_signature=error_signature,
            memory_context=memory_context,
        )

        def fallback():
            if past_knowledge:
                return past_knowledge.insight
            return fallback_root_cause(service_name, error_signature)

        result = await HybridAIClient.reason(prompt=prompt, fallback_fn=fallback)

        await CoordinatorAgent.log_decision(
            db=db,
            agent_name="Root-Cause Analysis Agent",
            module="aiops",
            decision_summary=result.text,
            used_llm=result.used_llm,
        )

        # Reinforce long-term memory with this outcome for next time.
        await MemoryAgent.remember(
            db, category="incident_resolution", key_signature=key_signature, insight=result.text
        )

        return {"root_cause": result.text, "used_llm": result.used_llm}
