"""Add hit_count and last_used_at to faq_entries

Revision ID: 003
Revises: 002
Create Date: 2026-04-11
"""
from alembic import op
import sqlalchemy as sa

revision = "003_faq_usage_tracking"
down_revision = "002_add_public_users"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("faq_entries", sa.Column("hit_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("faq_entries", sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True))


def downgrade():
    op.drop_column("faq_entries", "last_used_at")
    op.drop_column("faq_entries", "hit_count")
