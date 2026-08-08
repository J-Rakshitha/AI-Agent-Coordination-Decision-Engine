"""Human-in-the-Loop conflict resolution — approve, reject, defer, undo."""
import json
import secrets
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.memory_agent import MemoryAgent
from app.agents.notification_agent import NotificationAgent
from app.models.dev_collab import CommitLog, ConflictEvent, Developer
from app.models.user import User
from app.models.workflow import ConflictActionLog
from app.routers.websocket_routes import manager


def _snapshot(conflict: ConflictEvent) -> str:
    return json.dumps({
        "status": conflict.status,
        "approval_status": conflict.approval_status,
        "ai_suggestion": conflict.ai_suggestion,
        "resolved_by_name": conflict.resolved_by_name,
        "user_note": conflict.user_note,
    })


async def _log_action(
    db: AsyncSession,
    conflict: ConflictEvent,
    user: User,
    action: str,
    note: str | None = None,
) -> None:
    db.add(ConflictActionLog(
        conflict_id=conflict.id,
        user_id=user.id,
        action=action,
        previous_status=conflict.status,
        previous_approval_status=conflict.approval_status,
        note=note,
        snapshot_json=_snapshot(conflict),
        created_at=datetime.utcnow(),
    ))


async def approve_conflict(db: AsyncSession, conflict_id: int, user: User) -> dict:
    conflict = await db.get(ConflictEvent, conflict_id)
    if not conflict:
        raise ValueError("Conflict not found")
    if conflict.approval_status != "pending_approval":
        raise ValueError("No pending suggestion to approve")

    dev_a = await db.get(Developer, conflict.dev_a_id)
    dev_b = await db.get(Developer, conflict.dev_b_id)
    dev_a_name = dev_a.name if dev_a else "Developer A"
    dev_b_name = dev_b.name if dev_b else "Developer B"

    await _log_action(db, conflict, user, "approve")

    conflict.status = "resolved"
    conflict.approval_status = "approved"
    conflict.resolved_at = datetime.utcnow()
    conflict.resolved_by_user_id = user.id
    conflict.updated_by_user_id = user.id
    conflict.resolved_by_name = user.full_name

    commit = CommitLog(
        commit_hash=secrets.token_hex(4),
        developer_id=conflict.dev_a_id,
        file_path=conflict.file_path,
        message=f"Merge: resolved conflict in {conflict.function_name} ({dev_a_name} & {dev_b_name})",
        had_conflict=True,
        created_at=datetime.utcnow(),
    )
    db.add(commit)
    await db.commit()
    await db.refresh(conflict)

    await MemoryAgent.remember(
        db,
        category="conflict_resolution",
        key_signature=f"{conflict.file_path}:{conflict.function_name}",
        insight=conflict.ai_suggestion or "Approved merge resolution",
    )

    await NotificationAgent.notify_conflict_resolved(
        db,
        conflict_id=conflict.id,
        file_path=conflict.file_path,
        suggestion=conflict.ai_suggestion or "",
        dev_a=dev_a_name,
        dev_b=dev_b_name,
    )

    await manager.broadcast("conflict_resolved", {
        "conflict_id": conflict.id,
        "resolved_by": user.full_name,
        "suggestion": conflict.ai_suggestion,
    })

    return {"success": True, "status": conflict.status, "resolved_by_name": user.full_name}


async def reject_conflict(db: AsyncSession, conflict_id: int, user: User, note: str = "") -> dict:
    conflict = await db.get(ConflictEvent, conflict_id)
    if not conflict:
        raise ValueError("Conflict not found")

    await _log_action(db, conflict, user, "reject", note=note or None)

    conflict.status = "predicted"
    conflict.approval_status = "rejected"
    conflict.user_note = note or "Rejected by reviewer"
    conflict.updated_by_user_id = user.id
    db.add(conflict)
    await db.commit()

    await manager.broadcast("conflict_updated", {"conflict_id": conflict.id, "action": "reject"})
    return {"success": True, "status": conflict.status}


async def defer_conflict(db: AsyncSession, conflict_id: int, user: User, note: str = "") -> dict:
    conflict = await db.get(ConflictEvent, conflict_id)
    if not conflict:
        raise ValueError("Conflict not found")

    await _log_action(db, conflict, user, "defer", note=note or None)

    conflict.approval_status = "deferred"
    conflict.user_note = note or "Resolve later — pending business review"
    conflict.updated_by_user_id = user.id
    db.add(conflict)
    await db.commit()

    await manager.broadcast("conflict_updated", {"conflict_id": conflict.id, "action": "defer"})
    return {"success": True, "status": conflict.status, "approval_status": conflict.approval_status}


async def undo_last_action(db: AsyncSession, conflict_id: int, user: User) -> dict:
    conflict = await db.get(ConflictEvent, conflict_id)
    if not conflict:
        raise ValueError("Conflict not found")

    stmt = (
        select(ConflictActionLog)
        .where(ConflictActionLog.conflict_id == conflict_id)
        .order_by(ConflictActionLog.created_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    last = result.scalars().first()
    if not last or not last.snapshot_json:
        raise ValueError("Nothing to undo")

    snap = json.loads(last.snapshot_json)
    conflict.status = snap.get("status", "predicted")
    conflict.approval_status = snap.get("approval_status")
    conflict.resolved_by_name = snap.get("resolved_by_name")
    conflict.user_note = snap.get("user_note")
    conflict.resolved_at = None
    conflict.resolved_by_user_id = None
    conflict.updated_by_user_id = user.id

    await _log_action(db, conflict, user, "undo")
    db.add(conflict)
    await db.delete(last)
    await db.commit()

    await manager.broadcast("conflict_updated", {"conflict_id": conflict.id, "action": "undo"})
    return {"success": True, "status": conflict.status, "approval_status": conflict.approval_status}
