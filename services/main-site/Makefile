.PHONY: build dev test clean shell sync-secrets deploy help

build: ## build service image
	docker build -t $(shell basename $(PWD)) .

dev: ## serve locally with python
	@echo "Starting local development server..."
	@cd public && python3 -m http.server 8000

test: ## run basic tests
	@echo "Testing $(shell basename $(PWD))"
	@test -f public/index.html || (echo "❌ index.html not found" && exit 1)
	@echo "✅ Static files present"

shell: ## run interactive shell in container
	docker run -it --rm --entrypoint sh $(shell basename $(PWD))

clean: ## clean build artifacts
	docker rmi $(shell basename $(PWD)) || true

sync-secrets: ## sync secrets from .env file to Fly.io
	@if [ -f .env ]; then \
		echo "🔐 Syncing secrets from .env to Fly.io app: shmuel-tech-$(shell basename $(PWD))"; \
		fly secrets import --app shmuel-tech-$(shell basename $(PWD)) < .env; \
		echo "✅ Secrets synced successfully"; \
	else \
		echo "⚠️  No .env file found, skipping secret sync"; \
	fi

deploy: ## deploy this service to Fly.io
	@echo "🚀 Deploying service: $(shell basename $(PWD))"
	@cd ../.. && uv run deploy --service $(shell basename $(PWD))

help:
	@awk -F':.*##' '/^[a-zA-Z_-]+:.*##/{printf "\033[36m%-15s\033[0m %s\n", $$1,$$2}' $(MAKEFILE_LIST)