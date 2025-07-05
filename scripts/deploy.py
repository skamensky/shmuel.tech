#!/usr/bin/env python3
"""
Deployment script for shmuel-tech monorepo.
Handles creation and deployment of individual Fly.io apps for each service.
"""

import argparse
import os
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Dict, Any, Tuple


# Thread lock for safe printing during parallel operations
_print_lock = threading.Lock()

def run_command(cmd: List[str], check: bool = True, silent: bool = False) -> subprocess.CompletedProcess:
    """Run a command and return the result."""
    if not silent:
        with _print_lock:
            print(f"🔧 Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=check, capture_output=True, text=True)
        if result.stdout and not silent:
            with _print_lock:
                print(result.stdout.strip())
        return result
    except subprocess.CalledProcessError as e:
        if not silent:
            with _print_lock:
                print(f"❌ Command failed: {e}")
                if e.stderr:
                    print(f"Error: {e.stderr.strip()}")
        if check:
            sys.exit(1)
        return e


def get_services(services_dir: Path) -> List[Dict[str, Any]]:
    """Get list of services with their types."""
    services = []
    
    for service_dir in services_dir.iterdir():
        if service_dir.is_dir() and not service_dir.name.startswith('.'):
            service_info = {
                'name': service_dir.name,
                'path': service_dir,
                'type': 'go' if (service_dir / 'go.mod').exists() else 'static'
            }
            services.append(service_info)
    
    return services


def check_fly_auth() -> bool:
    """Check if user is authenticated with Fly.io."""
    print("🔐 Checking Fly.io authentication...")
    result = run_command(['fly', 'auth', 'whoami'], check=False)
    return result.returncode == 0


def app_exists(app_name: str, silent: bool = False) -> bool:
    """Check if a Fly.io app exists."""
    if not silent:
        print(f"📱 Checking if app '{app_name}' exists...")
    result = run_command(['fly', 'apps', 'list'], check=False, silent=silent)
    if result.returncode == 0:
        return app_name in result.stdout
    return False


def cert_exists(app_name: str, domain: str, silent: bool = False) -> bool:
    """Check if SSL certificate exists for domain."""
    if not silent:
        print(f"🔒 Checking SSL certificate for '{domain}' in app '{app_name}'...")
    result = run_command(['fly', 'certs', 'list', '--app', app_name], check=False, silent=silent)
    if result.returncode == 0:
        return domain in result.stdout
    return False


def create_app(app_name: str, org: str = "personal", silent: bool = False) -> bool:
    """Create a new Fly.io app."""
    if not silent:
        print(f"📱 Creating new Fly.io app: {app_name}")
    result = run_command(['fly', 'apps', 'create', app_name, '--org', org], check=False, silent=silent)
    return result.returncode == 0


def add_certificate(app_name: str, domain: str, silent: bool = False) -> bool:
    """Add SSL certificate for domain."""
    if not silent:
        print(f"🔒 Adding SSL certificate for '{domain}' to app '{app_name}'...")
    result = run_command(['fly', 'certs', 'add', domain, '--app', app_name], check=False, silent=silent)
    return result.returncode == 0


def deploy_service(service: Dict[str, Any], app_name: str, detach: bool = False, silent: bool = False) -> bool:
    """Deploy a service to Fly.io."""
    if not silent:
        print(f"🚀 Deploying service '{service['name']}' to app '{app_name}'...")
    
    fly_toml = service['path'] / 'fly.toml'
    if not fly_toml.exists():
        if not silent:
            print(f"❌ fly.toml not found for service '{service['name']}'")
        return False
    
    cmd = ['fly', 'deploy', '--config', str(fly_toml), '--app', app_name, '--remote-only']
    if detach:
        cmd.append('--detach')
    
    result = run_command(cmd, check=False, silent=silent)
    return result.returncode == 0


def deploy_single_service_worker(service: Dict[str, Any], org: str = "personal", detach: bool = False) -> Tuple[str, bool, str]:
    """
    Deploy a single service in a separate thread.
    Returns: (service_name, success, message)
    """
    service_name = service['name']
    app_name = f"shmuel-tech-{service_name}"
    
    try:
        # Use silent mode to avoid race conditions in output
        # Create app if it doesn't exist
        if not app_exists(app_name, silent=True):
            if not create_app(app_name, org, silent=True):
                return (service_name, False, f"Failed to create app '{app_name}'")
        
        # Add SSL certificate
        if service_name == "main-site":
            domain = "shmuel.tech"
        else:
            domain = f"{service_name}.shmuel.tech"
        
        if not cert_exists(app_name, domain, silent=True):
            if not add_certificate(app_name, domain, silent=True):
                # Continue anyway, just log warning
                pass
        
        # Deploy service
        if deploy_service(service, app_name, detach, silent=True):
            return (service_name, True, f"Successfully deployed to '{app_name}'")
        else:
            return (service_name, False, f"Failed to deploy to '{app_name}'")
            
    except Exception as e:
        return (service_name, False, f"Exception during deployment: {str(e)}")


def deploy_all_services(services_dir: Path, org: str = "personal", detach: bool = False) -> bool:
    """Deploy all services to Fly.io using parallel deployment."""
    print("🚀 Starting deployment of all services...")
    
    if not check_fly_auth():
        print("❌ Not authenticated with Fly.io. Run 'fly auth login' first.")
        return False
    
    services = get_services(services_dir)
    if not services:
        print("❌ No services found to deploy.")
        return False
    
    print(f"📋 Found {len(services)} services to deploy:")
    for service in services:
        print(f"  - {service['name']} ({service['type']})")
    
    # Deploy all services in parallel
    return _deploy_services_parallel(services, org, detach)


def deploy_specific_services(service_names: List[str], services_dir: Path, org: str = "personal", detach: bool = False) -> bool:
    """Deploy specific services to Fly.io using parallel deployment."""
    print(f"🚀 Deploying specific services: {', '.join(service_names)}")
    
    if not check_fly_auth():
        print("❌ Not authenticated with Fly.io. Run 'fly auth login' first.")
        return False
    
    # Validate all services exist first
    services_to_deploy = []
    for service_name in service_names:
        service_path = services_dir / service_name
        if not service_path.exists():
            print(f"❌ Service '{service_name}' not found in {services_dir}")
            return False
        
        service = {
            'name': service_name,
            'path': service_path,
            'type': 'go' if (service_path / 'go.mod').exists() else 'static'
        }
        services_to_deploy.append(service)
    
    print(f"📋 Found {len(services_to_deploy)} services to deploy:")
    for service in services_to_deploy:
        print(f"  - {service['name']} ({service['type']})")
    
    # Deploy all services in parallel
    return _deploy_services_parallel(services_to_deploy, org, detach)


def _deploy_services_parallel(services: List[Dict[str, Any]], org: str = "personal", detach: bool = False) -> bool:
    """Deploy multiple services in parallel and aggregate results."""
    print(f"\n🔄 Starting parallel deployment of {len(services)} services...")
    
    # Use ThreadPoolExecutor to deploy services in parallel
    results = []
    with ThreadPoolExecutor(max_workers=len(services)) as executor:
        # Submit all deployment tasks
        future_to_service = {
            executor.submit(deploy_single_service_worker, service, org, detach): service['name']
            for service in services
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_service):
            service_name = future_to_service[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                results.append((service_name, False, f"Unexpected error: {str(e)}"))
    
    # Sort results by service name for consistent output
    results.sort(key=lambda x: x[0])
    
    # Print results sequentially
    print(f"\n{'='*60}")
    print(f"📊 Deployment Results")
    print(f"{'='*60}")
    
    success_count = 0
    error_count = 0
    
    for service_name, success, message in results:
        if success:
            print(f"✅ {service_name}: {message}")
            success_count += 1
        else:
            print(f"❌ {service_name}: {message}")
            error_count += 1
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"📊 Deployment Summary")
    print(f"{'='*60}")
    print(f"✅ Successfully deployed: {success_count}/{len(services)} services")
    
    if error_count > 0:
        print(f"❌ Failed deployments: {error_count}/{len(services)} services")
        print(f"\n⚠️  There were {error_count} error(s). An exception will be raised.")
        raise Exception(f"Deployment failed for {error_count} out of {len(services)} services")
    else:
        print("🎉 All services deployed successfully!")
        return True


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Deploy services to Fly.io")
    parser.add_argument('--service', '-s', nargs='*', help='Deploy specific services (can specify multiple)')
    parser.add_argument('--org', '-o', default='personal', help='Fly.io organization (default: personal)')
    parser.add_argument('--detach', '-d', action='store_true', help='Detach from deployment process')
    parser.add_argument('--services-dir', default='services', help='Services directory (default: services)')
    
    args = parser.parse_args()
    
    # Get project root directory
    project_root = Path(__file__).parent.parent
    services_dir = project_root / args.services_dir
    
    if not services_dir.exists():
        print(f"❌ Services directory not found: {services_dir}")
        sys.exit(1)
    
    print(f"📂 Project root: {project_root}")
    print(f"📂 Services directory: {services_dir}")
    
    try:
        if args.service:
            # Handle both single service and multiple services
            service_list = args.service if isinstance(args.service, list) else [args.service]
            success = deploy_specific_services(service_list, services_dir, args.org, args.detach)
        else:
            success = deploy_all_services(services_dir, args.org, args.detach)
        
        sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"\n💥 Deployment failed with exception: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 