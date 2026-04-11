# Seaport — SBU Digital Campus

A unified AI platform for Stony Brook University, built for every stage of the Seawolf journey.

```
localhost:3000   Seaport Portal       — unified landing page for all apps
localhost:3001   Admin Dashboard      — source mgmt, crawl jobs, eval, FAQ
localhost:3002   SB-lumni             — alumni matching & community
localhost:3003   StudyCoach           — AI-powered Socratic tutor
localhost:8000   FastAPI Backend      — shared API for all apps
```

---

## The Three Platforms

### Ask Seawolf (`/chat`)
RAG-powered Q&A chatbot grounded in official SBU data.
- 22,000+ chunks crawled from stonybrook.edu
- Answers with source citations and confidence scores
- Office routing when a human is the right answer
- Conversation history, topic browsing, keyword search

### Admin Dashboard (`:3001`)
A full content management and quality monitoring interface for platform operators.

**Overview**
The dashboard home shows real-time platform health: total sources, ingested documents, chunk count, active chat sessions, and average confidence score across all responses. Crawl and reindex job status are shown inline.

**Source Management**
Add, edit, enable, or disable the URLs the AI learns from. Each source has a category (admissions, bursar, housing, etc.), an authority score that weights retrieval priority, and an optional office key for routing. Toggling a source live immediately excludes it from future retrieval without requiring a reindex.

**Crawl & Reindex Jobs**
Trigger a fresh crawl of all active sources directly from the dashboard. After crawling, run a reindex job to re-chunk, re-embed, and reload vectors into pgvector — all without touching code.

**Document & Chunk Inspection**
Browse every ingested page and drill down into the individual text chunks that make up the vector index. Each chunk shows its heading, content preview, token count, and embedding status.

**FAQ Overrides**
Curate guaranteed-correct Q&A pairs that bypass RAG retrieval entirely. Set priority levels so high-confidence answers (e.g., application deadlines, tuition figures) are always returned first, regardless of what the retrieval pipeline finds.

**Conversation Review**
Read every user chat session in full — messages, citations, confidence scores, and office routing decisions. Useful for auditing AI behavior and catching bad answers before users report them.

**Feedback & Evaluation**
- Feedback tab: user thumbs-up/down ratings and free-text comments per response
- Evaluation runner: run a structured test suite of SBU Q&A cases and see pass/fail rates, average scores, and per-case detail view — a full LLM evaluation loop without leaving the browser

### SB-lumni (`:3002`)
AI-powered alumni matching and community for Stony Brook graduates.
- Registration restricted to `@stonybrook.edu` / `@alumni.stonybrook.edu`
- 3-step onboarding with optional résumé upload (LLM-parsed)
- **Two-stage matching pipeline**: ANN retrieval via pgvector → multi-signal reranking (major, career, skills Jaccard, graduation year proximity, MMR diversity)
- Connect / disconnect with other alumni
- Community feed with hashtags, comments, and likes

### StudyCoach (`:3003`)
Socratic AI tutor built around a student's own course materials.
- Create courses, upload PDFs / DOCX / PPTX / code files
- AI auto-generates a **learning map** with titled sections and prereq relationships
- Per-material tab view, section-level study sessions
- **Teach mode**: AI teaches one concept at a time, asks one question per turn — it never just gives the answer
- Resume or restart any past study session
- Dashboard with all sessions, study plan, and progress ring

---

## Architecture

```
┌─────────────────────────────────────────────┐
│  Seaport Portal     localhost:3000            │
│  Admin Dashboard    localhost:3001            │
│  SB-lumni           localhost:3002            │
│  StudyCoach         localhost:3003            │
│           (Next.js App Router, TailwindCSS)  │
├─────────────────────────────────────────────┤
│  FastAPI Backend          localhost:8000     │
│  ┌──────────┬────────────┬────────────────┐  │
│  │  /public │  /alumni   │  /studycoach   │  │
│  │  RAG Q&A │  Matching  │  AI Teaching   │  │
│  └──────────┴────────────┴────────────────┘  │
│  /admin — content, crawl, eval, FAQ mgmt     │
├─────────────────────────────────────────────┤
│  PostgreSQL + pgvector   │   Redis           │
│  File Storage (local/S3) │   Alembic         │
└─────────────────────────────────────────────┘
```

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

That's it. All four apps and the API will start together.

Optionally seed demo data:
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

For StudyCoach and Ask Seawolf, register with any `@stonybrook.edu` address.

---

## Load SBU Data (for real Q&A answers)

The crawled dataset isn't stored in git (~25 MB). Run these once:

```bash
# Crawl stonybrook.edu — fetches up to 5,000 pages (~20 min)
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
brew install ollama
ollama serve
ollama pull llama3.2
# then set AI_PROVIDER=local in .env and restart: docker compose up -d api
```

---

## Project Structure

```
ask-seawolf/
├── apps/
│   ├── web/            # Seaport portal + Ask Seawolf chat (port 3000)
│   ├── admin/          # Admin dashboard (port 3001)
│   ├── alumni/         # SB-lumni frontend (port 3002)
│   ├── studycoach/     # StudyCoach frontend (port 3003)
│   └── api/            # FastAPI backend (shared, port 8000)
│       ├── app/
│       │   ├── routers/
│       │   │   ├── public.py       # Ask Seawolf RAG endpoints
│       │   │   ├── alumni.py       # SB-lumni matching + feed
│       │   │   ├── studycoach.py   # Courses, materials, sessions, teach
│       │   │   └── admin.py        # Admin CRUD + eval
│       │   ├── models/             # SQLAlchemy ORM models
│       │   ├── services/           # RAG pipeline, matching, AI providers
│       │   └── core/               # Config, DB session, JWT auth
│       ├── migrations/             # Alembic (001–006)
│       ├── seed_alumni.py
│       └── seed_posts.py
├── infra/terraform/    # AWS ECS/Fargate infrastructure
├── docs/               # Architecture, deployment, RAG pipeline docs
├── docker-compose.yml
└── .env.example
```

---

## Useful Commands

```bash
# Rebuild and start everything
docker compose up -d --build

# Follow logs
docker compose logs -f

# Run backend tests
docker compose exec api pytest

# Open API docs
open http://localhost:8000/docs

# Run a migration
docker compose exec api alembic upgrade head

# Shell into the API container
docker compose exec api bash
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `AI_PROVIDER` | `mock` | `mock` / `local` / `openai` / `bedrock` |
| `OPENAI_API_KEY` | — | Required when `AI_PROVIDER=openai` |
| `DATABASE_URL` | (see .env.example) | PostgreSQL async connection string |
| `REDIS_URL` | `redis://redis:6379/0` | Redis connection |
| `JWT_SECRET` | — | Change in production |
| `STORAGE_BACKEND` | `local` | `local` or `s3` |

Full list in `.env.example`.

---

## Deployment

AWS infrastructure (ECS Fargate + RDS + ElastiCache) is defined in `infra/terraform/`.
See [`docs/deployment.md`](docs/deployment.md) for step-by-step instructions.
