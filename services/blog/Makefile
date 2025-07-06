.PHONY: dev test build run clean shell sync-secrets deploy app-info help serve new-post

serve: ## run Hugo development server
	@echo "🚀 Starting Hugo development server..."
	@if ! command -v hugo >/dev/null 2>&1; then \
		echo "Installing Hugo..."; \
		wget -qO- https://github.com/gohugoio/hugo/releases/download/v0.124.1/hugo_extended_0.124.1_linux-amd64.tar.gz | tar -xzf - hugo; \
		sudo mv hugo /usr/local/bin/; \
	fi
	@hugo serve --bind 0.0.0.0 --port 1313 --buildDrafts --buildFuture

dev: serve ## alias for serve

test: ## test Hugo site build
	@echo "🧪 Testing Hugo site build..."
	@if ! command -v hugo >/dev/null 2>&1; then \
		echo "Installing Hugo..."; \
		wget -qO- https://github.com/gohugoio/hugo/releases/download/v0.124.1/hugo_extended_0.124.1_linux-amd64.tar.gz | tar -xzf - hugo; \
		sudo mv hugo /usr/local/bin/; \
	fi
	@hugo --minify --destination public-test
	@echo "✅ Hugo site builds successfully"
	@rm -rf public-test

build: ## build Hugo site in Docker
	@echo "🏗️  Building Hugo site Docker image..."
	@docker build -t blog-builder .

run: build ## run Hugo site locally in Docker
	@docker run --rm -p 3000:80 blog-builder

shell: build ## run interactive shell in Hugo container
	@docker run -it --rm --entrypoint sh blog-builder

clean: ## clean build artifacts
	@echo "🧹 Cleaning build artifacts..."
	@rm -rf public public-test
	@docker rmi blog-builder || true

new-post: ## create a new blog post: make new-post TITLE="My New Post"
	@if [ -z "$(TITLE)" ]; then \
		echo "❌ Error: TITLE is required. Usage: make new-post TITLE=\"My New Post\""; \
		exit 1; \
	fi
	@if ! command -v hugo >/dev/null 2>&1; then \
		echo "Installing Hugo..."; \
		wget -qO- https://github.com/gohugoio/hugo/releases/download/v0.124.1/hugo_extended_0.124.1_linux-amd64.tar.gz | tar -xzf - hugo; \
		sudo mv hugo /usr/local/bin/; \
	fi
	@SLUG=$$(echo "$(TITLE)" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | sed 's/^-\|-$$//g'); \
	hugo new post/$$SLUG/index.md; \
	echo "✅ Created new post: content/post/$$SLUG/index.md"

sync-secrets: ## sync secrets from .env file to Fly.io
	@echo "🔐 Syncing secrets from .env to Fly.io app: shmuel-tech-$(shell basename $(PWD))"
	@cd ../.. && uv run sync-secrets --service $(shell basename $(PWD))

deploy: ## deploy this service to Fly.io
	@echo "🚀 Deploying service: $(shell basename $(PWD))"
	@cd ../.. && uv run deploy --service $(shell basename $(PWD))

app-info: ## get app information from Fly.io
	@echo "📊 Getting app info for service: $(shell basename $(PWD))"
	@cd ../.. && uv run get-app-info --service $(shell basename $(PWD))

help:
	@awk -F':.*##' '/^[a-zA-Z_-]+:.*##/{printf "\033[36m%-15s\033[0m %s\n", $$1,$$2}' $(MAKEFILE_LIST)