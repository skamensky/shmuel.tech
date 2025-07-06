#!/usr/bin/env python3
"""
Deployment script for shmuel-tech monorepo.
Handles creation and deployment of individual Fly.io apps for each service.
Includes automatic DNS management via Namecheap API.
"""

import argparse
import json
import os
import subprocess
import sys
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

# Import shared utilities
from .utils import load_project_env, check_fly_auth, run_command as shared_run_command
# Import DNS management functions
from .namecheap_dns import (
    get_dns_proxy_config, 
    bulk_update_dns_for_services
)

# Load environment variables
load_project_env()


# Thread lock for safe printing during parallel operations
_print_lock = threading.Lock()

def run_command(cmd: List[str], check: bool = True, silent: bool = False, input: str = None) -> subprocess.CompletedProcess:
    """Run a command and return the result. Wrapper for shared run_command with thread safety."""
    if not silent:
        with _print_lock:
            print(f"🔧 Running: {' '.join(cmd)}")
    
    # Use shared run_command but handle input parameter compatibility
    result = shared_run_command(cmd, check=check, silent=True, input_data=input)
    
    if result.stdout and not silent:
        with _print_lock:
            print(result.stdout.strip())
    
    # Handle CalledProcessError compatibility
    if hasattr(result, 'returncode') and result.returncode != 0 and check:
        if not silent:
            with _print_lock:
                print(f"❌ Command failed: returncode {result.returncode}")
                if result.stderr:
                    print(f"Error: {result.stderr.strip()}")
        sys.exit(1)
    
    return result



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


# check_fly_auth function moved to shared utils


def app_exists(app_name: str, silent: bool = False) -> bool:
    """Check if a Fly.io app exists."""
    if not silent:
        print(f"📱 Checking if app '{app_name}' exists...")
    result = run_command(['flyctl', 'apps', 'list'], check=False, silent=silent)
    if result.returncode == 0:
        return app_name in result.stdout
    return False


def cert_exists(app_name: str, domain: str, silent: bool = False) -> bool:
    """Check if SSL certificate exists for domain."""
    if not silent:
        print(f"🔒 Checking SSL certificate for '{domain}' in app '{app_name}'...")
    result = run_command(['flyctl', 'certs', 'list', '--app', app_name], check=False, silent=silent)
    if result.returncode == 0:
        return domain in result.stdout
    return False


def create_app(app_name: str, org: str = "personal", silent: bool = False) -> Tuple[bool, Optional[str]]:
    """Create a new Fly.io app. Returns (success, error_message)."""
    if not silent:
        print(f"📱 Creating new Fly.io app: {app_name}")
    result = run_command(['flyctl', 'apps', 'create', app_name, '--org', org], check=False, silent=silent)
    if result.returncode == 0:
        return True, None
    else:
        return False, f"Exit code {result.returncode}: {result.stderr.strip() if result.stderr else 'Unknown error'}"


def add_certificate(app_name: str, domains: List[str], silent: bool = False) -> Tuple[bool, Optional[str]]:
    """Add SSL certificates for specified domains. Returns (success, error_message)."""
    if not silent:
        print(f"🔒 Adding SSL certificates for {domains} to app '{app_name}'...")
    
    # Add and wait for each certificate
    for domain in domains:
        # Add certificate
        result = run_command(['flyctl', 'certs', 'add', domain, '--app', app_name], check=False, silent=silent)
        if result.returncode != 0:
            return False, f"Exit code {result.returncode}: {result.stderr.strip() if result.stderr else 'Unknown error'}"
        
        # Wait for certificate to be issued
        if not silent:
            print(f"⏳ Waiting for certificate '{domain}' to be issued...")
        
        success, error_msg = wait_for_certificate_issuance(app_name, domain, silent=silent)
        if not success:
            return False, f"Failed to wait for certificate '{domain}': {error_msg}"
        
        if not silent:
            print(f"✅ Certificate for '{domain}' has been issued")
    
    return True, None


def wait_for_certificate_issuance(app_name: str, domain: str, silent: bool = False, timeout: int = 600) -> Tuple[bool, Optional[str]]:
    """Wait for certificate to be issued. Returns (success, error_message)."""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        # Check certificate status
        result = run_command(['flyctl', 'certs', 'show', domain, '--app', app_name, '--json'], check=False, silent=True)
        
        if result.returncode != 0:
            return False, f"Certificate check failed: {result.stderr}"
        
        try:
            cert_data = json.loads(result.stdout)
            
            # Check if certificate is issued by looking for Issued.Nodes
            if 'Issued' in cert_data and 'Nodes' in cert_data['Issued'] and cert_data['Issued']['Nodes']:
                # Certificate is issued
                return True, None
            
            # Also check if the certificate is configured and ready
            if cert_data.get('Configured', False) and cert_data.get('CertificateAuthority', ''):
                # Certificate is configured and ready
                return True, None
            
            # Check ClientStatus for additional information
            client_status = cert_data.get('ClientStatus', '')
            if not silent:
                print(f"📋 Certificate '{domain}' status: {client_status}")
            
            # Wait before checking again
            time.sleep(1)
            
        except json.JSONDecodeError as e:
            if not silent:
                print(f"⚠️  Failed to parse certificate status for '{domain}': {str(e)}")
                print(f"Raw output: {result.stdout}")
            time.sleep(1)
    
    return False, f"Timeout waiting for certificate '{domain}' to be issued after {timeout} seconds"


def deploy_service(service: Dict[str, Any], app_name: str, detach: bool = False, silent: bool = False) -> Tuple[bool, Optional[str]]:
    """Deploy a service to Fly.io. Returns (success, error_message)."""
    if not silent:
        print(f"🚀 Deploying service '{service['name']}' to app '{app_name}'...")
    
    fly_toml = service['path'] / 'fly.toml'
    if not fly_toml.exists():
        error_msg = f"fly.toml not found for service '{service['name']}'"
        if not silent:
            print(f"❌ {error_msg}")
        return False, error_msg
    
    # Change to service directory before deployment
    original_cwd = os.getcwd()
    try:
        os.chdir(service['path'])
        
        cmd = ['flyctl', 'deploy', '--config', 'fly.toml', '--app', app_name, '--remote-only']
        if detach:
            cmd.append('--detach')
        
        result = run_command(cmd, check=False, silent=silent)
        if result.returncode == 0:
            return True, None
        else:
            return False, f"Exit code {result.returncode}: {result.stderr.strip() if result.stderr else 'Unknown error'}"
    finally:
        # Always restore original working directory
        os.chdir(original_cwd)


def deploy_single_service_worker(service: Dict[str, Any], org: str = "personal", detach: bool = False) -> Tuple[str, bool, str, Optional[str]]:
    """
    Deploy a single service in a separate thread.
    Note: DNS is handled separately, but certificates are managed per service.
    Returns: (service_name, success, message, full_traceback)
    """
    service_name = service['name']
    app_name = f"shmuel-tech-{service_name}"
    
    try:
        # Thread-safe logging with lock
        with _print_lock:
            print(f"🚀 [{service_name}] Starting deployment...")
        
        # Create app if it doesn't exist
        if not app_exists(app_name, silent=True):
            with _print_lock:
                print(f"📱 [{service_name}] Creating new Fly.io app: {app_name}")
            success, error_msg = create_app(app_name, org, silent=True)
            if not success:
                return (service_name, False, f"Failed to create app '{app_name}': {error_msg}", None)
            with _print_lock:
                print(f"✅ [{service_name}] App created successfully")
        else:
            with _print_lock:
                print(f"✅ [{service_name}] App '{app_name}' already exists")
        
        # Add SSL certificate if it doesn't exist
        # Skip DNS proxy service - it doesn't need shmuel.tech domain certificates
        if service_name != "dns-proxy":
            if service_name == "main-site":
                domain = "shmuel.tech"
            else:
                domain = f"{service_name}.shmuel.tech"
            
            # Check for both regular and www certificates
            www_domain = f"www.{domain}"
            missing_certs = []
            
            # Check regular domain first, then www domain
            # Ordering is intentional: regular certs are processed first, then www certs
            if not cert_exists(app_name, domain, silent=True):
                missing_certs.append(domain)
            
            if not cert_exists(app_name, www_domain, silent=True):
                missing_certs.append(www_domain)
            
            # Add missing certificates
            if missing_certs:
                with _print_lock:
                    print(f"🔒 [{service_name}] Adding SSL certificates for: {missing_certs}")
                success, error_msg = add_certificate(app_name, missing_certs, silent=True)
                if not success:
                    return (service_name, False, f"Failed to add certificates for {missing_certs}: {error_msg}", None)
                with _print_lock:
                    print(f"✅ [{service_name}] Certificates added successfully")
            else:
                with _print_lock:
                    print(f"✅ [{service_name}] All certificates already exist")
        else:
            with _print_lock:
                print(f"⏭️  [{service_name}] Skipping certificate setup (DNS proxy service)")
        
        # Deploy service
        with _print_lock:
            print(f"🚀 [{service_name}] Starting service deployment...")
        success, error_msg = deploy_service(service, app_name, detach, silent=True)
        if success:
            with _print_lock:
                print(f"✅ [{service_name}] Service deployed successfully")
            return (service_name, True, f"Successfully deployed to '{app_name}'", None)
        else:
            with _print_lock:
                print(f"❌ [{service_name}] Service deployment failed: {error_msg}")
            return (service_name, False, f"Failed to deploy to '{app_name}': {error_msg}", None)
            
    except Exception as e:
        # Capture full traceback
        full_traceback = traceback.format_exc()
        with _print_lock:
            print(f"💥 [{service_name}] Exception during deployment: {str(e)}")
        return (service_name, False, f"Exception during deployment: {str(e)}", full_traceback)


def deploy_all_services(services_dir: Path, org: str = "personal", detach: bool = False, enable_dns: bool = True) -> bool:
    """Deploy all services to Fly.io using parallel deployment."""
    print("🚀 Starting deployment of all services...")
    
    if not check_fly_auth():
        print("❌ Not authenticated with Fly.io. Run 'fly auth login' first.")
        return False
    
    # Check DNS credentials if DNS is enabled
    if enable_dns:
        try:
            get_dns_proxy_config()
            print("✅ DNS proxy credentials found")
        except ValueError as e:
            print(f"❌ DNS automation disabled: {e}")
            enable_dns = False
    
    services = get_services(services_dir)
    if not services:
        print("❌ No services found to deploy.")
        return False
    
    print(f"📋 Found {len(services)} services to deploy:")
    for service in services:
        print(f"  - {service['name']} ({service['type']})")
    
    if enable_dns:
        print("🌐 DNS automation enabled")
    else:
        print("⚠️  DNS automation disabled, using manual certificate method")
    
    # Deploy all services in parallel
    return _deploy_services_parallel(services, org, detach, enable_dns)


def deploy_specific_services(service_names: List[str], services_dir: Path, org: str = "personal", detach: bool = False, enable_dns: bool = True) -> bool:
    """Deploy specific services to Fly.io using parallel deployment."""
    print(f"🚀 Deploying specific services: {', '.join(service_names)}")
    
    if not check_fly_auth():
        print("❌ Not authenticated with Fly.io. Run 'fly auth login' first.")
        return False
    
    # Check DNS credentials if DNS is enabled
    if enable_dns:
        try:
            get_dns_proxy_config()
            print("✅ DNS proxy credentials found")
        except ValueError as e:
            print(f"❌ DNS automation disabled: {e}")
            enable_dns = False
    
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
    
    if enable_dns:
        print("🌐 DNS automation enabled")
    else:
        print("⚠️  DNS automation disabled, using manual certificate method")
    
    # Deploy all services in parallel
    return _deploy_services_parallel(services_to_deploy, org, detach, enable_dns)


def _deploy_services_parallel(services: List[Dict[str, Any]], org: str = "personal", detach: bool = False, enable_dns: bool = True) -> bool:
    """Deploy multiple services with bulk DNS updates and parallel deployment."""
    print(f"\n🔄 Starting deployment of {len(services)} services...")
    
    # Step 1: Bulk DNS update (if enabled)
    print(f"\n🌐 Step 1: Bulk DNS update for all services...")

    if enable_dns:
        
        # Prepare service configurations for DNS
        # Skip DNS proxy service - it doesn't need to be under our shmuel.tech domain
        # and we don't want to bother with manual bootstrapping step
        service_configs = []
        for service in services:
            service_name = service['name']
            
            # Skip DNS proxy service from DNS automation
            if service_name == 'dns-proxy':
                print(f"⏭️  Skipping DNS for '{service_name}' - doesn't need shmuel.tech domain")
                continue
                
            app_name = f"shmuel-tech-{service_name}"
            service_configs.append({
                'service_name': service_name,
                'app_name': app_name
            })
        
        try:
            success, error_msg = bulk_update_dns_for_services(service_configs, silent=False)
            if not success:
                print(f"❌ Bulk DNS update failed: {error_msg}")
                return False
        except Exception as e:
            print(f"❌ DNS update exception: {str(e)}")
            return False
    else:
        print(f"\n⚠️  DNS automation disabled, skipping bulk DNS update")
    
    # Step 2: Deploy all services in parallel (including certificates)
    print(f"\n🚀 Step 2: Parallel deployment of all services...")
    
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
                full_traceback = traceback.format_exc()
                results.append((service_name, False, f"Unexpected error: {str(e)}", full_traceback))
    
    # Sort results by service name for consistent output
    results.sort(key=lambda x: x[0])
    
    # Print results sequentially
    print(f"\n{'='*60}")
    print(f"📊 Deployment Results")
    print(f"{'='*60}")
    
    success_count = 0
    error_count = 0
    failed_services = []
    
    for service_name, success, message, full_traceback in results:
        if success:
            print(f"✅ {service_name}: {message}")
            success_count += 1
        else:
            print(f"❌ {service_name}: {message}")
            error_count += 1
            failed_services.append((service_name, message, full_traceback))
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"📊 Deployment Summary")
    print(f"{'='*60}")
    print(f"✅ Successfully deployed: {success_count}/{len(services)} services")
    
    if error_count > 0:
        print(f"❌ Failed deployments: {error_count}/{len(services)} services")
        
        # Print detailed error information
        print(f"\n{'='*60}")
        print(f"🔍 Detailed Error Information")
        print(f"{'='*60}")
        
        for service_name, message, full_traceback in failed_services:
            print(f"\n{service_name} full error details:")
            print(f"---{'-'*50}---")
            if full_traceback:
                print(full_traceback)
            else:
                print(f"Error: {message}")
            print(f"---{'-'*50}---")
        
        print(f"\n⚠️  There were {error_count} error(s). An exception will be raised.")
        raise Exception(f"Deployment failed for {error_count} out of {len(services)} services")
    else:
        print("🎉 All services deployed successfully!")
        return True


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Deploy services to Fly.io")
    parser.add_argument('--service', '-s', action='append', help='Deploy specific services (can specify multiple)')
    parser.add_argument('--org', '-o', default='personal', help='Fly.io organization (default: personal)')
    parser.add_argument('--detach', '-d', action='store_true', help='Detach from deployment process')
    parser.add_argument('--services-dir', default='services', help='Services directory (default: services)')
    parser.add_argument('--no-dns', action='store_true', help='Disable DNS automation (use manual certificate method)')
    
    args = parser.parse_args()
    
    # Get project root directory
    project_root = Path(__file__).parent.parent
    services_dir = project_root / args.services_dir
    
    if not services_dir.exists():
        print(f"❌ Services directory not found: {services_dir}")
        sys.exit(1)
    
    print(f"📂 Project root: {project_root}")
    print(f"📂 Services directory: {services_dir}")
    
    # DNS automation is enabled by default unless --no-dns is specified
    enable_dns = not args.no_dns
    
    try:
        if args.service:
            success = deploy_specific_services(args.service, services_dir, args.org, args.detach, enable_dns)
        else:
            success = deploy_all_services(services_dir, args.org, args.detach, enable_dns)
        
        sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"\n💥 Deployment failed with exception: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 