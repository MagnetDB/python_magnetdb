#!/bin/bash
#
# Restore MinIO bucket from backup
#
# This script restores a MinIO bucket from a local backup by:
# 1. Extracting backup archive if compressed
# 2. Using MinIO client to mirror/sync files back to the bucket
# 3. Verifying restoration integrity
#
# Best practices implemented:
# - Confirmation prompts before overwriting data
# - Integrity verification
# - Support for both compressed and uncompressed backups
# - Dry-run option for testing

set -euo pipefail  # Exit on error, undefined variables, and pipe failures

# Load environment variables from .envrc if it exists (direnv)
if [ -f ".envrc" ]; then
    set -a  # automatically export all variables
    source .envrc
    set +a
fi

# MinIO configuration with defaults
MINIO_ENDPOINT="${S3_ENDPOINT:-localhost:9000}"
MINIO_ACCESS_KEY="${S3_ACCESS_KEY:-minio}"
MINIO_SECRET_KEY="${S3_SECRET_KEY:-minio123}"
MINIO_BUCKET="${S3_BUCKET:-magnetdb}"
MINIO_SECURE="${S3_SECURE:-false}"

# Restore options
DRY_RUN="${DRY_RUN:-no}"
OVERWRITE="${OVERWRITE:-ask}"  # ask, yes, no

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=== MinIO Bucket Restore ==="
echo "Endpoint: ${MINIO_ENDPOINT}"
echo "Bucket: ${MINIO_BUCKET}"
echo ""

# Check if backup path is provided
if [ -z "${1:-}" ]; then
    echo "Usage: $0 <backup_path|backup_archive.tar.gz> [options]"
    echo ""
    echo "Options:"
    echo "  DRY_RUN=yes          - Show what would be restored without making changes"
    echo "  OVERWRITE=yes        - Overwrite existing files without asking"
    echo "  OVERWRITE=no         - Skip existing files"
    echo ""
    echo "Available backups:"
    BACKUP_DIR="${MINIO_BACKUP_DIR:-./backups/minio}"
    if [ -d "${BACKUP_DIR}" ]; then
        echo ""
        echo "Compressed archives:"
        ls -lht "${BACKUP_DIR}"/*.tar.gz 2>/dev/null | head -5 | awk '{print "  " $9 " (" $5 ", " $6 " " $7 " " $8 ")"}' || echo "  None found"
        echo ""
        echo "Uncompressed backups:"
        ls -lhtd "${BACKUP_DIR}"/*/ 2>/dev/null | grep -v latest | head -5 | awk '{print "  " $9 " (" $6 " " $7 " " $8 ")"}' || echo "  None found"
        echo ""
        if [ -L "${BACKUP_DIR}/latest" ]; then
            LATEST=$(readlink "${BACKUP_DIR}/latest")
            echo "Latest backup: ${BACKUP_DIR}/${LATEST}"
        fi
    else
        echo "  No backups directory found at ${BACKUP_DIR}"
    fi
    exit 1
fi

BACKUP_SOURCE="$1"

# Check if backup exists
if [ ! -e "${BACKUP_SOURCE}" ]; then
    echo -e "${RED}✗ Error: Backup '${BACKUP_SOURCE}' not found.${NC}"
    exit 1
fi

# Check if mc (MinIO client) is installed
if ! command -v mc &> /dev/null; then
    echo -e "${RED}✗ Error: MinIO client (mc) is not installed.${NC}"
    echo ""
    echo "Install it using one of these methods:"
    echo "  # Linux (x86_64)"
    echo "  wget https://dl.min.io/client/mc/release/linux-amd64/mc"
    echo "  chmod +x mc"
    echo "  sudo mv mc /usr/local/bin/"
    echo ""
    echo "  # Using Docker"
    echo "  alias mc='docker run --rm -it --entrypoint=/bin/sh minio/mc'"
    exit 1
fi

# Configure MinIO client alias
echo "Configuring MinIO client..."
PROTOCOL="http"
if [ "${MINIO_SECURE}" = "true" ]; then
    PROTOCOL="https"
fi

mc alias set magnetdb-restore "${PROTOCOL}://${MINIO_ENDPOINT}" "${MINIO_ACCESS_KEY}" "${MINIO_SECRET_KEY}" --api S3v4 > /dev/null 2>&1

# Verify connection and bucket
if ! mc ls "magnetdb-restore" > /dev/null 2>&1; then
    echo -e "${RED}✗ Error: Cannot connect to MinIO.${NC}"
    exit 1
fi

# Create bucket if it doesn't exist
if ! mc ls "magnetdb-restore/${MINIO_BUCKET}" > /dev/null 2>&1; then
    echo -e "${YELLOW}! Bucket '${MINIO_BUCKET}' does not exist. Creating...${NC}"
    mc mb "magnetdb-restore/${MINIO_BUCKET}"
    echo -e "${GREEN}✓ Bucket created${NC}"
else
    echo -e "${GREEN}✓ Connected to MinIO successfully${NC}"
    
    # Check current bucket contents
    CURRENT_OBJECTS=$(mc ls --recursive "magnetdb-restore/${MINIO_BUCKET}" 2>/dev/null | wc -l || echo "0")
    if [ "$CURRENT_OBJECTS" -gt 0 ]; then
        echo -e "${YELLOW}⚠ Warning: Bucket currently contains ${CURRENT_OBJECTS} objects${NC}"
        
        if [ "${OVERWRITE}" = "ask" ]; then
            echo ""
            read -p "This will overwrite existing data. Continue? (yes/no): " -r
            if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
                echo "Restore cancelled."
                exit 0
            fi
        elif [ "${OVERWRITE}" = "no" ]; then
            echo "OVERWRITE=no specified. Existing files will be skipped."
        fi
    fi
fi

echo ""

# Determine if backup is compressed
RESTORE_PATH="${BACKUP_SOURCE}"
TEMP_EXTRACT=false

if [ -f "${BACKUP_SOURCE}" ] && [[ "${BACKUP_SOURCE}" == *.tar.gz ]]; then
    echo "Extracting compressed backup..."
    TEMP_DIR=$(mktemp -d)
    TEMP_EXTRACT=true
    RESTORE_PATH="${TEMP_DIR}"
    
    if tar -xzf "${BACKUP_SOURCE}" -C "${TEMP_DIR}"; then
        echo -e "${GREEN}✓ Backup extracted${NC}"
        # Find the actual backup directory (should be only one)
        BACKUP_DIR_NAME=$(ls "${TEMP_DIR}" | head -1)
        RESTORE_PATH="${TEMP_DIR}/${BACKUP_DIR_NAME}"
    else
        echo -e "${RED}✗ Failed to extract backup${NC}"
        rm -rf "${TEMP_DIR}"
        exit 1
    fi
    echo ""
fi

# Verify backup structure and read metadata
if [ ! -d "${RESTORE_PATH}" ]; then
    echo -e "${RED}✗ Error: Invalid backup path${NC}"
    [ "$TEMP_EXTRACT" = true ] && rm -rf "${TEMP_DIR}"
    exit 1
fi

echo "Backup details:"
if [ -f "${RESTORE_PATH}/backup-metadata.json" ]; then
    cat "${RESTORE_PATH}/backup-metadata.json" | while IFS= read -r line; do
        echo "  $line"
    done
else
    echo "  No metadata file found"
fi
echo ""

# Count files to restore
FILE_COUNT=$(find "${RESTORE_PATH}" -type f ! -name "backup-metadata.json" | wc -l)
echo "Files to restore: ${FILE_COUNT}"

if [ "${DRY_RUN}" = "yes" ]; then
    echo ""
    echo -e "${YELLOW}=== DRY RUN MODE ===${NC}"
    echo "The following files would be restored:"
    echo ""
    find "${RESTORE_PATH}" -type f ! -name "backup-metadata.json" | head -20 | while read -r file; do
        rel_path="${file#${RESTORE_PATH}/}"
        echo "  ${rel_path}"
    done
    if [ "$FILE_COUNT" -gt 20 ]; then
        echo "  ... and $((FILE_COUNT - 20)) more files"
    fi
    echo ""
    echo "To perform actual restore, run without DRY_RUN:"
    echo "  $0 ${BACKUP_SOURCE}"
    [ "$TEMP_EXTRACT" = true ] && rm -rf "${TEMP_DIR}"
    exit 0
fi

# Perform restore
echo ""
echo "Restoring bucket..."

MIRROR_OPTS="--preserve"
if [ "${OVERWRITE}" = "no" ]; then
    MIRROR_OPTS="${MIRROR_OPTS} --skip-existing"
else
    MIRROR_OPTS="${MIRROR_OPTS} --overwrite"
fi

if mc mirror ${MIRROR_OPTS} "${RESTORE_PATH}/" "magnetdb-restore/${MINIO_BUCKET}/"; then
    echo -e "${GREEN}✓ Restore completed successfully${NC}"
    
    # Verify restoration
    echo ""
    echo "Verifying restoration..."
    RESTORED_COUNT=$(mc ls --recursive "magnetdb-restore/${MINIO_BUCKET}" 2>/dev/null | wc -l || echo "0")
    echo "  Objects in bucket: ${RESTORED_COUNT}"
    
    if [ "$FILE_COUNT" -eq "$RESTORED_COUNT" ]; then
        echo -e "${GREEN}✓ Verification passed: All files restored${NC}"
    else
        echo -e "${YELLOW}⚠ Warning: File count mismatch${NC}"
        echo "  Expected: ${FILE_COUNT}"
        echo "  Found: ${RESTORED_COUNT}"
    fi
else
    echo -e "${RED}✗ Restore failed${NC}"
    [ "$TEMP_EXTRACT" = true ] && rm -rf "${TEMP_DIR}"
    exit 1
fi

# Cleanup temporary extraction
if [ "$TEMP_EXTRACT" = true ]; then
    rm -rf "${TEMP_DIR}"
fi

echo ""
echo -e "${GREEN}=== Restore completed ===${NC}"
echo "Bucket '${MINIO_BUCKET}' has been restored from backup"
echo ""
echo "You can verify the contents using:"
echo "  mc ls --recursive magnetdb-restore/${MINIO_BUCKET}"
echo "  # or via web console at: ${PROTOCOL}://${MINIO_ENDPOINT}"
