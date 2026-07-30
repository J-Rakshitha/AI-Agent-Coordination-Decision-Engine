"""
Code Review Agent
=================
When a merge conflict is predicted, reviews the affected file/function for
likely code-quality and style risks before resolution. Uses Hybrid AI
(LangChain LLM + rule-based fallback) and shared memory — same pattern as
the Resolution Suggestion Agent.
"""
from app.agents.llm.llm_client import HybridAIClient
from app.agents.llm.fallback_rules import fallback_code_review
from app.agents.llm.prompt_templates import CODE_REVIEW_PROMPT
from app.agents.coordinator_agent import CoordinatorAgent
from app.agents.memory_agent import MemoryAgent


class CodeReviewAgent:

    @staticmethod
    async def review(
        db,
        file_path: str,
        function_name: str,
        dev_a_name: str,
        dev_b_name: str,
        risk_score: float,
    ) -> dict:
        key_signature = f"review:{file_path}:{function_name or 'global'}"

        past_knowledge = await MemoryAgent.recall_knowledge(db, key_signature)
        recent_context = await MemoryAgent.recall_recent(db, module="dev_collab", limit=3)

        memory_context = ""
        if past_knowledge:
            memory_context += (
                f"\nLong-term memory (reviewed this target {past_knowledge.success_count}x before): "
                f"{past_knowledge.insight}"
            )
        if recent_context:
            memory_context += "\nShort-term memory (recent related activity):\n- " + "\n- ".join(recent_context)

        prompt = CODE_REVIEW_PROMPT.format(
            file_path=file_path,
            function_name=function_name or "(file-level)",
            dev_a_name=dev_a_name,
            dev_b_name=dev_b_name,
            risk_score=risk_score,
            memory_context=memory_context,
        )

        def fallback():
            if past_knowledge:
                return past_knowledge.insight
            return fallback_code_review(file_path, function_name, dev_a_name, dev_b_name, risk_score)

        result = await HybridAIClient.reason(prompt=prompt, fallback_fn=fallback)
        issues = CodeReviewAgent._extract_issues(result.text, file_path, risk_score)

        await CoordinatorAgent.log_decision(
            db=db,
            agent_name="Code Review Agent",
            module="dev_collab",
            decision_summary=result.text,
            used_llm=result.used_llm,
        )

        await MemoryAgent.remember(
            db, category="code_review", key_signature=key_signature, insight=result.text
        )

        return {"review": result.text, "issues": issues, "used_llm": result.used_llm}

    @staticmethod
    def _extract_issues(review_text: str, file_path: str, risk_score: float) -> list[str]:
        """Turn review prose into a structured issue list for APIs and notifications."""
        issues = []
        lower = review_text.lower()
        if risk_score >= 70:
            issues.append(f"High conflict risk ({risk_score}%) — coordinate before merging.")
        if file_path.endswith(".py") and "type hint" in lower:
            issues.append("Python: add type hints to public functions.")
        if file_path.endswith(".js") and ("const" in lower or "var" in lower):
            issues.append("JavaScript: prefer const/let over var.")
        if "test" in lower:
            issues.append("Ensure unit tests cover the overlapping changes.")
        if not issues:
            issues.append(review_text[:200] + ("..." if len(review_text) > 200 else ""))
        return issues
