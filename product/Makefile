# =============================================================================
# Makefile — RegRadar dev, test, and deploy helpers
# =============================================================================
#
# Prerequisites: docker, docker compose (v2)
#
# Quick start:
#   make build      — build Docker image
#   make up         — start full stack (redis + web + worker + beat + flower)
#   make test       — run 17-test pytest suite inside Docker (no live services needed)
#   make pre-push   — build + test gate before git push
# =============================================================================

COMPOSE = docker compose

# Minimal env vars that satisfy import-time validation for the test run.
# All external I/O (DB, Redis, OpenAI, Telegram) is mocked by the test fixtures,
# so placeholder values are safe — no real credentials needed for CI.
_TEST_ENV = \
	-e DATABASE_URL="sqlite:///:memory:" \
	-e REDIS_URL="redis://localhost:6379/0" \
	-e CELERY_RESULT_BACKEND="redis://localhost:6379/0" \
	-e OPENAI_API_KEY="sk-test-placeholder" \
	-e ANTHROPIC_API_KEY="sk-ant-test-placeholder" \
	-e TELEGRAM_BOT_TOKEN="0000000000:test-token" \
	-e SECRET_KEY="ci-test-secret-key" \
	-e REGRADA_API_KEY="ci-test-api-key"

.PHONY: build up down restart logs shell \
        test test-local test-ci \
        pre-push help

# ── Docker Compose stack ──────────────────────────────────────────────────────

build:                          ## Build the Docker image
	$(COMPOSE) build

up:                             ## Start full stack in background
	$(COMPOSE) up -d

down:                           ## Stop and remove all containers
	$(COMPOSE) down

restart:                        ## Restart only the web-api container
	$(COMPOSE) restart web-api

logs:                           ## Tail web-api and worker logs
	$(COMPOSE) logs -f web-api celery-worker

shell:                          ## Open a bash shell in the running web-api container
	$(COMPOSE) exec web-api bash

# ── Testing ───────────────────────────────────────────────────────────────────

test: build                     ## Full 17-test suite inside Docker (recommended)
	@echo "==> Running pytest inside Docker image..."
	$(COMPOSE) run --rm --no-deps \
		$(_TEST_ENV) \
		web-api \
		python -m pytest tests/ -v --tb=short
	@echo "==> Tests passed."

test-ci: build                  ## CI variant: JUnit XML + coverage report
	$(COMPOSE) run --rm --no-deps \
		$(_TEST_ENV) \
		web-api \
		python -m pytest tests/ -v --tb=short \
		--junitxml=/tmp/junit-regrada.xml \
		--cov=app --cov=services --cov-report=term-missing

test-local:                     ## Run tests on host (no Docker). Requires: pip install pytest pytest-mock
	python -m pytest tests/ -v --tb=short

# ── Pre-push gate ─────────────────────────────────────────────────────────────

pre-push: test                  ## Build + full test suite — run before every git push
	@echo ""
	@echo "✓  Build OK"
	@echo "✓  All 17 tests passed"
	@echo "✓  Safe to git push / trigger Railway deploy"

# ── Help ──────────────────────────────────────────────────────────────────────

help:                           ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?##' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  %-14s %s\n", $$1, $$2}'
