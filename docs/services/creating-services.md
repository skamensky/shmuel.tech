# Creating Services

Learn how to create and integrate new services into the shmuel-tech monorepo.

## Overview

Each service in the monorepo is:
- **Independent**: Has its own codebase, dependencies, and lifecycle
- **Containerized**: Runs in Docker for consistency across environments
- **Routed**: Accessible via `<service>.localhost` (dev) or `<service>.shmuel.tech` (prod)
- **Tested**: Includes its own test suite and CI/CD pipeline

## Quick Service Creation

The fastest way to create a new service is using our automated Python generator:

```bash
# First-time setup (installs uv and dependencies)
make setup

# Create a new service
make new-service NAME=my-awesome-service
```

The generator automatically:
- **Creates Go-based service** with HTTP server and static file serving
- **Generates complete directory structure** with source code and tests
- **Adds service to docker-compose.yml** for local development
- **Updates fly.toml** for production deployment
- **Provides beautiful HTML interface** with glassmorphism styling
- **Includes comprehensive test suite** with HTTP handler tests

## What You Get

When you run `make new-service NAME=my-service`, the generator creates:

```
services/my-service/
├── Dockerfile          # Multi-stage Go build
├── Makefile           # Go-specific commands (test, build, run, dev, clean)
├── go.mod             # Go module file
├── go.sum             # Go dependencies
├── src/
│   ├── main.go        # Full HTTP server with 3 endpoints
│   └── main_test.go   # HTTP handler tests
└── tests/
    └── main_test.go   # Test files
```

The generated Go service includes:
- 🏠 **Home page**: Beautiful HTML interface at `/`
- 🔍 **Health check**: JSON endpoint at `/health` with uptime
- 📊 **Status API**: JSON endpoint at `/api/status`
- 🎨 **Modern styling**: Glassmorphism design with gradients

## Automatic Integration

The generator automatically integrates your service into the monorepo:

### Docker Compose Integration
Automatically adds to `docker-compose.yml`:
```yaml
my-service:
  build: ./services/my-service
  environment:
    - SERVICE_NAME=my-service
  labels:
    - "traefik.enable=true"
    - "traefik.http.routers.my-service.rule=Host(`my-service.localhost`)"
    - "traefik.http.services.my-service.loadbalancer.server.port=80"
  depends_on:
    - traefik
```

### Fly.io Integration
Automatically adds to `fly.toml`:
```toml
[processes]
my-service = "/bin/my-service"
```

## Manual Service Creation

If you prefer manual setup or need a different tech stack:

### 1. Create Directory Structure

```bash
mkdir -p services/my-service/{src,tests}
cd services/my-service
```

### 2. Create Dockerfile

Example for a Go service (default):

```dockerfile
FROM golang:1.21-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN go build -o main ./src

FROM alpine:latest
RUN apk --no-cache add ca-certificates
WORKDIR /root/
COPY --from=builder /app/main .
EXPOSE 80
CMD ["./main"]
```

Example for a Node.js service:

```dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

FROM node:18-alpine
WORKDIR /app
COPY --from=builder /app/node_modules ./node_modules
COPY . .
EXPOSE 80
CMD ["node", "src/index.js"]
```

### 3. Create Service Makefile

For Go services:

```makefile
.PHONY: test build run dev clean

test: ## run service tests
	go test ./...

build: ## build service image
	docker build -t $(shell basename $(PWD)) .

run: ## run service locally
	docker run --rm -p 3000:80 $(shell basename $(PWD))

dev: ## run service in development mode
	go run ./src

clean: ## clean build artifacts
	go clean
	docker rmi $(shell basename $(PWD)) || true

help:
	@awk -F':.*##' '/^[a-zA-Z_-]+:.*##/{printf "\033[36m%-15s\033[0m %s\n", $$1,$$2}' $(MAKEFILE_LIST)
```

For Node.js services:

```makefile
.PHONY: test build run clean

test: ## run service tests
	npm test

build: ## build service image
	docker build -t $(shell basename $(PWD)) .

run: ## run service locally
	docker run --rm -p 3000:80 $(shell basename $(PWD))

clean: ## clean up build artifacts
	docker rmi $(shell basename $(PWD)) || true

help:
	@awk -F':.*##' '/^[a-zA-Z_-]+:.*##/{printf "\033[36m%-15s\033[0m %s\n", $$1,$$2}' $(MAKEFILE_LIST)
```

### 4. Add Source Code

Create your service's main application file and any dependencies.

### 5. Create Tests

Set up appropriate test files in the `tests/` directory.

### 6. Manual Integration

If you created the service manually, you need to manually add it to configuration files:

**docker-compose.yml**:
```yaml
  my-service:
    build: ./services/my-service
    environment:
      - SERVICE_NAME=my-service
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.my-service.rule=Host(`my-service.localhost`)"
      - "traefik.http.services.my-service.loadbalancer.server.port=80"
    depends_on:
      - traefik
```

**fly.toml**:
```toml
[processes]
my-service = "/bin/my-service"
```

## Development Commands

Each generated service comes with a comprehensive Makefile:

```bash
# Run in development mode (with hot reloading)
make -C services/my-service dev

# Run tests
make -C services/my-service test

# Build Docker image
make -C services/my-service build

# Run containerized service locally
make -C services/my-service run

# Clean up build artifacts
make -C services/my-service clean

# Show all available commands
make -C services/my-service help
```

## Service Configuration

### Environment Variables

Services can access environment variables:

- `SERVICE_NAME`: Automatically set to the service name
- `NODE_ENV`: Set to `development` or `production`
- `FQDN_SUFFIX`: Set to `shmuel.tech` in production

### Service Discovery

Services can communicate with each other using Docker's built-in DNS:

```go
// Go example - making HTTP request to another service
resp, err := http.Get("http://other-service/api/data")
```

```javascript
// Node.js example - making HTTP request to another service
const response = await fetch('http://other-service/api/data');
```

### Health Checks

Generated services include health check endpoints:

Go example:
```go
func healthHandler(w http.ResponseWriter, r *http.Request) {
    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(http.StatusOK)
    json.NewEncoder(w).Encode(map[string]interface{}{
        "status": "healthy",
        "service": os.Getenv("SERVICE_NAME"),
        "timestamp": time.Now(),
    })
}
```

Node.js example:
```javascript
app.get('/health', (req, res) => {
  res.json({ 
    status: 'healthy', 
    service: process.env.SERVICE_NAME,
    timestamp: new Date().toISOString()
  });
});
```

## Best Practices

### Dockerfile Optimization

- Use multi-stage builds for smaller images
- Leverage build cache with proper layer ordering
- Use `.dockerignore` to exclude unnecessary files
- Run as non-root user when possible

### Code Organization

```
services/my-service/
├── Dockerfile
├── Makefile
├── go.mod                   # or package.json, requirements.txt, etc.
├── .dockerignore
├── src/
│   ├── main.go             # main application
│   ├── handlers/           # HTTP handlers
│   ├── models/             # data models
│   └── utils/              # utility functions
├── tests/
│   ├── unit/               # unit tests
│   ├── integration/        # integration tests
│   └── fixtures/           # test data
└── docs/
    └── README.md           # service-specific documentation
```

### Security

- Don't expose unnecessary ports
- Use environment variables for secrets
- Implement proper error handling
- Add rate limiting for public APIs

### Performance

- Implement caching where appropriate
- Use connection pooling for databases
- Monitor resource usage
- Optimize Docker images for size

## Testing

### Unit Tests

Each service should have comprehensive unit tests:

Go:
```bash
# Run tests for a specific service
make -C services/my-service test

# Run all service tests
make test
```

Node.js:
```bash
# Run tests for a specific service
cd services/my-service && npm test

# Run all service tests
make test
```

### Integration Tests

Test service interactions:

Go example:
```go
func TestHealthEndpoint(t *testing.T) {
    req := httptest.NewRequest("GET", "/health", nil)
    w := httptest.NewRecorder()
    healthHandler(w, req)
    
    if w.Code != http.StatusOK {
        t.Errorf("Expected status 200, got %d", w.Code)
    }
}
```

### Load Testing

Consider adding load tests for critical services:

```bash
# Example with Apache Bench
ab -n 1000 -c 10 http://my-service.localhost/
```

## Deployment

### Local Development

```bash
# Start all services
make dev

# Start specific service
docker compose up my-service

# View logs
docker compose logs -f my-service
```

### Production Deployment

Services are automatically deployed when merged to main:

1. CI runs tests for all services
2. Docker images are built and pushed
3. Fly.io deployment is triggered
4. Services are accessible at `<service>.shmuel.tech`

## Monitoring

### Logs

```bash
# View service logs in production
fly logs -a shmuel-tech

# View specific service logs
fly logs -a shmuel-tech --region ams
```

### Metrics

Generated services include metrics endpoints:

Go example:
```go
func metricsHandler(w http.ResponseWriter, r *http.Request) {
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(map[string]interface{}{
        "requests": requestCount,
        "uptime": time.Since(startTime).String(),
        "memory": getMemoryStats(),
    })
}
```

## Python Generator Details

The service generator is built with Python 3.11+ and uses:

- **uv**: Fast Python package manager
- **PyYAML**: YAML parsing and modification
- **tomli-w**: TOML writing support

### Dependencies

All dependencies are managed via `pyproject.toml`:

```toml
[project]
dependencies = [
    "pyyaml>=6.0",
    "tomli-w>=1.0.0",
]
```

### Generator Features

- **Automatic YAML/TOML modification**: No manual copy-paste required
- **Validation**: Checks for existing services and valid names
- **Error handling**: Graceful error messages and rollback
- **Comprehensive output**: Clear success messages and next steps

## Troubleshooting

### Common Issues

**Service not accessible**: Check Traefik dashboard at http://localhost:8080

**Build failures**: Ensure Dockerfile is valid and dependencies are available

**Port conflicts**: Each service should expose port 80 internally

**Environment issues**: Verify environment variables are set correctly

**Python generator issues**: Run `make setup` to ensure dependencies are installed

### Debug Mode

Run services in debug mode:

```bash
# Go service development mode
make -C services/my-service dev

# Docker debug mode
docker compose up --build my-service
docker compose logs -f my-service

# Python generator debug
uv run scripts/service_handler.py --help
```

## Examples

See the existing services for reference implementations:

- **Web Service** (Node.js): Portfolio dashboard with HTML templating
- **API Service** (Node.js): RESTful API with interactive documentation
- **Generated Services** (Go): Simple HTTP server with health checks and static content

The service generator creates Go services by default, but you can easily modify them or create services in other languages following the patterns above. 