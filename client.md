## Pre-requisites

### MagnetDB server

Ensure the MagnetDB server is accessible. Add the following entries to `/etc/hosts` with the appropriate IP address:

```
aa.bb.xx.yy magnetdb.local
aa.bb.xx.yy api.magnetdb.local
aa.bb.xx.yy lemon.magnetdb.local
aa.bb.xx.yy manager.lemon.magnetdb.local
aa.bb.xx.yy auth.lemon.magnetdb.local
aa.bb.xx.yy pgadmin.magnetdb.local
aa.bb.xx.yy minio.magnetdb.local
aa.bb.xx.yy traefik.magnetdb.local
```

### Add the CA certificate

Retrieve and install the server certificate:

```bash
echo | openssl s_client -servername magnetdb.local -connect magnetdb.local:443 | cat > magnetdb.crt
sudo cp magnetdb.crt /usr/local/share/ca-certificates/
sudo update-ca-certificates
```
