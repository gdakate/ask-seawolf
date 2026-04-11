"""Migrate embedding columns from vector(384) to vector(1024) for Bedrock Titan v2.

Revision ID: 006
Revises: 005
Create Date: 2026-04-11
"""
from alembic import op

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop all embedding indexes first
    op.execute("DROP INDEX IF EXISTS ix_chunks_embedding")
    op.execute("DROP INDEX IF EXISTS ix_alumni_profiles_profile_embedding")
    op.execute("DROP INDEX IF EXISTS ix_alumni_profiles_skills_embedding")
    op.execute("DROP INDEX IF EXISTS ix_alumni_profiles_interests_embedding")

    # Resize embedding columns (nulls existing data — re-embed after migration)
    op.execute("ALTER TABLE chunks ALTER COLUMN embedding TYPE vector(1024) USING NULL")
    op.execute("ALTER TABLE alumni_profiles ALTER COLUMN profile_embedding TYPE vector(1024) USING NULL")
    op.execute("ALTER TABLE alumni_profiles ALTER COLUMN skills_embedding TYPE vector(1024) USING NULL")
    op.execute("ALTER TABLE alumni_profiles ALTER COLUMN interests_embedding TYPE vector(1024) USING NULL")

    # Rebuild HNSW indexes for 1024-dim vectors
    op.execute(
        "CREATE INDEX ix_chunks_embedding "
        "ON chunks USING hnsw (embedding vector_cosine_ops) "
        "WITH (m = 16, ef_construction = 64)"
    )
    op.execute(
        "CREATE INDEX ix_alumni_profiles_profile_embedding "
        "ON alumni_profiles USING hnsw (profile_embedding vector_cosine_ops) "
        "WITH (m = 16, ef_construction = 64)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_chunks_embedding")
    op.execute("DROP INDEX IF EXISTS ix_alumni_profiles_profile_embedding")

    op.execute("ALTER TABLE chunks ALTER COLUMN embedding TYPE vector(384) USING NULL")
    op.execute("ALTER TABLE alumni_profiles ALTER COLUMN profile_embedding TYPE vector(384) USING NULL")
    op.execute("ALTER TABLE alumni_profiles ALTER COLUMN skills_embedding TYPE vector(384) USING NULL")
    op.execute("ALTER TABLE alumni_profiles ALTER COLUMN interests_embedding TYPE vector(384) USING NULL")

    op.execute(
        "CREATE INDEX ix_chunks_embedding "
        "ON chunks USING hnsw (embedding vector_cosine_ops) "
        "WITH (m = 16, ef_construction = 64)"
    )
