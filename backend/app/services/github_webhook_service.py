"""
GitHub webhook verification and event handling.
"""
import hashlib
import hmac
import json
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.services.github_sync_service import run_github_sync

logger = logging.getLogger("github_webhook")

PULL_REQUEST_ACTIONS = frozenset({"opened", "synchronize", "reopened", "edited"})


class GitHubWebhookService:

    @staticmethod
    def webhook_url() -> str:
        base = settings.PUBLIC_BACKEND_URL.rstrip("/")
        return f"{base}/api/dev-collab/github/webhook"

    @staticmethod
    def verify_signature(payload_body: bytes, signature_header: str | None) -> bool:
        secret = (settings.GITHUB_WEBHOOK_SECRET or "").strip()
        if not secret:
            if settings.ENV == "development":
                logger.warning("GITHUB_WEBHOOK_SECRET not set — accepting webhook in development mode")
                return True
            logger.error("GITHUB_WEBHOOK_SECRET required in non-development environments")
            return False
        if not signature_header:
            logger.warning("Webhook rejected: missing X-Hub-Signature-256 header")
            return False
        parts = signature_header.split("=", 1)
        if len(parts) != 2 or parts[0].lower() != "sha256":
            logger.warning("Webhook rejected: invalid signature header format")
            return False
        expected = hmac.new(secret.encode("utf-8"), msg=payload_body, digestmod=hashlib.sha256).hexdigest()
        received = parts[1].strip().lower()
        if not hmac.compare_digest(expected.lower(), received):
            logger.warning(
                "Webhook rejected: signature mismatch — ensure GitHub webhook Secret "
                "exactly matches GITHUB_WEBHOOK_SECRET in backend/.env"
            )
            return False
        return True

    @staticmethod
    def signature_header_from_request(request) -> str | None:
        """Read GitHub signature header (FastAPI Header() can miss some proxy casings)."""
        return (
            request.headers.get("x-hub-signature-256")
            or request.headers.get("X-Hub-Signature-256")
            or request.headers.get("X-HUB-SIGNATURE-256")
        )

    @staticmethod
    async def handle_event(
        db: AsyncSession,
        event_name: str | None,
        payload: dict,
    ) -> dict:
        if event_name == "ping":
            return {"processed": True, "action": "ping", "zen": payload.get("zen")}

        if event_name != "pull_request":
            return {"processed": False, "reason": f"ignored event: {event_name}"}

        action = payload.get("action")
        if action not in PULL_REQUEST_ACTIONS:
            return {"processed": False, "reason": f"ignored pull_request action: {action}"}

        if not settings.GITHUB_TOKEN:
            return {"processed": False, "reason": "GitHub token not configured"}

        pr = payload.get("pull_request") or {}
        pr_number = pr.get("number")
        logger.info("GitHub webhook: pull_request #%s action=%s — running sync", pr_number, action)

        sync_result = await run_github_sync(db, trigger="webhook")
        return {
            "processed": True,
            "event": "pull_request",
            "action": action,
            "pull_request_number": pr_number,
            **sync_result,
        }

    @staticmethod
    def parse_payload(payload_body: bytes) -> dict:
        return json.loads(payload_body.decode("utf-8"))
