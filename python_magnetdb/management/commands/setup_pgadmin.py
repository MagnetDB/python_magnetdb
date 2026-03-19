#!/usr/bin/env python3
"""
Manage pgAdmin servers.json configuration.

This script allows you to add, remove, list, and generate pgAdmin server
configurations using environment variables from docker-compose.

Commands:
    add       - Add a new server to servers.json
    remove    - Remove a server from servers.json
    list      - List all configured servers
    generate  - Generate initial servers.json (overwrites existing)

Environment Variables:
    POSTGRES_HOST: PostgreSQL server hostname (default: magnetdb-postgres)
    POSTGRES_PORT: PostgreSQL server port (default: 5432)
    POSTGRES_DB: PostgreSQL database name (default: postgres)
    POSTGRES_USER: PostgreSQL username (default: magnetdb)
    POSTGRES_PASSWORD: PostgreSQL password (default: magnetdb)
    PGADMIN_SERVER_NAME: Display name in pgAdmin (default: magnetdb)
    PGADMIN_CONFIG_OUTPUT: Output path for servers.json (default: /var/lib/pgadmin/servers.json)

Usage:
    python setup_pgadmin.py                      # Generate initial config (default)
    python setup_pgadmin.py add                  # Add server from env vars
    python setup_pgadmin.py add --name myserver --host db.example.com --port 5433
    python setup_pgadmin.py remove myserver      # Remove by name
    python setup_pgadmin.py remove --id 2        # Remove by ID
    python setup_pgadmin.py list                 # List all servers
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, Optional


class PgAdminServerManager:
    """Manage pgAdmin server configurations."""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the server manager.

        Args:
            config_path: Path to servers.json file
        """
        if config_path is None:
            config_path = os.getenv("PGADMIN_CONFIG_OUTPUT", "/var/lib/pgadmin/servers.json")

        self.config_path = Path(config_path)
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """
        Load existing servers.json or create empty structure.

        Returns:
            dict: Server configuration
        """
        if self.config_path.exists():
            try:
                with self.config_path.open("r") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print(f"⚠ Warning: Invalid JSON in {self.config_path}, creating new config")
                return {"Servers": {}}
        else:
            return {"Servers": {}}

    def _save_config(self) -> None:
        """Save configuration to servers.json file."""
        # Create parent directories if they don't exist
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # Write configuration file
        with self.config_path.open("w") as f:
            json.dump(self.config, f, indent=2)

    def _get_next_server_id(self) -> int:
        """
        Get the next available server ID.

        Returns:
            int: Next server ID
        """
        if not self.config.get("Servers"):
            return 1

        existing_ids = [int(sid) for sid in self.config["Servers"].keys()]
        return max(existing_ids) + 1 if existing_ids else 1

    def _create_server_config(
        self,
        name: str,
        host: str,
        port: int,
        database: str,
        username: str,
        password: str,
        group: str = "Servers",
        ssl_mode: str = "prefer",
        comment: str = "",
    ) -> Dict:
        """
        Create a server configuration dictionary.

        Args:
            name: Server display name
            host: Database host
            port: Database port
            database: Maintenance database
            username: Database username
            password: Database password
            group: Server group name
            ssl_mode: SSL mode (prefer, require, disable, etc.)
            comment: Optional comment

        Returns:
            dict: Server configuration
        """
        return {
            "Name": name,
            "Group": group,
            "Host": host,
            "Port": port,
            "MaintenanceDB": database,
            "Username": username,
            "Password": password,
            "SSLMode": ssl_mode,
            "PassFile": "",
            "Comment": comment or f"Auto-configured {name} database server",
        }

    def add_server(
        self,
        name: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        database: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        group: str = "Servers",
        ssl_mode: str = "prefer",
    ) -> int:
        """
        Add a new server to the configuration.

        Args:
            name: Server name (from env PGADMIN_SERVER_NAME if not provided)
            host: Database host (from env POSTGRES_HOST if not provided)
            port: Database port (from env POSTGRES_PORT if not provided)
            database: Database name (from env POSTGRES_DB if not provided)
            username: Username (from env POSTGRES_USER if not provided)
            password: Password (from env POSTGRES_PASSWORD if not provided)
            group: Server group
            ssl_mode: SSL mode

        Returns:
            int: Server ID
        """
        # Use environment variables as defaults
        name = name or os.getenv("PGADMIN_SERVER_NAME", "magnetdb")
        host = host or os.getenv("POSTGRES_HOST", "magnetdb-postgres")
        port = port or int(os.getenv("POSTGRES_PORT", "5432"))
        database = database or os.getenv("POSTGRES_DB", "postgres")
        username = username or os.getenv("POSTGRES_USER", "magnetdb")
        password = password or os.getenv("POSTGRES_PASSWORD", "magnetdb")

        # Check if server with same name already exists
        for server_id, server_config in self.config.get("Servers", {}).items():
            if server_config.get("Name") == name:
                print(f"⚠ Warning: Server '{name}' already exists with ID {server_id}")
                return int(server_id)

        # Get next available ID
        server_id = self._get_next_server_id()

        # Create server configuration
        server_config = self._create_server_config(
            name=name,
            host=host,
            port=port,
            database=database,
            username=username,
            password=password,
            group=group,
            ssl_mode=ssl_mode,
        )

        # Add to configuration
        if "Servers" not in self.config:
            self.config["Servers"] = {}

        self.config["Servers"][str(server_id)] = server_config
        self._save_config()

        print(f"✓ Added server '{name}' with ID {server_id}")
        print(f"  Host: {host}:{port}")
        print(f"  Database: {database}")
        print(f"  Username: {username}")

        return server_id

    def remove_server(self, name: Optional[str] = None, server_id: Optional[int] = None) -> bool:
        """
        Remove a server from the configuration.

        Args:
            name: Server name to remove
            server_id: Server ID to remove

        Returns:
            bool: True if server was removed, False otherwise
        """
        if not name and not server_id:
            print("✗ Error: Must specify either --name or --id")
            return False

        # Find server by name
        if name:
            for sid, config in self.config.get("Servers", {}).items():
                if config.get("Name") == name:
                    server_id = int(sid)
                    break
            else:
                print(f"✗ Error: Server '{name}' not found")
                return False

        # Remove server by ID
        server_id_str = str(server_id)
        if server_id_str in self.config.get("Servers", {}):
            server_name = self.config["Servers"][server_id_str].get("Name")
            del self.config["Servers"][server_id_str]
            self._save_config()
            print(f"✓ Removed server '{server_name}' (ID: {server_id})")
            return True
        else:
            print(f"✗ Error: Server ID {server_id} not found")
            return False

    def list_servers(self) -> None:
        """List all configured servers."""
        servers = self.config.get("Servers", {})

        if not servers:
            print("No servers configured")
            return

        print(f"\nConfigured servers in {self.config_path}:")
        print("-" * 80)

        for server_id, config in sorted(servers.items(), key=lambda x: int(x[0])):
            print(f"ID {server_id}: {config.get('Name')}")
            print(f"  Host: {config.get('Host')}:{config.get('Port')}")
            print(f"  Database: {config.get('MaintenanceDB')}")
            print(f"  Username: {config.get('Username')}")
            print(f"  Group: {config.get('Group')}")
            if config.get("Comment"):
                print(f"  Comment: {config.get('Comment')}")
            print()

    def generate_initial_config(self) -> None:
        """Generate initial configuration, overwriting any existing config."""
        # Reset configuration
        self.config = {"Servers": {}}

        # Add default server from environment variables
        self.add_server()

        print(f"✓ Generated initial configuration at {self.config_path}")


def main():
    """Main entry point for pgAdmin server management."""
    parser = argparse.ArgumentParser(
        description="Manage pgAdmin server configurations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Generate initial config
  %(prog)s add                                # Add server from env vars
  %(prog)s add --name prod --host db.prod.com --port 5433 --user admin --password secret
  %(prog)s remove myserver                    # Remove by name
  %(prog)s remove --id 2                      # Remove by ID
  %(prog)s list                               # List all servers
        """,
    )

    parser.add_argument(
        "command",
        nargs="?",
        default="generate",
        choices=["add", "remove", "list", "generate"],
        help="Command to execute (default: generate)",
    )

    parser.add_argument("target", nargs="?", help="Server name (for remove command)")

    parser.add_argument("--id", type=int, help="Server ID (for remove command)")

    parser.add_argument("--name", help="Server name")

    parser.add_argument("--host", help="Database host")

    parser.add_argument("--port", type=int, help="Database port")

    parser.add_argument("--database", "--db", help="Maintenance database name")

    parser.add_argument("--user", "--username", help="Database username")

    parser.add_argument("--password", help="Database password")

    parser.add_argument("--group", default="Servers", help="Server group (default: Servers)")

    parser.add_argument(
        "--ssl-mode",
        default="prefer",
        choices=["disable", "allow", "prefer", "require", "verify-ca", "verify-full"],
        help="SSL mode (default: prefer)",
    )

    parser.add_argument("--config", help="Path to servers.json file")

    args = parser.parse_args()

    try:
        manager = PgAdminServerManager(args.config)

        if args.command == "generate":
            manager.generate_initial_config()

        elif args.command == "add":
            manager.add_server(
                name=args.name,
                host=args.host,
                port=args.port,
                database=args.database,
                username=args.user,
                password=args.password,
                group=args.group,
                ssl_mode=args.ssl_mode,
            )

        elif args.command == "remove":
            # Use target positional argument if provided, otherwise use --id or --name
            name = args.target if args.target else args.name
            manager.remove_server(name=name, server_id=args.id)

        elif args.command == "list":
            manager.list_servers()

    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
