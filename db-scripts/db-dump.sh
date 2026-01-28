#!/bin/bash
#
# Dump PostgreSQL database for backup
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

# Backup directory
BACKUP_DIR="${BACKUP_DIR:-./backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/${DB_NAME}_${TIMESTAMP}.sql"

echo "=== PostgreSQL Database Backup ==="
echo "Host: ${DB_HOST}"
echo "Database: ${DB_NAME}"
echo "User: ${DB_USER}"
echo "Backup file: ${BACKUP_FILE}"
echo ""

# Create backup directory if it doesn't exist
mkdir -p "${BACKUP_DIR}"

# Export password to avoid prompt
export PGPASSWORD="${DB_PASSWORD}"

echo "Creating backup..."

# Dump database
if pg_dump -h "${DB_HOST}" -U "${DB_USER}" -d "${DB_NAME}" -F p -f "${BACKUP_FILE}"; then
    echo "✓ Database backup created successfully."
    echo "  File: ${BACKUP_FILE}"
    
    # Show file size
    FILE_SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
    echo "  Size: ${FILE_SIZE}"
    
    # Optional: compress backup
    read -p "Compress backup with gzip? (y/n): " compress
    if [ "$compress" = "y" ]; then
        gzip "${BACKUP_FILE}"
        echo "✓ Backup compressed: ${BACKUP_FILE}.gz"
        COMPRESSED_SIZE=$(du -h "${BACKUP_FILE}.gz" | cut -f1)
        echo "  Compressed size: ${COMPRESSED_SIZE}"
    fi
else
    echo "✗ Failed to create database backup."
    exit 1
fi

# Unset password
unset PGPASSWORD

echo "Done."
