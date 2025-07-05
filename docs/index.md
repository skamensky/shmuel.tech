# Welcome to Shmuel Tech

[![CI](https://github.com/shmueltech/shmuel-tech/actions/workflows/ci.yml/badge.svg)](https://github.com/shmueltech/shmuel-tech/actions/workflows/ci.yml)
[![Fly Deploy](https://fly.io/badges/shmuel-tech.svg)](https://fly.io/apps/shmuel-tech)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A portfolio monorepo showcasing multiple Docker-based services deployed to Fly.io with wildcard subdomain routing.

## Overview

This monorepo demonstrates modern DevOps practices including:

- **Microservices Architecture**: Each service is independently deployable
- **Container-First Development**: Docker everywhere, from dev to prod
- **Wildcard Routing**: Clean subdomain-based service access
- **CI/CD Pipeline**: Automated testing and deployment
- **Infrastructure as Code**: Reproducible deployments

## Live Services

All services are available at `<service>.shmuel.tech`:

- **Production**: `https://<service>.shmuel.tech`
- **Development**: `http://<service>.localhost`

## Quick Links

- [Getting Started](getting-started/quick-start.md) - Set up your development environment
- [Creating Services](services/creating-services.md) - Add new services to the monorepo
- [Architecture](architecture/system-design.md) - Understanding the system design

## Architecture Highlights

### Local Development
- **Traefik**: Reverse proxy for `*.localhost` routing
- **Docker Compose**: Service orchestration
- **Hot Reloading**: Fast development cycles

### Production
- **Fly.io**: Global container hosting
- **Fly Machines**: Automatic scaling
- **SSL Certificates**: Secure by default

## Repository Structure

```
.
├── docker-compose.yml      # Local development orchestration
├── fly.toml                # Production deployment configuration
├── Makefile                # Development commands
├── services/               # Individual services
│   └── <service>/
│       ├── Dockerfile      # Service containerization
│       ├── Makefile        # Service-specific commands
│       ├── src/            # Source code
│       └── tests/          # Test files
├── scripts/
│   └── new-service.sh      # Service generator
└── docs/                   # This documentation
```

## Getting Started

1. **Prerequisites**: Install Docker, Docker Compose, and optionally Make
2. **Clone**: `git clone https://github.com/shmueltech/shmuel-tech.git`
3. **Develop**: `make dev` or `docker compose up --build`
4. **Create Services**: `make new-service NAME=my-service`

Visit the [Quick Start Guide](getting-started/quick-start.md) for detailed instructions. 