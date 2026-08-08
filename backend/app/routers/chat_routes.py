"""Chat history API — ChatGPT-style sessions per user."""
from pydantic import BaseModel

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.services import chat_service

router = APIRouter(prefix="/api/chat", tags=["Chat History"])


class CreateSessionIn(BaseModel):
    title: str = "New conversation"


class AskIn(BaseModel):
    question: str


@router.get("/sessions")
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await chat_service.list_sessions(db, user)


@router.post("/sessions")
async def create_session(
    payload: CreateSessionIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await chat_service.create_session(db, user, payload.title)


@router.get("/sessions/{session_id}/messages")
async def get_messages(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        return await chat_service.get_messages(db, user, session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/sessions/{session_id}/ask")
async def ask_question(
    session_id: int,
    payload: AskIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        return await chat_service.ask_question(db, user, session_id, payload.question)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
