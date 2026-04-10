"""Initial schema with pgvector

Revision ID: 001_initial
Revises:
Create Date: 2025-01-01 00:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSON
from pgvector.sqlalchemy import Vector

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Sources
    op.create_table(
        "sources",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("url", sa.Text, nullable=False, unique=True),
        sa.Column("category", sa.String(50), server_default="general"),
        sa.Column("office", sa.String(255)),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("crawl_frequency_hours", sa.Integer, server_default="168"),
        sa.Column("authority_score", sa.Float, server_default="1.0"),
        sa.Column("last_crawled_at", sa.DateTime(timezone=True)),
        sa.Column("metadata", JSON),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Documents
    op.create_table(
        "documents",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("source_id", UUID(as_uuid=True), sa.ForeignKey("sources.id"), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("source_url", sa.Text, nullable=False),
        sa.Column("content_type", sa.String(20), server_default="html"),
        sa.Column("raw_content", sa.Text),
        sa.Column("cleaned_content", sa.Text),
        sa.Column("content_hash", sa.String(64)),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("audience", sa.String(20), server_default="all"),
        sa.Column("academic_term", sa.String(50)),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("last_seen_at", sa.DateTime(timezone=True)),
        sa.Column("is_archived", sa.Boolean, server_default="false"),
        sa.Column("version", sa.Integer, server_default="1"),
        sa.Column("metadata", JSON),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_documents_source_id", "documents", ["source_id"])
    op.create_index("ix_documents_status", "documents", ["status"])

    # Chunks
    op.create_table(
        "chunks",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("document_id", UUID(as_uuid=True), sa.ForeignKey("documents.id"), nullable=False),
        sa.Column("chunk_index", sa.Integer, nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("heading", sa.String(500)),
        sa.Column("token_count", sa.Integer, server_default="0"),
        sa.Column("embedding", Vector(384)),
        sa.Column("metadata", JSON),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_chunks_document_id", "chunks", ["document_id"])

    # Vector similarity index
    op.execute("CREATE INDEX ix_chunks_embedding ON chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 10)")

    # Office Contacts
    op.create_table(
        "office_contacts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("office_key", sa.String(100), unique=True, nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("phone", sa.String(50)),
        sa.Column("email", sa.String(255)),
        sa.Column("url", sa.Text),
        sa.Column("location", sa.String(500)),
        sa.Column("hours", sa.String(255)),
        sa.Column("category", sa.String(50), server_default="general"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # FAQ Entries
    op.create_table(
        "faq_entries",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("question", sa.Text, nullable=False),
        sa.Column("answer", sa.Text, nullable=False),
        sa.Column("category", sa.String(50), server_default="general"),
        sa.Column("office_key", sa.String(100)),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("priority", sa.Integer, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Chat Sessions
    op.create_table(
        "chat_sessions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("session_token", sa.String(255), unique=True, nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("last_active_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("metadata", JSON),
    )

    # Chat Messages
    op.create_table(
        "chat_messages",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("session_id", UUID(as_uuid=True), sa.ForeignKey("chat_sessions.id"), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("citations", JSON),
        sa.Column("confidence_score", sa.Float),
        sa.Column("office_routing", JSON),
        sa.Column("follow_up_questions", JSON),
        sa.Column("model_used", sa.String(100)),
        sa.Column("latency_ms", sa.Integer),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_chat_messages_session_id", "chat_messages", ["session_id"])

    # User Feedback
    op.create_table(
        "user_feedback",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("message_id", UUID(as_uuid=True), sa.ForeignKey("chat_messages.id")),
        sa.Column("rating", sa.Integer),
        sa.Column("comment", sa.Text),
        sa.Column("feedback_type", sa.String(50), server_default="general"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Crawl Jobs
    op.create_table(
        "crawl_jobs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("source_id", UUID(as_uuid=True), sa.ForeignKey("sources.id")),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("pages_found", sa.Integer, server_default="0"),
        sa.Column("pages_ingested", sa.Integer, server_default="0"),
        sa.Column("error_message", sa.Text),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Index Jobs
    op.create_table(
        "index_jobs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("documents_processed", sa.Integer, server_default="0"),
        sa.Column("chunks_created", sa.Integer, server_default="0"),
        sa.Column("error_message", sa.Text),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Evaluation Runs
    op.create_table(
        "evaluation_runs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("total_cases", sa.Integer, server_default="0"),
        sa.Column("passed_cases", sa.Integer, server_default="0"),
        sa.Column("avg_retrieval_score", sa.Float),
        sa.Column("avg_answer_score", sa.Float),
        sa.Column("metadata", JSON),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
    )

    # Evaluation Cases
    op.create_table(
        "evaluation_cases",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("run_id", UUID(as_uuid=True), sa.ForeignKey("evaluation_runs.id"), nullable=False),
        sa.Column("question", sa.Text, nullable=False),
        sa.Column("expected_answer", sa.Text),
        sa.Column("actual_answer", sa.Text),
        sa.Column("retrieved_chunks", JSON),
        sa.Column("retrieval_score", sa.Float),
        sa.Column("answer_score", sa.Float),
        sa.Column("passed", sa.Boolean),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Admin Users
    op.create_table(
        "admin_users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), server_default=""),
        sa.Column("role", sa.String(50), server_default="admin"),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("last_login_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Audit Logs
    op.create_table(
        "audit_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("admin_email", sa.String(255), nullable=False),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(100)),
        sa.Column("resource_id", sa.String(255)),
        sa.Column("details", JSON),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("admin_users")
    op.drop_table("evaluation_cases")
    op.drop_table("evaluation_runs")
    op.drop_table("index_jobs")
    op.drop_table("crawl_jobs")
    op.drop_table("user_feedback")
    op.drop_table("chat_messages")
    op.drop_table("chat_sessions")
    op.drop_table("faq_entries")
    op.drop_table("office_contacts")
    op.drop_table("chunks")
    op.drop_table("documents")
    op.drop_table("sources")
    op.execute("DROP EXTENSION IF EXISTS vector")
