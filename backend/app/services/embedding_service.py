"""Gemini embedding API for semantic knowledge search (RAG)."""
from __future__ import annotations

import json
import logging
import math
from typing import Optional

from app.core.config import settings, is_llm_key_valid

logger = logging.getLogger("embedding_service")

EMBED_MODEL = "text-embedding-004"


class EmbeddingService:
    _client = None
    _configured = False

    @classmethod
    def _configure(cls):
        if cls._configured:
            return
        cls._configured = True
        if not is_llm_key_valid():
            return
        try:
            from google import genai

            cls._client = genai.Client(api_key=settings.GEMINI_API_KEY.strip())
        except Exception as exc:
            logger.warning("Embedding client init failed: %s", exc)

    @classmethod
    async def embed_text(cls, text: str) -> Optional[list[float]]:
        cls._configure()
        if not cls._client or not text.strip():
            return None
        try:
            result = await cls._client.aio.models.embed_content(
                model=EMBED_MODEL,
                contents=text[:8000],
            )
            values = None
            if hasattr(result, "embeddings") and result.embeddings:
                emb = result.embeddings[0]
                values = getattr(emb, "values", None) or emb.get("values") if isinstance(emb, dict) else None
            elif hasattr(result, "embedding"):
                values = getattr(result.embedding, "values", None)
            if values:
                return list(values)
        except Exception as exc:
            logger.warning("Embedding API failed, using hash fallback: %s", exc)
        return cls._hash_fallback_embedding(text)

    @classmethod
    def _hash_fallback_embedding(cls, text: str, dim: int = 128) -> list[float]:
        """Deterministic local fallback when API unavailable — still enables similarity ranking."""
        vec = [0.0] * dim
        tokens = text.lower().split()
        for i, tok in enumerate(tokens):
            idx = hash(tok) % dim
            vec[idx] += 1.0 / (1 + i * 0.01)
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]

    @staticmethod
    def cosine_similarity(a: list[float], b: list[float]) -> float:
        if not a or not b or len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a)) or 1.0
        nb = math.sqrt(sum(y * y for y in b)) or 1.0
        return dot / (na * nb)

    @staticmethod
    def vector_to_json(vec: list[float]) -> str:
        return json.dumps(vec)
