#!/bin/bash
set -e

echo "Waiting for PostgreSQL..."
while ! pg_isready -h postgres -p 5432 -U ${POSTGRES_USER:-sbu_user} -q 2>/dev/null; do
    sleep 1
done
echo "PostgreSQL is ready."

echo "Running migrations..."
cd /app
alembic upgrade head

echo "Seeding database..."
python -m seed.seed_data || true

echo "Starting API server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
