"""
Repository Discovery Agent — Phase 1
=====================================
Deep AST scan of the local codebase (and optional GitHub file metadata).
Builds a live symbol map stored in CodeSymbol for downstream agents.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

from sqlalchemy import delete, select

from app.agents.coordinator_agent import CoordinatorAgent
from app.models.enterprise import CodeSymbol
from app.services.code_parser import (
    DEFAULT_SCAN_ROOTS,
    find_symbol,
    scan_local_repository,
    symbol_to_dict,
)

logger = logging.getLogger("repository_discovery_agent")


class RepositoryDiscoveryAgent:

    @staticmethod
    async def discover(
        db,
        file_path: str | None = None,
        function_name: str | None = None,
        max_files: int = 200,
    ) -> dict:
        """Scan repository, persist symbols, return context for a conflict target."""
        roots = DEFAULT_SCAN_ROOTS
        symbols = scan_local_repository(roots=roots, max_files=max_files)

        await RepositoryDiscoveryAgent._persist_symbols(db, symbols)

        target = None
        if file_path:
            target = find_symbol(symbols, file_path, function_name)

        related = [
            symbol_to_dict(s)
            for s in symbols
            if file_path and file_path.replace("\\", "/") in s.file_path.replace("\\", "/")
        ][:15]

        context = {
            "scan_source": "local_ast",
            "symbols_indexed": len(symbols),
            "files_scanned": len({s.file_path for s in symbols}),
            "target_symbol": symbol_to_dict(target) if target else None,
            "related_symbols_in_file": related,
            "scan_roots": [str(r) for r in roots if r.exists()],
        }

        summary = (
            f"Indexed {context['symbols_indexed']} symbols across "
            f"{context['files_scanned']} files via AST scan."
        )
        if target:
            summary += (
                f" Target: {target.symbol_type} '{target.name}' "
                f"(complexity {target.complexity}, lines {target.line_start}-{target.line_end})."
            )

        await CoordinatorAgent.log_decision(
            db=db,
            agent_name="Repository Discovery Agent",
            module="dev_collab",
            decision_summary=summary,
            used_llm=False,
        )

        return {"context": context, "summary": summary}

    @staticmethod
    async def _persist_symbols(db, symbols) -> None:
        try:
            await db.execute(delete(CodeSymbol))
            now = datetime.utcnow()
            for sym in symbols[:500]:
                db.add(
                    CodeSymbol(
                        file_path=sym.file_path,
                        symbol_type=sym.symbol_type,
                        name=sym.name,
                        line_start=sym.line_start,
                        line_end=sym.line_end,
                        dependencies_json=json.dumps(sym.dependencies),
                        complexity=sym.complexity,
                        source_snippet=sym.source_snippet[:4000],
                        scan_source="local",
                        scanned_at=now,
                    )
                )
            await db.commit()
        except Exception as exc:
            logger.warning("Could not persist code symbols: %s", exc)
            await db.rollback()

    @staticmethod
    async def lookup_from_cache(db, file_path: str, function_name: str | None) -> dict | None:
        """Fast lookup from last discovery run."""
        normalized = file_path.replace("\\", "/")
        stmt = select(CodeSymbol).where(CodeSymbol.file_path.contains(normalized.split("/")[-1]))
        result = await db.execute(stmt)
        rows = result.scalars().all()
        for row in rows:
            if function_name and row.name == function_name and row.symbol_type == "function":
                return {
                    "file_path": row.file_path,
                    "name": row.name,
                    "complexity": row.complexity,
                    "dependencies": row.dependencies,
                    "source_snippet": row.source_snippet[:2000],
                }
        for row in rows:
            if row.symbol_type == "function":
                return {
                    "file_path": row.file_path,
                    "name": row.name,
                    "complexity": row.complexity,
                    "dependencies": row.dependencies,
                    "source_snippet": row.source_snippet[:2000],
                }
        return None
