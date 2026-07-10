"""
Coordinator Agent (Common Core)
================================
The central "brain" of the whole engine. Both modules (Dev-Collaboration
and AIOps) report their events here. It:
  1. Logs every decision made by any agent (explainable-AI trail)
  2. Performs the cross-module "Linked Incidents" correlation —
     connecting a production incident back to a recent risky commit/conflict.
"""
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.incident import AgentDecisionLog, Incident
from app.models.dev_collab import CommitLog


class CoordinatorAgent:

    @staticmethod
    async def log_decision(
        db: AsyncSession,
        agent_name: str,
        module: str,
        decision_summary: str,
        used_llm: bool,
        related_entity_id: int | None = None,
    ) -> AgentDecisionLog:
        entry = AgentDecisionLog(
            agent_name=agent_name,
            module=module,
            related_entity_id=related_entity_id,
            decision_summary=decision_summary,
            used_llm=used_llm,
        )
        db.add(entry)
        await db.commit()
        await db.refresh(entry)
        return entry

    @staticmethod
    async def find_linked_commit(db: AsyncSession, service_hint: str, window_hours: int = 48) -> CommitLog | None:
        """
        Cross-module unique feature: when an incident happens, look back at
        recent commits to suggest a likely trigger. This is what makes the
        two modules feel like ONE coordinated engine instead of two separate
        tools.

        Matching strategy:
          1. Prefer a commit whose file name shares a keyword with the
             affected service (e.g. "checkout.py" <-> "checkout-service").
          2. Otherwise, fall back to the most recent commit that had a
             resolved conflict — still a plausible risk signal.
        """
        since = datetime.utcnow() - timedelta(hours=window_hours)
        stmt = select(CommitLog).where(CommitLog.created_at >= since).order_by(CommitLog.created_at.desc())
        result = await db.execute(stmt)
        commits = result.scalars().all()
        if not commits:
            return None

        service_keyword = service_hint.lower().replace("-service", "").replace("-", "").replace("_", "")

        for commit in commits:
            file_keyword = commit.file_path.split(".")[0].lower().replace("_", "").replace("-", "")
            if service_keyword and (service_keyword in file_keyword or file_keyword in service_keyword):
                return commit

        for commit in commits:
            if commit.had_conflict:
                return commit

        return None

    @staticmethod
    async def link_incident_to_commit(db: AsyncSession, incident: Incident, commit: CommitLog) -> None:
        incident.linked_commit_id = commit.id
        db.add(incident)
        await db.commit()
