"""
Semantic Analysis Agent — Phase 2
==================================
Logic-level conflict analysis using AST diff + Hybrid AI reasoning.
"""
from __future__ import annotations

import json
import logging

from app.agents.coordinator_agent import CoordinatorAgent
from app.agents.llm.fallback_rules import fallback_semantic_analysis
from app.agents.llm.llm_client import HybridAIClient
from app.agents.llm.prompt_templates import SEMANTIC_ANALYSIS_PROMPT
from app.agents.memory_agent import MemoryAgent
from app.services.code_parser import ast_diff_summary, find_symbol, scan_local_repository

logger = logging.getLogger("semantic_analysis_agent")


class SemanticAnalysisAgent:

    @staticmethod
    async def analyze(
        db,
        file_path: str,
        function_name: str | None,
        dev_a_name: str,
        dev_b_name: str,
        risk_score: float,
        discovery_context: dict | None = None,
    ) -> dict:
        key_signature = f"semantic:{file_path}:{function_name or 'global'}"

        snippet = ""
        target_meta = (discovery_context or {}).get("target_symbol")
        if target_meta and target_meta.get("source_snippet"):
            snippet = target_meta["source_snippet"]
        else:
            symbols = scan_local_repository(max_files=40)
            target = find_symbol(symbols, file_path, function_name)
            snippet = target.source_snippet if target else ""

        ast_report = ast_diff_summary(snippet, snippet)
        if discovery_context and discovery_context.get("target_symbol"):
            ts = discovery_context["target_symbol"]
            ast_report["target_complexity"] = ts.get("complexity")
            ast_report["target_dependencies"] = ts.get("dependencies", [])

        past = await MemoryAgent.recall_knowledge(db, key_signature)
        memory_context = ""
        if past:
            memory_context = f"\nPrior semantic analysis ({past.success_count}x): {past.insight}"

        prompt = SEMANTIC_ANALYSIS_PROMPT.format(
            file_path=file_path,
            function_name=function_name or "(file-level)",
            dev_a_name=dev_a_name,
            dev_b_name=dev_b_name,
            risk_score=risk_score,
            ast_report=json.dumps(ast_report, indent=2),
            source_snippet=snippet[:1500] or "(no local source available)",
            memory_context=memory_context,
        )

        def fallback():
            if past:
                return past.insight
            return fallback_semantic_analysis(
                file_path, function_name, dev_a_name, dev_b_name, risk_score, ast_report
            )

        result = await HybridAIClient.reason(prompt=prompt, fallback_fn=fallback)

        semantic_risk = SemanticAnalysisAgent._compute_semantic_risk(ast_report, risk_score, result.text)

        analysis = {
            "semantic_risk_score": semantic_risk,
            "ast_diff": ast_report,
            "analysis_text": result.text,
            "conflict_type": SemanticAnalysisAgent._classify_conflict(ast_report, result.text),
            "used_llm": result.used_llm,
        }

        await CoordinatorAgent.log_decision(
            db=db,
            agent_name="Semantic Analysis Agent",
            module="dev_collab",
            decision_summary=f"Semantic risk {semantic_risk}% — {analysis['conflict_type']}: {result.text[:200]}",
            used_llm=result.used_llm,
        )

        await MemoryAgent.remember(
            db, category="semantic_analysis", key_signature=key_signature, insight=result.text
        )

        return analysis

    @staticmethod
    def _compute_semantic_risk(ast_report: dict, base_risk: float, text: str) -> float:
        score = base_risk * 0.6
        if ast_report.get("signature_changed"):
            score += 20
        if ast_report.get("functions_added") or ast_report.get("functions_removed"):
            score += 10
        cx_a = ast_report.get("complexity_a", 1)
        cx_b = ast_report.get("complexity_b", 1)
        if abs(cx_a - cx_b) > 3:
            score += 8
        lower = text.lower()
        if any(w in lower for w in ("breaking", "incompatible", "logic", "side effect")):
            score += 12
        return min(round(score, 1), 100.0)

    @staticmethod
    def _classify_conflict(ast_report: dict, text: str) -> str:
        if ast_report.get("signature_changed"):
            return "signature_mismatch"
        if ast_report.get("functions_added") or ast_report.get("functions_removed"):
            return "structural_divergence"
        lower = text.lower()
        if "logic" in lower or "behavior" in lower:
            return "logic_conflict"
        if "dependency" in lower or "import" in lower:
            return "dependency_overlap"
        return "concurrent_edit"
