"""Enterprise tables + conflict intelligence columns.

Revision ID: 002_enterprise_intelligence
Revises: 001_add_incident_sla
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002_enterprise_intelligence"
down_revision: Union[str, None] = "001_add_incident_sla"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _columns(table: str) -> set[str]:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if table not in insp.get_table_names():
        return set()
    return {c["name"] for c in insp.get_columns(table)}


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    tables = set(insp.get_table_names())

    if "code_symbols" not in tables:
        op.create_table(
            "code_symbols",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("file_path", sa.String(500), nullable=False),
            sa.Column("symbol_type", sa.String(30), nullable=False),
            sa.Column("name", sa.String(200), nullable=False),
            sa.Column("line_start", sa.Integer(), default=1),
            sa.Column("line_end", sa.Integer(), default=1),
            sa.Column("dependencies_json", sa.Text(), default="[]"),
            sa.Column("complexity", sa.Integer(), default=1),
            sa.Column("source_snippet", sa.Text(), default=""),
            sa.Column("scan_source", sa.String(30), default="local"),
            sa.Column("scanned_at", sa.DateTime(), nullable=True),
        )

    if "knowledge_embeddings" not in tables:
        op.create_table(
            "knowledge_embeddings",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("knowledge_entry_id", sa.Integer(), sa.ForeignKey("knowledge_entries.id"), nullable=True),
            sa.Column("source_type", sa.String(50), nullable=False),
            sa.Column("key_signature", sa.String(300), nullable=False),
            sa.Column("source_text", sa.Text(), nullable=False),
            sa.Column("embedding_json", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=True),
        )

    ce_cols = _columns("conflict_events")
    if ce_cols:
        with op.batch_alter_table("conflict_events") as batch:
            for col, typ in [
                ("discovery_context", sa.Text()),
                ("semantic_analysis", sa.Text()),
                ("quality_report", sa.Text()),
                ("resolution_options", sa.Text()),
            ]:
                if col not in ce_cols:
                    batch.add_column(sa.Column(col, typ, nullable=True))


def downgrade() -> None:
    ce_cols = _columns("conflict_events")
    if ce_cols:
        with op.batch_alter_table("conflict_events") as batch:
            for col in ("resolution_options", "quality_report", "semantic_analysis", "discovery_context"):
                if col in ce_cols:
                    batch.drop_column(col)
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if "knowledge_embeddings" in insp.get_table_names():
        op.drop_table("knowledge_embeddings")
    if "code_symbols" in insp.get_table_names():
        op.drop_table("code_symbols")
