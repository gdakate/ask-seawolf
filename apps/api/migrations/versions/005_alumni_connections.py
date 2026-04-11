"""Alumni connections table

Revision ID: 005_alumni_connections
Revises: 004_alumni_platform
Create Date: 2026-04-11
"""
from alembic import op
import sqlalchemy as sa

revision = "005_alumni_connections"
down_revision = "004_alumni_platform"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "alumni_connections",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("requester_id", sa.UUID(), nullable=False),
        sa.Column("target_id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["requester_id"], ["alumni_users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_id"], ["alumni_users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("requester_id", "target_id", name="uq_alumni_connection"),
    )
    op.create_index("ix_alumni_connections_requester", "alumni_connections", ["requester_id"])
    op.create_index("ix_alumni_connections_target", "alumni_connections", ["target_id"])


def downgrade():
    op.drop_table("alumni_connections")
