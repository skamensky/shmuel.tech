#!/usr/bin/env python3
"""
Shared utilities for shmuel-tech monorepo scripts.
Contains common functions for environment loading and Fly.io authentication.
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import List

# Load environment variables from .env file if it exists
from dotenv import load_dotenv


def load_project_env() -> None:
    """Load environment variables from .env file in project root."""
    # Load from root directory (../.env relative to this script)
    dotenv_path = Path(__file__).parent.parent / '.env'
    try:
        load_dotenv(dotenv_path, override=False)
    except Exception:
        if not os.environ.get('GITHUB_ACTIONS'):
            # we are not in ci, so we need to load the .env file
            print("\033[93m⚠️  Warning: .env file not found. Please create it in the root directory.\033[0m")


def run_command(cmd: List[str], check: bool = True, silent: bool = False, input_data: str = None) -> subprocess.CompletedProcess:
    """Run a command and return the result."""
    if not silent:
        print(f"🔧 Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd, 
            check=check, 
            capture_output=True, 
            text=True,
            input=input_data
        )
        if result.stdout and not silent:
            print(result.stdout.strip())
        return result
    except subprocess.CalledProcessError as e:
        if not silent:
            print(f"❌ Command failed: {e}")
            if e.stderr:
                print(f"Error: {e.stderr.strip()}")
        if check:
            sys.exit(1)
        return e


def check_fly_auth() -> bool:
    """Check if user is authenticated with Fly.io."""
    print("🔐 Checking Fly.io authentication...")
    result = run_command(['fly', 'auth', 'whoami'], check=False, silent=True)
    
    if result.returncode == 0:
        print("✅ Already authenticated with Fly.io")
        return True
        
    # Check if FLY_API_TOKEN exists
    token = os.environ.get('FLY_API_TOKEN')
    if not token:
        print("❌ Not authenticated with Fly.io and FLY_API_TOKEN environment variable not found")
        return False
        
    # Try to authenticate with token
    print("🔑 Attempting to authenticate using FLY_API_TOKEN...")
    auth_result = run_command(['fly', 'auth', 'token'], check=False, silent=True, input_data=token)
    
    if auth_result.returncode != 0:
        print(f"❌ Failed to authenticate with FLY_API_TOKEN: {auth_result.stderr.strip()}")
        return False
    
    print("✅ Successfully authenticated with Fly.io using API token")
    return True 