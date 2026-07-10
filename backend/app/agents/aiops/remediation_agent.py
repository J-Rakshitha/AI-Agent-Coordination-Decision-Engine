"""
Remediation Agent
==================
Attempts a known-issue auto-fix based on the root-cause hint.
In this project, "performing" an action means simulating it (restart,
clear cache, etc.) and logging it — safe for demos, same pattern real
runbook-automation tools (e.g. Rundeck, PagerDuty auto-remediation) use.
"""
from app.agents.llm.fallback_rules import fallback_remediation_action
from app.models.incident import RemediationAction


ACTION_LABELS = {
    "restart_service": "Restarted the affected service",
    "clear_cache": "Cleared service cache",
    "notify_oncall_engineer": "No known auto-fix — notified on-call engineer",
}


class RemediationAgent:

    @staticmethod
    def decide_action(root_cause_text: str) -> str:
        return fallback_remediation_action(root_cause_text)

    @staticmethod
    async def perform_action(db, incident_id: int, action_type: str) -> RemediationAction:
        action = RemediationAction(
            incident_id=incident_id,
            action_type=action_type,
            performed_by="Remediation Agent",
            success=action_type != "notify_oncall_engineer",
            notes=ACTION_LABELS.get(action_type, action_type),
        )
        db.add(action)
        await db.commit()
        await db.refresh(action)
        return action
