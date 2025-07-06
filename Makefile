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
	@failed_services=""; \
	for service_dir in services/*/; do \
		service=$$(basename "$$service_dir"); \
		echo "Testing $$service..."; \
		if ! $(MAKE) -C "$$service_dir" test; then \
			echo "❌ Tests failed for $$service"; \
			failed_services="$$failed_services $$service"; \
		else \
			echo "✅ Tests passed for $$service"; \
		fi; \
	done; \
	if [ -n "$$failed_services" ]; then \
		echo "❌ Tests failed for services:$$failed_services"; \
		exit 1; \
	else \
		echo "✅ All tests passed!"; \
	fi

build: ## build all service images
	@echo "🏗️  Building all service images..."
	@for service_dir in services/*/; do \
		service=$$(basename "$$service_dir"); \
		echo "Building $$service..."; \
		$(MAKE) -C "$$service_dir" build; \
	done

deploy: ## deploy all services to Fly.io
	@echo "🚀 Deploying all services to Fly.io..."
	@uv run deploy

deploy-service: setup ## deploy specific services: make deploy-service SERVICE="main-site media"
	@if [ "$(origin SERVICE)" != "command line" ] || [ -z "$(SERVICE)" ]; then \
		echo "❌ Error: SERVICE is required. Usage: make deploy-service SERVICE=\"service1 service2\""; \
		echo "   Example: make deploy-service SERVICE=main-site"; \
		echo "   Example: make deploy-service SERVICE=\"main-site media\""; \
		exit 1; \
	fi
	@echo "🚀 Deploying services: $(SERVICE)"
	@uv run deploy --service $(SERVICE)

deploy-detached: setup ## deploy all services to Fly.io in detached mode
	@echo "🚀 Deploying all services to Fly.io (detached)..."
	@uv run deploy --detach

new-service: setup ## create a new service: make new-service NAME=foo [TYPE=go|remote]
	@if [ "$(origin NAME)" != "command line" ] || [ -z "$(NAME)" ]; then \
		echo "❌ Error: NAME is required. Usage: make new-service NAME=my-service [TYPE=go|remote]"; \
		echo "   Example: make new-service NAME=test"; \
		echo "   Example: make new-service NAME=blog TYPE=remote"; \
		echo "   Note: Don't use 'make new-service test' - use 'make new-service NAME=test'"; \
		exit 1; \
	fi
	@SERVICE_TYPE=$${TYPE:-go}; \
	echo "🚀 Creating new $$SERVICE_TYPE service: $(NAME)"; \
	uv run new-service create $(NAME) --type $$SERVICE_TYPE

remove-service: setup ## remove an existing service: make remove-service NAME=foo [FORCE=1]
	@if [ "$(origin NAME)" != "command line" ] || [ -z "$(NAME)" ]; then \
		echo "❌ Error: NAME is required. Usage: make remove-service NAME=my-service"; \
		echo "   Example: make remove-service NAME=test"; \
		echo "   Add FORCE=1 to skip confirmation: make remove-service NAME=test FORCE=1"; \
		exit 1; \
	fi
	@if [ "$(FORCE)" = "1" ]; then \
		echo "🗑️  Removing service: $(NAME) (forced)"; \
		uv run new-service remove $(NAME) --force; \
	else \
		echo "🗑️  Removing service: $(NAME)"; \
		uv run new-service remove $(NAME); \
	fi

list-services: ## list all services and their status
	@echo "📋 Available services:"
	@for service_dir in services/*/; do \
		service=$$(basename "$$service_dir"); \
		if [ ! -f "$$service_dir/.shmuel-tech.json" ]; then \
			echo "❌ Error: Service '$$service' is missing .shmuel-tech.json config file"; \
			exit 1; \
		fi; \
		service_type=$$(jq -r '.service_type // "go"' "$$service_dir/.shmuel-tech.json"); \
		case "$$service_type" in \
			"go") echo "  - $$service (Go)" ;; \
			"remote") echo "  - $$service (Remote)" ;; \
			"static") echo "  - $$service (Static)" ;; \
			*) echo "  - $$service ($$service_type)" ;; \
		esac; \
	done

detect-changes: setup ## detect which services have changes: make detect-changes BASE=origin/main
	@if [ "$(origin BASE)" != "command line" ] || [ -z "$(BASE)" ]; then \
		echo "❌ Error: BASE is required. Usage: make detect-changes BASE=origin/master"; \
		echo "   Example: make detect-changes BASE=HEAD~1"; \
		echo "   Example: make detect-changes BASE=origin/master"; \
		exit 1; \
	fi
	@echo "🔍 Detecting changes against: $(BASE)"
	@uv run detect-changes $(BASE)

setup-dns-proxy: ## setup DNS proxy with static IP for Namecheap API
	@echo "🌐 Setting up DNS proxy..."
	@echo "📱 Creating DNS proxy app..."
	@fly apps create shmuel-tech-dns-proxy --org personal || echo "App may already exist"
	@echo "📡 Allocating static IPv4 address..."
	@fly ips allocate-v4 --shared -a shmuel-tech-dns-proxy
	@echo "🚀 Deploying DNS proxy..."
	@cd services/dns-proxy && fly deploy --config fly.toml --app shmuel-tech-dns-proxy --remote-only
	@echo "📋 Getting static IP address..."
	@echo ""
	@echo "🎯 Your DNS proxy static IP address:"
	@fly ips list -a shmuel-tech-dns-proxy
	@echo ""
	@echo "📋 Next steps:"
	@echo "1. Add the IP address shown above to your Namecheap API whitelist"
	@echo "2. Set PROXY_AUTH_TOKEN in fly.toml to a secure random value"
	@echo "3. Update deploy.py to use DNS_PROXY_URL environment variable"

get-dns-proxy-ip: ## get the static IP of the DNS proxy
	@echo "📡 DNS Proxy Static IP:"
	@fly ips list -a shmuel-tech-dns-proxy

deploy-dns-proxy: ## deploy only the DNS proxy service
	@echo "🌐 Deploying DNS proxy..."
	@cd services/dns-proxy && fly deploy --config fly.toml --app shmuel-tech-dns-proxy --remote-only

sync-secrets: ## sync secrets for all services with .env files
	@echo "🔐 Syncing secrets for all services..."
	@for service_dir in services/*/; do \
		service=$$(basename "$$service_dir"); \
		echo "Checking $$service for .env file..."; \
		if [ -f "$$service_dir/.env" ]; then \
			echo "🔐 Syncing secrets for $$service"; \
			$(MAKE) -C "$$service_dir" sync-secrets; \
		else \
			echo "⚠️  No .env file found for $$service, skipping"; \
		fi; \
	done
	@echo "✅ Secret sync completed for all services"