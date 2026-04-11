# AGENTS.md — Stony Brook AI Assistant Platform : Ask Seawolves

## Project Rules

1. **Monorepo Structure**: All code lives under this root. Frontend apps in `/apps`, backend services in `/services`, shared code in `/packages`, infra in `/infra`.
2. **Language Standards**: Python 3.12+ for backend, TypeScript for frontend. Strong typing everywhere.
3. **Environment Config**: All secrets and provider settings via environment variables. Never hardcode credentials.
4. **Local-First**: The platform must run locally via `docker-compose up` with seeded demo data and mock AI providers.
5. **Production-Shaped**: Code should be structured for real deployment, not demo shortcuts.
6. **RAG Architecture**: All answers grounded in retrieved context. Citation-first. No hallucinated content.
7. **Mock Mode**: When external services (OpenAI, Bedrock, S3) are unavailable, local stubs keep the system running.
8. **Database**: PostgreSQL + pgvector. SQLAlchemy models, Alembic migrations. Seed data included.
9. **Testing**: pytest for backend core logic. Tests must pass.
10. **Documentation**: README, architecture docs, setup guides all maintained.

## Key Decisions

- FastAPI for all backend APIs
- Next.js App Router for both web and admin frontends
- pgvector for vector search with abstraction for future OpenSearch
- Celery + Redis for background jobs
- Docker Compose for local development
- Terraform for AWS infrastructure definitions
- JWT-based admin auth with Cognito-ready abstraction
- Amazon Bedrock for hosting
