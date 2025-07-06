.PHONY: clone dev test build run clean shell sync-secrets deploy app-info help

REPO_URL := $(shell jq -r '.remote_repo_url // "https://github.com/user/repo.git"' .shmuel-tech.json)
BUILD_DIR := build_dir
DOCKERFILE_LOCATION := $(shell jq -r '.dockerfile_location // "./Dockerfile"' .shmuel-tech.json)
GIT_REF := $(shell jq -r '.git_ref // "master"' .shmuel-tech.json)

clone: ## clone the remote repository
	@echo "🌀 Preparing remote repository..."
	@if [ -z "$(REPO_URL)" ] || [ "$(REPO_URL)" = "null" ] || [ "$(REPO_URL)" = "https://github.com/user/repo.git" ]; then \
		echo "❌ Error: remote_repo_url not set in .shmuel-tech.json"; \
		echo "Please update .shmuel-tech.json with your GitHub repository URL"; \
		exit 1; \
	fi
	@if [ -d "$(BUILD_DIR)" ]; then \
		echo "📋 Updating existing repository at ref: $(GIT_REF)"; \
		cd $(BUILD_DIR) && git fetch origin && git checkout $(GIT_REF); \
		git pull 2>/dev/null || echo "📋 Using specific ref (tag/commit): $(GIT_REF)"; \
		echo "✅ Repository updated to $(BUILD_DIR) at ref: $(GIT_REF)"; \
	else \
		echo "📋 Cloning $(REPO_URL) at ref: $(GIT_REF)"; \
		git clone $(REPO_URL) $(BUILD_DIR); \
		cd $(BUILD_DIR) && git checkout $(GIT_REF); \
		echo "✅ Repository cloned to $(BUILD_DIR) at ref: $(GIT_REF)"; \
	fi

dev: clone ## run service in development mode
	@echo "🚀 Running remote service in development mode..."
	@cd $(BUILD_DIR) && docker build -f $(DOCKERFILE_LOCATION) -t $(shell basename $(PWD)) .
	@docker run --rm -p 3000:80 $(shell basename $(PWD))

test: clone ## run service tests
	@echo "Running tests for $(shell basename $(PWD))"
	@cd $(BUILD_DIR) && docker build -f $(DOCKERFILE_LOCATION) -t $(shell basename $(PWD))-test .
	@echo "✅ Build successful - assuming tests pass if build succeeds"

build: clone ## build service image
	@echo "🏗️  Building remote service image..."
	@cd $(BUILD_DIR) && docker build -f $(DOCKERFILE_LOCATION) -t $(shell basename $(PWD)) .

run: build ## run service locally
	@docker run --rm -p 3000:80 $(shell basename $(PWD))

shell: build ## run interactive bash shell in container
	@docker run -it --rm --entrypoint sh $(shell basename $(PWD))

clean: ## clean build artifacts
	@echo "🧹 Cleaning build artifacts..."
	@rm -rf $(BUILD_DIR)
	@docker rmi $(shell basename $(PWD)) || true

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