# MagnetDB

Tools for creating and manipulating a database designed for Magnet simulations.
Data may be partly retreived from **Lncmi control and monitoring website**.
See `python_magnetrun` for more details

## Development setup

0. Pre-requisites

* Certificates

On your host, set /etc/hosts:
```shell
echo "127.0.0.1 magnetdb-dev.local api.magnetdb-dev.local lemon.magnetdb-dev.local manager.lemon.magnetdb-dev.local auth.lemon.magnetdb-dev.local pgadmin.magnetdb-dev.local minio.magnetdb-dev.local traefik.magnetdb-dev.local" | sudo tee -a /etc/hosts
```

Create a self signed certificate for the magnetdb server:
   
```shell
mkdir -p certs
cd certs
mkcert -CAROOT
mkcert 'magnetdb-dev.local'
mkcert '*.magnetdb-dev.local'
mkcert -install
chmod 600 certs/*.key
```

* Create and Fix the permissions for pgadmin-data

```shell
sudo chown -R 5050:0 pgadmin-data 
```

1. Start dependencies with docker:

```shell
docker-compose -f docker-compose-dev-traefik-ssl.yml up
```

Note: if you see error messages about pgadmin, try to fix permissions on pgadmin-data directory by running `sudo chown -R 5050:5050 pgadmin-data`

5. Configure LemonLDAP (https://github.com/LemonLDAPNG/lemonldap-ng-docker):
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

4. Run migrations:

 Connect to magnetdb-api container

```shell
docker exec -it magnetdb-api bash
```


```shell
poetry run python3 manage.py migrate
```


7. Run seeds:

   To run this step you must have a '/data' directory. Connect to magnetdb-api container, check the directory is mounted, then
   
```shell
export DATA_DIR=/data
poetry run python3 -m python_magnetdb.seeds.seeds
poetry run python3 -m python_magnetdb.seeds.seed-again
poetry run python3 -m python_magnetdb.seeds.seed-records
```

8. PgAdmin setup

Load `https://pgadmin.magnetdb-dev.local/` in your web browser
add a server for magnetdb
   
magnetdb ip DB server shall be: `magnetdb-postgres`


