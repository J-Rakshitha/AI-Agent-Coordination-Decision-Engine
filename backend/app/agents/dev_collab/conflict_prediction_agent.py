"""
Overlap Detection Agent + Conflict Prediction Agent
====================================================
(Grouped in one file since they work on the same data — split further
in a later refactor phase if needed.)

Overlap Detection: checks if two developers are editing the same file/function.
Conflict Prediction: assigns a risk score % to that overlap.
"""
from sqlalchemy import select, and_

from app.models.dev_collab import FileEditSession, ConflictEvent, Developer


class OverlapDetectionAgent:

    @staticmethod
    async def find_overlaps(db) -> list[dict]:
        """Find active edit sessions where 2+ devs touch the same file+function."""
        stmt = select(FileEditSession).where(FileEditSession.is_active == True)  # noqa: E712
        result = await db.execute(stmt)
        sessions = result.scalars().all()

        overlaps = []
        seen_pairs = set()
        for i, s1 in enumerate(sessions):
            for s2 in sessions[i + 1:]:
                same_target = (
                    s1.file_path == s2.file_path
                    and s1.function_name == s2.function_name
                    and s1.developer_id != s2.developer_id
                )
                pair_key = tuple(sorted([s1.developer_id, s2.developer_id])) + (s1.file_path, s1.function_name)
                if same_target and pair_key not in seen_pairs:
                    seen_pairs.add(pair_key)
                    # Use whichever session started later — that's the true
                    # start of the overlap window between the two devs.
                    overlap_started_at = max(s1.started_at, s2.started_at)
                    overlaps.append({
                        "file_path": s1.file_path,
                        "function_name": s1.function_name,
                        "dev_a_id": s1.developer_id,
                        "dev_b_id": s2.developer_id,
                        "overlap_started_at": overlap_started_at,
                    })
        return overlaps


class ConflictPredictionAgent:

    @staticmethod
    def calculate_risk_score(same_function: bool, minutes_overlap: float) -> float:
        """
        Simple, transparent rule-based scoring (fast + always available,
        no need for LLM here since it's a numeric heuristic).
        """
        base = 60.0 if same_function else 20.0
        time_factor = min(minutes_overlap / 30 * 30, 30)  # up to +30 for sustained overlap
        score = min(base + time_factor, 98.0)
        return round(score, 1)

    @staticmethod
    async def create_conflict_event(db, file_path: str, function_name: str,
                                      dev_a_id: int, dev_b_id: int, risk_score: float) -> ConflictEvent:
        event = ConflictEvent(
            file_path=file_path,
            function_name=function_name,
            dev_a_id=dev_a_id,
            dev_b_id=dev_b_id,
            risk_score=risk_score,
            status="predicted",
        )
        db.add(event)
        await db.commit()
        await db.refresh(event)
        return event
