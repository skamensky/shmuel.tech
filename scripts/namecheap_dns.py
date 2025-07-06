#!/usr/bin/env python3
"""
Namecheap DNS management for shmuel-tech monorepo.
Handles DNS operations via Namecheap API through DNS proxy.
"""

import os
import requests
import time
from typing import List, Dict, Any, Tuple, Optional

# Import shared utilities
from .utils import load_project_env

# Load environment variables
load_project_env()

# DNS Proxy configuration
NAMECHEAP_DOMAIN = "shmuel.tech"

def get_dns_proxy_config() -> Tuple[str, str, str, str, str]:
    """Get DNS proxy configuration from environment variables."""
    proxy_url = os.getenv('DNS_PROXY_URL', 'https://shmuel-tech-dns-proxy.fly.dev')
    proxy_auth = os.getenv('DNS_PROXY_AUTH_TOKEN')
    api_user = os.getenv('NAMECHEAP_API_USER')
    api_key = os.getenv('NAMECHEAP_API_KEY')
    client_ip = os.getenv('NAMECHEAP_CLIENT_IP')
    
    if not all([proxy_auth, api_user, api_key, client_ip]):
        raise ValueError(
            "Missing DNS proxy credentials. Please set:\n"
            "- DNS_PROXY_AUTH_TOKEN\n"
            "- NAMECHEAP_API_USER\n"
            "- NAMECHEAP_API_KEY\n"
            "- NAMECHEAP_CLIENT_IP"
        )
    
    return proxy_url, proxy_auth, api_user, api_key, client_ip

def get_namecheap_dns_records(domain: str, silent: bool = False) -> List[Dict[str, str]]:
    """Get current DNS records from Namecheap via proxy."""
    if not silent:
        print(f"📋 Fetching DNS records for domain '{domain}' via proxy...")
    
    proxy_url, proxy_auth, api_user, api_key, client_ip = get_dns_proxy_config()
    
    payload = {
        "api_user": api_user,
        "api_key": api_key,
        "client_ip": client_ip,
        "command": "namecheap.domains.dns.getHosts",
        "data": {
            "domain": domain
        },
        "proxy_auth": proxy_auth
    }
    
    try:
        response = requests.post(f"{proxy_url}/api/dns", json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        if not result.get('success'):
            raise Exception(f"DNS proxy error: {result.get('error', 'Unknown error')}")
        
        records = result.get('data', [])
        
        if not silent:
            print(f"✅ Found {len(records)} DNS records")
        
        return records
        
    except Exception as e:
        if not silent:
            print(f"❌ Failed to fetch DNS records: {e}")
        raise

def update_namecheap_dns_records(domain: str, records: List[Dict[str, str]], silent: bool = False) -> bool:
    """Update DNS records in Namecheap via proxy."""
    if not silent:
        print(f"🔄 Updating DNS records for domain '{domain}' via proxy...")
        print(f"⚠️  This will replace ALL DNS records for {domain}")
        print(f"📝 Setting {len(records)} DNS records...")
    
    proxy_url, proxy_auth, api_user, api_key, client_ip = get_dns_proxy_config()
    
    # Prepare data for proxy
    data = {"domain": domain}
    
    # Add each record as parameters in the format expected by proxy
    for i, record in enumerate(records, 1):
        # Validate and normalize CNAME records
        address = record['Address']
        if record['Type'] == 'CNAME':
            # Remove any protocol prefixes that shouldn't be in CNAME records
            if address.startswith(('http://', 'https://')):
                address = address.split('://', 1)[1]
            # Ensure CNAME records are fully qualified (end with dot)
            if not address.endswith('.'):
                address = address + '.'
        
        data[f'HostName{i}'] = record['Name']
        data[f'RecordType{i}'] = record['Type']
        data[f'Address{i}'] = address
        data[f'TTL{i}'] = record['TTL']
        if record['Type'] == 'MX':
            data[f'MXPref{i}'] = record['MXPref']
    
    payload = {
        "api_user": api_user,
        "api_key": api_key,
        "client_ip": client_ip,
        "command": "namecheap.domains.dns.setHosts",
        "data": data,
        "proxy_auth": proxy_auth,
        "sandbox": False
    }
    
    try:
        response = requests.post(f"{proxy_url}/api/dns", json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        if not result.get('success'):
            raise Exception(f"DNS proxy error: {result.get('error', 'Unknown error')}")
        
        if not silent:
            records_updated = result.get('data', {}).get('recordsUpdated', len(records))
            print(f"✅ DNS records updated successfully ({records_updated} records)")
        
        return True
            
    except Exception as e:
        if not silent:
            print(f"❌ Failed to update DNS records: {e}")
        raise

def get_fly_app_cname(app_name: str, silent: bool = False) -> Optional[str]:
    """Get the CNAME target for a Fly.io app."""
    if not silent:
        print(f"🔍 Getting CNAME target for app '{app_name}'...")
    
    # The CNAME target is typically appname.fly.dev. (note the trailing dot for FQDN)
    return f"{app_name}.fly.dev."

def prepare_dns_changes_for_services(service_configs: List[Dict[str, str]], silent: bool = False) -> Tuple[List[Dict[str, str]], bool]:
    """
    Prepare DNS changes for multiple services in bulk.
    
    Args:
        service_configs: List of dicts with 'service_name' and 'app_name' keys
        silent: Whether to suppress output
    
    Returns:
        Tuple of (DNS records ready for bulk update, whether changes were made)
    """
    if not silent:
        print(f"🔄 Preparing DNS changes for {len(service_configs)} services...")
    
    # Get current DNS records
    try:
        current_records = get_namecheap_dns_records(NAMECHEAP_DOMAIN, silent=silent)
    except Exception as e:
        raise Exception(f"Failed to fetch current DNS records: {str(e)}")
    
    # Create a copy to work with
    updated_records = current_records.copy()
    
    # Process each service
    changes_made = False
    for config in service_configs:
        service_name = config['service_name']
        app_name = config['app_name']
        
        # Determine the hostname
        if service_name == "main-site":
            hostname = "@"  # Root domain
            www_hostname = "www"  # www subdomain
        else:
            hostname = service_name
            www_hostname = f"www.{service_name}"
        
        # Get the CNAME target from Fly
        cname_target = get_fly_app_cname(app_name, silent=True)
        if not cname_target:
            if not silent:
                print(f"⚠️  Could not determine CNAME target for app '{app_name}', skipping...")
            continue
        
        # Update or add the main record for this service
        record_updated = False
        for record in updated_records:
            if record['Name'] == hostname and record['Type'] == 'CNAME':
                if record['Address'] != cname_target:
                    if not silent:
                        print(f"🔄 Updating DNS: {hostname} -> {cname_target}")
                    record['Address'] = cname_target
                    changes_made = True
                record_updated = True
                break
        
        # If main record doesn't exist, add it
        if not record_updated:
            if not silent:
                print(f"➕ Adding DNS: {hostname} -> {cname_target}")
            new_record = {
                'Name': hostname,
                'Type': 'CNAME',
                'Address': cname_target,
                'TTL': '1800',
                'MXPref': '10'
            }
            updated_records.append(new_record)
            changes_made = True
        
        # Update or add the www record for this service
        www_record_updated = False
        for record in updated_records:
            if record['Name'] == www_hostname and record['Type'] == 'CNAME':
                if record['Address'] != cname_target:
                    if not silent:
                        print(f"🔄 Updating DNS: {www_hostname} -> {cname_target}")
                    record['Address'] = cname_target
                    changes_made = True
                www_record_updated = True
                break
        
        # If www record doesn't exist, add it
        if not www_record_updated:
            if not silent:
                print(f"➕ Adding DNS: {www_hostname} -> {cname_target}")
            new_www_record = {
                'Name': www_hostname,
                'Type': 'CNAME',
                'Address': cname_target,
                'TTL': '1800',
                'MXPref': '10'
            }
            updated_records.append(new_www_record)
            changes_made = True
    
    if not changes_made:
        if not silent:
            print("✅ No DNS changes needed")
        return current_records, False
    
    if not silent:
        print(f"✅ Prepared DNS changes for bulk update")
    
    return updated_records, True

def bulk_update_dns_for_services(service_configs: List[Dict[str, str]], silent: bool = False) -> Tuple[bool, Optional[str]]:
    """
    Update DNS records for multiple services in a single bulk request.
    
    Args:
        service_configs: List of dicts with 'service_name' and 'app_name' keys
        silent: Whether to suppress output
    
    Returns:
        Tuple of (success, error_message)
    """
    try:
        if not silent:
            print(f"🌐 Starting bulk DNS update for {len(service_configs)} services...")
        
        # Prepare all DNS changes
        updated_records, changes_made = prepare_dns_changes_for_services(service_configs, silent=silent)
        
        # Skip update if no changes are needed
        if not changes_made:
            if not silent:
                print("✅ Bulk DNS update completed - no changes needed")
            return True, None
        
        # Perform single bulk update
        update_namecheap_dns_records(NAMECHEAP_DOMAIN, updated_records, silent=silent)
        
        if not silent:
            print("✅ Bulk DNS update completed successfully")
        
        return True, None
        
    except Exception as e:
        error_msg = f"Bulk DNS update failed: {str(e)}"
        if not silent:
            print(f"❌ {error_msg}")
        return False, error_msg

def wait_for_certificate(app_name: str, domain: str, timeout: int = 300, silent: bool = False) -> bool:
    """Wait for Fly.io certificate to be issued and verified."""
    if not silent:
        print(f"⏳ Waiting for certificate for '{domain}' in app '{app_name}'...")
    
    from .utils import run_command
    
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        result = run_command(['flyctl', 'certs', 'show', domain, '--app', app_name], check=False, silent=True)
        
        if result.returncode == 0:
            # Parse the certificate status
            output = result.stdout.lower()
            if 'verified' in output and 'issued' in output:
                if not silent:
                    print(f"✅ Certificate ready for '{domain}'")
                return True
        
        if not silent:
            print(f"⏳ Certificate not ready yet, waiting... ({int(time.time() - start_time)}s)")
        
        time.sleep(10)
    
    if not silent:
        print(f"⚠️  Certificate for '{domain}' not ready after {timeout}s")
    return False

 