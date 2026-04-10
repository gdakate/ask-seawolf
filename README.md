# Ask Seawolves — Stony Brook University AI Assistant Platform

A production-ready, RAG-powered Q&A platform for Stony Brook University public information. Students, applicants, and visitors can ask questions and receive cited answers grounded in official university sources.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Public Web App                     │
│                   (Next.js :3000)                     │
├─────────────────────────────────────────────────────┤
│                   Admin Dashboard                     │
│                   (Next.js :3001)                     │
├─────────────────────────────────────────────────────┤
│                    FastAPI Backend                     │
│                     (Python :8000)                     │
│  ┌──────────┬───────────┬────────────┬────────────┐  │
│  │ Ingestion│  Indexing  │ Retrieval  │ Answering  │  │
│  │ Service  │  Service   │  Service   │  Service   │  │
│  └──────────┴───────────┴────────────┴────────────┘  │
├─────────────────────────────────────────────────────┤
│  PostgreSQL + pgvector  │  Redis  │  S3/Local Storage │
└─────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites
- Docker and Docker Compose
- (Optional) Node.js 20+ and Python 3.12+ for local development without Docker

### Run with Docker

```bash
# Clone and setup
cp .env.example .env

# Start all services
docker compose up -d --build

# The platform starts with:
#   - Public web app:  http://localhost:3000
#   - Admin dashboard: http://localhost:3001
#   - API + docs:      http://localhost:8000/docs
#   - PostgreSQL:      localhost:5432
```

The API automatically runs migrations and seeds demo data on first boot.

### Default Admin Login
- Email: `admin@stonybrook.edu`
- Password: `admin123`

## Project Structure

```
├── apps/
│   ├── web/          # Public Next.js frontend
│   ├── admin/        # Admin Next.js dashboard
│   └── api/          # FastAPI backend
│       ├── app/
│       │   ├── core/       # Config, database, auth
│       │   ├── models/     # SQLAlchemy models
│       │   ├── schemas/    # Pydantic schemas
│       │   ├── routers/    # API endpoints
│       │   └── services/   # Business logic (RAG pipeline)
│       ├── migrations/     # Alembic migrations
│       ├── seed/           # Demo seed data
│       └── tests/          # pytest tests
├── infra/terraform/        # AWS infrastructure
├── docs/                   # Documentation
├── docker-compose.yml      # Local development stack
└── Makefile               # Common commands
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `AI_PROVIDER` | `mock` | AI backend: `mock`, `openai`, or `bedrock` |
| `OPENAI_API_KEY` | — | OpenAI API key (when AI_PROVIDER=openai) |
| `DATABASE_URL` | — | PostgreSQL connection string |
| `REDIS_URL` | — | Redis connection string |
| `STORAGE_BACKEND` | `local` | Storage: `local` or `s3` |
| `JWT_SECRET` | — | Secret for admin JWT tokens |

See `.env.example` for the full list.

## AI Provider Configuration

The platform supports three AI provider modes:

- **Mock** (default): Deterministic embeddings and template responses. No external API required. Ideal for development.
- **OpenAI**: Set `AI_PROVIDER=openai` and `OPENAI_API_KEY`. Uses GPT-4o for generation and text-embedding-3-small for embeddings.
- **AWS Bedrock**: Set `AI_PROVIDER=bedrock` with AWS credentials. Uses Claude for generation and Titan for embeddings.

## Key Features

### Public App
- Chat interface with real-time Q&A
- Source citations on every answer
- Office routing for human help
- Topic browsing and document search
- Confidence indicators and warnings

### Admin Dashboard
- Source management (CRUD)
- Document and chunk inspection
- Crawl/index job management
- Conversation and feedback review
- FAQ override management
- Evaluation runner

### RAG Pipeline
- Heading-aware document chunking
- Vector search via pgvector
- Keyword fallback search
- Citation bundling
- Office routing detection
- Confidence scoring
- Term-dependency warnings

## Makefile Commands

```bash
make up          # Start all services
make down        # Stop all services
make test        # Run backend tests
make logs        # Follow logs
make seed        # Re-run seed data
make migrate     # Run migrations
make shell-api   # Shell into API container
make shell-db    # Open psql shell
```

## Deployment

See `docs/deployment.md` for AWS deployment instructions using Terraform and ECS/Fargate.

## Documentation

- [Architecture](docs/architecture.md)
- [Local Development](docs/local-development.md)
- [Deployment](docs/deployment.md)
- [Data Model](docs/data-model.md)
- [RAG Pipeline](docs/rag-pipeline.md)
- [Admin Guide](docs/admin-guide.md)
