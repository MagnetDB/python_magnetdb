# direnv Setup and Secret Management

This document explains how to use direnv for secure environment variable and secret management in the MagnetDB development environment.

## What is direnv?

[direnv](https://direnv.net/) is an environment switcher for the shell. It automatically loads and unloads environment variables depending on the current directory. This provides:

- **Automatic environment setup** when entering the project directory
- **Secure secret management** (secrets never committed to git)
- **Per-project configuration** without polluting your global shell environment
- **Team consistency** with shared configuration templates

## Installation

### Linux (Debian/Ubuntu)
```shell
sudo apt-get update
sudo apt-get install direnv
```

### Linux (Fedora/RHEL)
```shell
sudo dnf install direnv
```

### macOS
```shell
brew install direnv
```

### From Source
```shell
curl -sfL https://direnv.net/install.sh | bash
```

## Shell Configuration

After installing direnv, you need to hook it into your shell:

### Bash
Add to `~/.bashrc`:
```shell
eval "$(direnv hook bash)"
```

### Zsh
Add to `~/.zshrc`:
```shell
eval "$(direnv hook zsh)"
```

### Fish
Add to `~/.config/fish/config.fish`:
```shell
direnv hook fish | source
```

### Other Shells
See the [direnv documentation](https://direnv.net/docs/hook.html) for other shells.

**Important:** After adding the hook, restart your shell or run:
```shell
source ~/.bashrc  # or ~/.zshrc, etc.
```

## Quick Start

1. **Copy the example configuration:**
   ```shell
   cp .envrc.example .envrc
   ```

2. **Review and customize** (optional):
   ```shell
   nano .envrc  # or use your preferred editor
   ```
   
   The defaults should work for most users. Customize if you need to:
   - Change database passwords
   - Use different service ports
   - Modify MinIO credentials
   - Adjust timezone settings

3. **Allow direnv to load the file:**
   ```shell
   direnv allow
   ```

4. **Test it works:**
   ```shell
   # Navigate out and back in
   cd ..
   cd python_magnetdb
   
   # Check that variables are loaded
   echo $POSTGRES_USER
   # Should output: magnetdb
   ```

## Environment Variables Reference

The `.envrc` file contains the following categories of variables:

### User & Group IDs
- `UUID` - Your user ID (automatically set)
- `GID` - Your group ID (automatically set)

Used for Docker container permissions to avoid file ownership issues.

### Database Configuration
- `POSTGRES_USER` - PostgreSQL username
- `POSTGRES_PASSWORD` - PostgreSQL password
- `DATABASE_HOST` - Database hostname
- `TZ` / `PGTZ` - Timezone settings

### MinIO S3 Storage
- `S3_ENDPOINT` - MinIO server endpoint
- `S3_ACCESS_KEY` - MinIO access key
- `S3_SECRET_KEY` - MinIO secret key
- `S3_BUCKET` - Default bucket name
- `MINIO_ROOT_USER` - MinIO admin username
- `MINIO_ROOT_PASSWORD` - MinIO admin password

### Redis Configuration
- `REDIS_ADDR` - Redis connection URL

### PgAdmin
- `PGADMIN_DEFAULT_EMAIL` - PgAdmin login email
- `PGADMIN_DEFAULT_PASSWORD` - PgAdmin login password

### LemonLDAP SSO
- `DOMAIN_NAME`, `API_HOSTNAME`, etc. - LemonLDAP service URLs
- `SECURITY_AUTHORIZATION_SERVER` - Auth server endpoints

### Application Settings
- `IMAGES_DIR` - Path to images directory
- `DATA_DIR` - Path to data directory
- `API_ENDPOINT` - API server URL
- `NODE_ENV` - Node.js environment

## Security Best Practices

### DO
- ✓ Keep `.envrc` out of version control (already in `.gitignore`)
- ✓ Use different passwords for production environments
- ✓ Share `.envrc.example` with the team
- ✓ Review `.envrc` contents before running `direnv allow`
- ✓ Use strong passwords when customizing secrets

### DON'T
- ✗ Commit `.envrc` to git
- ✗ Share your `.envrc` file with others
- ✗ Use production secrets in development `.envrc`
- ✗ Allow direnv in untrusted directories without reviewing `.envrc` first

## Common Workflows

### Updating Environment Variables

1. Edit your `.envrc` file:
   ```shell
   nano .envrc
   ```

2. Reload the environment:
   ```shell
   direnv allow
   ```

3. Verify changes:
   ```shell
   echo $VARIABLE_NAME
   ```

### Sharing Configuration with Team

1. Update `.envrc.example` with new variables:
   ```shell
   # Add new configuration to .envrc.example
   export NEW_VAR=default_value
   ```

2. Commit `.envrc.example`:
   ```shell
   git add .envrc.example
   git commit -m "Add NEW_VAR to environment configuration"
   ```

3. Team members update their local `.envrc`:
   ```shell
   # Review changes in .envrc.example
   # Add the new variable to their .envrc
   # Run direnv allow
   ```

### Using with Docker Compose

The environment variables are automatically available to docker-compose:

```shell
# Variables from .envrc are automatically used
docker-compose -f docker-compose-dev-traefik-ssl.yml up
```

Docker Compose will use variables like `$UUID`, `$GID`, `$POSTGRES_PASSWORD`, etc.

### PgAdmin Automatic Setup

The development environment includes automatic pgAdmin server configuration. When you start the services, pgAdmin is automatically configured with connection information using environment variables from your `.envrc` file.

**To initialize the pgAdmin database server connection:**

After starting the services, run the setup script:

```shell
docker exec magnetdb-pgadmin python3 /setup_pgadmin.py generate
```

This creates a server configuration using the following variables from your `.envrc`:
- `PGADMIN_SERVER_NAME` - Display name in pgAdmin (default: "magnetdb")
- `POSTGRES_HOST` / `DATABASE_HOST` - Database hostname  
- `POSTGRES_PORT` - Database port (default: 5432)
- `POSTGRES_USER` / `DATABASE_USER` - Database username
- `POSTGRES_PASSWORD` / `DATABASE_PASSWORD` - Database password
- `POSTGRES_DB` / `DATABASE_NAME` - Database name

**Access pgAdmin:**

Open `https://pgadmin.magnetdb-dev.local/` in your browser and login with:
- **Email:** Value from `PGADMIN_DEFAULT_EMAIL` in `.envrc`
- **Password:** Value from `PGADMIN_DEFAULT_PASSWORD` in `.envrc`

The "magnetdb" server should appear in the left panel, ready to use without manual configuration.

**Managing pgAdmin servers:**

```shell
# List configured servers
docker exec magnetdb-pgadmin python3 /setup_pgadmin.py list

# Add another server using environment variables
docker exec magnetdb-pgadmin python3 /setup_pgadmin.py add

# Add a server with custom settings
docker exec magnetdb-pgadmin python3 /setup_pgadmin.py add \
  --name production \
  --host db.prod.example.com \
  --port 5433 \
  --user produser \
  --password prodpass

# Remove a server
docker exec magnetdb-pgadmin python3 /setup_pgadmin.py remove myserver
```

For more details, see [db-scripts/README.md](db-scripts/README.md).

### Temporarily Disabling direnv

```shell
# Disable for current shell session
direnv deny

# Or unload without disabling
direnv unload

# Re-enable
direnv allow
```

## Troubleshooting

### direnv not loading automatically

**Problem:** Variables not set when entering directory.

**Solution:**
1. Check that direnv is hooked into your shell:
   ```shell
   type direnv
   ```
   
2. Verify the hook is in your shell config:
   ```shell
   grep direnv ~/.bashrc  # or ~/.zshrc
   ```

3. Reload your shell configuration:
   ```shell
   source ~/.bashrc
   ```

### Permission denied errors

**Problem:** `direnv: error .envrc is blocked. Run 'direnv allow' to approve its content`

**Solution:**
```shell
direnv allow
```

This is a security feature. direnv requires explicit approval before loading `.envrc` files.

### Variables not available in docker-compose

**Problem:** Docker containers don't see environment variables.

**Solution:**
1. Ensure direnv is loaded in your current shell:
   ```shell
   echo $POSTGRES_USER
   ```

2. Run docker-compose from the same shell where direnv is active

3. Check that variables are exported (they should be in `.envrc.example`)

### Changes to .envrc not taking effect

**Problem:** Modified `.envrc` but variables unchanged.

**Solution:**
```shell
# Reload direnv
direnv allow

# Or reload explicitly
direnv reload
```

### UUID/GID not set correctly

**Problem:** Docker permission issues.

**Solution:**
The `.envrc.example` automatically sets these:
```shell
export UUID=$(id -u)
export GID=$(id -g)
```

Verify they're set:
```shell
echo "UUID: $UUID, GID: $GID"
```

## Advanced Usage

### Environment-Specific Overrides

Create environment-specific files:

```shell
# .envrc
source_env .envrc.example

# Override specific variables for your local setup
export POSTGRES_PASSWORD=my_custom_password
export PGADMIN_DEFAULT_EMAIL=myemail@example.com
```

### Using .env Files with direnv

You can also load traditional `.env` files:

```shell
# In .envrc
dotenv
```

This loads variables from a `.env` file if it exists.

### Conditional Configuration

```shell
# In .envrc
if [ "$HOSTNAME" = "development-machine" ]; then
  export DEBUG=true
else
  export DEBUG=false
fi
```

## Migration from Manual Export

If you were previously setting variables manually in `.bashrc`:

1. **Remove** the manual exports from `~/.bashrc`:
   ```shell
   # Remove these lines:
   # export UUID=$(id -u)
   # export GID=$(id -g)
   # export POSTGRES_PASSWORD=magnetdb
   # etc.
   ```

2. **Set up direnv** as described above

3. **Reload your shell:**
   ```shell
   source ~/.bashrc
   ```

4. **Navigate to the project:**
   ```shell
   cd /path/to/python_magnetdb
   # direnv will automatically load variables
   ```

## References

- [direnv official documentation](https://direnv.net/)
- [direnv GitHub repository](https://github.com/direnv/direnv)
- [direnv wiki](https://github.com/direnv/direnv/wiki)
