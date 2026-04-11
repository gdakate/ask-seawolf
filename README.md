# Seaport — SBU Digital Campus

A unified AI platform for Stony Brook University, built for every stage of the Seawolf journey.

```
localhost:3000   Seaport Portal       — unified landing page for all apps
localhost:3001   Admin Dashboard      — content management & quality monitoring
localhost:3002   SB-lumni             — alumni matching & community
localhost:3003   StudyCoach           — AI-powered Socratic tutor
localhost:8000   FastAPI Backend      — shared API for all apps
```

---

## The Four Platforms

### Ask Seawolf (`/chat`)
RAG-powered Q&A chatbot grounded in official SBU data.
- 22,000+ chunks crawled from stonybrook.edu, with source citations on every answer
- Intent classification → pgvector retrieval → authority reranking → LLM synthesis
- Office routing when a question needs a real person
- Confidence scoring, topic browsing, conversation history

### Admin Dashboard (`:3001`)
Full content management and quality monitoring interface for platform operators.
- **Source management** — add, edit, or toggle the URLs the AI learns from; set authority scores and categories per source
- **Crawl & reindex jobs** — trigger fresh data fetches and re-embeddings directly from the UI, no code needed
- **Chunk inspector** — browse every ingested page and drill into the individual vector chunks
- **FAQ overrides** — curate high-priority Q&A pairs that bypass RAG entirely for guaranteed-accurate answers
- **Conversation review** — read every chat session with full message history, confidence scores, and citations
- **Evaluation runner** — run structured SBU Q&A test suites and see pass/fail rates and scores per case

### SB-lumni (`:3002`)
AI-powered alumni matching and community for Stony Brook graduates.
- Restricted to `@stonybrook.edu` / `@alumni.stonybrook.edu` — enforced via JWT domain check
- 3-step onboarding with optional résumé upload (LLM-parsed)
- **Two-stage matching pipeline** — ANN retrieval via pgvector → multi-signal reranking (major, career path, skills Jaccard, graduation proximity, MMR diversity λ=0.7)
- Connect system, community feed with hashtags, comments, and likes

### StudyCoach (`:3003`)
Socratic AI tutor built around a student's own course materials.
- Upload PDFs, DOCX, PPTX, or code files — AI auto-generates a **learning map** with meaningful section titles
- Parsing pipeline: page extraction → concept grouping (~600 words) → LLM title generation
- **Teach mode** — Socratic system prompt: one concept per message, one question at the end, never gives the answer directly
- Session history, resume or restart any past study session, study plan with progress tracking

---

## Architecture

```
┌───────────────────────────────────────────────────────────────┐
│  Seaport Portal :3000  │  Admin :3001  │  SB-lumni :3002      │
│  StudyCoach :3003          (Next.js App Router + TailwindCSS) │
├───────────────────────────────────────────────────────────────┤
│  FastAPI Backend :8000                                        │
│  ┌──────────┬───────────┬────────────┬──────────────────────┐ │
│  │ /public  │  /admin   │  /alumni   │  /studycoach         │ │
│  │ RAG Q&A  │  Mgmt+Eval│  Matching  │  Courses + Teaching  │ │
│  └──────────┴───────────┴────────────┴──────────────────────┘ │
├───────────────────────────────────────────────────────────────┤
│  PostgreSQL + pgvector  │  Redis  │  File Storage (local/S3) │
└───────────────────────────────────────────────────────────────┘
```

JWT auth restricted to `@stonybrook.edu` and `@alumni.stonybrook.edu` domains.

---

## Quick Start

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- Git

```bash
git clone https://github.com/gdakate/ask-seawolf.git
cd ask-seawolf

cp .env.example .env

docker compose up -d --build
```

All four apps and the API start together. Optionally seed demo data:

```bash
docker compose exec api python seed_alumni.py   # 50+ alumni profiles
docker compose exec api python seed_posts.py    # feed posts + connections
```

### Default Accounts

| App | Email | Password |
|---|---|---|
| Admin (`localhost:3001`) | `admin@stonybrook.edu` | `admin123` |
| SB-lumni (`localhost:3002`) | `wolfie@stonybrook.edu` | `12345678` |
| All seeded alumni | any seeded `@stonybrook.edu` email | `demo1234` |

For Ask Seawolf and StudyCoach, register with any `@stonybrook.edu` address.

---

## Load SBU Data (for real Q&A answers)

The crawled dataset isn't stored in git (~25 MB). Run these once:

```bash
# Crawl stonybrook.edu — up to 5,000 pages (~20 min)
docker compose exec api python /app/data/crawl_sbu.py

# Embed and load into the database (~20 min, CPU-only)
docker compose exec api python -m seed.load_real_data --reload
```

---

## AI Provider

Set `AI_PROVIDER` in `.env`:

| Value | LLM | Embeddings | Cost |
|---|---|---|---|
| `mock` (default) | none — returns raw retrieved text | — | free |
| `local` | Ollama / llama3.2 | fastembed / BGE-small | free, offline |
| `openai` | GPT-4o | text-embedding-3-small | OpenAI pricing |
| `bedrock` | Claude 3 Sonnet | Titan Text v2 | AWS pricing |

**For local (offline, no API key):**
```bash
brew install ollama && ollama serve && ollama pull llama3.2
# Set AI_PROVIDER=local in .env, then: docker compose up -d api
```

---

## Project Structure

```
ask-seawolf/
├── apps/
│   ├── web/            # Seaport portal + Ask Seawolf chat (:3000)
│   ├── admin/          # Admin dashboard (:3001)
│   ├── alumni/         # SB-lumni frontend (:3002)
│   ├── studycoach/     # StudyCoach frontend (:3003)
│   └── api/            # FastAPI backend (shared, :8000)
│       ├── app/
│       │   ├── routers/
│       │   │   ├── public.py       # Ask Seawolf RAG endpoints
│       │   │   ├── admin.py        # Admin CRUD, crawl, eval
│       │   │   ├── alumni.py       # SB-lumni matching + feed
│       │   │   └── studycoach.py   # Courses, materials, sessions, teach
│       │   ├── models/             # SQLAlchemy ORM models
│       │   ├── services/           # RAG pipeline, matching, AI providers
│       │   └── core/               # Config, DB session, JWT auth
│       ├── migrations/             # Alembic (001–006)
│       ├── seed_alumni.py
│       └── seed_posts.py
├── infra/terraform/    # AWS ECS/Fargate infrastructure
├── docs/               # Architecture, deployment, RAG pipeline, video script
├── docker-compose.yml
└── .env.example
```

---

## Useful Commands

```bash
docker compose up -d --build    # Start everything
docker compose logs -f          # Follow logs
docker compose exec api pytest  # Run backend tests
open http://localhost:8000/docs # API docs (Swagger)
docker compose exec api alembic upgrade head  # Run migrations
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `AI_PROVIDER` | `mock` | `mock` / `local` / `openai` / `bedrock` |
| `OPENAI_API_KEY` | — | Required when `AI_PROVIDER=openai` |
| `DATABASE_URL` | see `.env.example` | PostgreSQL async connection string |
| `REDIS_URL` | `redis://redis:6379/0` | Redis connection |
| `JWT_SECRET` | — | Change in production |
| `STORAGE_BACKEND` | `local` | `local` or `s3` |

Full list in `.env.example`.

---

## Deployment

AWS infrastructure (ECS Fargate + RDS + ElastiCache) is defined in `infra/terraform/`.
See [`docs/deployment.md`](docs/deployment.md) for step-by-step instructions.
