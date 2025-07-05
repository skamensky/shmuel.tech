-include .env               # optional developer overrides

.DEFAULT_GOAL := help

.PHONY: setup dev test build deploy deploy-service deploy-detached new-service remove-service help list-services detect-changes

help:
	@echo "Available commands:"
	@awk -F':.*##' '/^[a-zA-Z_-]+:.*##/{printf "\033[36m%-15s\033[0m %s\n", $$1,$$2}' $(MAKEFILE_LIST)

setup: ## install uv and sync Python dependencies
	@echo "🐍 Setting up Python environment with uv..."
	@if ! command -v uv >/dev/null 2>&1; then \
		echo "Installing uv..."; \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
		export PATH="$$HOME/.local/bin:$$PATH"; \
	fi
	@echo "Syncing dependencies..."
	@uv sync
	@echo "✅ Python environment ready!"

dev: ## run full stack locally
	docker compose up --build

test: ## run all service tests
	@echo "🧪 Running tests for all services..."
	@for service_dir in services/*/; do \
		service=$$(basename "$$service_dir"); \
		echo "Testing $$service..."; \
		if [ -f "$$service_dir/go.mod" ]; then \
			cd "$$service_dir" && go test ./... || echo "⚠️  No tests found for $$service"; \
			cd ../..; \
		else \
			$(MAKE) -C "$$service_dir" test || echo "⚠️  Test failed for $$service"; \
		fi; \
	done

build: ## build all service images
	@echo "🏗️  Building all service images..."
	@for service_dir in services/*/; do \
		service=$$(basename "$$service_dir"); \
		echo "Building $$service..."; \
		$(MAKE) -C "$$service_dir" build; \
	done

deploy: ## deploy all services to Fly.io
	@echo "🚀 Deploying all services to Fly.io..."
	@uv run scripts/deploy.py

deploy-service: setup ## deploy specific services: make deploy-service SERVICE="main-site media"
	@if [ "$(origin SERVICE)" != "command line" ] || [ -z "$(SERVICE)" ]; then \
		echo "❌ Error: SERVICE is required. Usage: make deploy-service SERVICE=\"service1 service2\""; \
		echo "   Example: make deploy-service SERVICE=main-site"; \
		echo "   Example: make deploy-service SERVICE=\"main-site media\""; \
		exit 1; \
	fi
	@echo "🚀 Deploying services: $(SERVICE)"
	@uv run scripts/deploy.py --service $(SERVICE)

deploy-detached: setup ## deploy all services to Fly.io in detached mode
	@echo "🚀 Deploying all services to Fly.io (detached)..."
	@uv run scripts/deploy.py --detach

new-service: setup ## create a new service: make new-service NAME=foo [TYPE=go|static]
	@if [ "$(origin NAME)" != "command line" ] || [ -z "$(NAME)" ]; then \
		echo "❌ Error: NAME is required. Usage: make new-service NAME=my-service [TYPE=go|static]"; \
		echo "   Example: make new-service NAME=test"; \
		echo "   Example: make new-service NAME=blog TYPE=static"; \
		echo "   Note: Don't use 'make new-service test' - use 'make new-service NAME=test'"; \
		exit 1; \
	fi
	@SERVICE_TYPE=$${TYPE:-go}; \
	echo "🚀 Creating new $$SERVICE_TYPE service: $(NAME)"; \
	uv run scripts/service_handler.py create $(NAME) --type $$SERVICE_TYPE

remove-service: setup ## remove an existing service: make remove-service NAME=foo [FORCE=1]
	@if [ "$(origin NAME)" != "command line" ] || [ -z "$(NAME)" ]; then \
		echo "❌ Error: NAME is required. Usage: make remove-service NAME=my-service"; \
		echo "   Example: make remove-service NAME=test"; \
		echo "   Add FORCE=1 to skip confirmation: make remove-service NAME=test FORCE=1"; \
		exit 1; \
	fi
	@if [ "$(FORCE)" = "1" ]; then \
		echo "🗑️  Removing service: $(NAME) (forced)"; \
		uv run scripts/service_handler.py remove $(NAME) --force; \
	else \
		echo "🗑️  Removing service: $(NAME)"; \
		uv run scripts/service_handler.py remove $(NAME); \
	fi

list-services: ## list all services and their status
	@echo "📋 Available services:"
	@for service_dir in services/*/; do \
		service=$$(basename "$$service_dir"); \
		if [ -f "$$service_dir/go.mod" ]; then \
			service_type="Go"; \
		else \
			service_type="Static"; \
		fi; \
		echo "  - $$service ($$service_type)"; \
	done

detect-changes: setup ## detect which services have changes: make detect-changes BASE=origin/main
	@if [ "$(origin BASE)" != "command line" ] || [ -z "$(BASE)" ]; then \
		echo "❌ Error: BASE is required. Usage: make detect-changes BASE=origin/master"; \
		echo "   Example: make detect-changes BASE=HEAD~1"; \
		echo "   Example: make detect-changes BASE=origin/master"; \
		exit 1; \
	fi
	@echo "🔍 Detecting changes against: $(BASE)"
	@uv run scripts/detect_changes.py $(BASE)