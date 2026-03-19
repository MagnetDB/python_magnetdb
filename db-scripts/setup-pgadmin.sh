#!/bin/bash
# Setup script to configure pgAdmin server connections
# Run this inside the pgadmin container to auto-configure database servers

set -e

COMMAND="${1:-generate}"

case "$COMMAND" in
    generate)
        echo "Generating initial pgAdmin server configuration..."
        python3 /setup_pgadmin.py generate
        ;;
    add)
        echo "Adding pgAdmin server..."
        shift
        python3 /setup_pgadmin.py add "$@"
        ;;
    remove)
        echo "Removing pgAdmin server..."
        shift
        python3 /setup_pgadmin.py remove "$@"
        ;;
    list)
        echo "Listing pgAdmin servers..."
        python3 /setup_pgadmin.py list
        ;;
    help|--help|-h)
        echo "Usage: $0 [command] [options]"
        echo ""
        echo "Commands:"
        echo "  generate      Generate initial configuration (default)"
        echo "  add           Add a new server"
        echo "  remove NAME   Remove a server by name"
        echo "  list          List all configured servers"
        echo ""
        echo "Examples:"
        echo "  $0                                    # Generate initial config"
        echo "  $0 add                                # Add server from env vars"
        echo "  $0 add --name prod --host db.prod.com"
        echo "  $0 remove myserver"
        echo "  $0 list"
        exit 0
        ;;
    *)
        echo "Unknown command: $COMMAND"
        echo "Run '$0 help' for usage information"
        exit 1
        ;;
esac

echo "pgAdmin setup complete!"
echo "Note: Restart pgAdmin to load the new configuration."

