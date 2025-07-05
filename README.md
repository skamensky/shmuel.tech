# shmuel-tech

[![CI](https://github.com/shmueltech/shmuel-tech/actions/workflows/ci.yml/badge.svg)](https://github.com/shmueltech/shmuel-tech/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A portfolio monorepo showcasing multiple containerized services with independent Fly.io deployments and wildcard subdomain routing.

## 🌐 Live Services

Each service is deployed as a separate Fly.io app with its own subdomain:

- **Main Site**: `https://shmuel.tech` (Portfolio landing page)
- **Media Service**: `https://media.shmuel.tech` (Media processing and serving)
- **Development**: `http://shmuel.localhost` & `http://media.localhost`

## 🏗️ Architecture

This monorepo uses a **multi-app architecture** where:

- **Local Development**: Docker Compose + Traefik for unified development experience
- **Production**: Each service is a separate Fly.io app for independent scaling and deployment
- **Service Types**: Static sites (Nginx) and Go applications with health checks

## 🚀 Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) & [Docker Compose](https://docs.docker.com/compose/install/)
- [Fly CLI](https://fly.io/docs/hands-on/install-flyctl/) (for deployment)
- [Python 3.11+](https://www.python.org/downloads/) with [uv](https://docs.astral.sh/uv/)

### Local Development

```bash
# Clone the repository
git clone https://github.com/shmueltech/shmuel-tech.git
cd shmuel-tech

# Set up Python environment
make setup

# Start all services locally
make dev

# Or manually with Docker Compose
docker compose up --build
```

Visit:
- **Main Site**: http://shmuel.localhost
- **Media Service**: http://media.localhost
- **Traefik Dashboard**: http://localhost:8080

### Creating Services

```bash
# Create a new Go service
make new-service NAME=api

# Create a new static site service
make new-service NAME=blog TYPE=static

# List all services
make list-services
```

## 📁 Repository Structure

```
.
├── docker-compose.yml      # Local development orchestration
├── Makefile                # Development commands
├── pyproject.toml          # Python dependencies and configuration
├── .github/
│   └── workflows/ci.yml    # CI/CD pipeline for multi-app deployment
├── services/               # Individual services
│   ├── main-site/          # Static portfolio site
│   │   ├── fly.toml        # Fly.io app configuration
│   │   ├── Dockerfile      # Nginx-based static serving
│   │   └── public/         # Static files
│   └── media/              # Go-based media service
│       ├── fly.toml        # Fly.io app configuration
│       ├── Dockerfile      # Go application
│       └── src/            # Source code
├── scripts/
│   ├── service_handler.py  # Service generator and manager
│   ├── deploy.py           # Fly.io deployment automation
│   └── detect_changes.py   # Git change detection for CI/CD
└── docs/                   # Documentation
```

## 🛠️ Available Commands

```bash
make help             # Show all available commands
make setup            # Install dependencies and set up Python environment
make dev              # Start local development environment
make test             # Run tests for all services
make build            # Build all service Docker images
make deploy           # Deploy all services to Fly.io
make deploy-service   # Deploy specific services (requires SERVICE="service1 service2")
make deploy-detached  # Deploy all services in detached mode
make detect-changes   # Detect which services have changes (requires BASE=git-ref)
make list-services    # List all services and their types
make new-service      # Create a new service (requires NAME=<name>)
make remove-service   # Remove an existing service (requires NAME=<name>)
```

## 🚢 Deployment

### Production Architecture

Each service is deployed as a separate Fly.io app:

- **shmuel-tech-main-site** → `shmuel.tech`
- **shmuel-tech-media** → `media.shmuel.tech`
- **shmuel-tech-{service}** → `{service}.shmuel.tech`

### Manual Deployment

```bash
# Deploy all services
make deploy

# Deploy a single service
make deploy-service SERVICE=main-site

# Deploy multiple specific services
make deploy-service SERVICE="main-site media"

# Deploy all services in detached mode (faster for CI/CD)
make deploy-detached

# Detect which services have changes
make detect-changes BASE=origin/main

# Or use the scripts directly
uv run scripts/deploy.py --service main-site media
uv run scripts/deploy.py --detach
uv run scripts/detect_changes.py origin/main
```

### Automatic Deployment

The CI/CD pipeline uses intelligent change detection to only deploy services that actually changed:

**Change Detection** (`scripts/detect_changes.py`):
1. Compares git commits to find modified files
2. Maps changed files to affected services
3. Handles root-level changes (deploys all services when core files change)
4. Outputs list of services that need deployment

**Deployment** (`scripts/deploy.py`):
1. Accepts single or multiple services for deployment
2. **Parallel deployment** - deploys multiple services simultaneously for speed
3. Authenticates with Fly.io automatically
4. Creates Fly.io apps if they don't exist
5. Adds SSL certificates for each subdomain
6. **Error aggregation** - allows all deployments to complete before reporting failures
7. **Sequential reporting** - prints results in order for clear status visibility

**CI/CD Flow**:
- Detects which services changed between commits
- Only deploys affected services (saves time and resources)
- **Parallel deployment** of multiple services for faster CI/CD
- Falls back to deploying all services if core infrastructure changes

### Parallel Deployment Benefits

The deployment system uses **multithreading** to deploy services simultaneously:

- **Faster deployments**: Multiple services deploy at the same time
- **Error resilience**: All deployments complete before reporting failures
- **Clear reporting**: Results printed sequentially for easy reading
- **Exception handling**: Deployment fails only if any service fails (after all complete)

## 🔧 DNS Configuration

Configure your domain registrar with:

```
Host: *        Type: CNAME    Value: shmuel.tech (or use A records to Fly.io IPs)
Host: @        Type: CNAME    Value: shmuel.tech (or use A records to Fly.io IPs)
```

## 📊 Service Types

### Static Sites
- **Technology**: Nginx + static files
- **Use Case**: Portfolio sites, documentation, blogs
- **Local Development**: Python HTTP server (`make dev`)
- **Health Check**: `/health` endpoint

### Go Applications
- **Technology**: Go with built-in HTTP server
- **Use Case**: APIs, microservices, dynamic applications
- **Local Development**: `go run` or Docker
- **Health Check**: `/health` and `/api/status` endpoints

## 🧪 Testing

```bash
# Run all tests
make test

# Test a specific service
make -C services/main-site test     # Static site test
make -C services/media test         # Go service test
```

## 🔧 Service Management

### Adding a Service

```bash
# Go service (default)
make new-service NAME=auth

# Static site service
make new-service NAME=docs TYPE=static
```

### Removing a Service

```bash
# Interactive removal
make remove-service NAME=auth

# Force removal (no confirmation)
make remove-service NAME=auth FORCE=1
```

**Note**: Removing a service only removes local files. To remove the Fly.io app:
```bash
fly apps destroy shmuel-tech-auth
```

## 🔍 Change Detection

The system includes intelligent change detection to optimize deployments:

### Manual Change Detection
```bash
# Detect changes against main branch
make detect-changes BASE=origin/main

# Detect changes against specific commit
make detect-changes BASE=HEAD~3

# Use script directly for more options
uv run scripts/detect_changes.py origin/main --output-format json
uv run scripts/detect_changes.py HEAD~1 --force-all
```

### How Change Detection Works
- **Service Changes**: Monitors `services/*/` directories for modifications
- **Root Changes**: Detects infrastructure changes that affect all services
- **Smart Logic**: Only deploys services that actually need updates
- **Fallback**: Deploys all services when core files change

### Deployment Based on Changes
```bash
# Get changed services and deploy them
CHANGED=$(uv run scripts/detect_changes.py origin/main)
make deploy-service SERVICE="$CHANGED"

# Or in one command (CI/CD style)
uv run scripts/deploy.py --service $(uv run scripts/detect_changes.py origin/main)
```

### Example: Parallel Deployment Output
```
🚀 Deploying specific services: main-site, media
📋 Found 2 services to deploy:
  - main-site (static)
  - media (go)

🔄 Starting parallel deployment of 2 services...

============================================================
📊 Deployment Results
============================================================
✅ main-site: Successfully deployed to 'shmuel-tech-main-site'
✅ media: Successfully deployed to 'shmuel-tech-media'

============================================================
📊 Deployment Summary
============================================================
✅ Successfully deployed: 2/2 services
🎉 All services deployed successfully!
```

If errors occur, they are aggregated and reported:
```
❌ main-site: Failed to deploy to 'shmuel-tech-main-site'
✅ media: Successfully deployed to 'shmuel-tech-media'

============================================================
📊 Deployment Summary
============================================================
✅ Successfully deployed: 1/2 services
❌ Failed deployments: 1/2 services

⚠️  There were 1 error(s). An exception will be raised.
💥 Deployment failed with exception: Deployment failed for 1 out of 2 services
```

## 📈 Scaling & Monitoring

Each service can be scaled independently:

```bash
# Scale a specific service
fly scale count 3 --app shmuel-tech-media

# Check service status
fly status --app shmuel-tech-media

# View logs
fly logs --app shmuel-tech-media
```

## 🔗 Service URLs

- **Development**: `http://{service}.localhost`
- **Production**: `https://{service}.shmuel.tech`
- **Main Site**: `https://shmuel.tech` (main-site service)

## 📝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Links

- **Live Site**: https://shmuel.tech
- **Documentation**: https://shmueltech.github.io/shmuel-tech/
- **Issues**: https://github.com/shmueltech/shmuel-tech/issues 