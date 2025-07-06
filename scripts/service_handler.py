#!/usr/bin/env python3
"""
Service handler for shmuel-tech monorepo.
Creates and removes services with individual Fly.io apps, automatically managing docker-compose.yml integration.
"""

import argparse
import os
import shutil
import sys
from pathlib import Path
from typing import Dict, Any
import yaml



def create_go_service_structure(service_name: str, services_dir: Path) -> None:
    """Create the directory structure and files for a Go service."""
    service_dir = services_dir / service_name
    
    if service_dir.exists():
        print(f"❌ Error: Service '{service_name}' already exists at {service_dir}")
        sys.exit(1)
    
    print(f"📁 Creating Go service directory structure for: {service_name}")
    
    # Create directory structure
    src_dir = service_dir / "src"
    tests_dir = service_dir / "tests"
    src_dir.mkdir(parents=True, exist_ok=True)
    tests_dir.mkdir(parents=True, exist_ok=True)
    
    # Create Dockerfile
    dockerfile_content = '''FROM golang:1.21-alpine AS builder
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
CMD ["./main"]'''
    
    (service_dir / "Dockerfile").write_text(dockerfile_content)
    
    # Create Makefile
    makefile_content = '''.PHONY: test build run dev clean shell sync-secrets deploy app-info help

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
	@awk -F':.*##' '/^[a-zA-Z_-]+:.*##/{printf "\\033[36m%-15s\\033[0m %s\\n", $$1,$$2}' $(MAKEFILE_LIST)'''
    
    (service_dir / "Makefile").write_text(makefile_content)
    
    # Create go.mod
    go_mod_content = f'''module {service_name}

go 1.21'''
    
    (service_dir / "go.mod").write_text(go_mod_content)
    
    # Create empty go.sum
    (service_dir / "go.sum").write_text("")
    
    # Create main.go
    main_go_content = '''package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"time"
)

type Response struct {
	Service   string    `json:"service"`
	Message   string    `json:"message"`
	Timestamp time.Time `json:"timestamp"`
	Status    string    `json:"status"`
}

type HealthResponse struct {
	Status    string    `json:"status"`
	Service   string    `json:"service"`
	Timestamp time.Time `json:"timestamp"`
	Uptime    string    `json:"uptime"`
}

var startTime = time.Now()

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "80"
	}

	serviceName := os.Getenv("SERVICE_NAME")
	if serviceName == "" {
		serviceName = "unknown"
	}

	http.HandleFunc("/", homeHandler(serviceName))
	http.HandleFunc("/health", healthHandler(serviceName))
	http.HandleFunc("/api/status", statusHandler(serviceName))

	log.Printf("🚀 %s service listening on port %s", serviceName, port)
	log.Printf("📊 Health check: http://localhost:%s/health", port)
	
	if err := http.ListenAndServe(":"+port, nil); err != nil {
		log.Fatal("Server failed to start:", err)
	}
}

func homeHandler(serviceName string) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/" {
			http.NotFound(w, r)
			return
		}

		html := fmt.Sprintf(`
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>%s Service</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 2rem;
            background: linear-gradient(135deg, #667eea 0%%, #764ba2 100%%);
            min-height: 100vh;
            color: white;
        }
        .container {
            text-align: center;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 2rem;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        h1 { margin-bottom: 1rem; }
        .info { margin: 1rem 0; padding: 1rem; background: rgba(255, 255, 255, 0.1); border-radius: 8px; }
        .links a {
            display: inline-block;
            margin: 0.5rem;
            padding: 0.5rem 1rem;
            background: rgba(255, 255, 255, 0.2);
            color: white;
            text-decoration: none;
            border-radius: 5px;
            border: 1px solid rgba(255, 255, 255, 0.3);
        }
        .links a:hover { background: rgba(255, 255, 255, 0.3); }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 %s Service</h1>
        <div class="info">
            <p><strong>Status:</strong> Running</p>
            <p><strong>Language:</strong> Go</p>
            <p><strong>Timestamp:</strong> %s</p>
        </div>
        <div class="links">
            <a href="/health">Health Check</a>
            <a href="/api/status">API Status</a>
        </div>
    </div>
</body>
</html>`, serviceName, serviceName, time.Now().Format(time.RFC3339))

		w.Header().Set("Content-Type", "text/html")
		w.WriteHeader(http.StatusOK)
		w.Write([]byte(html))
	}
}

func healthHandler(serviceName string) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		uptime := time.Since(startTime)
		
		response := HealthResponse{
			Status:    "healthy",
			Service:   serviceName,
			Timestamp: time.Now(),
			Uptime:    uptime.String(),
		}

		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(response)
	}
}

func statusHandler(serviceName string) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		response := Response{
			Service:   serviceName,
			Message:   fmt.Sprintf("Hello from %s", serviceName),
			Timestamp: time.Now(),
			Status:    "running",
		}

		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(response)
	}
}'''
    
    (src_dir / "main.go").write_text(main_go_content)
    
    # Create test file
    test_content = '''package main

import (
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestHealthHandler(t *testing.T) {
	req, err := http.NewRequest("GET", "/health", nil)
	if err != nil {
		t.Fatal(err)
	}

	rr := httptest.NewRecorder()
	handler := healthHandler("test-service")

	handler.ServeHTTP(rr, req)

	if status := rr.Code; status != http.StatusOK {
		t.Errorf("handler returned wrong status code: got %v want %v",
			status, http.StatusOK)
	}

	expected := "application/json"
	if ct := rr.Header().Get("Content-Type"); ct != expected {
		t.Errorf("handler returned wrong content type: got %v want %v",
			ct, expected)
	}
}

func TestStatusHandler(t *testing.T) {
	req, err := http.NewRequest("GET", "/api/status", nil)
	if err != nil {
		t.Fatal(err)
	}

	rr := httptest.NewRecorder()
	handler := statusHandler("test-service")

	handler.ServeHTTP(rr, req)

	if status := rr.Code; status != http.StatusOK {
		t.Errorf("handler returned wrong status code: got %v want %v",
			status, http.StatusOK)
	}
}'''
    
    # Write test file to both locations
    (tests_dir / "main_test.go").write_text(test_content)
    (src_dir / "main_test.go").write_text(test_content)
    
    # Create sample .env file
    env_sample = '''# Sample environment variables for this service
# Copy this to .env and modify with your actual values
# Note: .env files should be added to .gitignore for security

SAMPLE_SECRET=sample_secret_value
DATABASE_URL=postgres://user:password@localhost:5432/dbname
API_KEY=your_api_key_here
DEBUG=false
'''
    
    (service_dir / ".env").write_text(env_sample)
    
    print(f"✅ Go service structure created for: {service_name}")


def create_fly_toml(service_name: str, service_dir: Path) -> None:
    """Create individual fly.toml file for the service."""
    print(f"🪰 Creating fly.toml for {service_name}...")
    
    app_name = f"shmuel-tech-{service_name}"
    
    # Go service configuration
    fly_content = f'''app = "{app_name}"
primary_region = "ams"
kill_signal = "SIGINT"

[build]
  dockerfile = "Dockerfile"

[env]
  SERVICE_NAME = "{service_name}"
  PORT = "80"

[http_service]
  internal_port = 80
  force_https = true
  auto_stop_machines = "stop"
  auto_start_machines = true
  min_machines_running = 0
  
  [[http_service.checks]]
    path = "/health"
    method = "GET"
    interval = "30s"
    timeout = "5s"
    grace_period = "10s"
'''
    
    (service_dir / "fly.toml").write_text(fly_content)
    print(f"✅ Created fly.toml for {service_name}")


def update_docker_compose(service_name: str, compose_file: Path) -> None:
    """Update docker-compose.yml to include the new service."""
    print(f"🐳 Updating docker-compose.yml...")
    
    if not compose_file.exists():
        print(f"❌ Error: {compose_file} not found")
        sys.exit(1)
    
    # Load existing docker-compose.yml
    with open(compose_file, 'r') as f:
        compose_data = yaml.safe_load(f)
    
    # Add the new service
    if 'services' not in compose_data:
        compose_data['services'] = {}
    
    if service_name in compose_data['services']:
        print(f"⚠️  Warning: Service '{service_name}' already exists in docker-compose.yml")
        return
    
    # Determine the host rule
    if service_name == "main-site":
        host_rule = f'Host(`shmuel.localhost`)'
    else:
        host_rule = f'Host(`{service_name}.localhost`)'
    
    compose_data['services'][service_name] = {
        'build': f'./services/{service_name}',
        'environment': [
            f'SERVICE_NAME={service_name}'
        ],
        'labels': [
            'traefik.enable=true',
            f'traefik.http.routers.{service_name}.rule={host_rule}',
            f'traefik.http.services.{service_name}.loadbalancer.server.port=80'
        ],
        'depends_on': ['traefik']
    }
    
    # Write back to file
    with open(compose_file, 'w') as f:
        yaml.dump(compose_data, f, default_flow_style=False, indent=2, sort_keys=False)
    
    print(f"✅ Added '{service_name}' to docker-compose.yml")


def remove_service_structure(service_name: str, services_dir: Path) -> None:
    """Remove the service directory and all its contents."""
    service_dir = services_dir / service_name
    
    if not service_dir.exists():
        print(f"❌ Error: Service '{service_name}' does not exist at {service_dir}")
        sys.exit(1)
    
    print(f"🗑️  Removing service directory: {service_dir}")
    
    shutil.rmtree(service_dir)
    
    print(f"✅ Service directory removed: {service_name}")


def remove_from_docker_compose(service_name: str, compose_file: Path) -> None:
    """Remove service from docker-compose.yml."""
    print(f"🐳 Removing from docker-compose.yml...")
    
    if not compose_file.exists():
        print(f"❌ Error: {compose_file} not found")
        sys.exit(1)
    
    # Load existing docker-compose.yml
    with open(compose_file, 'r') as f:
        compose_data = yaml.safe_load(f)
    
    # Remove the service
    if 'services' in compose_data and service_name in compose_data['services']:
        del compose_data['services'][service_name]
        
        # Write back to file
        with open(compose_file, 'w') as f:
            yaml.dump(compose_data, f, default_flow_style=False, indent=2, sort_keys=False)
        
        print(f"✅ Removed '{service_name}' from docker-compose.yml")
    else:
        print(f"⚠️  Warning: Service '{service_name}' not found in docker-compose.yml")


def create_service(service_name: str) -> None:
    """Create a new Go service."""
    # Get project root directory
    project_root = Path(__file__).parent.parent
    services_dir = project_root / "services"
    compose_file = project_root / "docker-compose.yml"
    
    print(f"🚀 Creating new Go service: {service_name}")
    print(f"📂 Project root: {project_root}")
    
    # Create Go service structure
    create_go_service_structure(service_name, services_dir)
    
    # Create individual fly.toml
    service_dir = services_dir / service_name
    create_fly_toml(service_name, service_dir)
    
    # Update docker-compose.yml
    update_docker_compose(service_name, compose_file)
    
    # Show success message
    print(f"""
🎉 Go service '{service_name}' created successfully!

📋 Next steps:
1. Configure secrets: modify .env and update values
2. Start development: make dev
3. Visit your service: http://{service_name}.localhost
4. Check health: http://{service_name}.localhost/health
5. View API status: http://{service_name}.localhost/api/status

🛠️  Service commands:
- make -C services/{service_name} dev         # Run in development mode
- make -C services/{service_name} test        # Run tests
- make -C services/{service_name} build       # Build Docker image
- make -C services/{service_name} sync-secrets # Sync .env to Fly.io secrets
- make -C services/{service_name} help        # Show all commands
- make -C services/{service_name} deploy      # Deploy to Fly.io
- make -C services/{service_name} app-info    # Get app information from Fly.io

🔐 Secret management:
- Modify .env file with your secrets
- Run 'make sync-secrets' to upload to Fly.io
""")


def remove_service(service_name: str, force: bool = False) -> None:
    """Remove an existing service."""
    # Get project root directory
    project_root = Path(__file__).parent.parent
    services_dir = project_root / "services"
    compose_file = project_root / "docker-compose.yml"
    
    service_dir = services_dir / service_name
    
    if not service_dir.exists():
        print(f"❌ Error: Service '{service_name}' does not exist")
        sys.exit(1)
    
    print(f"🗑️  Removing service: {service_name}")
    print(f"📂 Project root: {project_root}")
    
    # Interactive confirmation unless --force is used
    if not force:
        print(f"""
⚠️  This will permanently remove:
- Service directory: {service_dir}
- Entry from docker-compose.yml
- Individual fly.toml file

⚠️  NOTE: This will NOT remove the Fly.io app. To remove it:
- fly apps destroy shmuel-tech-{service_name}

This action cannot be undone.
""")
        
        while True:
            confirm = input(f"Are you sure you want to remove service '{service_name}'? (y/N): ").strip().lower()
            if confirm in ['y', 'yes']:
                break
            elif confirm in ['n', 'no', '']:
                print("❌ Operation cancelled")
                sys.exit(0)
            else:
                print("Please enter 'y' or 'n'")
    
    # Remove from docker-compose.yml
    remove_from_docker_compose(service_name, compose_file)
    
    # Remove service directory
    remove_service_structure(service_name, services_dir)
    
    print(f"""
🎉 Service '{service_name}' removed successfully!

📋 Cleanup completed:
✅ Service directory removed
✅ Removed from docker-compose.yml

🚀 To also remove the Fly.io app:
- fly apps destroy shmuel-tech-{service_name}
""")


def main() -> None:
    """Main function to create or remove services."""
    parser = argparse.ArgumentParser(description="Service handler for shmuel-tech monorepo")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Create service command
    create_parser = subparsers.add_parser('create', help='Create a new Go service')
    create_parser.add_argument('name', help='Name of the service to create')
    
    # Remove service command
    remove_parser = subparsers.add_parser('remove', help='Remove an existing service')
    remove_parser.add_argument('name', help='Name of the service to remove')
    remove_parser.add_argument('--force', '-f', action='store_true', 
                              help='Skip interactive confirmation')
    
    # For backward compatibility, also accept service name as first argument
    if len(sys.argv) > 1 and sys.argv[1] not in ['create', 'remove', '-h', '--help']:
        # Legacy mode: assume it's a service name to create
        service_name = sys.argv[1]
        
        # Validate service name
        if not service_name or not service_name.replace('-', '').replace('_', '').isalnum():
            print("❌ Error: Service name must contain only alphanumeric characters, hyphens, and underscores")
            sys.exit(1)
        
        create_service(service_name)
        return
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Validate service name
    if not args.name or not args.name.replace('-', '').replace('_', '').isalnum():
        print("❌ Error: Service name must contain only alphanumeric characters, hyphens, and underscores")
        sys.exit(1)
    
    if args.command == 'create':
        create_service(args.name)
    elif args.command == 'remove':
        remove_service(args.name, args.force)


if __name__ == "__main__":
    main() 