"""
Severity / Priority Agent
==========================
Classifies an incident as P1 / P2 / P3. This is a deterministic business-rule
decision (real ITSM tools like ServiceNow work this way too) — no LLM needed,
so it's instant and always consistent.
"""
from app.agents.llm.fallback_rules import fallback_severity


class SeverityAgent:

    @staticmethod
    def classify(error_rate_pct: float, affected_users_pct: float) -> str:
        return fallback_severity("", error_rate_pct, affected_users_pct)

    @staticmethod
    def sla_minutes_for(severity: str) -> int:
        return {"P1": 30, "P2": 120, "P3": 480}.get(severity, 480)
