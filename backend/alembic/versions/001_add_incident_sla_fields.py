"""Add SLA escalation fields to incidents table.

Revision ID: 001_add_incident_sla
Revises:
Create Date: 2026-08-01

Idempotent: skips columns that already exist (safe for DBs created via create_all).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001_add_incident_sla"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _incident_columns() -> set[str]:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if "incidents" not in insp.get_table_names():
        return set()
    return {col["name"] for col in insp.get_columns("incidents")}


def upgrade() -> None:
    cols = _incident_columns()
    if not cols:
        return

    with op.batch_alter_table("incidents") as batch_op:
        if "sla_minutes" not in cols:
            batch_op.add_column(sa.Column("sla_minutes", sa.Integer(), nullable=True))
        if "sla_deadline" not in cols:
            batch_op.add_column(sa.Column("sla_deadline", sa.DateTime(), nullable=True))
        if "escalated_to" not in cols:
            batch_op.add_column(sa.Column("escalated_to", sa.String(length=100), nullable=True))


def downgrade() -> None:
    cols = _incident_columns()
    with op.batch_alter_table("incidents") as batch_op:
        if "escalated_to" in cols:
            batch_op.drop_column("escalated_to")
        if "sla_deadline" in cols:
            batch_op.drop_column("sla_deadline")
        if "sla_minutes" in cols:
            batch_op.drop_column("sla_minutes")
