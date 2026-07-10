"""
Code-Watch Agent
=================
Records live "presence" — which developer is editing which file/function
right now. In a real IDE integration this would be fed by a VS Code
extension or git pre-commit hook. For this project, it's fed by the
synthetic data generator (Phase 9) and/or a manual "simulate edit" API call.
"""
from datetime import datetime
from sqlalchemy import select

from app.models.dev_collab import FileEditSession, Developer


class CodeWatchAgent:

    @staticmethod
    async def get_or_create_developer(db, name: str, avatar_color: str = "#6C63FF") -> Developer:
        stmt = select(Developer).where(Developer.name == name)
        result = await db.execute(stmt)
        dev = result.scalars().first()
        if dev:
            return dev
        dev = Developer(name=name, avatar_color=avatar_color)
        db.add(dev)
        await db.commit()
        await db.refresh(dev)
        return dev

    @staticmethod
    async def start_edit_session(db, developer_id: int, file_path: str, function_name: str | None) -> FileEditSession:
        session = FileEditSession(
            developer_id=developer_id,
            file_path=file_path,
            function_name=function_name,
            started_at=datetime.utcnow(),
            is_active=True,
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session

    @staticmethod
    async def end_edit_session(db, session_id: int) -> None:
        stmt = select(FileEditSession).where(FileEditSession.id == session_id)
        result = await db.execute(stmt)
        session = result.scalars().first()
        if session:
            session.is_active = False
            db.add(session)
            await db.commit()

    @staticmethod
    async def get_active_sessions(db) -> list[FileEditSession]:
        stmt = select(FileEditSession).where(FileEditSession.is_active == True)  # noqa: E712
        result = await db.execute(stmt)
        return result.scalars().all()
