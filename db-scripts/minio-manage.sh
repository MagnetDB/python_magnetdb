#!/bin/bash
#
# MinIO Bucket Management Script
#
# This script provides common bucket management operations:
# - List buckets and objects
# - Create/delete buckets
# - Get bucket statistics
# - Configure bucket policies
# - Manage bucket lifecycle rules
# - Sync between buckets (useful for replication)

set -euo pipefail

# Load environment variables
if [ -f ".envrc" ]; then
    set -a
    source .envrc
    set +a
fi

# MinIO configuration
MINIO_ENDPOINT="${S3_ENDPOINT:-localhost:9000}"
MINIO_ACCESS_KEY="${S3_ACCESS_KEY:-minio}"
MINIO_SECRET_KEY="${S3_SECRET_KEY:-minio123}"
MINIO_BUCKET="${S3_BUCKET:-magnetdb}"
MINIO_SECURE="${S3_SECURE:-false}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check if mc is installed
check_mc() {
    if ! command -v mc &> /dev/null; then
        echo -e "${RED}✗ MinIO client (mc) is not installed${NC}"
        echo ""
        echo "Install: wget https://dl.min.io/client/mc/release/linux-amd64/mc"
        echo "         chmod +x mc && sudo mv mc /usr/local/bin/"
        exit 1
    fi
}

# Configure MinIO client
configure_mc() {
    local alias_name="${1:-magnetdb-mgmt}"
    local protocol="http"
    
    if [ "${MINIO_SECURE}" = "true" ]; then
        protocol="https"
    fi
    
    mc alias set "${alias_name}" "${protocol}://${MINIO_ENDPOINT}" \
        "${MINIO_ACCESS_KEY}" "${MINIO_SECRET_KEY}" --api S3v4 > /dev/null 2>&1
    
    echo "${alias_name}"
}

# List all buckets
list_buckets() {
    echo -e "${BLUE}=== MinIO Buckets ===${NC}"
    echo "Endpoint: ${MINIO_ENDPOINT}"
    echo ""
    
    local alias=$(configure_mc)
    
    mc ls "${alias}" | while read -r line; do
        echo "  $line"
    done
}

# List bucket contents
list_objects() {
    local bucket="${1:-${MINIO_BUCKET}}"
    local recursive="${2:-no}"
    
    echo -e "${BLUE}=== Bucket Contents: ${bucket} ===${NC}"
    echo ""
    
    local alias=$(configure_mc)
    
    if [ "${recursive}" = "yes" ]; then
        mc ls --recursive "${alias}/${bucket}"
    else
        mc ls "${alias}/${bucket}"
    fi
}

# Get bucket statistics
bucket_stats() {
    local bucket="${1:-${MINIO_BUCKET}}"
    
    echo -e "${BLUE}=== Bucket Statistics: ${bucket} ===${NC}"
    echo ""
    
    local alias=$(configure_mc)
    
    # Object count
    local count=$(mc ls --recursive "${alias}/${bucket}" 2>/dev/null | wc -l)
    echo "Total objects: ${count}"
    
    # Total size
    echo -n "Total size: "
    mc du "${alias}/${bucket}" 2>/dev/null | awk '{print $1, $2}'
    
    # File type breakdown (by extension)
    echo ""
    echo "File types:"
    mc ls --recursive "${alias}/${bucket}" 2>/dev/null | \
        awk '{print $NF}' | \
        sed 's/.*\.//' | \
        sort | uniq -c | sort -rn | head -10 | \
        awk '{printf "  %-10s %s files\n", $2, $1}'
}

# Create bucket
create_bucket() {
    local bucket="${1}"
    
    if [ -z "${bucket}" ]; then
        echo -e "${RED}✗ Bucket name required${NC}"
        echo "Usage: $0 create <bucket-name>"
        exit 1
    fi
    
    echo -e "${BLUE}=== Creating Bucket: ${bucket} ===${NC}"
    
    local alias=$(configure_mc)
    
    if mc mb "${alias}/${bucket}"; then
        echo -e "${GREEN}✓ Bucket created successfully${NC}"
    else
        echo -e "${RED}✗ Failed to create bucket${NC}"
        exit 1
    fi
}

# Delete bucket
delete_bucket() {
    local bucket="${1}"
    local force="${2:-no}"
    
    if [ -z "${bucket}" ]; then
        echo -e "${RED}✗ Bucket name required${NC}"
        echo "Usage: $0 delete <bucket-name> [force]"
        exit 1
    fi
    
    echo -e "${YELLOW}⚠ Warning: This will delete bucket '${bucket}'${NC}"
    
    local alias=$(configure_mc)
    
    # Check if bucket has objects
    local count=$(mc ls --recursive "${alias}/${bucket}" 2>/dev/null | wc -l || echo "0")
    
    if [ "$count" -gt 0 ]; then
        echo "  Bucket contains ${count} objects"
        
        if [ "${force}" != "yes" ]; then
            read -p "Delete bucket and all objects? (yes/no): " -r
            if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
                echo "Cancelled"
                exit 0
            fi
        fi
        
        # Remove all objects first
        echo "Removing objects..."
        mc rm --recursive --force "${alias}/${bucket}"
    fi
    
    # Remove bucket
    if mc rb "${alias}/${bucket}"; then
        echo -e "${GREEN}✓ Bucket deleted successfully${NC}"
    else
        echo -e "${RED}✗ Failed to delete bucket${NC}"
        exit 1
    fi
}

# Set bucket policy (public/private)
set_policy() {
    local bucket="${1}"
    local policy="${2:-private}"
    
    if [ -z "${bucket}" ]; then
        echo -e "${RED}✗ Bucket name required${NC}"
        echo "Usage: $0 policy <bucket-name> [public|private|download]"
        exit 1
    fi
    
    echo -e "${BLUE}=== Setting Bucket Policy ===${NC}"
    echo "Bucket: ${bucket}"
    echo "Policy: ${policy}"
    echo ""
    
    local alias=$(configure_mc)
    
    case "${policy}" in
        public)
            # Public read-write
            mc anonymous set public "${alias}/${bucket}"
            ;;
        download|readonly)
            # Public read-only
            mc anonymous set download "${alias}/${bucket}"
            ;;
        private)
            # Private (default)
            mc anonymous set private "${alias}/${bucket}"
            ;;
        *)
            echo -e "${RED}✗ Invalid policy. Use: public, download, or private${NC}"
            exit 1
            ;;
    esac
    
    echo -e "${GREEN}✓ Policy set successfully${NC}"
}

# Get bucket policy
get_policy() {
    local bucket="${1:-${MINIO_BUCKET}}"
    
    echo -e "${BLUE}=== Bucket Policy: ${bucket} ===${NC}"
    echo ""
    
    local alias=$(configure_mc)
    
    mc anonymous get "${alias}/${bucket}"
}

# Show usage
usage() {
    cat <<EOF
MinIO Bucket Management Script

Usage: $0 <command> [options]

Commands:
  list                          List all buckets
  objects [bucket] [recursive]  List objects in bucket
  stats [bucket]                Show bucket statistics
  create <bucket>               Create new bucket
  delete <bucket> [force]       Delete bucket
  policy <bucket> [type]        Set bucket policy (public/private/download)
  get-policy [bucket]           Get current bucket policy
  
Examples:
  $0 list
  $0 objects magnetdb yes
  $0 stats magnetdb
  $0 create new-bucket
  $0 delete old-bucket yes
  $0 policy magnetdb private
  
Environment Variables:
  S3_ENDPOINT      MinIO endpoint (default: localhost:9000)
  S3_ACCESS_KEY    Access key (default: minio)
  S3_SECRET_KEY    Secret key (default: minio123)
  S3_BUCKET        Default bucket (default: magnetdb)
  S3_SECURE        Use HTTPS (default: false)

EOF
}

# Main
check_mc

case "${1:-help}" in
    list)
        list_buckets
        ;;
    objects)
        list_objects "${2:-${MINIO_BUCKET}}" "${3:-no}"
        ;;
    stats)
        bucket_stats "${2:-${MINIO_BUCKET}}"
        ;;
    create)
        create_bucket "${2:-}"
        ;;
    delete)
        delete_bucket "${2:-}" "${3:-no}"
        ;;
    policy)
        set_policy "${2:-}" "${3:-private}"
        ;;
    get-policy)
        get_policy "${2:-${MINIO_BUCKET}}"
        ;;
    help|--help|-h)
        usage
        ;;
    *)
        echo -e "${RED}✗ Unknown command: $1${NC}"
        echo ""
        usage
        exit 1
        ;;
esac
