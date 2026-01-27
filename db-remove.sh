#!/bin/bash
#
# Remove PostgreSQL database
#

# Load environment variables if settings.env exists
if [ -f "settings.env" ]; then
    source settings.env
fi

# Database configuration with defaults
DB_HOST="${DATABASE_HOST:-localhost}"
DB_NAME="${DATABASE_NAME:-magnetdb}"
DB_USER="${DATABASE_USER:-magnetdb}"
DB_PASSWORD="${DATABASE_PASSWORD:-magnetdb}"

echo "=== PostgreSQL Database Removal ==="
echo "Host: ${DB_HOST}"
echo "Database: ${DB_NAME}"
echo "User: ${DB_USER}"
echo ""

# Confirmation prompt
read -p "Are you sure you want to DROP database '${DB_NAME}'? This action cannot be undone! (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Database removal cancelled."
    exit 0
fi

echo "Dropping database '${DB_NAME}'..."

# Export password to avoid prompt
export PGPASSWORD="${DB_PASSWORD}"

# Drop database
if psql -h "${DB_HOST}" -U "${DB_USER}" -d postgres -c "DROP DATABASE IF EXISTS ${DB_NAME};"; then
    echo "✓ Database '${DB_NAME}' successfully dropped."
else
    echo "✗ Failed to drop database '${DB_NAME}'."
    exit 1
fi

# Unset password
unset PGPASSWORD

echo "Done."
