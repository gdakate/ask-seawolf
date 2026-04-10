#!/bin/bash
set -e

echo "================================================"
echo "  Stony Brook AI Assistant Platform Setup"
echo "================================================"
echo ""

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is required. Install from https://docs.docker.com/get-docker/"
    exit 1
fi

if ! docker compose version &> /dev/null; then
    echo "ERROR: Docker Compose v2 is required."
    exit 1
fi

echo "✓ Docker and Docker Compose found"

# Create .env if not exists
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✓ Created .env from .env.example"
else
    echo "✓ .env already exists"
fi

# Build and start
echo ""
echo "Building and starting all services..."
docker compose up -d --build

echo ""
echo "Waiting for services to be healthy..."
sleep 10

# Check health
echo ""
echo "Checking service health..."
for i in {1..30}; do
    if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
        echo "✓ API is healthy"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "⚠ API health check timed out. Check: docker compose logs api"
    fi
    sleep 2
done

echo ""
echo "================================================"
echo "  Platform is running!"
echo "================================================"
echo ""
echo "  Public Web App:    http://localhost:3000"
echo "  Admin Dashboard:   http://localhost:3001"
echo "  API Documentation: http://localhost:8000/docs"
echo ""
echo "  Admin Login:"
echo "    Email:    admin@stonybrook.edu"
echo "    Password: admin123"
echo ""
echo "  Useful commands:"
echo "    make logs      - View logs"
echo "    make test      - Run tests"
echo "    make down      - Stop services"
echo "    make clean     - Remove everything"
echo ""
