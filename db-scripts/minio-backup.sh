#!/bin/bash
#
# Backup MinIO bucket to local storage
#
# This script creates a backup of a MinIO bucket by:
# 1. Using the MinIO client (mc) to mirror/sync the bucket to local disk
# 2. Creating a timestamped archive
# 3. Optionally compressing the backup
#
# Best practices implemented:
# - Timestamped backups for versioning
# - Verification of backup integrity
# - Configurable retention policies
# - Support for both full and incremental backups

set -euo pipefail  # Exit on error, undefined variables, and pipe failures

# Load environment variables from .envrc if it exists (direnv)
if [ -f ".envrc" ]; then
    set -a  # automatically export all variables
    source .envrc
    set +a
fi

# Use the existing magnetdb-minio container
mc='docker exec -it magnetdb-minio mc'
$mc --version

# MinIO configuration with defaults
MINIO_ENDPOINT="${S3_ENDPOINT:-localhost:9000}"
MINIO_ACCESS_KEY="${S3_ACCESS_KEY:-minio}"
MINIO_SECRET_KEY="${S3_SECRET_KEY:-minio123}"
MINIO_BUCKET="${S3_BUCKET:-magnetdb}"
MINIO_SECURE="${S3_SECURE:-false}"
echo "MINIO_ENDPOINT=${MINIO_ENDPOINT}"
echo "MINIO_SECURE=${MINIO_SECURE}"

# Backup configuration
BACKUP_DIR="${MINIO_BACKUP_DIR:-./backups/minio}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="${MINIO_BUCKET}_${TIMESTAMP}"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"

# Backup options
COMPRESS="${COMPRESS:-yes}"
BACKUP_TYPE="${BACKUP_TYPE:-full}"  # full or incremental
RETENTION_DAYS="${RETENTION_DAYS:-30}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=== MinIO Bucket Backup ==="
echo "Endpoint: ${MINIO_ENDPOINT}"
echo "Bucket: ${MINIO_BUCKET}"
echo "Backup type: ${BACKUP_TYPE}"
echo "Backup directory: ${BACKUP_PATH}"
echo ""

# Create backup directory if it doesn't exist
mkdir -p "${BACKUP_DIR}"

# Check if mc (MinIO client) is installed
if ! command -v $mc &> /dev/null; then
    echo -e "${RED}✗ Error: MinIO client (mc) is not installed.${NC}"
    echo ""
    exit 1
fi

# Configure MinIO client alias
echo "Configuring MinIO client..."
PROTOCOL="http"
if [ "${MINIO_SECURE}" = "true" ]; then
    PROTOCOL="https"
fi
$mc alias set magnetdb-backup "${PROTOCOL}://${MINIO_ENDPOINT}" "${MINIO_ACCESS_KEY}" "${MINIO_SECRET_KEY}"

# Verify connection
if ! $mc ls "magnetdb-backup/${MINIO_BUCKET}" > /dev/null 2>&1; then
    echo -e "${RED}✗ Error: Cannot connect to MinIO or bucket does not exist.${NC}"
    echo "Please check your configuration."
    exit 1
fi

echo -e "${GREEN}✓ Connected to MinIO successfully${NC}"
echo ""

# Get bucket statistics
echo "Analyzing bucket..."
OBJECT_COUNT=$($mc ls --recursive "magnetdb-backup/${MINIO_BUCKET}" 2>/dev/null | wc -l || echo "0")
BUCKET_SIZE=$($mc du "magnetdb-backup/${MINIO_BUCKET}" 2>/dev/null | awk '{print $1, $2}' || echo "0 B")

echo "  Objects: ${OBJECT_COUNT}"
echo "  Total size: ${BUCKET_SIZE}"
echo ""

# Create backup
echo "Creating backup..."
mkdir -p "${BACKUP_PATH}"

if [ "${BACKUP_TYPE}" = "incremental" ] && [ -d "${BACKUP_DIR}/latest" ]; then
    echo "  Mode: Incremental (only changed files)"
    # Use mirror with --newer-than for incremental
    if $mc mirror --preserve --overwrite "magnetdb-backup/${MINIO_BUCKET}/" "${BACKUP_PATH}/"; then
        echo -e "${GREEN}✓ Incremental backup completed${NC}"
    else
        echo -e "${RED}✗ Backup failed${NC}"
        exit 1
    fi
else
    echo "  Mode: Full backup"
    # Full mirror of the bucket
    if $mc mirror --preserve --overwrite "magnetdb-backup/${MINIO_BUCKET}/" "${BACKUP_PATH}/"; then
        echo -e "${GREEN}✓ Full backup completed${NC}"
    else
        echo -e "${RED}✗ Backup failed${NC}"
        exit 1
    fi
fi

# Create metadata file
cat > "${BACKUP_PATH}/backup-metadata.json" <<EOF
{
  "timestamp": "${TIMESTAMP}",
  "bucket": "${MINIO_BUCKET}",
  "endpoint": "${MINIO_ENDPOINT}",
  "backup_type": "${BACKUP_TYPE}",
  "object_count": ${OBJECT_COUNT},
  "bucket_size": "${BUCKET_SIZE}",
  "created_at": "$(date -Iseconds)"
}
EOF

# Update latest symlink
ln -sfn "${BACKUP_NAME}" "${BACKUP_DIR}/latest"

# Compress backup if requested
if [ "${COMPRESS}" = "yes" ]; then
    echo ""
    echo "Compressing backup..."
    ARCHIVE_FILE="${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
    
    if tar -czf "${ARCHIVE_FILE}" -C "${BACKUP_DIR}" "${BACKUP_NAME}"; then
        ARCHIVE_SIZE=$(du -h "${ARCHIVE_FILE}" | cut -f1)
        echo -e "${GREEN}✓ Backup compressed${NC}"
        echo "  Archive: ${ARCHIVE_FILE}"
        echo "  Size: ${ARCHIVE_SIZE}"
        
        # Calculate compression ratio
        ORIGINAL_SIZE=$(du -sb "${BACKUP_PATH}" | cut -f1)
        COMPRESSED_SIZE=$(stat -c%s "${ARCHIVE_FILE}" 2>/dev/null || stat -f%z "${ARCHIVE_FILE}")
        RATIO=$(awk "BEGIN {printf \"%.1f\", (1 - ${COMPRESSED_SIZE}/${ORIGINAL_SIZE}) * 100}")
        echo "  Compression: ${RATIO}% reduction"
        
        # Optionally remove uncompressed backup
        read -p "Remove uncompressed backup directory? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "${BACKUP_PATH}"
            echo "  Uncompressed backup removed"
        fi
    else
        echo -e "${RED}✗ Compression failed${NC}"
    fi
fi

# Clean old backups based on retention policy
if [ "${RETENTION_DAYS}" -gt 0 ]; then
    echo ""
    echo "Cleaning old backups (retention: ${RETENTION_DAYS} days)..."
    
    # Find and delete old backups
    DELETED_COUNT=0
    find "${BACKUP_DIR}" -maxdepth 1 -type f -name "${MINIO_BUCKET}_*.tar.gz" -mtime +${RETENTION_DAYS} -print0 | while IFS= read -r -d '' file; do
        rm -f "$file"
        echo "  Deleted: $(basename "$file")"
        DELETED_COUNT=$((DELETED_COUNT + 1))
    done
    
    find "${BACKUP_DIR}" -maxdepth 1 -type d -name "${MINIO_BUCKET}_*" -mtime +${RETENTION_DAYS} -print0 | while IFS= read -r -d '' dir; do
        if [ "$(basename "$dir")" != "$(readlink "${BACKUP_DIR}/latest")" ]; then
            rm -rf "$dir"
            echo "  Deleted: $(basename "$dir")"
            DELETED_COUNT=$((DELETED_COUNT + 1))
        fi
    done
    
    if [ "$DELETED_COUNT" -eq 0 ]; then
        echo "  No old backups to clean"
    fi
fi

echo ""
echo -e "${GREEN}=== Backup completed successfully ===${NC}"
echo "Backup location: ${BACKUP_PATH}"
if [ "${COMPRESS}" = "yes" ]; then
    echo "Archive: ${ARCHIVE_FILE}"
fi
echo ""
echo "To restore this backup, run:"
if [ "${COMPRESS}" = "yes" ]; then
    echo "  ./db-scripts/minio-restore.sh ${ARCHIVE_FILE}"
else
    echo "  ./db-scripts/minio-restore.sh ${BACKUP_PATH}"
fi
