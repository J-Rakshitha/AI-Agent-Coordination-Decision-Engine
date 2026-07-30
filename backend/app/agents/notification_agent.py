"""
Notification Agent
==================
Delivers team alerts when agents complete significant actions. Channels:
  - WebSocket — live dashboard updates (always)
  - Email — real SMTP when configured, otherwise simulated delivery logged to DB

Every delivery is persisted in TeamNotification so the audit trail survives
page refreshes and can be queried via REST.
"""
import logging
import smtplib
from email.mime.text import MIMEText

from sqlalchemy import select

from app.core.config import settings
from app.models.notification import TeamNotification
from app.agents.coordinator_agent import CoordinatorAgent
from app.routers.websocket_routes import manager

logger = logging.getLogger("notification_agent")

DEFAULT_TEAM_RECIPIENTS = [
    "priya@infosys.com",
    "arjun@infosys.com",
    "dev-team@infosys.com",
]


class NotificationAgent:

    @staticmethod
    async def list_recent(db, limit: int = 30) -> list[TeamNotification]:
        stmt = select(TeamNotification).order_by(TeamNotification.created_at.desc()).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def _persist(
        db,
        channel: str,
        event_type: str,
        module: str,
        recipient: str,
        subject: str,
        message: str,
        related_entity_id: int | None = None,
        delivered: bool = True,
    ) -> TeamNotification:
        entry = TeamNotification(
            channel=channel,
            event_type=event_type,
            module=module,
            recipient=recipient,
            subject=subject,
            message=message,
            related_entity_id=related_entity_id,
            delivered=delivered,
        )
        db.add(entry)
        await db.commit()
        await db.refresh(entry)
        return entry

    @staticmethod
    def _send_email_sync(recipient: str, subject: str, message: str) -> bool:
        if not settings.NOTIFICATION_SMTP_HOST:
            return False
        try:
            msg = MIMEText(message)
            msg["Subject"] = subject
            msg["From"] = settings.NOTIFICATION_FROM_EMAIL
            msg["To"] = recipient
            with smtplib.SMTP(settings.NOTIFICATION_SMTP_HOST, settings.NOTIFICATION_SMTP_PORT, timeout=5) as server:
                if settings.NOTIFICATION_SMTP_USER:
                    server.starttls()
                    server.login(settings.NOTIFICATION_SMTP_USER, settings.NOTIFICATION_SMTP_PASSWORD)
                server.send_message(msg)
            return True
        except Exception as exc:
            logger.warning("Email delivery failed for %s: %s", recipient, exc)
            return False

    @staticmethod
    async def _deliver_email(db, recipient: str, subject: str, message: str, event_type: str,
                              module: str, related_entity_id: int | None) -> TeamNotification:
        if settings.NOTIFICATION_EMAIL_ENABLED and settings.NOTIFICATION_SMTP_HOST:
            delivered = NotificationAgent._send_email_sync(recipient, subject, message)
            channel = "email" if delivered else "email_simulated"
        else:
            delivered = True
            channel = "email_simulated"

        return await NotificationAgent._persist(
            db, channel, event_type, module, recipient, subject, message, related_entity_id, delivered
        )

    @staticmethod
    async def _notify_team(
        db,
        event_type: str,
        module: str,
        subject: str,
        message: str,
        related_entity_id: int | None = None,
        ws_payload: dict | None = None,
        recipients: list[str] | None = None,
    ) -> list[TeamNotification]:
        targets = recipients or DEFAULT_TEAM_RECIPIENTS
        sent: list[TeamNotification] = []

        for recipient in targets:
            sent.append(await NotificationAgent._deliver_email(
                db, recipient, subject, message, event_type, module, related_entity_id
            ))

        await NotificationAgent._persist(
            db, "websocket", event_type, module, "dashboard", subject, message, related_entity_id
        )

        if ws_payload is not None:
            await manager.broadcast("team_notification", ws_payload)

        await CoordinatorAgent.log_decision(
            db=db,
            agent_name="Notification Agent",
            module=module,
            decision_summary=f"Notified team ({event_type}): {subject}",
            used_llm=False,
            related_entity_id=related_entity_id,
        )

        return sent

    @staticmethod
    async def notify_conflict_detected(
        db,
        conflict_id: int,
        file_path: str,
        function_name: str | None,
        dev_a: str,
        dev_b: str,
        risk_score: float,
        code_review: str | None = None,
    ) -> list[TeamNotification]:
        fn = function_name or "(file-level)"
        subject = f"[Dev-Collab] Conflict risk {risk_score}% — {file_path}"
        message = (
            f"Merge conflict predicted between {dev_a} and {dev_b} "
            f"in {file_path} ({fn}). Risk score: {risk_score}%."
        )
        if code_review:
            message += f"\n\nCode review:\n{code_review}"

        return await NotificationAgent._notify_team(
            db,
            event_type="conflict_detected",
            module="dev_collab",
            subject=subject,
            message=message,
            related_entity_id=conflict_id,
            ws_payload={
                "event_type": "conflict_detected",
                "conflict_id": conflict_id,
                "file_path": file_path,
                "function_name": function_name,
                "dev_a": dev_a,
                "dev_b": dev_b,
                "risk_score": risk_score,
                "subject": subject,
            },
        )

    @staticmethod
    async def notify_conflict_resolved(
        db,
        conflict_id: int,
        file_path: str,
        suggestion: str,
        dev_a: str,
        dev_b: str,
    ) -> list[TeamNotification]:
        subject = f"[Dev-Collab] Conflict resolved — {file_path}"
        message = (
            f"Conflict between {dev_a} and {dev_b} in {file_path} was resolved.\n"
            f"AI suggestion: {suggestion}"
        )
        return await NotificationAgent._notify_team(
            db,
            event_type="conflict_resolved",
            module="dev_collab",
            subject=subject,
            message=message,
            related_entity_id=conflict_id,
            ws_payload={
                "event_type": "conflict_resolved",
                "conflict_id": conflict_id,
                "file_path": file_path,
                "subject": subject,
            },
        )

    @staticmethod
    async def notify_incident_created(
        db,
        incident_id: int,
        service_name: str,
        severity: str,
        root_cause: str,
        status: str,
    ) -> list[TeamNotification]:
        subject = f"[AIOps] {severity} incident on {service_name}"
        message = (
            f"Incident #{incident_id} on {service_name} — severity {severity}, status {status}.\n"
            f"Root cause: {root_cause}"
        )
        oncall = settings.NOTIFICATION_ONCALL_EMAIL
        recipients = [oncall] if oncall else None
        return await NotificationAgent._notify_team(
            db,
            event_type="incident_created",
            module="aiops",
            subject=subject,
            message=message,
            related_entity_id=incident_id,
            recipients=recipients,
            ws_payload={
                "event_type": "incident_created",
                "incident_id": incident_id,
                "service_name": service_name,
                "severity": severity,
                "subject": subject,
            },
        )
