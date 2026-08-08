"""Enterprise workflow models — HITL audit, per-user repos, chat sessions."""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class UserRepo(Base):
    __tablename__ = "user_repos"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    repo_url: Mapped[str] = mapped_column(String(500))
    repo_owner: Mapped[str] = mapped_column(String(100))
    repo_name: Mapped[str] = mapped_column(String(200))
    symbols_indexed: Mapped[int] = mapped_column(Integer, default=0)
    conflicts_found: Mapped[int] = mapped_column(Integer, default=0)
    last_scanned_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ConflictActionLog(Base):
    __tablename__ = "conflict_action_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    conflict_id: Mapped[int] = mapped_column(ForeignKey("conflict_events.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(30))
    previous_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    previous_approval_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    snapshot_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(200), default="New conversation")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("chat_sessions.id"))
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
