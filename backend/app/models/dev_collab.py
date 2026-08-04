"""
Data models for Module 1: Dev-Collaboration Conflict Prevention.
"""
from datetime import datetime
from sqlalchemy import String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Developer(Base):
    __tablename__ = "developers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    avatar_color: Mapped[str] = mapped_column(String(20), default="#6C63FF")

    edits: Mapped[list["FileEditSession"]] = relationship(back_populates="developer")


class FileEditSession(Base):
    """Represents a developer actively editing a file/function (live presence)."""
    __tablename__ = "file_edit_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    developer_id: Mapped[int] = mapped_column(ForeignKey("developers.id"))
    file_path: Mapped[str] = mapped_column(String(255))
    function_name: Mapped[str] = mapped_column(String(150), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_active: Mapped[bool] = mapped_column(default=True)

    developer: Mapped["Developer"] = relationship(back_populates="edits")


class ConflictEvent(Base):
    """A predicted or actual merge conflict between two developers."""
    __tablename__ = "conflict_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    file_path: Mapped[str] = mapped_column(String(255))
    function_name: Mapped[str] = mapped_column(String(150), nullable=True)
    dev_a_id: Mapped[int] = mapped_column(ForeignKey("developers.id"))
    dev_b_id: Mapped[int] = mapped_column(ForeignKey("developers.id"))
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)  # 0-100 %
    status: Mapped[str] = mapped_column(String(30), default="predicted")  # predicted | resolved | ignored
    source: Mapped[str] = mapped_column(String(20), default="simulated")  # simulated | github
    source_url: Mapped[str] = mapped_column(String(500), nullable=True)
    ai_suggestion: Mapped[str] = mapped_column(Text, nullable=True)
    code_review_notes: Mapped[str] = mapped_column(Text, nullable=True)
    discovery_context: Mapped[str] = mapped_column(Text, nullable=True)
    semantic_analysis: Mapped[str] = mapped_column(Text, nullable=True)
    quality_report: Mapped[str] = mapped_column(Text, nullable=True)
    resolution_options: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    resolved_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)


class CommitLog(Base):
    """Simplified commit record used to link dev-collab activity to incidents."""
    __tablename__ = "commit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    commit_hash: Mapped[str] = mapped_column(String(40))
    developer_id: Mapped[int] = mapped_column(ForeignKey("developers.id"))
    file_path: Mapped[str] = mapped_column(String(255))
    message: Mapped[str] = mapped_column(String(255))
    had_conflict: Mapped[bool] = mapped_column(default=False)
    related_service: Mapped[str] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
