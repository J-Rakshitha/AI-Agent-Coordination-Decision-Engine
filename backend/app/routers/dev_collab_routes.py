"""
Dev-Collaboration Module API routes.
Prefix: /api/dev-collab
"""
import random
import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.schemas import StartEditRequest
from app.models.dev_collab import Developer, ConflictEvent, CommitLog
from app.agents.dev_collab.code_watch_agent import CodeWatchAgent
from app.agents.dev_collab.conflict_prediction_agent import OverlapDetectionAgent, ConflictPredictionAgent
from app.agents.dev_collab.resolution_suggestion_agent import ResolutionSuggestionAgent
from app.services.synthetic_data_generator import random_edit_event
from app.routers.websocket_routes import manager

router = APIRouter(prefix="/api/dev-collab", tags=["Dev Collaboration"])

# Demo-safe developer pool used by the "Simulate Conflict" button, so a
# presenter can trigger a realistic scenario with one click, no real
# IDE/git integration required.
DEMO_DEV_NAMES = [
    ("Priya Sharma", "#4F8CFF"),
    ("Arjun Mehta", "#FF6B6B"),
    ("Sneha Reddy", "#3ECF8E"),
    ("Karthik Rao", "#F5A623"),
]


@router.post("/edit-session/start")
async def start_edit_session(payload: StartEditRequest, db: AsyncSession = Depends(get_db)):
    """Register that a developer started editing a file/function (live presence)."""
    dev = await CodeWatchAgent.get_or_create_developer(db, payload.developer_name)
    session = await CodeWatchAgent.start_edit_session(
        db, developer_id=dev.id, file_path=payload.file_path, function_name=payload.function_name
    )
    await manager.broadcast("edit_session_started", {
        "session_id": session.id, "developer_id": dev.id, "developer_name": dev.name,
        "file_path": payload.file_path, "function_name": payload.function_name,
    })
    return {"session_id": session.id, "developer_id": dev.id}


@router.post("/edit-session/{session_id}/end")
async def end_edit_session_route(session_id: int, db: AsyncSession = Depends(get_db)):
    """Mark an edit session as finished (developer saved/pushed their work)."""
    await CodeWatchAgent.end_edit_session(db, session_id)
    await manager.broadcast("edit_session_ended", {"session_id": session_id})
    return {"ended": session_id}


@router.get("/active-sessions")
async def get_active_sessions(db: AsyncSession = Depends(get_db)):
    """Live map of who's editing what right now."""
    sessions = await CodeWatchAgent.get_active_sessions(db)
    output = []
    for s in sessions:
        dev = await db.get(Developer, s.developer_id)
        output.append({
            "session_id": s.id,
            "developer_id": s.developer_id,
            "developer_name": dev.name if dev else f"Dev #{s.developer_id}",
            "avatar_color": dev.avatar_color if dev else "#6C63FF",
            "file_path": s.file_path,
            "function_name": s.function_name,
            "started_at": s.started_at,
        })
    return output


@router.post("/check-conflicts")
async def check_conflicts(db: AsyncSession = Depends(get_db)):
    """
    Runs Overlap Detection + Conflict Prediction across all active sessions.
    Risk score factors in how long the two developers have actually been
    overlapping (real elapsed time, not a fixed guess).
    """
    overlaps = await OverlapDetectionAgent.find_overlaps(db)
    created_events = []

    for overlap in overlaps:
        minutes_overlap = 5.0
        started = overlap.get("overlap_started_at")
        if started:
            if started.tzinfo is None:
                started = started.replace(tzinfo=timezone.utc)
            minutes_overlap = max((datetime.now(timezone.utc) - started).total_seconds() / 60, 1)

        risk_score = ConflictPredictionAgent.calculate_risk_score(same_function=True, minutes_overlap=minutes_overlap)
        event = await ConflictPredictionAgent.create_conflict_event(
            db,
            file_path=overlap["file_path"],
            function_name=overlap["function_name"],
            dev_a_id=overlap["dev_a_id"],
            dev_b_id=overlap["dev_b_id"],
            risk_score=risk_score,
        )
        created_events.append(event)

        dev_a = await db.get(Developer, overlap["dev_a_id"])
        dev_b = await db.get(Developer, overlap["dev_b_id"])
        await manager.broadcast("conflict_detected", {
            "conflict_id": event.id,
            "file_path": event.file_path,
            "function_name": event.function_name,
            "dev_a": dev_a.name if dev_a else "Unknown",
            "dev_b": dev_b.name if dev_b else "Unknown",
            "risk_score": risk_score,
        })

    return {"conflicts_found": len(created_events), "events": [e.id for e in created_events]}


@router.get("/conflicts")
async def list_conflicts(db: AsyncSession = Depends(get_db)):
    """All predicted/resolved conflicts, newest first, with developer names resolved."""
    result = await db.execute(select(ConflictEvent).order_by(ConflictEvent.created_at.desc()))
    conflicts = result.scalars().all()

    output = []
    for c in conflicts:
        dev_a = await db.get(Developer, c.dev_a_id)
        dev_b = await db.get(Developer, c.dev_b_id)
        output.append({
            "id": c.id,
            "file_path": c.file_path,
            "function_name": c.function_name,
            "dev_a": dev_a.name if dev_a else f"Dev #{c.dev_a_id}",
            "dev_b": dev_b.name if dev_b else f"Dev #{c.dev_b_id}",
            "risk_score": c.risk_score,
            "status": c.status,
            "ai_suggestion": c.ai_suggestion,
            "created_at": c.created_at,
        })
    return output


@router.post("/conflicts/{conflict_id}/suggest-resolution")
async def suggest_resolution(conflict_id: int, db: AsyncSession = Depends(get_db)):
    """Ask the Resolution Suggestion Agent (Hybrid AI) how to resolve a specific conflict."""
    conflict = await db.get(ConflictEvent, conflict_id)
    if not conflict:
        raise HTTPException(status_code=404, detail="Conflict not found")

    dev_a = await db.get(Developer, conflict.dev_a_id)
    dev_b = await db.get(Developer, conflict.dev_b_id)
    dev_a_name = dev_a.name if dev_a else "Developer A"
    dev_b_name = dev_b.name if dev_b else "Developer B"

    result = await ResolutionSuggestionAgent.suggest(
        db, dev_a_name, dev_b_name, conflict.file_path, conflict.function_name
    )

    conflict.ai_suggestion = result["suggestion"]
    conflict.status = "resolved"
    conflict.resolved_at = datetime.utcnow()
    db.add(conflict)

    # Record this as a "commit" that resolved a conflict — this is what
    # the AIOps Coordinator Agent later searches when an incident happens,
    # to trace production issues back to risky recent merges.
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

    await manager.broadcast("conflict_resolved", {
        "conflict_id": conflict.id, "suggestion": result["suggestion"], "used_llm": result["used_llm"],
    })

    return {"conflict_id": conflict.id, **result}


@router.get("/commits")
async def list_commits(db: AsyncSession = Depends(get_db)):
    """Recent commit history (created automatically when conflicts are resolved)."""
    result = await db.execute(select(CommitLog).order_by(CommitLog.created_at.desc()).limit(20))
    commits = result.scalars().all()
    output = []
    for c in commits:
        dev = await db.get(Developer, c.developer_id)
        output.append({
            "id": c.id,
            "commit_hash": c.commit_hash,
            "developer_name": dev.name if dev else f"Dev #{c.developer_id}",
            "file_path": c.file_path,
            "message": c.message,
            "had_conflict": c.had_conflict,
            "created_at": c.created_at,
        })
    return output


@router.post("/simulate-demo-conflict")
async def simulate_demo_conflict(db: AsyncSession = Depends(get_db)):
    """
    Demo-safe one-click scenario generator: creates two developers editing the
    SAME file/function at the same time, runs overlap + conflict-risk
    detection, and returns the result. No real IDE/git integration needed —
    perfect for a live presentation where you can't rely on external tools.
    """
    (dev_a_name, dev_a_color), (dev_b_name, dev_b_color) = random.sample(DEMO_DEV_NAMES, 2)
    edit_event = random_edit_event()

    dev_a = await CodeWatchAgent.get_or_create_developer(db, dev_a_name, avatar_color=dev_a_color)
    dev_b = await CodeWatchAgent.get_or_create_developer(db, dev_b_name, avatar_color=dev_b_color)

    await CodeWatchAgent.start_edit_session(db, dev_a.id, edit_event["file_path"], edit_event["function_name"])
    await CodeWatchAgent.start_edit_session(db, dev_b.id, edit_event["file_path"], edit_event["function_name"])

    risk_score = ConflictPredictionAgent.calculate_risk_score(same_function=True, minutes_overlap=6)
    conflict = await ConflictPredictionAgent.create_conflict_event(
        db, edit_event["file_path"], edit_event["function_name"], dev_a.id, dev_b.id, risk_score
    )

    payload = {
        "conflict_id": conflict.id,
        "dev_a": dev_a_name,
        "dev_b": dev_b_name,
        "file_path": edit_event["file_path"],
        "function_name": edit_event["function_name"],
        "risk_score": risk_score,
    }
    await manager.broadcast("conflict_detected", payload)
    return payload
