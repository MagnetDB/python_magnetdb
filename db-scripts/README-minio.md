# MinIO Backup and Management Scripts

This directory contains scripts for managing MinIO buckets, including backup and restore operations.

## Scripts Overview

### 1. `minio-backup.sh` - Backup MinIO Buckets
Creates timestamped backups of MinIO buckets to local storage.

**Features:**
- Full and incremental backup modes
- Automatic compression
- Backup metadata tracking
- Configurable retention policies
- Automatic cleanup of old backups

**Usage:**
```bash
# Basic backup
./db-scripts/minio-backup.sh

# Custom configuration
MINIO_BACKUP_DIR=/custom/path COMPRESS=yes ./db-scripts/minio-backup.sh

# Incremental backup
BACKUP_TYPE=incremental ./db-scripts/minio-backup.sh

# No compression
COMPRESS=no ./db-scripts/minio-backup.sh

# Custom retention (keep backups for 60 days)
RETENTION_DAYS=60 ./db-scripts/minio-backup.sh
```

**Environment Variables:**
- `S3_ENDPOINT` - MinIO endpoint (default: localhost:9000)
- `S3_ACCESS_KEY` - Access key (default: minio)
- `S3_SECRET_KEY` - Secret key (default: minio123)
- `S3_BUCKET` - Bucket to backup (default: magnetdb)
- `S3_SECURE` - Use HTTPS (default: false)
- `MINIO_BACKUP_DIR` - Backup directory (default: ./backups/minio)
- `COMPRESS` - Compress backup (default: yes)
- `BACKUP_TYPE` - Backup type: full or incremental (default: full)
- `RETENTION_DAYS` - Days to keep backups (default: 30)

### 2. `minio-restore.sh` - Restore MinIO Buckets
Restores MinIO buckets from local backups.

**Features:**
- Supports compressed and uncompressed backups
- Dry-run mode for testing
- Overwrite protection
- Integrity verification
- Metadata validation

**Usage:**
```bash
# List available backups
./db-scripts/minio-restore.sh

# Restore from compressed backup
./db-scripts/minio-restore.sh ./backups/minio/magnetdb_20250128_143000.tar.gz

# Restore from uncompressed backup
./db-scripts/minio-restore.sh ./backups/minio/magnetdb_20250128_143000

# Restore latest backup
./db-scripts/minio-restore.sh ./backups/minio/latest

# Dry run (test without making changes)
DRY_RUN=yes ./db-scripts/minio-restore.sh ./backups/minio/magnetdb_20250128_143000.tar.gz

# Force overwrite without confirmation
OVERWRITE=yes ./db-scripts/minio-restore.sh ./backups/minio/magnetdb_20250128_143000.tar.gz

# Skip existing files
OVERWRITE=no ./db-scripts/minio-restore.sh ./backups/minio/magnetdb_20250128_143000.tar.gz
```

**Environment Variables:**
- `S3_ENDPOINT`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `S3_BUCKET`, `S3_SECURE` - Same as backup
- `DRY_RUN` - Test mode without making changes (default: no)
- `OVERWRITE` - Overwrite mode: ask, yes, or no (default: ask)

### 3. `minio-manage.sh` - Bucket Management
General-purpose bucket management utilities.

**Features:**
- List buckets and objects
- Bucket statistics
- Create/delete buckets
- Bucket policy management
- File type analysis

**Usage:**
```bash
# List all buckets
./db-scripts/minio-manage.sh list

# List objects in default bucket
./db-scripts/minio-manage.sh objects

# List objects recursively
./db-scripts/minio-manage.sh objects magnetdb yes

# Show bucket statistics
./db-scripts/minio-manage.sh stats magnetdb

# Create new bucket
./db-scripts/minio-manage.sh create new-bucket

# Delete bucket
./db-scripts/minio-manage.sh delete old-bucket

# Delete bucket with force (no confirmation)
./db-scripts/minio-manage.sh delete old-bucket yes

# Set bucket policy to private
./db-scripts/minio-manage.sh policy magnetdb private

# Set bucket policy to public read-only
./db-scripts/minio-manage.sh policy magnetdb download

# Get current bucket policy
./db-scripts/minio-manage.sh get-policy magnetdb
```

## Prerequisites

### MinIO Client (mc)

All scripts require the MinIO client. Install it:

**Linux:**
```bash
wget https://dl.min.io/client/mc/release/linux-amd64/mc
chmod +x mc
sudo mv mc /usr/local/bin/
```

**macOS:**
```bash
brew install minio/stable/mc
```

**Using Docker:**
```bash
# Run via Docker
docker run --rm -it minio/mc --help

# Or create an alias
alias mc='docker run --rm -it --entrypoint=/bin/sh minio/mc'
```

## Best Practices

### 1. Regular Backups
- **Daily backups**: For production environments
- **Full weekly, incremental daily**: Balance storage and recovery time
- **Off-site storage**: Copy backups to remote location

```bash
# Cron example for daily backup at 2 AM
0 2 * * * cd /path/to/project && ./db-scripts/minio-backup.sh >> /var/log/minio-backup.log 2>&1
```

### 2. Backup Strategy

**3-2-1 Rule:**
- **3** copies of data
- **2** different storage types
- **1** off-site copy

```bash
# Example: Backup to local and sync to remote
./db-scripts/minio-backup.sh
rsync -av ./backups/minio/ remote-server:/backups/minio/
```

### 3. Testing Restores
Regular restore testing ensures backups are valid:

```bash
# Monthly restore test
DRY_RUN=yes ./db-scripts/minio-restore.sh ./backups/minio/latest
```

### 4. Retention Policy
Configure retention based on requirements:

- **Development**: 7-14 days
- **Staging**: 30 days
- **Production**: 90+ days

```bash
# Production retention
RETENTION_DAYS=90 ./db-scripts/minio-backup.sh
```

### 5. Monitoring Backup Size
Track backup growth to plan storage:

```bash
# Monitor backup directory
du -sh ./backups/minio/
ls -lht ./backups/minio/ | head
```

### 6. Encryption (for sensitive data)
Encrypt backups for sensitive environments:

```bash
# Encrypt backup
COMPRESS=yes ./db-scripts/minio-backup.sh
gpg --symmetric --cipher-algo AES256 ./backups/minio/magnetdb_*.tar.gz

# Decrypt for restore
gpg --decrypt ./backups/minio/magnetdb_*.tar.gz.gpg > /tmp/backup.tar.gz
./db-scripts/minio-restore.sh /tmp/backup.tar.gz
```

### 7. Versioning
MinIO supports object versioning for additional protection:

```bash
# Enable versioning on bucket
mc version enable magnetdb-mgmt/magnetdb

# View object versions
mc ls --versions magnetdb-mgmt/magnetdb
```

## Integration with Database Backups

For complete system backup, combine with database backups:

```bash
#!/bin/bash
# complete-backup.sh

echo "=== Complete System Backup ==="

# Backup database
./db-scripts/db-dump.sh

# Backup MinIO
./db-scripts/minio-backup.sh

# Create combined archive
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
tar -czf "backups/complete-backup-${TIMESTAMP}.tar.gz" \
    backups/magnetdb_*.sql \
    backups/minio/magnetdb_*

echo "✓ Complete backup created"
```

## Disaster Recovery Procedure

1. **Restore Database:**
   ```bash
   ./db-scripts/db-load.sh backups/magnetdb_20250128_140000.sql
   ```

2. **Restore MinIO:**
   ```bash
   ./db-scripts/minio-restore.sh backups/minio/magnetdb_20250128_140000.tar.gz
   ```

3. **Verify Application:**
   ```bash
   docker-compose up -d
   # Check application health
   ```

## Troubleshooting

### Connection Issues
```bash
# Test MinIO connection
mc alias set test http://localhost:9000 minio minio123
mc ls test
```

### Permission Issues
```bash
# Check MinIO is running
docker ps | grep minio

# Check bucket permissions
./db-scripts/minio-manage.sh get-policy magnetdb
```

### Backup Failures
```bash
# Check disk space
df -h

# Verify MinIO client
mc --version

# Check MinIO logs
docker logs magnetdb-minio
```

## Security Considerations

1. **Access Keys**: Use environment variables, never hardcode
2. **Network**: Use TLS/SSL in production (`S3_SECURE=true`)
3. **Permissions**: Restrict backup directory access
4. **Encryption**: Encrypt backups containing sensitive data
5. **Audit**: Log all backup/restore operations

## Performance Tips

1. **Incremental Backups**: Use for large buckets
2. **Compression**: Balance CPU usage vs storage
3. **Parallel Operations**: MinIO client supports parallel uploads
4. **Network**: Ensure sufficient bandwidth for large backups

## Additional Resources

- [MinIO Client Documentation](https://min.io/docs/minio/linux/reference/minio-mc.html)
- [MinIO Backup Best Practices](https://min.io/docs/minio/linux/operations/backup-restore.html)
- [S3 API Compatibility](https://docs.aws.amazon.com/AmazonS3/latest/API/)
