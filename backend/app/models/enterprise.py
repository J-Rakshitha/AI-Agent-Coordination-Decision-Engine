"""Enterprise intelligence models — repository symbols, embeddings, extended conflict metadata."""
from datetime import datetime
import json

from sqlalchemy import String, Float, DateTime, ForeignKey, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CodeSymbol(Base):
    """Cached AST scan of repository symbols (Repository Discovery Agent)."""
    __tablename__ = "code_symbols"

    id: Mapped[int] = mapped_column(primary_key=True)
    file_path: Mapped[str] = mapped_column(String(500), index=True)
    symbol_type: Mapped[str] = mapped_column(String(30))
    name: Mapped[str] = mapped_column(String(200), index=True)
    line_start: Mapped[int] = mapped_column(Integer, default=1)
    line_end: Mapped[int] = mapped_column(Integer, default=1)
    dependencies_json: Mapped[str] = mapped_column(Text, default="[]")
    complexity: Mapped[int] = mapped_column(Integer, default=1)
    source_snippet: Mapped[str] = mapped_column(Text, default="")
    scan_source: Mapped[str] = mapped_column(String(30), default="local")  # local | github
    scanned_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    @property
    def dependencies(self) -> list:
        try:
            return json.loads(self.dependencies_json or "[]")
        except json.JSONDecodeError:
            return []


class KnowledgeEmbedding(Base):
    """Vector embedding for semantic search (RAG) over knowledge and decisions."""
    __tablename__ = "knowledge_embeddings"

    id: Mapped[int] = mapped_column(primary_key=True)
    knowledge_entry_id: Mapped[int | None] = mapped_column(ForeignKey("knowledge_entries.id"), nullable=True)
    source_type: Mapped[str] = mapped_column(String(50))  # knowledge | decision | incident
    key_signature: Mapped[str] = mapped_column(String(300), index=True)
    source_text: Mapped[str] = mapped_column(Text)
    embedding_json: Mapped[str] = mapped_column(Text)  # JSON array of floats
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def embedding_vector(self) -> list[float]:
        try:
            return json.loads(self.embedding_json or "[]")
        except json.JSONDecodeError:
            return []
