# Environment Variables Reference

This document provides a comprehensive reference of all environment variables used in the MagnetDB project.

## Quick Reference Table

| Variable Name | Used By | Default Value | Description |
|---------------|---------|---------------|-------------|
| `UUID` | Docker Compose | `$(id -u)` | User ID for Docker permissions |
| `GID` | Docker Compose | `$(id -g)` | Group ID for Docker permissions |
| `POSTGRES_USER` | Docker (postgres) | `magnetdb` | PostgreSQL superuser name |
| `POSTGRES_PASSWORD` | Docker (postgres) | `magnetdb` | PostgreSQL superuser password |
| `POSTGRES_DB` | Docker (postgres) | `magnetdb` | PostgreSQL database name |
| `DATABASE_HOST` | Shell scripts, API | `postgres` | PostgreSQL host (container name or IP) |
| `DATABASE_NAME` | Shell scripts | `magnetdb` | Database name for shell scripts |
| `DATABASE_USER` | Shell scripts | `magnetdb` | Database user for shell scripts |
| `DATABASE_PASSWORD` | Shell scripts | `magnetdb` | Database password for shell scripts |
| `POSTGRES_CONTAINER` | Shell scripts | `magnetdb-postgres` | Docker container name for PostgreSQL |
| `BACKUP_DIR` | db-dump.sh | `./backups` | Directory for database backups |
| `TZ` | Docker (postgres) | `Europe/Paris` | Timezone |
| `PGTZ` | Docker (postgres) | `Europe/Paris` | PostgreSQL timezone |
| `S3_ENDPOINT` | API, Worker | `minio:9000` | MinIO S3 endpoint |
| `S3_ACCESS_KEY` | API, Worker | `minio` | MinIO access key |
| `S3_SECRET_KEY` | API, Worker | `minio123` | MinIO secret key |
| `S3_BUCKET` | API, Worker | `magnetdb` | MinIO bucket name |
| `MINIO_ROOT_USER` | Docker (minio) | `minio` | MinIO admin username |
| `MINIO_ROOT_PASSWORD` | Docker (minio) | `minio123` | MinIO admin password |
| `MINIO_BROWSER_REDIRECT_URL` | Docker (minio) | `https://minio.magnetdb-dev.local` | MinIO console URL |
| `REDIS_ADDR` | API, Worker | `redis://redis:6379/0` | Redis connection URL |
| `IMAGES_DIR` | API, Worker | `/images` | Path to images directory |
| `DATA_DIR` | Seeds scripts | `/data` | Path to data directory |
| `SECURITY_AUTHORIZATION_SERVER` | API | `http://lemonldap` | Internal auth server URL |
| `FRONT_SECURITY_AUTHORIZATION_SERVER` | API | `https://auth.lemon.magnetdb-dev.local` | Public auth server URL |
| `FRONT_SECURITY_AUTHORIZATION_HOST_SERVER` | API | `auth.lemon.magnetdb-dev.local` | Auth server hostname |
| `PGADMIN_DEFAULT_EMAIL` | Docker (pgadmin) | `christophe.trophime@lncmi.cnrs.fr` | PgAdmin login email |
| `PGADMIN_DEFAULT_PASSWORD` | Docker (pgadmin) | `admin` | PgAdmin login password |
| `LOGLEVEL` | Docker (lemonldap) | `debug` | LemonLDAP log level |
| `DOMAIN_NAME` | Docker (lemonldap) | `lemon.magnetdb-dev.local` | LemonLDAP base domain |
| `API_HOSTNAME` | Docker (lemonldap) | `api.lemon.magnetdb-dev.local` | LemonLDAP API hostname |
| `MANAGER_HOSTNAME` | Docker (lemonldap) | `manager.lemon.magnetdb-dev.local` | LemonLDAP manager hostname |
| `PORTAL_HOSTNAME` | Docker (lemonldap) | `auth.lemon.magnetdb-dev.local` | LemonLDAP portal hostname |
| `HANDLER_HOSTNAME` | Docker (lemonldap) | `handler.lemon.magnetdb-dev.local` | LemonLDAP handler hostname |
| `TEST_HOSTNAME` | Docker (lemonldap) | `test.lemon.magnetdb-dev.local` | LemonLDAP test hostname |
| `TIMEZONE` | Docker (lemonldap) | `Europe/Paris` | LemonLDAP timezone |
| `MANAGER_LOG_LEVEL` | Docker (lemonldap) | `debug` | LemonLDAP manager log level |
| `API_ENDPOINT` | Web App | `https://api.magnetdb-dev.local` | API endpoint URL |
| `NODE_ENV` | Web App | `development` | Node.js environment |

## Variable Groups

### Docker Permissions
```bash
export UUID=$(id -u)
export GID=$(id -g)
```
- Required for proper file permissions in Docker containers
- Automatically set by direnv
- Used by: web-api, web-worker containers

### PostgreSQL Database
```bash
# Docker container environment
export POSTGRES_USER=magnetdb
export POSTGRES_PASSWORD=magnetdb
export POSTGRES_DB=magnetdb
export TZ='Europe/Paris'
export PGTZ='Europe/Paris'

# Shell script connections
export DATABASE_HOST=postgres
export DATABASE_NAME=magnetdb
export DATABASE_USER=magnetdb
export DATABASE_PASSWORD=magnetdb
export POSTGRES_CONTAINER=magnetdb-postgres

# Backup settings
export BACKUP_DIR=./backups
```

**Note on naming:**
- `POSTGRES_*` variables are used by the PostgreSQL Docker image
- `DATABASE_*` variables are used by shell scripts (db-dump.sh, db-load.sh, etc.)
- Both sets should have the same values for consistency

### MinIO S3 Storage
```bash
# Application connection
export S3_ENDPOINT=minio:9000
export S3_ACCESS_KEY=minio
export S3_SECRET_KEY=minio123
export S3_BUCKET=magnetdb

# MinIO server configuration
export MINIO_ROOT_USER=minio
export MINIO_ROOT_PASSWORD=minio123
export MINIO_BROWSER_REDIRECT_URL=https://minio.magnetdb-dev.local
```

### Redis
```bash
export REDIS_ADDR=redis://redis:6379/0
```

### LemonLDAP SSO
```bash
export LOGLEVEL=debug
export DOMAIN_NAME=lemon.magnetdb-dev.local
export API_HOSTNAME=api.lemon.magnetdb-dev.local
export MANAGER_HOSTNAME=manager.lemon.magnetdb-dev.local
export PORTAL_HOSTNAME=auth.lemon.magnetdb-dev.local
export HANDLER_HOSTNAME=handler.lemon.magnetdb-dev.local
export TEST_HOSTNAME=test.lemon.magnetdb-dev.local
export TIMEZONE=Europe/Paris
export MANAGER_LOG_LEVEL=debug

# API integration
export SECURITY_AUTHORIZATION_SERVER=http://lemonldap
export FRONT_SECURITY_AUTHORIZATION_SERVER=https://auth.lemon.magnetdb-dev.local
export FRONT_SECURITY_AUTHORIZATION_HOST_SERVER=auth.lemon.magnetdb-dev.local
```

### PgAdmin
```bash
export PGADMIN_DEFAULT_EMAIL=christophe.trophime@lncmi.cnrs.fr
export PGADMIN_DEFAULT_PASSWORD=admin
```

### Application Paths
```bash
export IMAGES_DIR=/images
export DATA_DIR=/data
```

### Frontend
```bash
export API_ENDPOINT=https://api.magnetdb-dev.local
export NODE_ENV=development
```

## Files That Use These Variables

### Docker Compose
- `docker-compose-dev-traefik-ssl.yml` - Uses most environment variables for container configuration

### Shell Scripts
- `db-dump.sh` - Uses: `DATABASE_HOST`, `DATABASE_NAME`, `DATABASE_USER`, `DATABASE_PASSWORD`, `BACKUP_DIR`
- `db-load.sh` - Uses: `DATABASE_HOST`, `DATABASE_NAME`, `DATABASE_USER`, `DATABASE_PASSWORD`
- `db-remove.sh` - Uses: `DATABASE_HOST`, `DATABASE_NAME`, `DATABASE_USER`, `DATABASE_PASSWORD`
- `db-fix-collation.sh` - Uses: `DATABASE_HOST`, `DATABASE_NAME`, `DATABASE_USER`, `DATABASE_PASSWORD`, `POSTGRES_CONTAINER`

### Python Application
- `python_magnetdb/settings.py` - Reads various environment variables for configuration
- Seed scripts - Use: `DATA_DIR`

### Web Application
- `web/` - Uses: `API_ENDPOINT`, `NODE_ENV`

## Environment Priority

When running shell scripts, environment variables are loaded in this order (first found wins):

1. **Current shell environment** (e.g., from direnv)
2. **`.envrc`** file (if exists and manually sourced by script)
3. **`settings.env`** file (legacy, fallback)
4. **Default values** (hardcoded in scripts)

When running Docker Compose:

1. **Current shell environment** (e.g., from direnv)
2. **Inline defaults in docker-compose.yml** (e.g., `${UUID:-1000}`)

## Customization Guide

### For Development (Local Changes)

1. Copy the example file:
   ```bash
   cp .envrc.example .envrc
   ```

2. Edit `.envrc` with your custom values:
   ```bash
   # Example: Change PostgreSQL password
   export POSTGRES_PASSWORD=my_secure_password
   export DATABASE_PASSWORD=my_secure_password  # Keep in sync!
   ```

3. Allow direnv to load it:
   ```bash
   direnv allow
   ```

### For Team (Shared Defaults)

1. Update `.envrc.example` with new defaults
2. Document the change in this file
3. Commit `.envrc.example` to git
4. Team members update their local `.envrc`

## Important Notes

### Synchronized Variables

These variable pairs **must have the same value**:
- `POSTGRES_PASSWORD` ↔ `DATABASE_PASSWORD`
- `POSTGRES_USER` ↔ `DATABASE_USER`
- `POSTGRES_DB` ↔ `DATABASE_NAME`

### Security Considerations

- **Never commit `.envrc`** - It's gitignored for security
- **Change default passwords** for production environments
- **Keep `.envrc.example`** with safe default values for development

### Container vs Host

Some variables have different values depending on context:
- `DATABASE_HOST=postgres` (inside Docker network)
- `DATABASE_HOST=localhost` (when running scripts on host)

The default values work for the containerized development setup.

## Troubleshooting

### Variables Not Loading

If variables aren't being set:

1. Check direnv is working:
   ```bash
   direnv status
   ```

2. Verify `.envrc` exists:
   ```bash
   ls -la .envrc
   ```

3. Reload direnv:
   ```bash
   direnv allow
   ```

### Database Connection Failures

If shell scripts can't connect to the database:

1. Verify variables are set:
   ```bash
   echo $DATABASE_HOST $DATABASE_NAME $DATABASE_USER
   ```

2. For host connections, set `DATABASE_HOST=localhost`:
   ```bash
   export DATABASE_HOST=localhost
   ```

3. For Docker connections, use container name:
   ```bash
   export DATABASE_HOST=postgres
   ```

### Password Mismatches

If you get authentication errors:

1. Ensure synchronized variables match:
   ```bash
   echo "POSTGRES_PASSWORD=$POSTGRES_PASSWORD"
   echo "DATABASE_PASSWORD=$DATABASE_PASSWORD"
   ```

2. Update both in `.envrc` if they differ

## Migration from settings.env

If you're migrating from `settings.env`:

1. Review your `settings.env` file
2. Copy relevant values to `.envrc`
3. Add any custom variables to `.envrc`
4. Test that everything works
5. Optionally remove or archive `settings.env`

The shell scripts will automatically prefer `.envrc` if it exists, falling back to `settings.env` for compatibility.
