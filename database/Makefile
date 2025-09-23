# Database Management Makefile
# Easy-to-use commands for database operations

.PHONY: help build up down logs shell health migrate migrate-down seed reset backup restore clean

# Default environment variables
COMPOSE_FILE ?= docker-compose.db.yml
POSTGRES_USER ?= mad
POSTGRES_PASSWORD ?= mad_password
POSTGRES_DB ?= mad
DATABASE_URL ?= postgresql+asyncpg://$(POSTGRES_USER):$(POSTGRES_PASSWORD)@localhost:5432/$(POSTGRES_DB)

# Colors for output
BLUE := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
RESET := \033[0m

help: ## Show this help message
	@echo "$(BLUE)Database Management Commands$(RESET)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(RESET) %s\n", $$1, $$2}'

# Docker operations
build: ## Build database container
	@echo "$(BLUE)Building database container...$(RESET)"
	docker compose -f $(COMPOSE_FILE) build

up: ## Start database services
	@echo "$(BLUE)Starting database services...$(RESET)"
	docker compose -f $(COMPOSE_FILE) up -d postgres redis
	@echo "$(GREEN)Database services started!$(RESET)"
	@echo "PostgreSQL: localhost:5432"
	@echo "Redis: localhost:6379"

down: ## Stop database services
	@echo "$(YELLOW)Stopping database services...$(RESET)"
	docker compose -f $(COMPOSE_FILE) down

logs: ## Show database logs
	docker compose -f $(COMPOSE_FILE) logs -f postgres redis

shell: ## Open PostgreSQL shell
	docker compose -f $(COMPOSE_FILE) exec postgres psql -U $(POSTGRES_USER) -d $(POSTGRES_DB)

# Health and monitoring
health: ## Run database health check
	@echo "$(BLUE)Running database health check...$(RESET)"
	docker compose -f $(COMPOSE_FILE) run --rm healthcheck python scripts/health_check.py

health-continuous: ## Run continuous health monitoring
	@echo "$(BLUE)Starting continuous health monitoring...$(RESET)"
	docker compose -f $(COMPOSE_FILE) run --rm healthcheck

# Migration operations
migrate: ## Run database migrations (default: metadata)
	@echo "$(BLUE)Running database migrations...$(RESET)"
	docker compose -f $(COMPOSE_FILE) run --rm migrate

migrate-results: ## Run results database migrations for organization
	@echo "$(BLUE)Running results database migrations...$(RESET)"
	@if [ -z "$(ORG_ID)" ]; then \
		echo "$(RED)Error: ORG_ID is required. Usage: make migrate-results ORG_ID=org123$(RESET)"; \
		exit 1; \
	fi
	docker compose -f $(COMPOSE_FILE) run --rm -e ALEMBIC_BRANCH=results -e ORG_ID=$(ORG_ID) migrate

migrate-status: ## Show current migration status
	@echo "$(BLUE)Migration status:$(RESET)"
	docker compose -f $(COMPOSE_FILE) run --rm migrate python scripts/migrate.py --current

migrate-history: ## Show migration history
	@echo "$(BLUE)Migration history:$(RESET)"
	docker compose -f $(COMPOSE_FILE) run --rm migrate python scripts/migrate.py --history

migrate-down: ## Downgrade database migration
	@echo "$(YELLOW)Downgrading database migration...$(RESET)"
	@if [ -z "$(REV)" ]; then \
		echo "$(RED)Error: REV is required. Usage: make migrate-down REV=<revision>$(RESET)"; \
		exit 1; \
	fi
	docker compose -f $(COMPOSE_FILE) run --rm migrate python scripts/migrate.py --downgrade $(REV)

# Data operations
seed: ## Seed database with initial data
	@echo "$(BLUE)Seeding database with initial data...$(RESET)"
	docker compose -f $(COMPOSE_FILE) run --rm seed

seed-force: ## Force reseed database (replaces existing data)
	@echo "$(YELLOW)Force reseeding database...$(RESET)"
	docker compose -f $(COMPOSE_FILE) run --rm seed python scripts/seed.py --force

# Database management
reset: ## Reset database (drop and recreate)
	@echo "$(RED)Resetting database...$(RESET)"
	@read -p "Are you sure you want to reset the database? This will delete all data! (y/N): " confirm && \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		docker compose -f $(COMPOSE_FILE) down -v; \
		docker compose -f $(COMPOSE_FILE) up -d postgres redis; \
		sleep 5; \
		make migrate; \
		make seed; \
		echo "$(GREEN)Database reset complete!$(RESET)"; \
	else \
		echo "$(YELLOW)Database reset cancelled.$(RESET)"; \
	fi

backup: ## Backup database
	@echo "$(BLUE)Creating database backup...$(RESET)"
	@mkdir -p backups
	@BACKUP_FILE="backups/mad_backup_$(shell date +%Y%m%d_%H%M%S).sql"
	docker compose -f $(COMPOSE_FILE) exec postgres pg_dump -U $(POSTGRES_USER) -d $(POSTGRES_DB) > $$BACKUP_FILE
	@echo "$(GREEN)Backup created: $$BACKUP_FILE$(RESET)"

restore: ## Restore database from backup
	@echo "$(YELLOW)Restoring database from backup...$(RESET)"
	@if [ -z "$(BACKUP_FILE)" ]; then \
		echo "$(RED)Error: BACKUP_FILE is required. Usage: make restore BACKUP_FILE=backups/file.sql$(RESET)"; \
		exit 1; \
	fi
	@if [ ! -f "$(BACKUP_FILE)" ]; then \
		echo "$(RED)Error: Backup file $(BACKUP_FILE) not found$(RESET)"; \
		exit 1; \
	fi
	docker compose -f $(COMPOSE_FILE) exec -T postgres psql -U $(POSTGRES_USER) -d $(POSTGRES_DB) < $(BACKUP_FILE)
	@echo "$(GREEN)Database restored from $(BACKUP_FILE)$(RESET)"

# Development helpers
dev-setup: up migrate seed ## Complete development setup
	@echo "$(GREEN)Development environment ready!$(RESET)"
	@make health

clean: ## Clean up containers and volumes
	@echo "$(YELLOW)Cleaning up containers and volumes...$(RESET)"
	docker compose -f $(COMPOSE_FILE) down -v --remove-orphans
	docker system prune -f

# Local development (without Docker)
local-migrate: ## Run migrations locally (requires local PostgreSQL)
	@echo "$(BLUE)Running local migrations...$(RESET)"
	@cd database && python scripts/migrate.py --upgrade

local-seed: ## Seed local database
	@echo "$(BLUE)Seeding local database...$(RESET)"
	@cd database && python scripts/seed.py

local-health: ## Check local database health
	@echo "$(BLUE)Checking local database health...$(RESET)"
	@cd database && python scripts/health_check.py

# Testing
test-migrations: ## Test migrations (up and down)
	@echo "$(BLUE)Testing migrations...$(RESET)"
	@echo "$(YELLOW)This will modify your database!$(RESET)"
	@read -p "Continue? (y/N): " confirm && \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		make migrate-status; \
		echo "$(BLUE)Running upgrade...$(RESET)"; \
		make migrate; \
		echo "$(BLUE)Running downgrade...$(RESET)"; \
		make migrate-down REV=-1; \
		echo "$(BLUE)Running upgrade again...$(RESET)"; \
		make migrate; \
		echo "$(GREEN)Migration test complete!$(RESET)"; \
	fi

# Quick commands
quick-reset: down up migrate seed ## Quick reset for development

# Documentation
docs: ## Generate database documentation
	@echo "$(BLUE)Database structure documented in README.md$(RESET)"
	@echo "Models: database/models/"
	@echo "Migrations: database/alembic/versions/"
	@echo "Scripts: database/scripts/"
