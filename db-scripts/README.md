# Database Management Scripts

Several shell scripts are available for database and storage operations:

## PostgreSQL Database Scripts

- `db-dump.sh` - Backup the PostgreSQL database
- `db-load.sh` - Restore database from a backup
- `db-remove.sh` - Remove/clean the database
- `db-fix-collation.sh` - Fix collation version mismatch warnings
- `db-change-user-role.sh` - Change the role of a user in the database

## pgAdmin Configuration

- `setup-pgadmin.sh` - Auto-configure pgAdmin server connections using environment variables

## MinIO Storage Scripts

- `minio-backup.sh` - Backup MinIO bucket to local storage
- `minio-restore.sh` - Restore MinIO bucket from backup
- `minio-manage.sh` - Manage MinIO buckets (list, create, delete, stats, policies)

For detailed MinIO backup and management documentation, see [README-minio.md](README-minio.md)


## Usage

> **Important:** Currently, the repository is not mounted in the `magnetdb-postgres` container
> so these scripts must be run from the **host machine**.

Run the scripts from the repository root:

```shell
./db-scripts/db-dump.sh
./db-scripts/db-fix-collation.sh
./db-scripts/db-load.sh backups/magnetdb_20240101_120000.sql
./db-scripts/db-remove.sh
./db-scripts/db-change-user-role.sh username new_role
```

The scripts will automatically detect and use the Docker container when available.

> NOTE: backups are stored outside the container in `./backups/`

> NOTE: removing the database requires that magnet-webapp, magnet-worker and magnet-postgres containers are stopped.
> It is recommended to look for reamining sessions using: 
> 
> ```shell
> docker exec magnetdb-postgres psql -U "${DATABASE_USER:-magnetdb}" -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${DATABASE_NAME:-magnetdb}' AND pid <> pg_backend_pid();"
> ```
>
> You may also consider removing minio bucket data using:
> ```shell
> ./db-scripts/minio-manage.sh delete-bucket
> ```

## pgAdmin Auto-Configuration

The pgAdmin service can be automatically configured with database server connections using environment variables from the docker-compose file. The script supports managing multiple servers.

### Quick Start

Generate initial configuration with default server:

```shell
docker exec magnetdb-pgadmin python3 /setup_pgadmin.py
```

### Commands

The script supports the following commands:

```shell
# Generate initial configuration (overwrites existing)
docker exec magnetdb-pgadmin python3 /setup_pgadmin.py generate

# Add a server from environment variables
docker exec magnetdb-pgadmin python3 /setup_pgadmin.py add

# Add a server with custom parameters
docker exec magnetdb-pgadmin python3 /setup_pgadmin.py add \
  --name production \
  --host db.example.com \
  --port 5433 \
  --database postgres \
  --user admin \
  --password secret

# List all configured servers
docker exec magnetdb-pgadmin python3 /setup_pgadmin.py list

# Remove a server by name
docker exec magnetdb-pgadmin python3 /setup_pgadmin.py remove myserver

# Remove a server by ID
docker exec magnetdb-pgadmin python3 /setup_pgadmin.py remove --id 2
```

### Environment Variables

The following environment variables from [docker-compose-dev-traefik-ssl.yml](../.devcontainer/docker-compose-dev-traefik-ssl.yml#L220) are used as defaults when adding servers:

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_HOST` | `postgres` | PostgreSQL server hostname |
| `POSTGRES_PORT` | `5432` | PostgreSQL server port |
| `POSTGRES_DB` | `postgres` | Maintenance database name |
| `POSTGRES_USER` | `magnetdb` | Database username |
| `POSTGRES_PASSWORD` | `magnetdb` | Database password |
| `PGADMIN_SERVER_NAME` | `magnetdb` | Display name in pgAdmin |
| `PGADMIN_CONFIG_OUTPUT` | `/var/lib/pgadmin/servers.json` | Output path for configuration |

### Examples

#### Add multiple servers

```shell
# Add local development server (from env vars)
docker exec magnetdb-pgadmin python3 /setup_pgadmin.py add

# Add production server
docker exec magnetdb-pgadmin python3 /setup_pgadmin.py add \
  --name "Production DB" \
  --host prod-db.example.com \
  --port 5432 \
  --user readonly \
  --password readpass

# Add staging server
docker exec magnetdb-pgadmin python3 /setup_pgadmin.py add \
  --name "Staging DB" \
  --host staging-db.example.com \
  --port 5432

# List all servers
docker exec magnetdb-pgadmin python3 /setup_pgadmin.py list
```

#### Manage servers

```shell
# View current configuration
docker exec magnetdb-pgadmin python3 /setup_pgadmin.py list

# Remove a server
docker exec magnetdb-pgadmin python3 /setup_pgadmin.py remove "Staging DB"

# Reset to default configuration
docker exec magnetdb-pgadmin python3 /setup_pgadmin.py generate
```

### Manual Configuration

If you prefer manual configuration or need to customize settings, you can:

1. Access pgAdmin at `https://pgadmin.magnetdb-dev.local/`
2. Login with credentials:
   - Email: `christophe.trophime@lncmi.cnrs.fr`
   - Password: `admin`
3. Right-click "Servers" → "Register" → "Server"
4. Configure:
   - **Name**: `magnetdb`
   - **Host**: `postgres` (or `magnetdb-postgres`)
   - **Port**: `5432`
   - **Username**: `magnetdb`
   - **Password**: `magnetdb`

### Python API Implementation

The auto-configuration is implemented in [setup_pgadmin.py](../python_magnetdb/management/commands/setup_pgadmin.py) which:
- Reads environment variables from the docker-compose configuration
- Generates a `servers.json` file with server connection details
- Creates the configuration in the pgAdmin data directory

This eliminates manual server registration after pgAdmin deployment.

## PostgreSQL Database Scheme

The database uses PostgreSQL with the following configuration:

- **Database Name:** `magnetdb` (or as configured in environment variables)
- **Schema:** Django ORM manages the database schema automatically through migrations
- **Location:** Database files are stored in `magnetdb-data/django/postgres-data` volume
- **Migrations:** Schema changes are tracked in `python_magnetdb/migrations/`

To view the current database schema, you can connect to the PostgreSQL container:

```shell
docker exec -it magnetdb-postgres psql -U magnetuser -d magnetdb
```

Common schema inspection commands:
```sql
\dt          -- List all tables
\d+ tablename -- Show table structure
\dn          -- List schemas
\l           -- List databases
```

### Changing User Roles
#### Using the Script

The easiest way to change a user's role is using the provided script:

```shell
./db-scripts/db-change-user-role.sh username new_role
```

Example:
```shell
./db-scripts/db-change-user-role.sh john.doe admin
```

The script will:
- Show the current user information
- Update the role
- Display the updated user information
- Work automatically with Docker or local PostgreSQL

#### Manual SQL Method

Alternatively, you can connect to PostgreSQL directly and execute SQL commands
To modify a user's role in the database, connect to PostgreSQL and update the user's role field:

```shell
docker exec -it magnetdb-postgres psql -U magnetuser -d magnetdb
```

Then execute SQL commands to change the role:

```sql
-- View current users and their roles
SELECT id, username, email, role FROM users;

-- Change a user's role
UPDATE users SET role = 'admin' WHERE username = 'example_user';
-- or by user ID
UPDATE users SET role = 'user' WHERE id = 123;

-- Verify the change
SELECT username, role FROM users WHERE username = 'example_user';
```

Common roles might include: `admin`, `user`, `readonly` (check your application's role definitions).

### Alternative: Running inside the container

To run scripts inside the container, you would need to mount the repository in `docker-compose-dev-traefik-ssl.yml`:

```yaml
postgres:
  container_name: magnetdb-postgres
  volumes:
    - ../magnetdb-data/django/postgres-data:/var/lib/postgresql/data
    - .:/workspace:ro  # Add this line
```

Then you can exec into the container:
```shell
docker exec -it magnetdb-postgres bash
cd /workspace
./db-scripts/db-dump.sh
```
