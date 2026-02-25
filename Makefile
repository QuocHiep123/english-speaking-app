# =============================================================================
# VietSpeak AI - Makefile
# =============================================================================

.PHONY: help setup install dev test lint format clean docker-build docker-up

# Default target
help:
	@echo "VietSpeak AI - Development Commands"
	@echo "===================================="
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make setup          - Complete project setup"
	@echo "  make install        - Install all dependencies"
	@echo ""
	@echo "Development:"
	@echo "  make dev            - Start development servers"
	@echo "  make dev-frontend   - Start frontend only"
	@echo "  make dev-backend    - Start backend only"
	@echo ""
	@echo "Testing:"
	@echo "  make test           - Run all tests"
	@echo "  make test-unit      - Run unit tests"
	@echo "  make test-integration - Run integration tests"
	@echo "  make test-e2e       - Run end-to-end tests"
	@echo "  make eval-model     - Run model evaluation"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint           - Run linters"
	@echo "  make format         - Format code"
	@echo "  make type-check     - Run type checking"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build   - Build Docker images"
	@echo "  make docker-up      - Start Docker containers"
	@echo "  make docker-down    - Stop Docker containers"
	@echo ""
	@echo "AI/ML:"
	@echo "  make train          - Run model training"
	@echo "  make eval           - Run model evaluation"
	@echo "  make data-prep      - Prepare datasets"

# =============================================================================
# Setup & Installation
# =============================================================================

setup: install
	@echo "✅ Setup complete!"

install: install-backend install-frontend install-ai

install-backend:
	@echo "📦 Installing backend dependencies..."
	cd apps/backend && pip install -r requirements.txt -r requirements-dev.txt

install-frontend:
	@echo "📦 Installing frontend dependencies..."
	cd apps/frontend && npm install

install-ai:
	@echo "📦 Installing AI core dependencies..."
	cd ai-core && pip install -r requirements.txt -r requirements-dev.txt

# =============================================================================
# Development
# =============================================================================

dev:
	docker-compose -f infra/docker/docker-compose.dev.yml up

dev-frontend:
	cd apps/frontend && npm run dev

dev-backend:
	cd apps/backend && uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

dev-mcp:
	cd mcp && python -m src.server

# =============================================================================
# Testing
# =============================================================================

test: test-unit test-integration

test-unit:
	@echo "🧪 Running unit tests..."
	cd apps/backend && pytest tests/unit -v --cov=src --cov-report=html
	cd apps/frontend && npm run test:unit

test-integration:
	@echo "🧪 Running integration tests..."
	cd apps/backend && pytest tests/integration -v

test-e2e:
	@echo "🧪 Running E2E tests..."
	cd apps/frontend && npm run test:e2e

eval-model:
	@echo "📊 Running model evaluation..."
	cd ai-core && python scripts/evaluate.py --config configs/eval_config.yaml

test-coverage:
	@echo "📊 Generating coverage report..."
	cd apps/backend && pytest tests/ --cov=src --cov-report=html --cov-report=xml

# =============================================================================
# Code Quality
# =============================================================================

lint: lint-python lint-js

lint-python:
	@echo "🔍 Linting Python code..."
	ruff check apps/backend ai-core mcp
	mypy apps/backend ai-core mcp

lint-js:
	@echo "🔍 Linting JavaScript/TypeScript..."
	cd apps/frontend && npm run lint

format: format-python format-js

format-python:
	@echo "✨ Formatting Python code..."
	ruff format apps/backend ai-core mcp
	isort apps/backend ai-core mcp

format-js:
	@echo "✨ Formatting JavaScript/TypeScript..."
	cd apps/frontend && npm run format

type-check:
	@echo "🔍 Running type checks..."
	cd apps/backend && mypy src
	cd apps/frontend && npm run type-check

# =============================================================================
# Docker
# =============================================================================

docker-build:
	@echo "🐳 Building Docker images..."
	docker-compose -f infra/docker/docker-compose.yml build

docker-up:
	@echo "🐳 Starting Docker containers..."
	docker-compose -f infra/docker/docker-compose.yml up -d

docker-down:
	@echo "🐳 Stopping Docker containers..."
	docker-compose -f infra/docker/docker-compose.yml down

docker-logs:
	docker-compose -f infra/docker/docker-compose.yml logs -f

# =============================================================================
# AI/ML Operations
# =============================================================================

data-prep:
	@echo "📊 Preparing datasets..."
	cd ai-core && python scripts/data_prep.py

train:
	@echo "🚀 Starting model training..."
	cd ai-core && python scripts/train.py --config configs/train_config.yaml

eval:
	@echo "📊 Running evaluation..."
	cd ai-core && python scripts/evaluate.py --config configs/eval_config.yaml

# =============================================================================
# Cleanup
# =============================================================================

clean:
	@echo "🧹 Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".next" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "dist" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
