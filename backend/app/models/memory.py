"""
Data model for Shared Knowledge & Memory Management (long-term memory).
"""
from datetime import datetime
from sqlalchemy import String, Text, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class KnowledgeEntry(Base):
    """
    Long-term memory: durable, persists in the database across restarts.
    Built up over time as agents resolve incidents/conflicts, and consulted
    BEFORE falling back to generic hardcoded rules — this is what lets the
    system's answers get sharper the more it has seen, instead of reasoning
    from scratch every single time.
    """
    __tablename__ = "knowledge_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    category: Mapped[str] = mapped_column(String(50))  # incident_resolution | conflict_pattern
    key_signature: Mapped[str] = mapped_column(String(255), index=True)
    insight: Mapped[str] = mapped_column(Text)
    success_count: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_used_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
