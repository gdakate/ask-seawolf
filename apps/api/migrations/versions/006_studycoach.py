"""StudyCoach tables

Revision ID: 006_studycoach
Revises: 005_alumni_connections
Create Date: 2026-04-11
"""
from alembic import op
import sqlalchemy as sa

revision = "006_studycoach"
down_revision = "005_alumni_connections"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "sc_users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), default=True, nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )

    op.create_table(
        "sc_courses",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["sc_users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "sc_materials",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("course_id", sa.UUID(), nullable=False),
        sa.Column("filename", sa.String(500), nullable=False),
        sa.Column("file_type", sa.String(20), nullable=False),
        sa.Column("raw_text", sa.Text()),
        sa.Column("status", sa.String(20), default="pending", nullable=False),
        sa.Column("parsed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["course_id"], ["sc_courses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "sc_sections",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("material_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("order", sa.Integer(), default=0, nullable=False),
        sa.Column("content", sa.Text()),
        sa.Column("difficulty", sa.Integer(), default=3, nullable=False),
        sa.Column("concepts", sa.JSON(), nullable=False),
        sa.Column("prerequisites", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["material_id"], ["sc_materials.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "sc_plan_items",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("course_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("due_date", sa.DateTime(timezone=True)),
        sa.Column("item_type", sa.String(30), default="study", nullable=False),
        sa.Column("is_completed", sa.Boolean(), default=False, nullable=False),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["course_id"], ["sc_courses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "sc_teach_sessions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("course_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("section_id", sa.UUID()),
        sa.Column("knowledge_level", sa.String(20), default="unknown", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["course_id"], ["sc_courses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["sc_users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["section_id"], ["sc_sections.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "sc_teach_messages",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("session_id", sa.UUID(), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("intent", sa.String(50)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["sc_teach_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    op.drop_table("sc_teach_messages")
    op.drop_table("sc_teach_sessions")
    op.drop_table("sc_plan_items")
    op.drop_table("sc_sections")
    op.drop_table("sc_materials")
    op.drop_table("sc_courses")
    op.drop_table("sc_users")
