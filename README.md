# MagnetDB

Tools for creating and manipulating a database designed for Magnet simulations.
Data may be partly retreived from **Lncmi control and monitoring website**.
See `python_magnetrun` for more details

## Cloning the depot

```shell
git clone ...
git submodule update --init --recursive
```

## Development setup

0. Pre-requisites

On your host:
```shell
echo "127.0.0.1 handler.sso.grenoble.lncmi.local api.manager.sso.grenoble.lncmi.local manager.sso.grenoble.lncmi.local sso.grenoble.lncmi.local test.sso.grenoble.lncmi" | sudo tee -a /etc/hosts
echo "127.0.0.1 magnetdb.grenoble.lncmi.local" | sudo tee -a /etc/hosts
echo "127.0.0.1 magnetdb-api.grenoble.lncmi.local" | sudo tee -a /etc/hosts
echo "127.0.0.1 magnetdb-worker.grenoble.lncmi.local" | sudo tee -a /etc/hosts
echo "127.0.0.1 redis.grenoble.lncmi.local" | sudo tee -a /etc/hosts
echo "127.0.0.1 postgres.grenoble.lncmi.local" | sudo tee -a /etc/hosts
echo "127.0.0.1 pgadmin.grenoble.lncmi.local" | sudo tee -a /etc/hosts
echo "127.0.0.1 minio.grenoble.lncmi.local" | sudo tee -a /etc/hosts
```

Create a self signed certificate for the magnetdb server
   
```shell
mkdir -p certs
openssl req -new -x509 -days 365 -nodes -out certs/cert.pem -keyout certs/cert.key
chmod 600 certs/cert.perm certs.cert.key
```

NB: eventually remove poetry-cache data before starting the services


1. Start the services

```shell
docker-compose up
```

The first time you run the service, you would need to:

* Fix the premissions for pgadmin-data

```shell
sudo chown -R 5050:5050 pgadmin-data
```

2. Set timezone in nginx-proxy


```shell
docker exec -it magnetdb-nginx-proxy
```

then run

```shell
ln -snf /usr/share/zoneinfo/Europe/Paris /etc/localtime
echo "Europe/Paris" > /etc/timezone
```

3. Create/Update Database

```shell
docker exec -it magnetdb-api /bin/bash
```

In the container, to perform database migration run:

```shell
poetry run orator migrate -c python_magnetdb/database.py
```

Eventually, run seeds to populate the database

```shell
export DATA_DIR=/data
poetry run python3 -m python_magnetdb.seeds
poetry run python3 -m python_magnetdb.seed-again
poetry run python3 -m python_magnetdb.seed-records
```
    
4. Configure LemonLDAP (https://github.com/LemonLDAPNG/lemonldap-ng-docker):
   1. Sign in to http://sso.grenoble.lncmi.local/ with dwho/dwho
   2. Enable OpenID Connect in Administration > WebSSO Manager > General Parameters > Issuer modules > OpenID Connect
   3. Create OpenID relying party in Administration > WebSSO Manager > OpenID Connect Relying Parties > Add OpenID Relying Party
   4. Go in Administration > WebSSO Manager > OpenID Connect Relying Parties > "Name of the relying party" > Options > Basic
   5. Set Client ID to `testid`
   6. Set Client secret to `testsecret`
   7. Set Allowed redirection addresses for login to `http://localhost:8080/sign_in`

5. Setup pgadmin

Load `localhost:5050/` in your web browser
add a server for magnetdb
   

Note: This may be needed to update the magnetdb IP after each restart of docker-compose
Check magnetdb ip server with: `docker inspect postgres-app  | grep IPAddress`

6. Custom LemonLDAP settings

```shell
docker exec -it lemonldap-app bash
```

7. To test

To change Lemonldap settings

```shell
firefox -private http://sso.grenoble.lncmi.local
```

To change user role:

```shell
firefox -private http://localhost:5050/
```

To start magnetdb:

```shell
firefox -private http://localhost:8080/
```

