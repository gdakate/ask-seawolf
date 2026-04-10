.PHONY: help up down build logs api-logs web-logs admin-logs seed migrate test lint clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

up: ## Start all services
	docker compose up -d --build

down: ## Stop all services
	docker compose down

build: ## Build all images
	docker compose build

logs: ## Follow all logs
	docker compose logs -f

api-logs: ## Follow API logs
	docker compose logs -f api

web-logs: ## Follow web logs
	docker compose logs -f web

admin-logs: ## Follow admin logs
	docker compose logs -f admin

seed: ## Re-run seed data
	docker compose exec api python -m seed.seed_data

migrate: ## Run database migrations
	docker compose exec api alembic upgrade head

migrate-new: ## Create a new migration (usage: make migrate-new msg="description")
	docker compose exec api alembic revision --autogenerate -m "$(msg)"

test: ## Run backend tests
	docker compose exec api python -m pytest tests/ -v

lint: ## Run linting
	cd apps/api && python -m py_compile app/main.py

shell-api: ## Open shell in API container
	docker compose exec api bash

shell-db: ## Open psql shell
	docker compose exec postgres psql -U sbu_user -d sbu_assistant

clean: ## Remove all containers, volumes, and images
	docker compose down -v --rmi local
	docker system prune -f

status: ## Show service status
	docker compose ps
