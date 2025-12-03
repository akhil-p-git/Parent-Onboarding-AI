# Zapier Triggers API - Makefile
# Common development commands

.PHONY: help install dev test lint format run docker-up docker-down clean

# Default target
help:
	@echo "Zapier Triggers API - Development Commands"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Setup:"
	@echo "  install      Install production dependencies"
	@echo "  dev          Install development dependencies"
	@echo "  pre-commit   Install pre-commit hooks"
	@echo ""
	@echo "Development:"
	@echo "  run          Run the API locally"
	@echo "  run-reload   Run with hot reload"
	@echo "  worker       Run the worker process"
	@echo ""
	@echo "Testing:"
	@echo "  test         Run all tests"
	@echo "  test-unit    Run unit tests only"
	@echo "  test-int     Run integration tests only"
	@echo "  test-cov     Run tests with coverage report"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint         Run linters (ruff, mypy)"
	@echo "  format       Format code (black, ruff)"
	@echo "  check        Run all checks (lint + test)"
	@echo ""
	@echo "Docker:"
	@echo "  docker-up    Start all services"
	@echo "  docker-down  Stop all services"
	@echo "  docker-logs  View service logs"
	@echo "  docker-test  Run tests in Docker"
	@echo ""
	@echo "Database:"
	@echo "  db-migrate   Run database migrations"
	@echo "  db-revision  Create new migration"
	@echo "  db-reset     Reset database"
	@echo ""
	@echo "Cleanup:"
	@echo "  clean        Remove build artifacts"
	@echo "  clean-docker Remove Docker volumes"

# Setup
install:
	pip install -r backend/requirements.txt

dev:
	pip install -e ".[dev]"

pre-commit:
	pip install pre-commit
	pre-commit install

# Development
run:
	cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000

run-reload:
	cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

worker:
	cd backend && python -m app.workers.delivery_worker

# Testing
test:
	pytest tests/ -v

test-unit:
	pytest tests/unit -v -m unit

test-int:
	pytest tests/integration -v -m integration

test-cov:
	pytest tests/ -v --cov=backend/app --cov-report=html --cov-report=term-missing
	@echo "Coverage report: htmlcov/index.html"

# Code Quality
lint:
	ruff check backend/
	mypy backend/app

format:
	black backend/ tests/
	ruff check backend/ --fix

check: lint test

# Docker
docker-up:
	docker-compose up -d
	@echo "Services started. API: http://localhost:8000"

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

docker-test:
	docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit
	docker-compose -f docker-compose.test.yml down -v

docker-build:
	docker-compose build

# Database
db-migrate:
	cd backend && alembic upgrade head

db-revision:
	@read -p "Migration message: " msg; \
	cd backend && alembic revision --autogenerate -m "$$msg"

db-reset:
	docker-compose down -v
	docker-compose up -d db
	sleep 3
	make db-migrate

# Cleanup
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true

clean-docker:
	docker-compose down -v --remove-orphans
	docker system prune -f
