"""
Quality Agent — Phase 4
========================
Structured code-quality scorecard from real AST metrics + Hybrid AI review.
"""
from __future__ import annotations

import json
import logging

from app.agents.coordinator_agent import CoordinatorAgent
from app.agents.llm.fallback_rules import fallback_quality_report
from app.agents.llm.llm_client import HybridAIClient
from app.agents.llm.prompt_templates import QUALITY_SCORECARD_PROMPT
from app.services.code_parser import find_symbol, scan_local_repository

logger = logging.getLogger("quality_agent")

GRADE_THRESHOLDS = {"A": 85, "B": 65, "C": 0}


class QualityAgent:

    @staticmethod
    async def evaluate(
        db,
        file_path: str,
        function_name: str | None,
        risk_score: float,
        semantic_risk: float | None = None,
        discovery_context: dict | None = None,
    ) -> dict:
        target = None
        target_meta = (discovery_context or {}).get("target_symbol")
        if target_meta:
            from app.services.code_parser import SymbolInfo

            target = SymbolInfo(
                file_path=target_meta.get("file_path", file_path),
                symbol_type=target_meta.get("symbol_type", "function"),
                name=target_meta.get("name", function_name or ""),
                line_start=target_meta.get("line_start", 1),
                line_end=target_meta.get("line_end", 1),
                dependencies=target_meta.get("dependencies", []),
                complexity=target_meta.get("complexity", 5),
                source_snippet=target_meta.get("source_snippet", ""),
            )
        else:
            symbols = scan_local_repository(max_files=40)
            target = find_symbol(symbols, file_path, function_name)

        metrics = QualityAgent._compute_metrics(target, file_path, risk_score, semantic_risk)

        prompt = QUALITY_SCORECARD_PROMPT.format(
            file_path=file_path,
            function_name=function_name or "(file-level)",
            metrics_json=json.dumps(metrics, indent=2),
            source_snippet=(target.source_snippet[:1200] if target else "(no source)"),
        )

        def fallback():
            return fallback_quality_report(metrics)

        result = await HybridAIClient.reason(prompt=prompt, fallback_fn=fallback)
        grade = QualityAgent._score_to_grade(metrics["quality_score"])

        report = {
            "grade": grade,
            "quality_score": metrics["quality_score"],
            "metrics": metrics,
            "recommendations": QualityAgent._extract_recommendations(result.text, metrics),
            "report_text": result.text,
            "used_llm": result.used_llm,
        }

        await CoordinatorAgent.log_decision(
            db=db,
            agent_name="Quality Agent",
            module="dev_collab",
            decision_summary=f"Quality grade {grade} ({metrics['quality_score']}/100) for {file_path}",
            used_llm=result.used_llm,
        )

        return report

    @staticmethod
    def _compute_metrics(target, file_path: str, risk_score: float, semantic_risk: float | None) -> dict:
        complexity = target.complexity if target else 5
        lines = (target.line_end - target.line_start + 1) if target else 0
        deps = len(target.dependencies) if target else 0

        score = 100.0
        if complexity > 15:
            score -= 25
        elif complexity > 10:
            score -= 15
        elif complexity > 6:
            score -= 8

        if lines > 80:
            score -= 15
        elif lines > 50:
            score -= 8

        if deps > 20:
            score -= 10
        elif deps > 12:
            score -= 5

        score -= risk_score * 0.15
        if semantic_risk:
            score -= semantic_risk * 0.1

        snippet = target.source_snippet if target else ""
        has_docstring = '"""' in snippet or "'''" in snippet
        if not has_docstring and target and target.symbol_type == "function":
            score -= 5

        if file_path.endswith(".py") and target:
            has_type_hints = ": " in snippet.split("\n", 3)[-1] if snippet else False
            if not has_type_hints:
                score -= 5

        return {
            "cyclomatic_complexity": complexity,
            "line_count": lines,
            "dependency_count": deps,
            "has_docstring": has_docstring,
            "risk_penalty": round(risk_score * 0.15, 1),
            "quality_score": max(round(score, 1), 0),
        }

    @staticmethod
    def _score_to_grade(score: float) -> str:
        if score >= GRADE_THRESHOLDS["A"]:
            return "A"
        if score >= GRADE_THRESHOLDS["B"]:
            return "B"
        return "C"

    @staticmethod
    def _extract_recommendations(text: str, metrics: dict) -> list[str]:
        recs = []
        if metrics["cyclomatic_complexity"] > 10:
            recs.append("Reduce cyclomatic complexity — extract helper functions.")
        if metrics["line_count"] > 50:
            recs.append("Function exceeds 50 lines — consider splitting responsibilities.")
        if not metrics.get("has_docstring"):
            recs.append("Add a docstring describing purpose and parameters.")
        if metrics["quality_score"] < 65:
            recs.append("Schedule a pair-review before merge due to low quality score.")
        if not recs:
            recs.append(text[:180] + ("..." if len(text) > 180 else ""))
        return recs
