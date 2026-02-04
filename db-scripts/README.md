# Database Management Scripts

Several shell scripts are available for database and storage operations:

## PostgreSQL Database Scripts

- `db-dump.sh` - Backup the PostgreSQL database
- `db-load.sh` - Restore database from a backup
- `db-remove.sh` - Remove/clean the database
- `db-fix-collation.sh` - Fix collation version mismatch warnings
- `db-change-user-role.sh` - Change the role of a user in the database

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
