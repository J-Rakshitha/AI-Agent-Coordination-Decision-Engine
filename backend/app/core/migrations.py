"""
Alembic migration runner — applies additive schema changes without deleting data.

Startup flow: create_all() ensures base tables exist, then Alembic applies any
new columns/indexes idempotently (safe for existing SQLite databases).
"""
import logging
from pathlib import Path

from alembic import command
from alembic.config import Config

logger = logging.getLogger("migrations")

_BACKEND_DIR = Path(__file__).resolve().parents[2]


def run_migrations() -> None:
    """Run Alembic upgrade to head (sync — call via asyncio.to_thread)."""
    ini_path = _BACKEND_DIR / "alembic.ini"
    if not ini_path.exists():
        logger.warning("alembic.ini not found — skipping migrations")
        return
    cfg = Config(str(ini_path))
    cfg.set_main_option("script_location", str(_BACKEND_DIR / "alembic"))
    command.upgrade(cfg, "head")
    logger.info("Database migrations applied (head)")
