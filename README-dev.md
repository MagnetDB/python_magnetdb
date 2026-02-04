# `MagnetDB`

Tools for creating and manipulating a database designed for Magnet simulations.
Data may be partly retreived from **Lncmi control and monitoring website**.
See `python_magnetrun` for more details

## Development setup

0. Pre-requisites

* Hosts settings

On your host, set /etc/hosts:
```shell
echo "127.0.0.1 magnetdb-dev.local api.magnetdb-dev.local lemon.magnetdb-dev.local manager.lemon.magnetdb-dev.local auth.lemon.magnetdb-dev.local pgadmin.magnetdb-dev.local minio.magnetdb-dev.local traefik.magnetdb-dev.local" | sudo tee -a /etc/hosts
```

* Environment Variables & Secret Management with direnv

Install direnv for automatic environment variable loading:

**Install direnv:**
```shell
# On Debian/Ubuntu
sudo apt-get install direnv
```

**Configure your shell:**

Add the following to your shell configuration file:

For bash (~/.bashrc):
```shell
eval "$(direnv hook bash)"
```

For zsh (~/.zshrc):
```shell
eval "$(direnv hook zsh)"
```

For fish (~/.config/fish/config.fish):
```shell
direnv hook fish | source
```

Restart your shell or run `source ~/.bashrc` (or equivalent).

**Setup environment variables:**

```shell
# Copy the example file
cp .envrc.example .envrc

# Edit .envrc to customize any values (optional - defaults should work)
# nano .envrc  # or your preferred editor

# Allow direnv to load the file
direnv allow
```

The `.envrc` file will automatically load environment variables when you `cd` into the project directory. This provides:
- Secure secret management (`.envrc` is gitignored)
- Automatic environment setup
- Easy customization for local development
- UUID/GID automatically set for Docker permissions

> **Note:** The `.envrc.example` file contains all default values used by docker-compose. You can use it as-is or customize for your needs.

* magetdb-data directory

Create a `magnetdb-data` directory in the main repo directory:

```shell
mkdir ../magnetdb-data
mkdir -p ../magnetdb-data/pgadmin-data
mkdir -p ../magnetdb-data/django/poetry-cache
```

Set appropriate ownership/permissions if needed.

```shell
chmod 775 ../magnetdb-data
chmod 775 ../magnetdb-data/pgadmin-data
chmod 775 ../magnetdb-data/django
chmod 775 ../magnetdb-data/django/poetry-cache

chown -R 5050:5050 ../magnetdb-data/pgadmin-data
chown -R $(id -u):$(id -g) ../magnetdb-data/django/poetry-cache
```
* Certificates

Create a self signed certificate for the magnetdb server:
   
```shell
mkdir -p ../magnetdb-data/certs
cd ../magnetdb-data/certs
mkcert -CAROOT
mkcert 'magnetdb-dev.local' '*.magnetdb-dev.local'  '*.lemon.magnetdb-dev.local'
mkcert -install
chmod 600 certs/*.key
```

> **Note:** The `mkcert -install` command automatically installs the CA certificate for most browsers.
> 
> For detailed browser-specific installation instructions, troubleshooting, and verification steps, see [certificates.md](certificates.md).


* Legacy Bashrc Setup (Optional - direnv is preferred)

> **Recommended:** Use direnv (see above) for automatic environment variable management.

If you prefer not to use direnv, manually add these lines to your `.bashrc`:

```shell
# UID exists by default
export UUID=$(id -u)
export GID=$(id -g)
```

Start a new shell to load the new bashrc or `source ~/.bashrc`

> NOTE
> * For zsh:
>
> ```shell
> # Exporting UUID and GID
> export UUID=$(id -u)
> export GID=$(id -g)
> ```
> and then `source ~/.zshrc`
>
> * For other shell see the shell docs.
> * **direnv handles this automatically** - see the Environment Variables section above.

1. Start dependencies with docker:

```shell
docker-compose -f docker-compose-dev-traefik-ssl.yml up
```

> Note
> if you see error messages about pgadmin, try to fix permissions on pgadmin-data directory by running `sudo chown -R 5050:5050 pgadmin-data`
> relaunch docker-compose

2. Configure LemonLDAP (https://github.com/LemonLDAPNG/lemonldap-ng-docker):
   1. Sign in to https://auth.lemon.magnetdb-dev.local/ with dwho/dwho
   2. Enable OpenID Connect in Administration > WebSSO Manager > General Parameters > Issuer modules > OpenID Connect
   3. Create OpenID relying party in Administration > WebSSO Manager > OpenID Connect Relying Parties > Add OpenID Relying Party
   4. Go in Administration > WebSSO Manager > OpenID Connect Relying Parties > "Name of the relying party" > Options > Basic
   5. Set Client ID to `testid`
   6. Set Client secret to `testsecret`
   7. Set Allowed redirection addresses for login to `https://magnetdb-dev.local/sign_in`


3. Setup Minio bucket:
   1. Sign in to https://minio.magnetdb-dev.local/ with minio/minio123
   2. Create bucket on https://minio.magnetdb-dev.local/add-bucket

> **Minio** basic setup
> basic setup is done automatically (for more details see [storage.md](storage.md))
> So you can skip this step if you want to use the automatic bucket creation feature.

4. Run migrations:

 Connect to magnetdb-api container

```shell
docker exec -it magnetdb-api bash
```


```shell
poetry run python3 manage.py migrate
```

> **Database Management Scripts**
>
> For database backup, restore, and maintenance operations, see [db-scripts/README.md](db-scripts/README.md).

> **Important: Modifying Django Models**
>
> When you modify files in `python_magnetdb/models/`, you **must** create and apply migrations:
>
> 1. After modifying any model files, create a migration:
>    ```shell
>    poetry run python manage.py makemigrations
>    ```
>
> 2. Review the generated migration file in `python_magnetdb/migrations/`
>
> 3. Apply the migration:
>    ```shell
>    poetry run python manage.py migrate
>    ```
>
> For detailed migration documentation and history, see [migrations.md](migrations.md).


5. Run seeds:

   Before running seeds, make sur that data directory exists and that it contains required files (aka geometry yaml files).
In the `magnetdb` main repo, add a symlink to actual directory holding data, for example:

```shell
ln -s ../python_magnetsetup/data data
```

   To run this step you must have a '/data' directory. Connect to magnetdb-api container, check the directory is mounted, then
   
```shell
export DATA_DIR=/data

# version test
poetry run python3 -m python_magnetdb.seeds.seeds # test only
poetry run python3 -m python_magnetdb.seeds.seed-probes

# version advanced test
poetry run python3 -m python_magnetdb.seeds.seeds-Bitters # bitters only
poetry run python3 -m python_magnetdb.seeds.seed-M18110501
poetry run python3 -m python_magnetdb.seeds.seed-M19020601
poetry run python3 -m python_magnetdb.seeds.seed-M19061901
poetry run python3 -m python_magnetdb.seeds.seed-M19071101
poetry run python3 -m python_magnetdb.seeds.seed-M20022001
poetry run python3 -m python_magnetdb.seeds.seed-M22011801 
poetry run python3 -m python_magnetdb.seeds.seed-HL37 # HL-37 magnet
poetry run python3 -m python_magnetdb.seeds.seed-Hybrid # Hybrid magnet
poetry run python3 -m python_magnetdb.seeds.seed-records
```

> **For a production version**, use `python_magnetapi` instead of seeds.
>
> * retreive data from LNCMI control and monitoring website using ``python_magnetrun
> 
> ```shell
> poetry run python3 -m python_magnetrun.requests.cli --user email --datadir srvdata
> ```
>
> You need to have a LNCMI email account for that
> This will dump data files in `srvdata` directory, 
> 
> * use `python_magnetapi` to import data into magnetdb.
> ```shell
> poetry run python3 -m python_magnetapi.importer.cli --datadir srvdata ...
> ```

6. PgAdmin setup

Load `https://pgadmin.magnetdb-dev.local/` in your web browser
add a server for `magnetdb`
   
`magnetdb` ip DB server shall be: `magnetdb-postgres`

7. Access MagnetDB web app

Load `https://magnetdb-dev.local/` in your web browser
Login with your lemonldap credentials (dwho/dwho)

Next, load `https://pgadmin.magnetdb-dev.local/` in your web browser
Change dwho role to "Admin"

# API calls

## How to get YOUR_TOKEN

* login to magnetdb-dev.local
* check your settings
* copy YOUR_TOKEN

## Examples

```bash
curl -s -H "Authorization: YOUR_TOKEN" "https://api.magnetdb-dev.local/api/magnets/1" | jq
```
