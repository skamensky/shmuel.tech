.PHONY: test build run dev clean shell

test: ## run service tests
	@echo "Running tests for $(shell basename $(PWD))"
	go test ./...

build: ## build service image
	docker build -t $(shell basename $(PWD)) .

run: ## run service locally
	docker run --rm -p 3000:80 $(shell basename $(PWD))

dev: ## run service in development mode
	go run ./src

shell: ## run interactive bash shell in container
	docker run -it --rm --entrypoint sh $(shell basename $(PWD))

clean: ## clean build artifacts
	go clean
	docker rmi $(shell basename $(PWD)) || true

help:
	@awk -F':.*##' '/^[a-zA-Z_-]+:.*##/{printf "\033[36m%-15s\033[0m %s\n", $$1,$$2}' $(MAKEFILE_LIST)