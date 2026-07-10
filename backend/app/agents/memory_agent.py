"""
Memory Agent — Shared Knowledge & Memory Management
======================================================
Short-term memory: recent decisions within the current run (queried from
AgentDecisionLog), giving agents immediate situational context — e.g.
"we've just seen 3 similar incidents in the last few minutes."

Long-term memory: the persistent KnowledgeEntry table. Agents check here
FIRST before reasoning from scratch or falling back to generic rules — the
system gets sharper the more incidents/conflicts it has handled, instead of
repeating the same reasoning every time.
"""
from datetime import datetime
from sqlalchemy import select

from app.models.memory import KnowledgeEntry
from app.models.incident import AgentDecisionLog


class MemoryAgent:

    @staticmethod
    async def recall_recent(db, module: str, limit: int = 5) -> list[str]:
        """Short-term memory: the last few decisions made in this module."""
        stmt = (
            select(AgentDecisionLog)
            .where(AgentDecisionLog.module == module)
            .order_by(AgentDecisionLog.created_at.desc())
            .limit(limit)
        )
        result = await db.execute(stmt)
        logs = result.scalars().all()
        return [f"{l.agent_name}: {l.decision_summary}" for l in reversed(logs)]

    @staticmethod
    async def recall_knowledge(db, key_signature: str) -> KnowledgeEntry | None:
        """Long-term memory: exact-match lookup on a normalized key signature."""
        stmt = select(KnowledgeEntry).where(KnowledgeEntry.key_signature == key_signature)
        result = await db.execute(stmt)
        return result.scalars().first()

    @staticmethod
    async def remember(db, category: str, key_signature: str, insight: str) -> KnowledgeEntry:
        """Write a new long-term memory entry, or reinforce an existing one."""
        existing = await MemoryAgent.recall_knowledge(db, key_signature)
        if existing:
            existing.success_count += 1
            existing.insight = insight
            existing.last_used_at = datetime.utcnow()
            db.add(existing)
            await db.commit()
            await db.refresh(existing)
            return existing

        entry = KnowledgeEntry(category=category, key_signature=key_signature, insight=insight)
        db.add(entry)
        await db.commit()
        await db.refresh(entry)
        return entry

    @staticmethod
    async def list_recent_knowledge(db, limit: int = 20) -> list[KnowledgeEntry]:
        stmt = select(KnowledgeEntry).order_by(KnowledgeEntry.last_used_at.desc()).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()
