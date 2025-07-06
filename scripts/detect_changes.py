#!/usr/bin/env python3
"""
Detect which services have changes between git commits.
Used by CI/CD to only deploy services that actually changed.
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List, Set


def run_git_command(cmd: List[str], verbose: bool = False) -> str:
    """Run a git command and return the output."""
    try:
        result = subprocess.run(['git'] + cmd, check=True, capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ Git command failed: {e}", file=sys.stderr)
        if e.stderr:
            print(f"Error: {e.stderr.strip()}", file=sys.stderr)
        sys.exit(1)


def get_changed_files(base_ref: str, head_ref: str = "HEAD", verbose: bool = False) -> List[str]:
    """Get list of changed files between two git references."""
    if verbose:
        print(f"🔍 Detecting changes between {base_ref} and {head_ref}", file=sys.stderr)
    
    # Get list of changed files
    cmd = ["diff", "--name-only", base_ref, head_ref]
    output = run_git_command(cmd, verbose)
    
    if not output:
        if verbose:
            print("📋 No changes detected", file=sys.stderr)
        return []
    
    changed_files = output.split('\n')
    if verbose:
        print(f"📋 Found {len(changed_files)} changed files:", file=sys.stderr)
        for file in changed_files:
            print(f"  - {file}", file=sys.stderr)
    
    return changed_files


def get_changed_services(changed_files: List[str], services_dir: str = "services") -> Set[str]:
    """Extract service names from changed file paths."""
    changed_services = set()
    
    for file_path in changed_files:
        if file_path.startswith(f"{services_dir}/"):
            # Extract service name from path like "services/main-site/..."
            path_parts = file_path.split('/')
            if len(path_parts) >= 2:
                service_name = path_parts[1]
                changed_services.add(service_name)
    
    return changed_services


def get_all_services(services_dir: Path) -> Set[str]:
    """Get list of all available services."""
    services = set()
    
    if not services_dir.exists():
        return services
    
    for service_dir in services_dir.iterdir():
        if service_dir.is_dir() and not service_dir.name.startswith('.'):
            services.add(service_dir.name)
    
    return services


def detect_changes(base_ref: str, head_ref: str = "HEAD", services_dir_name: str = "services", 
                  force_all: bool = False, include_root_changes: bool = True, verbose: bool = False) -> List[str]:
    """
    Detect which services have changes.
    
    Args:
        base_ref: Base git reference to compare against
        head_ref: Head git reference (default: HEAD)
        services_dir_name: Name of services directory
        force_all: If True, return all services regardless of changes
        include_root_changes: If True, deploy all services when root files change
        verbose: If True, print debug information to stderr
    
    Returns:
        List of service names that should be deployed
    """
    project_root = Path(__file__).parent.parent
    services_dir = project_root / services_dir_name
    
    all_services = get_all_services(services_dir)
    
    if force_all:
        if verbose:
            print("🚀 Force deployment requested - returning all services", file=sys.stderr)
        return sorted(list(all_services))
    
    if not all_services:
        if verbose:
            print("❌ No services found", file=sys.stderr)
        return []
    
    if verbose:
        print(f"📂 Available services: {', '.join(sorted(all_services))}", file=sys.stderr)
    
    changed_files = get_changed_files(base_ref, head_ref, verbose)
    
    if not changed_files:
        if verbose:
            print("📋 No changes detected - no services to deploy", file=sys.stderr)
        return []
    
    # Check for root-level changes that affect all services
    root_changes = False
    if include_root_changes:
        root_files = [
            "docker-compose.yml",
            "Makefile", 
            ".github/workflows/",
            "scripts/deploy.py",
            "scripts/service_handler.py"
        ]
        
        for file_path in changed_files:
            for root_file in root_files:
                if file_path.startswith(root_file):
                    if verbose:
                        print(f"🔧 Root change detected in {file_path} - deploying all services", file=sys.stderr)
                    root_changes = True
                    break
            if root_changes:
                break
    
    if root_changes:
        return sorted(list(all_services))
    
    # Get services with changes
    changed_services = get_changed_services(changed_files, services_dir_name)
    
    # Filter to only include services that actually exist
    valid_changed_services = changed_services.intersection(all_services)
    
    if not valid_changed_services:
        if verbose:
            print("📋 No service changes detected - no services to deploy", file=sys.stderr)
        return []
    
    if verbose:
        print(f"🎯 Services with changes: {', '.join(sorted(valid_changed_services))}", file=sys.stderr)
    return sorted(list(valid_changed_services))


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Detect which services have changes")
    parser.add_argument('base_ref', help='Base git reference to compare against (e.g., origin/main)')
    parser.add_argument('--head-ref', default='HEAD', help='Head git reference (default: HEAD)')
    parser.add_argument('--services-dir', default='services', help='Services directory name (default: services)')
    parser.add_argument('--force-all', action='store_true', help='Return all services regardless of changes')
    parser.add_argument('--no-root-changes', action='store_true', help='Don\'t deploy all services on root changes')
    parser.add_argument('--verbose', '-v', action='store_true', help='Print debug information to stderr')
    parser.add_argument('--output-format', choices=['list', 'space-separated', 'json'], default='space-separated',
                       help='Output format (default: space-separated)')
    
    args = parser.parse_args()
    
    try:
        changed_services = detect_changes(
            base_ref=args.base_ref,
            head_ref=args.head_ref,
            services_dir_name=args.services_dir,
            force_all=args.force_all,
            include_root_changes=not args.no_root_changes,
            verbose=args.verbose
        )
        
        if not changed_services:
            if args.verbose:
                print("📋 No services to deploy", file=sys.stderr)
            sys.exit(0)
        
        # Output in requested format
        if args.output_format == 'list':
            for service in changed_services:
                print(service)
        elif args.output_format == 'space-separated':
            print(' '.join(changed_services))
        elif args.output_format == 'json':
            import json
            print(json.dumps(changed_services))
        
    except Exception as e:
        print(f"❌ Error detecting changes: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main() 