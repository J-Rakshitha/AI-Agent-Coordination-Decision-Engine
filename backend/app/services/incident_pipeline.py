"""
Shared incident pipeline — used by REST ingest, simulate, and background monitor.
"""
import json
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.incident import Incident
from app.models.dev_collab import CommitLog
from app.agents.aiops.monitoring_agent import MonitoringAgent
from app.agents.aiops.root_cause_agent import RootCauseAgent
from app.agents.aiops.severity_agent import SeverityAgent
from app.agents.aiops.escalation_agent import EscalationAgent
from app.agents.aiops.external_lookup_agent import ExternalLookupAgent
from app.agents.coordinator_agent import CoordinatorAgent
from app.agents.tools.tool_executor_agent import ToolExecutorAgent
from app.agents.tools import tool_handlers  # noqa: F401


async def run_incident_pipeline(db: AsyncSession, metrics: dict) -> dict:
    """
    Monitoring -> Root Cause -> Severity -> Tool Selection -> Escalation -> Coordinator link.
    """
    anomaly = MonitoringAgent.detect_anomaly(metrics)
    if not anomaly:
        return {"anomaly_detected": False}

    incident = Incident(
        title=f"Anomaly detected on {anomaly['service_name']}",
        service_name=anomaly["service_name"],
        detected_at=datetime.utcnow(),
        status="open",
    )
    db.add(incident)
    await db.commit()
    await db.refresh(incident)

    root_cause_result = await RootCauseAgent.analyze(
        db, anomaly["service_name"], anomaly["error_signature"], anomaly["raw_metrics"]
    )
    incident.root_cause = root_cause_result["root_cause"]

    search_terms = anomaly["error_signature"].replace("_", " ")
    external_refs = await ExternalLookupAgent.find_related_issues(search_terms)
    incident.external_references = json.dumps(external_refs)
    await CoordinatorAgent.log_decision(
        db=db,
        agent_name="External Lookup Agent",
        module="aiops",
        decision_summary=(
            f"Queried GitHub's public issue tracker for '{search_terms}' — "
            f"found {len(external_refs)} related reference(s)."
        ),
        used_llm=False,
    )

    severity = SeverityAgent.classify(anomaly["error_rate_pct"], anomaly["affected_users_pct"])
    incident.severity = severity

    situation = f"Incident on {anomaly['service_name']}, severity {severity}: {root_cause_result['root_cause']}"
    tool_result = await ToolExecutorAgent.select_and_execute(
        db, situation,
        incident_id=incident.id,
        severity=severity,
        reason=root_cause_result["root_cause"],
    )
    action_taken = tool_result["tool_name"]
    remediation_succeeded = tool_result["tool_name"] in ("restart_service", "clear_cache") and tool_result["success"]

    if remediation_succeeded:
        incident.status = "auto_resolved"
        incident.resolved_at = datetime.utcnow()
        incident.mttr_seconds = int((incident.resolved_at - incident.detected_at).total_seconds())
    else:
        incident.status = "escalated"

    db.add(incident)
    await db.commit()
    await db.refresh(incident)

    escalation = None
    if not remediation_succeeded or severity == "P1":
        escalation = EscalationAgent.build_escalation(incident.id, severity, root_cause_result["root_cause"])

    linked_commit = await CoordinatorAgent.find_linked_commit(db, anomaly["service_name"])
    linked_commit_info = None
    if linked_commit:
        await CoordinatorAgent.link_incident_to_commit(db, incident, linked_commit)
        linked_commit_info = {
            "commit_hash": linked_commit.commit_hash,
            "file_path": linked_commit.file_path,
            "message": linked_commit.message,
            "had_conflict": linked_commit.had_conflict,
        }

    return {
        "anomaly_detected": True,
        "incident_id": incident.id,
        "severity": severity,
        "root_cause": incident.root_cause,
        "action_taken": action_taken,
        "tool_selection_used_llm": tool_result["used_llm_selection"],
        "status": incident.status,
        "escalation": escalation,
        "linked_commit_id": incident.linked_commit_id,
        "linked_commit": linked_commit_info,
        "external_references": external_refs,
        "source": metrics.get("monitor_source", "manual"),
    }
