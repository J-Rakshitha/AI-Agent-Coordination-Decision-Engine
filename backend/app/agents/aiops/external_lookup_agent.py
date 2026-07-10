"""
External Lookup Agent — Tool & System Integration
=====================================================
Calls a REAL external API (GitHub's public Issue Search API) to check
whether a similar error pattern has been publicly reported/discussed
before. This is genuine external tool/system integration — not just
internal DB queries — the kind of thing a real DevOps AIOps tool does
when cross-referencing a known-issues tracker.

Network calls are wrapped in a strict timeout + try/except so a
slow/unreachable external API can NEVER break the incident pipeline or
the live demo — it just degrades to an empty result.
"""
import logging
import httpx

logger = logging.getLogger("external_lookup_agent")

GITHUB_SEARCH_URL = "https://api.github.com/search/issues"


class ExternalLookupAgent:

    @staticmethod
    async def find_related_issues(query: str, timeout: float = 4.0, max_results: int = 3) -> list[dict]:
        """
        Searches GitHub's public issue tracker for the given query (an
        external enterprise-style knowledge source). Returns [] on any
        failure — this tool is a nice-to-have enrichment, never a hard
        dependency for the pipeline to complete.
        """
        params = {"q": f"{query} in:title", "per_page": max_results}
        headers = {"Accept": "application/vnd.github+json"}

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(GITHUB_SEARCH_URL, params=params, headers=headers)
                response.raise_for_status()
                data = response.json()
        except Exception as exc:
            logger.warning(f"External lookup (GitHub) unavailable, skipping enrichment: {exc}")
            return []

        items = data.get("items", [])
        return [
            {
                "title": item.get("title", ""),
                "url": item.get("html_url", ""),
                "repo": (item.get("repository_url", "").split("/repos/")[-1]) or "unknown/repo",
            }
            for item in items
        ]
