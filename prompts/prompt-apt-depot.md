# Prompt: Private apt Depot — CI Integration for MagnetDB

## Context

You are helping integrate an **existing** private Debian apt repository into the MagnetDB
CI/CD pipeline. The depot already exists and works — the goal is NOT to set it up from
scratch, but to make it accessible from GitHub Actions and to document it properly as an
external dependency of the MagnetDB Docker Compose stack.

## Existing infrastructure

- **Depot tool**: `apt-ftparchive` (generates `Packages`, `Release`, `Sources` index files)
- **Upload tool**: `dupload` (uploads `.changes` + `.deb` files via SCP, triggers index rebuild)
- **Hosting**: baremetal machine on the LNCMI internal network
- **Access**: only reachable from inside LNCMI (no public exposure) — developers use VPN
- **Signing**: Debian Developer GPG key (personal key, registered with Debian keyserver)
- **Target distro**: Debian trixie / amd64
- **Packages currently distributed**: `magnettools` and its C++ runtime dependencies

## Signing key strategy — DD subkey for CI

The existing repo is signed with a personal Debian Developer key. This key must NOT be
exported wholesale into CI secrets — it carries Debian Developer identity and web-of-trust
relationships. The correct approach is a **dedicated signing subkey**.

### Create a signing-only subkey

```bash
gpg --expert --edit-key christophe.trophime@lncmi.cnrs.fr
gpg> addkey
# Choose: RSA (sign only)
# Key size: 4096
# Expiry: 2 years (set a reminder to rotate)
# Comment: "LNCMI apt repo CI signing"
gpg> save
```

### Export only the subkey private material

The `!` suffix is mandatory — without it gpg exports the full secret key including
the primary key material.

```bash
# Find the subkey fingerprint
gpg --list-keys --with-subkey-fingerprints christophe.trophime@lncmi.cnrs.fr

# Export ONLY the subkey (! = this subkey only, not the primary)
gpg --armor --export-secret-subkeys <SUBKEY_FINGERPRINT>! \
  > lncmi-repo-ci-signing-subkey.asc

# This file goes into GitHub Secrets as APT_SIGNING_KEY
# NEVER commit it to git
```

### Import on the CI runner

```bash
echo "${{ secrets.APT_SIGNING_KEY }}" | gpg --import
# gpg imports the subkey; the primary key appears as [stub]
# Signing works because the subkey private material is present
```

### Use the subkey explicitly in the postupload hook

The `!` forces gpg to use that specific subkey, not the primary:

```bash
gpg --batch -u <SUBKEY_FINGERPRINT>! \
  -bao dists/trixie/Release.gpg dists/trixie/Release
```

### Subkey rotation

Set a calendar reminder before expiry (2 years). Rotation procedure:
1. `gpg --expert --edit-key` → `addkey` → new signing subkey
2. Revoke the old CI subkey: `gpg --edit-key` → `key N` → `revkey`
3. Re-export and update the GitHub Secret
4. Update `APT_SIGNING_KEY` in all repos that use it
5. The public key served at the depot URL automatically includes the new subkey
   after `gpg --export --armor | ...` is re-run

## dupload configuration for CI

`dupload` is the upload client. It already works manually — the CI integration just
needs a dupload config that:
- targets the baremetal depot via SCP
- triggers `apt-ftparchive` index rebuild and GPG re-signing in the `postupload` hook
- uses the CI subkey fingerprint for signing

### `~/.dupload.conf` for the CI runner

```perl
package config;

$cfg{"lncmi"} = {
    fqdn         => "apt.lncmi.cnrs.fr",   # baremetal depot hostname
    method       => "scpb",                 # SCP batch (no interactive prompts)
    incoming     => "/srv/apt/pool/main",   # adjust to actual pool path
    dinstall_runs => 1,                     # suppress dupload announce email
};

# Rebuild index + re-sign after every successful upload
$cfg{"lncmi"}{postupload}{"changes"} = "
    ssh apt-ci\@apt.lncmi.cnrs.fr '
        cd /srv/apt &&
        apt-ftparchive generate aptgenerate.conf &&
        apt-ftparchive release -c aptftp.conf dists/trixie \
            > dists/trixie/Release &&
        rm -f dists/trixie/Release.gpg &&
        gpg --batch -u <SUBKEY_FINGERPRINT>! \
            -bao dists/trixie/Release.gpg dists/trixie/Release
    '
"; 1;
```

Note: `apt-ci` is a dedicated unprivileged user on the baremetal machine with:
- write access to `/srv/apt/pool/main` and `/srv/apt/dists/`
- the CI signing subkey imported in its GPG keyring
- SSH access restricted to the `authorized_keys` of the CI deploy key

### SSH deploy key setup (one-time, on the baremetal machine)

```bash
# Generate a dedicated deploy key (no passphrase — used by CI)
ssh-keygen -t ed25519 -C "magnettools-ci-deploy" -f magnettools-ci-deploy -N ""

# Add public key to the depot machine
cat magnettools-ci-deploy.pub >> ~apt-ci/.ssh/authorized_keys

# Restrict it to the post-upload commands only (belt-and-suspenders)
# In authorized_keys, prefix with:
# command="/srv/apt/scripts/ci-post-upload.sh",no-pty,no-port-forwarding <pubkey>

# Private key → GitHub Secret: APT_DEPLOY_KEY
# NEVER commit to git
```

## Tasks to accomplish in this session

### 1. Verify the existing dupload/apt-ftparchive pipeline

Before adding CI, confirm the current manual flow still works end-to-end:

```bash
# Build the package
dpkg-buildpackage -us -uc -b

# Upload (manual, with your personal DD key for signing)
dupload --to lncmi ../magnettools_*.changes

# Verify the depot was updated
apt-get update && apt-cache show magnettools
```

### 2. Create the `apt-ci` system user on the baremetal machine

```bash
sudo adduser --system --no-create-home --shell /bin/bash apt-ci
sudo mkdir -p /home/apt-ci/.ssh /home/apt-ci/.gnupg
sudo chown -R apt-ci:apt-ci /home/apt-ci
sudo chmod 700 /home/apt-ci/.gnupg

# Give write access to the relevant depot directories
sudo setfacl -R -m u:apt-ci:rwx /srv/apt/pool/main
sudo setfacl -R -m u:apt-ci:rwx /srv/apt/dists/trixie
```

### 3. Import the CI signing subkey on the depot machine

```bash
sudo -u apt-ci gpg --import lncmi-repo-ci-signing-subkey.asc
sudo -u apt-ci gpg --list-secret-keys  # verify subkey shows as [stub] primary + live subkey
```

### 4. Write the restricted post-upload script

Rather than allowing full SSH shell access from CI, restrict the deploy key to a
single script:

```bash
# /srv/apt/scripts/ci-post-upload.sh
#!/bin/bash
set -euo pipefail
cd /srv/apt
apt-ftparchive generate aptgenerate.conf
apt-ftparchive release -c aptftp.conf dists/trixie > dists/trixie/Release
rm -f dists/trixie/Release.gpg
gpg --batch -u <SUBKEY_FINGERPRINT>! \
    -bao dists/trixie/Release.gpg dists/trixie/Release
echo "Depot updated successfully."
```

### 5. Document the depot as an external dependency in docker-compose

The depot is NOT declared as a Compose service — it is a baremetal external dependency.
Document it consistently with other external dependencies:

```yaml
# docker-compose.yml
services:
  api:
    build:
      context: .
      args:
        # Depot URL — only reachable on LNCMI network or VPN
        # For pre-built images (CI/student use), this is not needed at runtime
        APT_DEPOT_URL: ${APT_DEPOT_URL:-https://apt.lncmi.cnrs.fr}
```

```bash
# .env.example (committed to git — just a URL, not a secret)
APT_DEPOT_URL=https://apt.lncmi.cnrs.fr

# DEPLOYMENT.md — list under "External dependencies (must exist before docker compose up)"
# - LemonLDAP::NG SSO: https://auth.lncmi.cnrs.fr
# - LNCMI apt depot: https://apt.lncmi.cnrs.fr  (LNCMI network / VPN required)
# - MinIO (if external): ...
```

### 6. Dockerfile integration

```dockerfile
# Dockerfile (api service)
ARG APT_DEPOT_URL=https://apt.lncmi.cnrs.fr

RUN curl -fsSL ${APT_DEPOT_URL}/lncmi-apt.gpg.pub \
      | gpg --dearmor \
      | tee /etc/apt/keyrings/lncmi.gpg > /dev/null \
    && echo "deb [signed-by=/etc/apt/keyrings/lncmi.gpg] \
      ${APT_DEPOT_URL}/apt trixie main" \
      > /etc/apt/sources.list.d/lncmi.list \
    && apt-get update \
    && apt-get install -y magnettools \
    && rm -rf /var/lib/apt/lists/*
```

This replaces the current `{path = "/home/feelpp/magnettools-1.1.0...whl"}` in
`pyproject.toml` — `magnettools` is installed as a system package and the Python
bindings are available automatically.

## Constraints

- The baremetal depot is only reachable on the LNCMI network or VPN
- `docker compose build` therefore only works on LNCMI network — this is intentional;
  see the CI/CD prompt for the pre-built image strategy that removes this constraint
  for students and external collaborators
- GPG primary key never leaves the developer's machine — only the subkey export
  is in CI secrets
- The `apt-ci` user on the depot machine has minimal privileges (write to pool + dists only)
- CI deploy key is restricted to the post-upload script via `authorized_keys` `command=`

## Open questions to resolve during the session

1. What is the actual hostname and pool path of the baremetal depot?
2. Does the existing `dupload.conf` already have a `postupload` hook, or is index
   rebuild done manually today?
3. Is the CI signing subkey approach acceptable, or is there a lab policy requiring
   the full DD key for all depot signatures?
4. What is the exact `apt-ftparchive` config structure (`aptftp.conf`,
   `aptgenerate.conf`) currently in use? The CI hook must call the same commands
   in the same way as the manual process.
5. Should `bookworm` be added as a second codename for older LNCMI machines?

## Definition of done

- `dupload --to lncmi` from the self-hosted CI runner uploads a `.deb` and
  triggers automatic index rebuild + signing
- The depot is signed with the CI subkey (same public key, trusted by all LNCMI machines)
- `apt-get install magnettools` works on a clean trixie machine on LNCMI VPN
  after `apt-get update`
- The Dockerfile `apt-get install magnettools` works during CI build (self-hosted runner
  on LNCMI network)
- `DEPLOYMENT.md` documents the depot as an external dependency with setup instructions
- Subkey rotation procedure is documented and a calendar reminder is set
