"""
Knowledge Search Agent — Phase 5
==================================
Semantic RAG search over knowledge base, decisions, and conflict history.
Uses Gemini embeddings with deterministic hash fallback.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime

from sqlalchemy import select

from app.agents.coordinator_agent import CoordinatorAgent
from app.models.enterprise import KnowledgeEmbedding
from app.models.incident import AgentDecisionLog
from app.models.memory import KnowledgeEntry
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger("knowledge_search_agent")


class KnowledgeSearchAgent:

    @staticmethod
    async def index_knowledge_base(db, limit: int = 50) -> dict:
        """Embed recent knowledge entries for semantic search."""
        stmt = select(KnowledgeEntry).order_by(KnowledgeEntry.last_used_at.desc()).limit(limit)
        result = await db.execute(stmt)
        entries = result.scalars().all()
        indexed = 0

        for entry in entries:
            text = f"{entry.category}: {entry.key_signature} — {entry.insight}"
            vec = await EmbeddingService.embed_text(text)
            if not vec:
                continue

            sig = f"kb:{entry.id}:{entry.key_signature[:200]}"
            existing = await db.execute(
                select(KnowledgeEmbedding).where(KnowledgeEmbedding.key_signature == sig)
            )
            row = existing.scalars().first()
            if row:
                row.source_text = text
                row.embedding_json = EmbeddingService.vector_to_json(vec)
            else:
                db.add(
                    KnowledgeEmbedding(
                        knowledge_entry_id=entry.id,
                        source_type="knowledge",
                        key_signature=sig,
                        source_text=text,
                        embedding_json=EmbeddingService.vector_to_json(vec),
                        created_at=datetime.utcnow(),
                    )
                )
            indexed += 1

        await db.commit()
        return {"indexed": indexed, "total_entries": len(entries)}

    @staticmethod
    async def search(db, query: str, top_k: int = 5) -> dict:
        """Semantic search across indexed knowledge + recent decisions."""
        query = (query or "").strip()
        if not query:
            return {"query": query, "results": [], "used_embeddings": False}

        await KnowledgeSearchAgent.index_knowledge_base(db, limit=30)

        query_vec = await EmbeddingService.embed_text(query)
        if not query_vec:
            return await KnowledgeSearchAgent._keyword_fallback(db, query, top_k)

        stmt = select(KnowledgeEmbedding).order_by(KnowledgeEmbedding.created_at.desc()).limit(200)
        result = await db.execute(stmt)
        embeddings = result.scalars().all()

        scored = []
        for emb in embeddings:
            vec = emb.embedding_vector()
            if not vec:
                continue
            sim = EmbeddingService.cosine_similarity(query_vec, vec)
            if sim > 0.05:
                scored.append({
                    "source_type": emb.source_type,
                    "key_signature": emb.key_signature,
                    "text": emb.source_text,
                    "similarity": round(sim, 4),
                })

        if len(scored) < top_k:
            decision_hits = await KnowledgeSearchAgent._search_decisions(db, query, top_k - len(scored))
            for hit in decision_hits:
                dvec = await EmbeddingService.embed_text(hit["text"])
                if dvec:
                    hit["similarity"] = round(EmbeddingService.cosine_similarity(query_vec, dvec), 4)
                scored.append(hit)

        scored.sort(key=lambda x: x["similarity"], reverse=True)
        results = scored[:top_k]

        await CoordinatorAgent.log_decision(
            db=db,
            agent_name="Knowledge Search Agent",
            module="system",
            decision_summary=f"Semantic search '{query[:60]}' returned {len(results)} result(s).",
            used_llm=False,
        )

        return {
            "query": query,
            "results": results,
            "used_embeddings": True,
            "embedding_dim": len(query_vec),
        }

    @staticmethod
    async def _search_decisions(db, query: str, limit: int) -> list[dict]:
        stmt = (
            select(AgentDecisionLog)
            .order_by(AgentDecisionLog.created_at.desc())
            .limit(50)
        )
        result = await db.execute(stmt)
        logs = result.scalars().all()
        q = query.lower()
        hits = []
        for log in logs:
            text = f"{log.agent_name}: {log.decision_summary}"
            if any(tok in text.lower() for tok in q.split() if len(tok) > 2):
                hits.append({
                    "source_type": "decision",
                    "key_signature": f"decision:{log.id}",
                    "text": text,
                    "similarity": 0.3,
                })
                if len(hits) >= limit:
                    break
        return hits

    @staticmethod
    async def _keyword_fallback(db, query: str, top_k: int) -> dict:
        stmt = select(KnowledgeEntry).order_by(KnowledgeEntry.last_used_at.desc()).limit(30)
        result = await db.execute(stmt)
        entries = result.scalars().all()
        q = query.lower()
        results = []
        for e in entries:
            blob = f"{e.key_signature} {e.insight}".lower()
            if any(tok in blob for tok in q.split() if len(tok) > 2):
                results.append({
                    "source_type": "knowledge",
                    "key_signature": e.key_signature,
                    "text": e.insight,
                    "similarity": 0.5,
                })
        return {"query": query, "results": results[:top_k], "used_embeddings": False}
