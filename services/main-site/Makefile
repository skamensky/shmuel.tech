.PHONY: build dev test clean shell help

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

help:
	@awk -F':.*##' '/^[a-zA-Z_-]+:.*##/{printf "\033[36m%-15s\033[0m %s\n", $$1,$$2}' $(MAKEFILE_LIST)