"""
AIOps Incident Response Module API routes.
Prefix: /api/incidents
"""
import json
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.schemas import MetricsSnapshotIn
from app.models.incident import Incident
from app.models.dev_collab import CommitLog
from app.agents.aiops.monitoring_agent import MonitoringAgent
from app.agents.aiops.root_cause_agent import RootCauseAgent
from app.agents.aiops.severity_agent import SeverityAgent
from app.agents.aiops.remediation_agent import RemediationAgent
from app.agents.aiops.escalation_agent import EscalationAgent
from app.agents.aiops.external_lookup_agent import ExternalLookupAgent
from app.agents.coordinator_agent import CoordinatorAgent
from app.services.synthetic_data_generator import random_metrics_snapshot
from app.routers.websocket_routes import manager

router = APIRouter(prefix="/api/incidents", tags=["AIOps Incident Response"])


async def run_incident_pipeline(db: AsyncSession, metrics: dict) -> dict:
    """
    The full agent pipeline, shared by both the real ingest endpoint and the
    demo "Simulate Incident" button:
    Monitoring -> Root Cause -> Severity -> Remediation -> Escalation -> Coordinator link.
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

    # Genuine external tool integration — query a real external API (GitHub's
    # public issue tracker) for related known issues. Never blocks or breaks
    # the pipeline if the external service is slow/unreachable.
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

    action_type = RemediationAgent.decide_action(root_cause_result["root_cause"])
    action = await RemediationAgent.perform_action(db, incident.id, action_type)

    if action.success:
        incident.status = "auto_resolved"
        incident.resolved_at = datetime.utcnow()
        incident.mttr_seconds = int((incident.resolved_at - incident.detected_at).total_seconds())
    else:
        incident.status = "escalated"

    db.add(incident)
    await db.commit()
    await db.refresh(incident)

    escalation = None
    if not action.success or severity == "P1":
        escalation = EscalationAgent.build_escalation(incident.id, severity, root_cause_result["root_cause"])

    # Cross-module linking (unique differentiator) — trace the incident back
    # to a recent commit that touched a similarly-named file/service.
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
        "action_taken": action.action_type,
        "status": incident.status,
        "escalation": escalation,
        "linked_commit_id": incident.linked_commit_id,
        "linked_commit": linked_commit_info,
        "external_references": external_refs,
    }


@router.post("/ingest-metrics")
async def ingest_metrics(payload: MetricsSnapshotIn, db: AsyncSession = Depends(get_db)):
    """
    Main entry point: a metrics snapshot comes in (from real monitoring
    or an external tool). Runs the full agent pipeline end-to-end.
    """
    result = await run_incident_pipeline(db, payload.model_dump())
    if result.get("anomaly_detected"):
        await manager.broadcast("incident_created", result)
    return result


@router.post("/simulate")
async def simulate_incident(db: AsyncSession = Depends(get_db)):
    """
    Demo-safe one-click scenario generator: creates a forced anomaly on a
    random service and runs it through the full pipeline. No real servers
    or monitoring integration needed — perfect for a live presentation.
    """
    metrics = random_metrics_snapshot(force_anomaly=True)
    result = await run_incident_pipeline(db, metrics)
    if result.get("anomaly_detected"):
        await manager.broadcast("incident_created", result)
    return result


@router.get("/")
async def list_incidents(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Incident).order_by(Incident.detected_at.desc()))
    incidents = result.scalars().all()

    output = []
    for i in incidents:
        linked_commit = None
        if i.linked_commit_id:
            commit = await db.get(CommitLog, i.linked_commit_id)
            if commit:
                linked_commit = {
                    "commit_hash": commit.commit_hash,
                    "file_path": commit.file_path,
                    "message": commit.message,
                    "had_conflict": commit.had_conflict,
                }
        output.append({
            "id": i.id, "title": i.title, "service_name": i.service_name,
            "severity": i.severity, "status": i.status, "root_cause": i.root_cause,
            "detected_at": i.detected_at, "resolved_at": i.resolved_at,
            "mttr_seconds": i.mttr_seconds, "linked_commit_id": i.linked_commit_id,
            "linked_commit": linked_commit,
            "external_references": json.loads(i.external_references) if i.external_references else [],
        })
    return output
