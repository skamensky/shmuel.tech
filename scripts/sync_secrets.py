#!/usr/bin/env python3
"""
Secret synchronization script for shmuel-tech monorepo.
Syncs environment variables from .env files to Fly.io secrets.
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Import shared utilities
from .utils import load_project_env, check_fly_auth, run_command

# Load environment variables
load_project_env()


def parse_env_file(env_file: Path) -> Dict[str, str]:
    """Parse .env file and return dictionary of key-value pairs."""
    if not env_file.exists():
        raise FileNotFoundError(f".env file not found: {env_file}")
    
    secrets = {}
    
    with open(env_file, 'r') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            
            # Parse key=value pairs
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                
                if key:
                    secrets[key] = value
            else:
                print(f"⚠️  Warning: Skipping invalid line {line_num} in {env_file}: {line}")
    
    return secrets


def sync_secrets_to_fly(app_name: str, secrets: Dict[str, str], dry_run: bool = False) -> bool:
    """Sync secrets to Fly.io app using fly secrets set command."""
    if not secrets:
        print("ℹ️  No secrets to sync")
        return True
    
    print(f"🔐 Syncing {len(secrets)} secrets to Fly.io app: {app_name}")
    
    # Build the fly secrets set command
    cmd = ['flyctl', 'secrets', 'set', '--app', app_name]
    
    # Add each secret as key=value
    for key, value in secrets.items():
        # Escape special characters in values
        cmd.append(f'{key}={value}')
    
    if dry_run:
        print(f"🧪 Dry run - would execute: {' '.join(cmd[:4])} [REDACTED SECRETS]")
        print(f"🔑 Secrets to set: {', '.join(secrets.keys())}")
        return True
    
    print(f"🔑 Setting secrets: {', '.join(secrets.keys())}")
    
    try:
        result = run_command(cmd, check=True, silent=False)
        print("✅ Secrets synced successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to sync secrets: {e}")
        return False


def get_services(services_dir: Path) -> List[str]:
    """Get list of service names."""
    services = []
    
    for service_dir in services_dir.iterdir():
        if service_dir.is_dir() and not service_dir.name.startswith('.'):
            services.append(service_dir.name)
    
    return sorted(services)


def sync_service_secrets(service_name: str, services_dir: Path, dry_run: bool = False) -> bool:
    """Sync secrets for a specific service."""
    service_dir = services_dir / service_name
    env_file = service_dir / '.env'
    app_name = f"shmuel-tech-{service_name}"
    
    if not service_dir.exists():
        print(f"❌ Service '{service_name}' not found in {services_dir}")
        return False
    
    if not env_file.exists():
        print(f"⚠️  No .env file found for service '{service_name}' at {env_file}")
        return True  # Not an error, just no secrets to sync
    
    print(f"📋 Processing service: {service_name}")
    print(f"📄 Reading secrets from: {env_file}")
    
    try:
        secrets = parse_env_file(env_file)
        
        if not secrets:
            print(f"ℹ️  No secrets found in {env_file}")
            return True
        
        return sync_secrets_to_fly(app_name, secrets, dry_run)
        
    except Exception as e:
        print(f"❌ Error processing secrets for '{service_name}': {e}")
        return False


def sync_all_services(services_dir: Path, dry_run: bool = False) -> bool:
    """Sync secrets for all services."""
    print("🔄 Syncing secrets for all services...")
    
    services = get_services(services_dir)
    
    if not services:
        print("❌ No services found to sync secrets for")
        return False
    
    print(f"📋 Found {len(services)} services: {', '.join(services)}")
    
    success_count = 0
    error_count = 0
    
    for service_name in services:
        print(f"\n{'='*60}")
        success = sync_service_secrets(service_name, services_dir, dry_run)
        
        if success:
            success_count += 1
        else:
            error_count += 1
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"📊 Secret Sync Summary")
    print(f"{'='*60}")
    print(f"✅ Successfully synced: {success_count}/{len(services)} services")
    
    if error_count > 0:
        print(f"❌ Failed to sync: {error_count}/{len(services)} services")
        return False
    else:
        print("🎉 All services synced successfully!")
        return True


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Sync secrets from .env files to Fly.io")
    parser.add_argument('--service', '-s', help='Sync secrets for specific service')
    parser.add_argument('--services-dir', default='services', help='Services directory (default: services)')
    parser.add_argument('--dry-run', '-n', action='store_true', help='Show what would be done without actually doing it')
    
    args = parser.parse_args()
    
    # Check Fly.io authentication
    if not check_fly_auth():
        print("❌ Not authenticated with Fly.io. Run 'fly auth login' first.")
        sys.exit(1)
    
    # Get project root directory
    project_root = Path(__file__).parent.parent
    services_dir = project_root / args.services_dir
    
    if not services_dir.exists():
        print(f"❌ Services directory not found: {services_dir}")
        sys.exit(1)
    
    print(f"📂 Project root: {project_root}")
    print(f"📂 Services directory: {services_dir}")
    
    if args.dry_run:
        print("🧪 Dry run mode - no actual changes will be made")
    
    try:
        if args.service:
            success = sync_service_secrets(args.service, services_dir, args.dry_run)
        else:
            success = sync_all_services(services_dir, args.dry_run)
        
        sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"\n💥 Secret sync failed with exception: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 