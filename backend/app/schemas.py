"""
Pydantic schemas for API request/response validation.
Kept separate from SQLAlchemy models (app/models) on purpose —
DB models and API contracts are allowed to evolve independently.
"""
from datetime import datetime
from pydantic import BaseModel


# ---------- Dev-Collaboration ----------

class StartEditRequest(BaseModel):
    developer_name: str
    file_path: str
    function_name: str | None = None


class ConflictEventOut(BaseModel):
    id: int
    file_path: str
    function_name: str | None
    dev_a_id: int
    dev_b_id: int
    risk_score: float
    status: str
    ai_suggestion: str | None
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- AIOps ----------

class MetricsSnapshotIn(BaseModel):
    service_name: str
    response_time_ms: int
    error_rate_pct: float
    db_pool_usage_pct: float
    affected_users_pct: float


class IncidentOut(BaseModel):
    id: int
    title: str
    service_name: str
    severity: str
    status: str
    root_cause: str | None
    detected_at: datetime
    resolved_at: datetime | None
    mttr_seconds: int | None
    linked_commit_id: int | None

    class Config:
        from_attributes = True


class AgentDecisionLogOut(BaseModel):
    id: int
    agent_name: str
    module: str
    decision_summary: str
    used_llm: bool
    created_at: datetime

    class Config:
        from_attributes = True
