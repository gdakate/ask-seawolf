"""Alumni platform tables

Revision ID: 004_alumni_platform
Revises: 003_faq_usage_tracking
Create Date: 2026-04-10
"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

revision = "004_alumni_platform"
down_revision = "003_faq_usage_tracking"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "alumni_users",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "alumni_profiles",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.UUID(as_uuid=True), sa.ForeignKey("alumni_users.id"), unique=True, nullable=False),
        sa.Column("major", sa.String(255), nullable=False),
        sa.Column("degree", sa.String(20), nullable=False),
        sa.Column("graduation_year", sa.Integer(), nullable=False),
        sa.Column("is_international", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("current_company", sa.String(255), nullable=True),
        sa.Column("job_title", sa.String(255), nullable=True),
        sa.Column("industry", sa.String(255), nullable=True),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("skills", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("interests", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("open_to", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("linkedin_url", sa.String(500), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("is_visible", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("profile_embedding", Vector(384), nullable=True),
        sa.Column("skills_embedding", Vector(384), nullable=True),
        sa.Column("interests_embedding", Vector(384), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_alumni_profiles_major", "alumni_profiles", ["major"])
    op.create_index("ix_alumni_profiles_graduation_year", "alumni_profiles", ["graduation_year"])

    op.create_table(
        "alumni_posts",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("author_id", sa.UUID(as_uuid=True), sa.ForeignKey("alumni_profiles.id"), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("likes_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("comments_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_pinned", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_alumni_posts_created_at", "alumni_posts", ["created_at"])

    op.create_table(
        "alumni_comments",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("post_id", sa.UUID(as_uuid=True), sa.ForeignKey("alumni_posts.id"), nullable=False),
        sa.Column("author_id", sa.UUID(as_uuid=True), sa.ForeignKey("alumni_profiles.id"), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "alumni_likes",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("post_id", sa.UUID(as_uuid=True), sa.ForeignKey("alumni_posts.id"), nullable=False),
        sa.Column("user_id", sa.UUID(as_uuid=True), sa.ForeignKey("alumni_users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_alumni_likes_post_user", "alumni_likes", ["post_id", "user_id"], unique=True)


def downgrade():
    op.drop_table("alumni_likes")
    op.drop_table("alumni_comments")
    op.drop_table("alumni_posts")
    op.drop_index("ix_alumni_profiles_major", "alumni_profiles")
    op.drop_index("ix_alumni_profiles_graduation_year", "alumni_profiles")
    op.drop_table("alumni_profiles")
    op.drop_table("alumni_users")
