"""
Escalation Agent
=================
If auto-remediation doesn't fully resolve the root cause (e.g. restart is
only a temporary fix), this agent creates an escalation record with an
SLA countdown for the responsible human team.
"""
from datetime import datetime, timedelta

from app.agents.aiops.severity_agent import SeverityAgent


class EscalationAgent:

    @staticmethod
    def build_escalation(incident_id: int, severity: str, reason: str) -> dict:
        sla_minutes = SeverityAgent.sla_minutes_for(severity)
        deadline = datetime.utcnow() + timedelta(minutes=sla_minutes)
        return {
            "incident_id": incident_id,
            "escalated_to": "Backend Engineering Team",
            "reason": reason,
            "sla_minutes": sla_minutes,
            "sla_deadline": deadline.isoformat(),
        }
