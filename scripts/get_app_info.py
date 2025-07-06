#!/usr/bin/env python3
"""
Get Fly.io app information script for shmuel-tech monorepo.
Fetches and displays app status information from Fly.io in table or JSON format.
"""

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from tabulate import tabulate

# Import shared utilities
from .utils import load_project_env, check_fly_auth, run_command

# Load environment variables
load_project_env()


@dataclass
class Organization:
    """Organization information."""
    id: str
    internal_numeric_id: str
    name: str
    slug: str
    raw_slug: str
    paid_plan: bool


@dataclass
class ImageRef:
    """Docker image reference."""
    registry: str
    repository: str
    tag: str
    digest: str


@dataclass
class GuestConfig:
    """Guest configuration for machine."""
    cpu_kind: str
    cpus: int
    memory_mb: int


@dataclass
class ServicePort:
    """Service port configuration."""
    port: int
    handlers: List[str]
    force_https: Optional[bool] = None


@dataclass
class ServiceCheck:
    """Service health check configuration."""
    type: str
    interval: str
    timeout: str
    grace_period: str
    method: str
    path: str


@dataclass
class ServiceConfig:
    """Service configuration."""
    protocol: str
    internal_port: int
    autostop: bool
    autostart: bool
    min_machines_running: int
    ports: List[ServicePort]
    checks: List[ServiceCheck]
    force_instance_key: Optional[str] = None


@dataclass
class RestartConfig:
    """Restart policy configuration."""
    policy: str
    max_retries: int


@dataclass
class StopConfig:
    """Stop signal configuration."""
    signal: str


@dataclass
class MachineConfig:
    """Machine configuration."""
    env: Dict[str, str]
    init: Dict[str, Any]
    guest: GuestConfig
    metadata: Dict[str, str]
    services: List[ServiceConfig]
    image: str
    restart: RestartConfig
    stop_config: StopConfig


@dataclass
class MachineEvent:
    """Machine event."""
    type: str
    status: str
    request: Dict[str, Any]
    source: str
    timestamp: int


@dataclass
class MachineCheck:
    """Machine health check result."""
    name: str
    status: str
    output: str
    updated_at: str


@dataclass
class Machine:
    """Fly.io machine information."""
    id: str
    name: str
    state: str
    region: str
    image_ref: ImageRef
    instance_id: str
    private_ip: str
    created_at: str
    updated_at: str
    config: MachineConfig
    events: List[MachineEvent]
    checks: List[MachineCheck]
    host_status: str


@dataclass
class AppInfo:
    """Complete Fly.io app information."""
    app_url: str
    deployed: bool
    hostname: str
    id: str
    name: str
    organization: Organization
    platform_version: str
    status: str
    version: int
    machines: List[Machine] = field(default_factory=list)


# run_command function moved to shared utils


def parse_service_port(port_data: Dict[str, Any]) -> ServicePort:
    """Parse service port configuration."""
    return ServicePort(
        port=port_data["port"],
        handlers=port_data["handlers"],
        force_https=port_data.get("force_https")
    )


def parse_service_check(check_data: Dict[str, Any]) -> ServiceCheck:
    """Parse service health check configuration."""
    return ServiceCheck(
        type=check_data["type"],
        interval=check_data["interval"],
        timeout=check_data["timeout"],
        grace_period=check_data["grace_period"],
        method=check_data["method"],
        path=check_data["path"]
    )


def parse_service_config(service_data: Dict[str, Any]) -> ServiceConfig:
    """Parse service configuration."""
    return ServiceConfig(
        protocol=service_data["protocol"],
        internal_port=service_data["internal_port"],
        autostop=service_data["autostop"],
        autostart=service_data["autostart"],
        min_machines_running=service_data["min_machines_running"],
        ports=[parse_service_port(p) for p in service_data["ports"]],
        checks=[parse_service_check(c) for c in service_data["checks"]],
        force_instance_key=service_data.get("force_instance_key")
    )


def parse_machine_config(config_data: Dict[str, Any]) -> MachineConfig:
    """Parse machine configuration."""
    return MachineConfig(
        env=config_data["env"],
        init=config_data["init"],
        guest=GuestConfig(
            cpu_kind=config_data["guest"]["cpu_kind"],
            cpus=config_data["guest"]["cpus"],
            memory_mb=config_data["guest"]["memory_mb"]
        ),
        metadata=config_data["metadata"],
        services=[parse_service_config(s) for s in config_data["services"]],
        image=config_data["image"],
        restart=RestartConfig(
            policy=config_data["restart"]["policy"],
            max_retries=config_data["restart"]["max_retries"]
        ),
        stop_config=StopConfig(signal=config_data["stop_config"]["signal"])
    )


def parse_machine(machine_data: Dict[str, Any]) -> Machine:
    """Parse machine information."""
    return Machine(
        id=machine_data["id"],
        name=machine_data["name"],
        state=machine_data["state"],
        region=machine_data["region"],
        image_ref=ImageRef(
            registry=machine_data["image_ref"]["registry"],
            repository=machine_data["image_ref"]["repository"],
            tag=machine_data["image_ref"]["tag"],
            digest=machine_data["image_ref"]["digest"]
        ),
        instance_id=machine_data["instance_id"],
        private_ip=machine_data["private_ip"],
        created_at=machine_data["created_at"],
        updated_at=machine_data["updated_at"],
        config=parse_machine_config(machine_data["config"]),
        events=[
            MachineEvent(
                type=event["type"],
                status=event["status"],
                request=event.get("request", {}),  # Use .get() to handle missing request field
                source=event["source"],
                timestamp=event["timestamp"]
            )
            for event in machine_data["events"]
        ],
        checks=[
            MachineCheck(
                name=check["name"],
                status=check["status"],
                output=check["output"],
                updated_at=check["updated_at"]
            )
            for check in machine_data["checks"]
        ],
        host_status=machine_data["host_status"]
    )


def parse_app_info(data: Dict[str, Any]) -> AppInfo:
    """Parse complete app information from Fly.io JSON response."""
    return AppInfo(
        app_url=data["AppURL"],
        deployed=data["Deployed"],
        hostname=data["Hostname"],
        id=data["ID"],
        name=data["Name"],
        organization=Organization(
            id=data["Organization"]["ID"],
            internal_numeric_id=data["Organization"]["InternalNumericID"],
            name=data["Organization"]["Name"],
            slug=data["Organization"]["Slug"],
            raw_slug=data["Organization"]["RawSlug"],
            paid_plan=data["Organization"]["PaidPlan"]
        ),
        platform_version=data["PlatformVersion"],
        status=data["Status"],
        version=data["Version"],
        machines=[parse_machine(m) for m in data["Machines"]]
    )


def get_app_info(app_name: str) -> AppInfo:
    """Get app information from Fly.io."""
    print(f"📱 Getting app information for: {app_name}")
    
    result = run_command(['flyctl', 'status', '--json', '--app', app_name], silent=True)
    
    try:
        data = json.loads(result.stdout)
        return parse_app_info(data)
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse JSON response: {e}", file=sys.stderr)
        sys.exit(1)


def format_datetime(dt_str: str) -> str:
    """Format datetime string for display."""
    try:
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M:%S UTC')
    except ValueError:
        return dt_str


def format_timestamp(timestamp: int) -> str:
    """Format timestamp for display."""
    try:
        dt = datetime.fromtimestamp(timestamp / 1000)  # Convert milliseconds to seconds
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except (ValueError, OSError):
        return str(timestamp)


def display_table_format(app_info: AppInfo) -> None:
    """Display app information in table format."""
    print(f"\n🚀 Application Information: {app_info.name}")
    print("=" * 60)
    
    # Basic app info
    app_table = [
        ["App ID", app_info.id],
        ["Name", app_info.name],
        ["Status", app_info.status],
        ["Deployed", "✅ Yes" if app_info.deployed else "❌ No"],
        ["Hostname", app_info.hostname],
        ["App URL", app_info.app_url],
        ["Platform Version", app_info.platform_version],
        ["Version", app_info.version],
        ["Organization", app_info.organization.slug],
        ["Paid Plan", "✅ Yes" if app_info.organization.paid_plan else "❌ No"],
    ]
    
    print(tabulate(app_table, headers=["Property", "Value"], tablefmt="grid"))
    
    # Machines summary
    print(f"\n🖥️  Machines ({len(app_info.machines)} total)")
    print("=" * 60)
    
    if app_info.machines:
        machines_table = []
        for machine in app_info.machines:
            # Get health status
            health_status = "❓ Unknown"
            if machine.checks:
                latest_check = machine.checks[0]  # Assuming first check is most recent
                if latest_check.status == "passing":
                    health_status = "✅ Healthy"
                elif latest_check.status == "failing":
                    health_status = "❌ Unhealthy"
                else:
                    health_status = f"⚠️ {latest_check.status.title()}"
            
            # Get resources
            resources = f"{machine.config.guest.cpus} CPU, {machine.config.guest.memory_mb}MB RAM"
            
            # Get environment variables
            env_vars = ", ".join(f"{k}={v}" for k, v in machine.config.env.items())
            if not env_vars:
                env_vars = "No environment variables"
            
            machines_table.append([
                machine.id[:12] + "...",  # Truncate ID
                machine.name,
                machine.state,
                machine.region,
                resources,
                health_status,
                format_datetime(machine.created_at),
                env_vars
            ])
        
        print(tabulate(
            machines_table,
            headers=["Machine ID", "Name", "State", "Region", "Resources", "Health", "Created", "Environment"],
            tablefmt="grid"
        ))
        
        # Service configuration
        print(f"\n🔧 Service Configuration")
        print("=" * 60)
        
        if app_info.machines and app_info.machines[0].config.services:
            service = app_info.machines[0].config.services[0]  # First service
            service_table = [
                ["Internal Port", service.internal_port],
                ["Protocol", service.protocol],
                ["Auto Start", "✅ Yes" if service.autostart else "❌ No"],
                ["Auto Stop", "✅ Yes" if service.autostop else "❌ No"],
                ["Min Machines", service.min_machines_running],
                ["External Ports", ", ".join(f"{p.port} ({', '.join(p.handlers)})" for p in service.ports)],
                ["Health Checks", f"{len(service.checks)} configured"],
            ]
            
            print(tabulate(service_table, headers=["Setting", "Value"], tablefmt="grid"))
    else:
        print("No machines found for this app.")


def display_json_format(app_info: AppInfo) -> None:
    """Display app information in JSON format."""
    # Convert dataclass to dict for JSON serialization
    def dataclass_to_dict(obj):
        if hasattr(obj, '__dict__'):
            return {k: dataclass_to_dict(v) for k, v in obj.__dict__.items()}
        elif isinstance(obj, list):
            return [dataclass_to_dict(item) for item in obj]
        else:
            return obj
    
    app_dict = dataclass_to_dict(app_info)
    print(json.dumps(app_dict, indent=2))


def get_services_dir() -> Path:
    """Get the services directory path."""
    project_root = Path(__file__).parent.parent
    return project_root / "services"


def get_app_name_from_service(service_name: str) -> str:
    """Convert service name to Fly.io app name."""
    return f"shmuel-tech-{service_name}"


def list_available_services() -> List[str]:
    """List all available services."""
    services_dir = get_services_dir()
    if not services_dir.exists():
        return []
    
    services = []
    for service_dir in services_dir.iterdir():
        if service_dir.is_dir() and not service_dir.name.startswith('.'):
            services.append(service_dir.name)
    
    return sorted(services)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Get Fly.io app information")
    parser.add_argument('app_name', nargs='?', help='App name or service name to get info for')
    parser.add_argument('--json', action='store_true', help='Output in JSON format')
    parser.add_argument('--service', '-s', help='Service name (will be converted to app name)')
    parser.add_argument('--list-services', action='store_true', help='List available services')
    
    args = parser.parse_args()
    
    if args.list_services:
        services = list_available_services()
        if services:
            print("📋 Available services:")
            for service in services:
                app_name = get_app_name_from_service(service)
                print(f"  - {service} (app: {app_name})")
        else:
            print("❌ No services found in services directory")
        return
    
    # Determine app name
    if args.service:
        app_name = get_app_name_from_service(args.service)
        print(f"🔄 Converting service '{args.service}' to app name '{app_name}'")
    elif args.app_name:
        app_name = args.app_name
    else:
        print("❌ Please provide either --service or an app name")
        print("💡 Use --list-services to see available services")
        sys.exit(1)
    
    # Check authentication before trying to get app info
    if not check_fly_auth():
        print("❌ Not authenticated with Fly.io. Run 'fly auth login' first.")
        sys.exit(1)
    
    try:
        app_info = get_app_info(app_name)
        
        if args.json:
            display_json_format(app_info)
        else:
            display_table_format(app_info)
            
    except Exception as e:
        print(f"❌ Failed to get app information: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main() 