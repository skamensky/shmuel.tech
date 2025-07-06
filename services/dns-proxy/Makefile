.PHONY: test build run dev clean shell deploy sync-secrets

test: ## run service tests
	@echo "Running tests for $(shell basename $(PWD))"
	go test ./...

build: ## build service image
	docker build -t $(shell basename $(PWD)) .

run: ## run service locally
	docker run --rm -p 3000:80 -e LOG_LEVEL=debug -e PROXY_AUTH_TOKEN=$(PROXY_AUTH_TOKEN) $(shell basename $(PWD))

dev: ## run service in development mode
	go run ./src

shell: ## run interactive bash shell in container
	docker run -it --rm --entrypoint sh $(shell basename $(PWD))

clean: ## clean build artifacts
	go clean
	docker rmi $(shell basename $(PWD)) || true

deploy: ## deploy this service to Fly.io
	@echo "🚀 Deploying service: $(shell basename $(PWD))"
	@cd ../.. && uv run deploy --service $(shell basename $(PWD)) --no-dns

sync-secrets: ## sync secrets from .env file to Fly.io
	@echo "🔐 Syncing secrets from .env to Fly.io app: shmuel-tech-$(shell basename $(PWD))"
	@cd ../.. && uv run sync-secrets --service $(shell basename $(PWD))

app-info: ## get app information from Fly.io
	@echo "📊 Getting app info for service: $(shell basename $(PWD))"
	@cd ../.. && uv run get-app-info --service $(shell basename $(PWD))


help:
	@awk -F':.*##' '/^[a-zA-Z_-]+:.*##/{printf "\033[36m%-15s\033[0m %s\n", $$1,$$2}' $(MAKEFILE_LIST)