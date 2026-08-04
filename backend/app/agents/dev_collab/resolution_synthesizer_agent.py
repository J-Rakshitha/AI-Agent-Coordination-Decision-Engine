"""
Resolution Synthesizer Agent — Phase 3
=======================================
Generates multiple merge strategies, scores them, and selects the best option.
"""
from __future__ import annotations

import json
import logging

from app.agents.coordinator_agent import CoordinatorAgent
from app.agents.llm.fallback_rules import fallback_resolution_strategies
from app.agents.llm.llm_client import HybridAIClient
from app.agents.llm.prompt_templates import RESOLUTION_SYNTHESIZER_PROMPT
from app.agents.memory_agent import MemoryAgent

logger = logging.getLogger("resolution_synthesizer_agent")


class ResolutionSynthesizerAgent:

    STRATEGIES = ["rebase_and_merge", "feature_branch_split", "pair_programming_sync"]

    @staticmethod
    async def synthesize(
        db,
        dev_a_name: str,
        dev_b_name: str,
        file_path: str,
        function_name: str | None,
        semantic_analysis: dict | None = None,
        quality_report: dict | None = None,
    ) -> dict:
        key_signature = f"synth:{file_path}:{function_name or 'global'}"

        past = await MemoryAgent.recall_knowledge(db, key_signature)
        memory_context = ""
        if past:
            memory_context = f"\nPrior synthesis ({past.success_count}x): {past.insight}"

        sem_risk = (semantic_analysis or {}).get("semantic_risk_score", 50)
        grade = (quality_report or {}).get("grade", "B")
        conflict_type = (semantic_analysis or {}).get("conflict_type", "concurrent_edit")

        prompt = RESOLUTION_SYNTHESIZER_PROMPT.format(
            dev_a_name=dev_a_name,
            dev_b_name=dev_b_name,
            file_path=file_path,
            function_name=function_name or "(file-level)",
            semantic_risk=sem_risk,
            conflict_type=conflict_type,
            quality_grade=grade,
            memory_context=memory_context,
        )

        def fallback():
            if past:
                return past.insight
            return fallback_resolution_strategies(
                dev_a_name, dev_b_name, file_path, function_name, sem_risk, conflict_type, grade
            )

        result = await HybridAIClient.reason(prompt=prompt, fallback_fn=fallback)
        options = ResolutionSynthesizerAgent._parse_options(
            result.text, dev_a_name, dev_b_name, sem_risk, conflict_type, grade
        )
        best = max(options, key=lambda o: o["score"])

        output = {
            "options": options,
            "best_strategy": best,
            "suggestion": best["description"],
            "used_llm": result.used_llm,
        }

        await CoordinatorAgent.log_decision(
            db=db,
            agent_name="Resolution Synthesizer Agent",
            module="dev_collab",
            decision_summary=(
                f"Selected '{best['strategy']}' (score {best['score']}) "
                f"from {len(options)} strategies for {file_path}."
            ),
            used_llm=result.used_llm,
        )

        await MemoryAgent.remember(
            db, category="resolution_synthesis", key_signature=key_signature, insight=best["description"]
        )

        return output

    @staticmethod
    def _parse_options(
        llm_text: str,
        dev_a: str,
        dev_b: str,
        sem_risk: float,
        conflict_type: str,
        grade: str,
    ) -> list[dict]:
        """Build structured strategy list from LLM prose + deterministic scoring."""
        base = fallback_resolution_strategies(dev_a, dev_b, "", None, sem_risk, conflict_type, grade)
        try:
            parsed = json.loads(base) if base.strip().startswith("[") else None
        except json.JSONDecodeError:
            parsed = None

        if parsed and isinstance(parsed, list):
            return parsed

        strategies = [
            {
                "strategy": "rebase_and_merge",
                "description": (
                    f"{dev_a} rebases onto {dev_b}'s latest commit, resolves conflicts in IDE, "
                    f"then {dev_b} reviews before merge. Best when changes are sequential."
                ),
                "score": 70 - int(sem_risk * 0.2),
                "risk": "medium",
            },
            {
                "strategy": "feature_branch_split",
                "description": (
                    f"Split '{conflict_type}' overlap: {dev_a} owns core logic, {dev_b} owns tests/docs. "
                    f"Merge via separate PRs to reduce collision surface."
                ),
                "score": 75 - int(sem_risk * 0.15) + (5 if grade == "C" else 0),
                "risk": "low",
            },
            {
                "strategy": "pair_programming_sync",
                "description": (
                    f"{dev_a} and {dev_b} pair for 30 min on shared screen, merge one combined change set. "
                    f"Recommended when semantic risk is {sem_risk}%."
                ),
                "score": 80 - int(sem_risk * 0.1) + (10 if sem_risk >= 60 else 0),
                "risk": "lowest",
            },
        ]

        if conflict_type == "signature_mismatch":
            strategies[0]["score"] -= 15
            strategies[2]["score"] += 10

        if llm_text and len(llm_text) > 50:
            strategies[2]["description"] += f" AI note: {llm_text[:120]}"

        for s in strategies:
            s["score"] = max(min(s["score"], 100), 10)

        return strategies
