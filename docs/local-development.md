# Local Development

## Prerequisites

- Docker and Docker Compose v2+
- Git

## Quick Start

```bash
# 1. Clone the repository
git clone <repo-url> && cd sbu-assistant

# 2. Create environment file
cp .env.example .env

# 3. Start all services
make up
# or: docker compose up -d --build

# 4. Wait for services to be healthy (~30 seconds)
make status

# 5. Access the platform
#    Public web:  http://localhost:3000
#    Admin panel: http://localhost:3001
#    API docs:    http://localhost:8000/docs
```

## Services

| Service | Port | Description |
|---------|------|-------------|
| web | 3000 | Public Next.js frontend |
| admin | 3001 | Admin Next.js dashboard |
| api | 8000 | FastAPI backend |
| postgres | 5432 | PostgreSQL + pgvector |
| redis | 6379 | Redis cache/queue |

## Seed Data

The API automatically seeds demo data on first boot, including:
- Admin user (admin@stonybrook.edu / admin123)
- 9 office contacts
- 8 content sources
- 7 documents with 14 indexed chunks
- 8 curated FAQ entries

To re-seed: `make seed`

## Hot Reload

All services support hot reload:
- **API**: uvicorn watches Python files
- **Web/Admin**: Next.js dev server watches TypeScript/React files

Source code is mounted as volumes, so changes are reflected immediately.

## Common Tasks

```bash
make logs          # Follow all service logs
make api-logs      # Follow API logs only
make test          # Run backend tests
make shell-api     # Open bash in API container
make shell-db      # Open psql shell
make migrate       # Run database migrations
```

## Running Tests Locally (without Docker)

```bash
cd apps/api
pip install -r requirements.txt
pytest tests/ -v
```

## Troubleshooting

**Database connection errors**: Wait for PostgreSQL to be healthy (`make status`). The API entrypoint script waits automatically.

**Port conflicts**: If ports 3000, 3001, or 8000 are in use, update the port mappings in `docker-compose.yml`.

**Stale containers**: Run `make clean` to remove all containers and volumes, then `make up` to start fresh.
