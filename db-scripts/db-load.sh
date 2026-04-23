#!/bin/bash
#
# Load PostgreSQL database from dump
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

echo "=== PostgreSQL Database Restore ==="
echo "Host: ${DB_HOST}"
echo "Database: ${DB_NAME}"
echo "User: ${DB_USER}"
echo ""

# Check if dump file is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <dump_file.sql|dump_file.sql.gz>"
    echo ""
    echo "Available backups:"
    if [ -d "./backups" ]; then
        ls -lh ./backups/*.sql ./backups/*.sql.gz 2>/dev/null | awk '{print "  " $9 " (" $5 ")"}'
    else
        echo "  No backups directory found."
    fi
    exit 1
fi

DUMP_FILE="$1"

# Check if file exists
if [ ! -f "${DUMP_FILE}" ]; then
    echo "✗ Error: File '${DUMP_FILE}' not found."
    exit 1
fi

echo "Dump file: ${DUMP_FILE}"
echo ""

# Export password to avoid prompt
export PGPASSWORD="${DB_PASSWORD}"

# Check if file is compressed
if [[ "${DUMP_FILE}" == *.gz ]]; then
    echo "Detected compressed file, will decompress on-the-fly..."
    IS_COMPRESSED=true
else
    IS_COMPRESSED=false
fi

# Confirmation prompt
read -p "This will overwrite database '${DB_NAME}'. Continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Database restore cancelled."
    exit 0
fi

echo "Restoring database..."

# Drop existing database and recreate
echo "Dropping existing database..."
psql -h "${DB_HOST}" -U "${DB_USER}" -d postgres -c "DROP DATABASE IF EXISTS ${DB_NAME};"

echo "Creating new database..."
if ! psql -h "${DB_HOST}" -U "${DB_USER}" -d postgres -c "CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};"; then
    echo "✗ Failed to create database."
    exit 1
fi

# Restore from dump
echo "Restoring from dump file..."
if [ "$IS_COMPRESSED" = true ]; then
    if gunzip -c "${DUMP_FILE}" | psql -h "${DB_HOST}" -U "${DB_USER}" -d "${DB_NAME}"; then
        echo "✓ Database restored successfully from compressed dump."
    else
        echo "✗ Failed to restore database from compressed dump."
        exit 1
    fi
else
    if psql -h "${DB_HOST}" -U "${DB_USER}" -d "${DB_NAME}" -f "${DUMP_FILE}"; then
        echo "✓ Database restored successfully."
    else
        echo "✗ Failed to restore database."
        exit 1
    fi
fi

# Unset password
unset PGPASSWORD

echo "Done."
