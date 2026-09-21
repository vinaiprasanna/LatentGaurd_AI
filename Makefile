# Cross-Platform Makefile for BurnInGuard AI 2.0
#
# Usage:
#   make install      - Install all dependencies
#   make dev          - Start backend and frontend concurrently
#   make dev-backend  - Start backend only
#   make dev-frontend - Start frontend only
#   make train        - Train all ML models
#   make build        - Build Docker images
#   make up           - Start all services with Docker Compose
#   make down         - Stop all Docker services
#   make logs         - View backend logs
#   make test         - Run all tests
#   make clean        - Remove generated artifacts
#
# NOTE: Makefile works on Linux and macOS only.
# Windows users: use npm run commands or scripts/*.bat files.
#   npm run install    - Install dependencies
#   npm run dev        - Start backend + frontend
#   npm run train      - Train models

.PHONY: install dev dev-backend dev-frontend train build up down logs test clean

# Default target
all: dev

# Install all dependencies
install:
	./scripts/install-dependencies.sh

# Start backend and frontend concurrently
dev: dev-backend dev-frontend

# Start backend only
dev-backend:
	./scripts/run-backend.sh

# Start frontend only
dev-frontend:
	./scripts/run-frontend.sh

# Train all ML models
train:
	./scripts/train-models.sh

# Build Docker images
build:
	docker-compose build

# Start all services
up:
	docker-compose up -d

# Stop all services
down:
	docker-compose down

# View backend logs
logs:
	docker-compose logs -f backend

# Run tests
test:
	cd backend && python -m pytest tests/ -v
	cd frontend && npm test

# Clean generated artifacts
clean:
	rm -rf backend/outputs/*.csv backend/outputs/jobs/ backend/outputs/audit_jobs.json backend/outputs/review_actions.json backend/models/*.pkl
	rm -rf frontend/dist/
	@echo "Cleaned generated artifacts."
