# Ask Seawolves — Stony Brook University AI Assistant Platform

A production-ready, RAG-powered Q&A platform for Stony Brook University public information, plus **SB-lumni** — an AI-powered alumni matching and community platform exclusively for SBU graduates.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Public Web App                     │
│                   (Next.js :3000)                     │
├─────────────────────────────────────────────────────┤
│                   Admin Dashboard                     │
│                   (Next.js :3001)                     │
├─────────────────────────────────────────────────────┤
│               SB-lumni Alumni Platform                │
│                   (Next.js :3002)                     │
├─────────────────────────────────────────────────────┤
│                    FastAPI Backend                     │
│                     (Python :8000)                     │
│  ┌──────────┬───────────┬────────────┬────────────┐  │
│  │ Ingestion│  Indexing  │ Retrieval  │ Answering  │  │
│  └──────────┴───────────┴────────────┴────────────┘  │
├─────────────────────────────────────────────────────┤
│  PostgreSQL + pgvector  │  Redis  │  S3/Local Storage │
└─────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- (Optional for AI answers) [Ollama](https://ollama.com)

### Run with Docker

```bash
# 1. Clone the repo
git clone https://github.com/gdakate/ask-seawolf.git
cd ask-seawolf

# 2. Copy environment config
cp .env.example .env

# 3. Start all services (builds images, runs migrations, seeds demo data)
docker compose up -d --build

# 4. Seed alumni demo data (50+ profiles + posts + connections)
docker compose exec api python seed_alumni.py
docker compose exec api python seed_posts.py
```

Once running:
- Public web app:    http://localhost:3000
- Admin dashboard:  http://localhost:3001
- SB-lumni:         http://localhost:3002
- API docs:         http://localhost:8000/docs

### Load Real SBU Data (required for useful answers)

The crawled dataset is not stored in git (it's ~25MB). Generate it:

```bash
# Step 1 — Crawl the SBU website (~20 min, fetches up to 5000 pages)
docker compose exec api python /app/data/crawl_sbu.py

# Step 2 — Embed and load into the database (~20 min, CPU-only)
docker compose exec api python -m seed.load_real_data --reload
```

To recrawl and refresh the data any time, just run both commands again.

### Enable AI Answer Generation (optional)

Without this, the app returns raw retrieved text. With it, answers are synthesized by an LLM.

**Option A — Local (free, private, no API key)**
```bash
brew install ollama        # macOS
ollama serve               # start the server
ollama pull llama3.2       # download model (~2GB, one time)
```
Set in `.env`: `AI_PROVIDER=local`

**Option B — OpenAI**
Set in `.env`:
```
AI_PROVIDER=openai
OPENAI_API_KEY=sk-...
```
Then restart: `docker compose up -d api`

### Default Login Accounts

**Admin Dashboard** (http://localhost:3001)
- Email: `admin@stonybrook.edu`
- Password: `admin123`

**SB-lumni Alumni Platform** (http://localhost:3002)
- Email: `wolfie@stonybrook.edu`
- Password: `12345678`

> All 50+ seeded alumni accounts use password `demo1234`.

## Project Structure

```
├── apps/
│   ├── web/          # Public Next.js frontend (Ask Wolfie)
│   ├── admin/        # Admin Next.js dashboard
│   ├── alumni/       # SB-lumni Next.js frontend (:3002)
│   └── api/          # FastAPI backend (shared)
│       ├── app/
│       │   ├── core/       # Config, database, auth
│       │   ├── models/     # SQLAlchemy models
│       │   ├── schemas/    # Pydantic schemas
│       │   ├── routers/    # API endpoints
│       │   │   └── alumni.py  # Alumni platform routes
│       │   └── services/   # Business logic (RAG + matching pipeline)
│       ├── migrations/     # Alembic migrations (001–005)
│       ├── seed/           # Ask Wolfie demo seed data
│       ├── seed_alumni.py  # Alumni profiles + embeddings seed
│       ├── seed_posts.py   # Alumni feed posts + connections seed
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

The platform supports four AI provider modes:

- **Mock** (default): Returns raw retrieved text. No external service needed. Good for testing retrieval.
- **Local**: Ollama (LLM) + fastembed (embeddings). Fully offline, no API key. Set `AI_PROVIDER=local`.
- **OpenAI**: Set `AI_PROVIDER=openai` and `OPENAI_API_KEY`. Uses GPT-4o + text-embedding-3-small.
- **AWS Bedrock**: Set `AI_PROVIDER=bedrock` with AWS credentials. Uses Claude + Titan embeddings.

## Key Features

### Public App — Ask Wolfie
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
- FAQ override management with semantic clustering
- Evaluation runner with per-case detail view
- Live settings and analytics

### RAG Pipeline
- Heading-aware document chunking
- Vector search via pgvector
- Keyword fallback search
- Citation bundling
- Office routing detection
- Confidence scoring
- Term-dependency warnings

### SB-lumni — Alumni Platform
- SBU-only registration (`@stonybrook.edu` / `@alumni.stonybrook.edu`)
- 3-step onboarding with optional résumé upload (LLM-parsed)
- **AI-powered People matching** — 2-stage pipeline:
  - Stage 1: ANN retrieval via pgvector (cosine similarity on profile/skills/interests embeddings)
  - Stage 2: Multi-signal reranking (major, career path, skills Jaccard, graduation proximity, open-to compatibility)
  - MMR (Maximal Marginal Relevance) diversity selection, λ = 0.7
  - Human-readable match reasons on every card
- **Connect system** — connect/disconnect with any alumni, dedicated Connected tab
- **Community Feed** — post with hashtags (#career, #research, #networking, …), comments, likes
- Profile view & edit (own profile + public profiles of other alumni)
- 50+ seeded alumni profiles across all majors, industries, degrees, and graduation years (2007–2025)

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
