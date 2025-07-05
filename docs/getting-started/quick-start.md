# Quick Start Guide

Get up and running with the shmuel-tech monorepo in minutes.

## Prerequisites

Before you begin, ensure you have the following installed:

- [Docker](https://docs.docker.com/get-docker/) (v20.10+)
- [Docker Compose](https://docs.docker.com/compose/install/) (v2.0+)
- [Make](https://www.gnu.org/software/make/) (optional, for convenience)
- [Git](https://git-scm.com/) (for version control)

Optional (for deployment):
- [Fly CLI](https://fly.io/docs/hands-on/install-flyctl/)

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/shmueltech/shmuel-tech.git
   cd shmuel-tech
   ```

2. **Copy environment template** (optional):
   ```bash
   cp .env.template .env
   # Edit .env with your preferences
   ```

3. **Start the development environment**:
   ```bash
   make dev
   # or
   docker compose up --build
   ```

## First Steps

### View Your Services

Once the containers are running:

1. **Traefik Dashboard**: http://localhost:8080
2. **Services**: http://`<service>`.localhost (once you create some)

### Create Your First Service

```bash
# Create a new service
make new-service NAME=hello-world

# Follow the printed instructions to add it to docker-compose.yml
```

The generator will create:
- Service directory structure
- Basic Dockerfile
- Example source code
- Test files
- Service-specific Makefile

### Add Service to Docker Compose

After creating a service, add it to `docker-compose.yml`:

```yaml
  hello-world:
    build: ./services/hello-world
    environment:
      - SERVICE_NAME=hello-world
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.hello-world.rule=Host(`hello-world.localhost`)"
      - "traefik.http.services.hello-world.loadbalancer.server.port=80"
```

### Test Your Service

```bash
# Restart to pick up the new service
docker compose up --build

# Visit your service
curl http://hello-world.localhost
# or open in browser
```

## Available Commands

| Command | Description |
|---------|-------------|
| `make dev` | Start all services in development mode |
| `make test` | Run tests for all services |
| `make build` | Build all service images |
| `make new-service NAME=foo` | Create a new service |
| `make deploy` | Deploy to Fly.io |
| `make help` | Show all available commands |

## Next Steps

- [Development Guide](development.md) - Learn about the development workflow
- [Creating Services](../services/creating-services.md) - Deep dive into service creation
- [Architecture](../architecture/system-design.md) - Understand the system design
- [Deployment](deployment.md) - Deploy to production

## Troubleshooting

### Common Issues

**Port conflicts**: If port 80 is already in use:
```bash
# Stop conflicting services
sudo systemctl stop apache2  # or nginx

# Or modify docker-compose.yml to use different ports
```

**Permission errors**: On Linux, you may need to add your user to the docker group:
```bash
sudo usermod -aG docker $USER
# Log out and back in
```

**Service not accessible**: Check Traefik dashboard at http://localhost:8080 to see if your service is registered.

### Getting Help

- Check the [Issues](https://github.com/shmueltech/shmuel-tech/issues) page
- Review the [Contributing Guide](../contributing.md)
- Join the discussion in GitHub Discussions 