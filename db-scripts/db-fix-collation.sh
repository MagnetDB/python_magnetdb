#!/bin/bash
#
# Fix PostgreSQL collation version mismatch
# This script rebuilds all indexes and updates the collation version
#

# Load environment variables from .envrc if it exists (direnv)
if [ -f ".envrc" ]; then
    set -a  # automatically export all variables
    source .envrc
    set +a
fi

# Database configuration with defaults
DB_HOST="${DATABASE_HOST:-localhost}"
DB_NAME="${DATABASE_NAME:-magnetdb}"
DB_USER="${DATABASE_USER:-magnetdb}"
DB_PASSWORD="${DATABASE_PASSWORD:-magnetdb}"
DOCKER_CONTAINER="${POSTGRES_CONTAINER:-magnetdb-postgres}"

echo "=== PostgreSQL Collation Version Fix ==="
echo "Host: ${DB_HOST}"
echo "Database: ${DB_NAME}"
echo "User: ${DB_USER}"
echo ""

# Check if we're using Docker
USE_DOCKER=false
if command -v docker &> /dev/null; then
    if docker ps --format '{{.Names}}' | grep -q "^${DOCKER_CONTAINER}$"; then
        echo "✓ Detected Docker container: ${DOCKER_CONTAINER}"
        USE_DOCKER=true
    fi
fi

# Function to execute SQL commands
execute_sql() {
    local sql_command="$1"
    
    if [ "$USE_DOCKER" = true ]; then
        docker exec -i "${DOCKER_CONTAINER}" psql -U "${DB_USER}" -d "${DB_NAME}" -c "${sql_command}"
    else
        export PGPASSWORD="${DB_PASSWORD}"
        psql -h "${DB_HOST}" -U "${DB_USER}" -d "${DB_NAME}" -c "${sql_command}"
    fi
}

# Warning message
echo "⚠️  WARNING: This operation will:"
echo "   1. Reindex all database objects (may take time on large databases)"
echo "   2. Update the collation version to match your current system"
echo ""
echo "   The database should not be under heavy load during this operation."
echo ""

# Ask for confirmation
read -p "Do you want to proceed? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Operation cancelled."
    exit 0
fi

echo ""
echo "Step 1: Checking current collation version..."
execute_sql "SELECT datname, datcollversion FROM pg_database WHERE datname = '${DB_NAME}';"

echo ""
echo "Step 2: Reindexing database (this may take a while)..."
if execute_sql "REINDEX DATABASE ${DB_NAME};"; then
    echo "✓ Database reindexed successfully."
else
    echo "✗ Failed to reindex database."
    exit 1
fi

echo ""
echo "Step 3: Updating collation version..."
if execute_sql "ALTER DATABASE ${DB_NAME} REFRESH COLLATION VERSION;"; then
    echo "✓ Collation version updated successfully."
else
    echo "✗ Failed to update collation version."
    exit 1
fi

echo ""
echo "Step 4: Verifying new collation version..."
execute_sql "SELECT datname, datcollversion FROM pg_database WHERE datname = '${DB_NAME}';"

echo ""
echo "=== Collation fix completed successfully! ==="
echo ""
echo "The warning should no longer appear when connecting to the database."
