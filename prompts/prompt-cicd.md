# Prompt: CI/CD Integration for MagnetDB Package Distribution

## Context

You are helping set up GitHub Actions workflows for the MagnetDB ecosystem at LNCMI.
The goal is to automate building and distributing:
- Pure Python wheels (`python-magnetgeo`, `python-magnetsetup`, `python-magnetapi`, `python-magnetrun`)
- The `magnettools` C++ extension wheel (via multistage Docker + auditwheel) → GitHub Packages
- The `magnettools` Debian package (`.deb`) → existing baremetal apt depot via `dupload`
- Pre-built Docker images → GitHub Container Registry (GHCR)

Pre-built images are the critical output for student and external use: they encapsulate
`magnettools` (installed from the LNCMI apt depot at build time) so that consumers never
need access to the depot at runtime.

## Repository map

```
MagnetDB/
├── python_magnetdb       ← main application (consumes all packages below)
├── python_magnetgeo      ← pure Python, git submodule of python_magnetdb
├── python_magnetsetup    ← pure Python, git submodule of python_magnetdb
├── python_magnetapi      ← pure Python, git submodule of python_magnetdb
├── python_magnetrun      ← pure Python
└── magnettools           ← C++ + pybind11, produces .deb AND .whl
```

## Infrastructure constraints

### The baremetal depot constraint

The LNCMI apt depot runs on a baremetal machine **only reachable from inside the LNCMI
network**. Any `docker build` step containing `apt-get install magnettools` fails if
the build runs somewhere that cannot reach that machine.

See `constraint-scenarios.md` for a full analysis of all failure scenarios and their
mitigations.

### The DockerHub base image — the structural mitigation

`magnettools` is already shipped as a Docker base image on DockerHub
(`feelpp/magnettools:X.Y.Z`). This is the key architectural decision that limits the
self-hosted runner requirement to a single job:

```
Self-hosted runner (LNCMI network) — required ONLY here:
  apt-get install magnettools → docker build → push feelpp/magnettools:1.1.0 (DockerHub)

GitHub-hosted runner — sufficient for ALL of these:
  FROM feelpp/magnettools:1.1.0 → add Python env → push ghcr.io/magnetdb/magnetdb-jupyter
  FROM feelpp/magnettools:1.1.0 → add api code  → push ghcr.io/magnetdb/python_magnetdb
  FROM ghcr.io/magnetdb/...     → run tests     → integration check
```

Downstream Dockerfiles `FROM feelpp/magnettools:X.Y.Z` — no `apt-get install magnettools`,
no depot contact. The depot constraint is encapsulated at the base image boundary.

### Runner assignment strategy

| Job | Runner | Reason |
|---|---|---|
| Build + publish pure Python wheels | `ubuntu-latest` | No depot access needed |
| Build + publish `magnettools` wheel (auditwheel) | `ubuntu-latest` | Uses manylinux image, not the depot |
| Build + upload `magnettools` .deb | `[self-hosted, lncmi]` | `dupload` targets internal depot |
| Build + push `feelpp/magnettools` base image | `[self-hosted, lncmi]` | `apt-get install magnettools` contacts depot |
| Build + push `python_magnetdb` api image | `ubuntu-latest` | `FROM feelpp/magnettools:X.Y.Z` — no depot |
| Build + push Jupyter image | `ubuntu-latest` | `FROM feelpp/magnettools:X.Y.Z` — no depot |
| Run integration tests | `ubuntu-latest` | Uses pre-built images from GHCR |

See `prompt-github-runner.md` for the full self-hosted runner setup procedure.

## Trigger strategy (ALL repos)

```yaml
on:
  push:
    tags:
      - 'v*.*.*'          # Semver tags only: v1.2.3
  workflow_dispatch:
    inputs:
      dry_run:
        description: 'Build without uploading/pushing'
        type: boolean
        default: false
```

Never trigger publishing on every push to main. Publish only on explicit version tags.

## Self-hosted runner setup

One self-hosted runner on an LNCMI machine covers all jobs that need depot access.

```bash
mkdir -p ~/actions-runner && cd ~/actions-runner
curl -o actions-runner-linux-x64.tar.gz -L \
  https://github.com/actions/runner/releases/download/v2.x.x/actions-runner-linux-x64-2.x.x.tar.gz
tar xzf actions-runner-linux-x64.tar.gz
./config.sh --url https://github.com/MagnetDB --token <ORG_RUNNER_TOKEN>
sudo ./svc.sh install && sudo ./svc.sh start
```

Label the runner: `self-hosted, lncmi, trixie`

The runner machine needs:
- Docker (with buildx)
- `dpkg-dev`, `devscripts`, `dupload` installed
- SSH access to the baremetal depot (via deploy key)
- Access to the LNCMI network (it's on the network by definition)
- GHCR write access (via `GITHUB_TOKEN` — works without extra config)

## Workflow 1: Pure Python packages

Applies to: `python_magnetgeo`, `python_magnetsetup`, `python_magnetapi`, `python_magnetrun`

```yaml
# .github/workflows/publish.yml
name: Build and Publish

on:
  push:
    tags: ['v*.*.*']
  workflow_dispatch:
    inputs:
      dry_run:
        type: boolean
        default: false

jobs:
  publish:
    runs-on: ubuntu-latest
    permissions:
      packages: write
      contents: read

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Build wheel and sdist
        run: |
          pip install build
          python -m build

      - name: Publish to GitHub Packages
        if: ${{ !inputs.dry_run }}
        run: |
          pip install twine
          twine upload \
            --repository-url https://nuget.pkg.github.com/MagnetDB/ \
            --username ${{ github.actor }} \
            --password ${{ secrets.GITHUB_TOKEN }} \
            dist/*

      - name: Trigger downstream integration check
        if: ${{ !inputs.dry_run }}
        uses: peter-evans/repository-dispatch@v3
        with:
          token: ${{ secrets.MAGNETDB_DISPATCH_TOKEN }}
          repository: MagnetDB/python_magnetdb
          event-type: package-published
          client-payload: >
            {"package": "${{ github.repository }}", "version": "${{ github.ref_name }}"}
```

## Workflow 2: magnettools — wheel (C++ + auditwheel)

Runs on GitHub-hosted runner. The multistage Docker build uses
`quay.io/pypa/manylinux_2_28_x86_64` as the build base — no LNCMI depot contact needed.

```yaml
# .github/workflows/publish-wheel.yml
name: Build and Publish magnettools Wheel

on:
  push:
    tags: ['v*.*.*']
  workflow_dispatch:
    inputs:
      dry_run:
        type: boolean
        default: false

jobs:
  build-wheel:
    runs-on: ubuntu-latest
    permissions:
      packages: write

    strategy:
      matrix:
        python: ['cp311', 'cp312']

    steps:
      - uses: actions/checkout@v4

      - uses: docker/setup-buildx-action@v3

      - name: Build repaired wheel via multistage Docker
        run: |
          docker buildx build \
            --build-arg PYTHON_VERSION=${{ matrix.python }} \
            --target export \
            --output type=local,dest=./dist \
            .

      - name: Verify wheel (auditwheel show)
        run: |
          pip install auditwheel
          auditwheel show dist/magnettools-*.whl

      - name: Smoke test in clean trixie container
        run: |
          docker run --rm \
            -v $(pwd)/dist:/dist \
            debian:trixie \
            bash -c "pip install /dist/magnettools-*.whl && \
                     python -c 'import magnettools; print(magnettools.__version__)'"

      - name: Publish to GitHub Packages
        if: ${{ !inputs.dry_run }}
        run: |
          pip install twine
          twine upload \
            --repository-url https://nuget.pkg.github.com/MagnetDB/ \
            --username ${{ github.actor }} \
            --password ${{ secrets.GITHUB_TOKEN }} \
            dist/magnettools-*.whl
```

## Workflow 3: magnettools — Debian package + apt depot upload

Runs on self-hosted runner (LNCMI network). Uses `dupload` with the existing
`apt-ftparchive`-based depot. The CI signing subkey is used (see apt depot prompt).

```yaml
# .github/workflows/publish-deb.yml
name: Build and Publish magnettools .deb

on:
  push:
    tags: ['v*.*.*']
  workflow_dispatch:
    inputs:
      dry_run:
        type: boolean
        default: false

jobs:
  build-deb:
    runs-on: [self-hosted, lncmi, trixie]

    steps:
      - uses: actions/checkout@v4

      - name: Install build dependencies
        run: |
          sudo apt-get update
          sudo apt-get install -y \
            debhelper devscripts cmake \
            libboost-python3-dev pybind11-dev

      - name: Set version from git tag
        run: |
          VERSION=${GITHUB_REF_NAME#v}
          echo "PKG_VERSION=${VERSION}" >> $GITHUB_ENV
          dch --newversion "${VERSION}-1" \
              --distribution trixie \
              "Release ${VERSION}"

      - name: Build .deb
        run: dpkg-buildpackage -us -uc -b

      - name: Import CI signing subkey
        run: echo "${{ secrets.APT_SIGNING_KEY }}" | gpg --import

      - name: Configure dupload
        run: |
          cat > ~/.dupload.conf <<'EOF'
          package config;
          $cfg{"lncmi"} = {
              fqdn         => "${{ secrets.APT_DEPOT_HOST }}",
              method       => "scpb",
              incoming     => "${{ secrets.APT_DEPOT_INCOMING }}",
              dinstall_runs => 1,
          };
          $cfg{"lncmi"}{postupload}{"changes"} = "
              ssh -i $HOME/.ssh/apt_deploy_key \
                  apt-ci\@${{ secrets.APT_DEPOT_HOST }} \
                  /srv/apt/scripts/ci-post-upload.sh
          "; 1;
          EOF

      - name: Configure SSH deploy key
        run: |
          mkdir -p ~/.ssh
          echo "${{ secrets.APT_DEPLOY_KEY }}" > ~/.ssh/apt_deploy_key
          chmod 600 ~/.ssh/apt_deploy_key
          echo "StrictHostKeyChecking accept-new" >> ~/.ssh/config

      - name: Upload to apt depot
        if: ${{ !inputs.dry_run }}
        run: dupload --to lncmi ../magnettools_*.changes

      - name: Upload .deb as GitHub release asset
        if: ${{ !inputs.dry_run }}
        uses: softprops/action-gh-release@v2
        with:
          files: ../magnettools_*.deb

      - name: Cleanup secrets from runner
        if: always()
        run: |
          rm -f ~/.ssh/apt_deploy_key
          gpg --batch --yes --delete-secret-keys \
            $(gpg --list-secret-keys --with-colons | grep '^fpr' | head -1 | cut -d: -f10) \
            || true
```

## Workflow 4a: magnettools — DockerHub base image build and push

Runs on self-hosted runner. This is the ONLY image build job that contacts the apt depot.
The base image (`feelpp/magnettools`) is pushed to DockerHub and becomes the foundation
for all downstream images.

```yaml
# In the magnettools repository
# .github/workflows/publish-image-base.yml
name: Build and Push magnettools Base Image

on:
  push:
    tags: ['v*.*.*']
  workflow_dispatch:
    inputs:
      dry_run:
        type: boolean
        default: false

jobs:
  build-base-image:
    runs-on: [self-hosted, lncmi, trixie]
    # Self-hosted required: apt-get install magnettools contacts the baremetal depot

    steps:
      - uses: actions/checkout@v4

      - uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - uses: docker/setup-buildx-action@v3

      - name: Build and push base image
        uses: docker/build-push-action@v6
        with:
          context: .
          file: Dockerfile.base
          push: ${{ !inputs.dry_run }}
          tags: |
            feelpp/magnettools:${{ github.ref_name }}
            feelpp/magnettools:latest
          build-args: |
            APT_DEPOT_URL=https://${{ secrets.APT_DEPOT_HOST }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
          # The apt-get install magnettools layer is cached until version changes.
          # Most builds never invalidate it.
```

`Dockerfile.base` structure — `magnettools` installed early for stable caching:
```dockerfile
FROM debian:trixie-slim
ARG APT_DEPOT_URL=https://apt.lncmi.cnrs.fr
ARG MAGNETTOOLS_VERSION=1.1.0

# Layer 1: depot setup + magnettools install
# Only invalidated when MAGNETTOOLS_VERSION changes
RUN curl -fsSL ${APT_DEPOT_URL}/lncmi-apt.gpg.pub \
      | gpg --dearmor | tee /etc/apt/keyrings/lncmi.gpg > /dev/null \
    && echo "deb [signed-by=/etc/apt/keyrings/lncmi.gpg] \
      ${APT_DEPOT_URL}/apt trixie main" \
      > /etc/apt/sources.list.d/lncmi.list \
    && apt-get update \
    && apt-get install -y magnettools=${MAGNETTOOLS_VERSION} \
    && rm -rf /var/lib/apt/lists/*
```

## Workflow 4b: python_magnetdb — api and Jupyter image build and push

Runs on GitHub-hosted runner. `FROM feelpp/magnettools:X.Y.Z` — no depot contact.

```yaml
# .github/workflows/publish-image.yml
name: Build and Push Docker Images

on:
  push:
    tags: ['v*.*.*']
  workflow_dispatch:
    inputs:
      dry_run:
        type: boolean
        default: false
      base_image_tag:
        description: 'feelpp/magnettools tag to use as base'
        default: 'latest'

jobs:
  build-image:
    runs-on: ubuntu-latest   # GitHub-hosted: no depot access needed
    permissions:
      packages: write

    steps:
      - uses: actions/checkout@v4
        with:
          submodules: true

      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - uses: docker/setup-buildx-action@v3

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ghcr.io/magnetdb/python_magnetdb
          tags: |
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=raw,value=latest

      - name: Build and push api image
        uses: docker/build-push-action@v6
        with:
          context: .
          push: ${{ !inputs.dry_run }}
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          build-args: |
            BASE_IMAGE=feelpp/magnettools:${{ inputs.base_image_tag || 'latest' }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

      - name: Build and push jupyter image
        uses: docker/build-push-action@v6
        with:
          context: .
          file: Dockerfile.jupyter
          push: ${{ !inputs.dry_run }}
          tags: |
            ghcr.io/magnetdb/magnetdb-jupyter:${{ github.ref_name }}
            ghcr.io/magnetdb/magnetdb-jupyter:latest
          build-args: |
            BASE_IMAGE=feelpp/magnettools:${{ inputs.base_image_tag || 'latest' }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

`Dockerfile` / `Dockerfile.jupyter` for downstream images:
```dockerfile
ARG BASE_IMAGE=feelpp/magnettools:latest
FROM ${BASE_IMAGE}
# No apt-get install magnettools — already in base. No depot contact.

# Python environment
COPY pyproject.toml .
RUN pip install --no-deps .
COPY . .
```

## Workflow 5: Integration check

Runs on GitHub-hosted runner. Uses pre-built images from GHCR — no depot access needed.

```yaml
# .github/workflows/integration-check.yml
name: Integration Check

on:
  repository_dispatch:
    types: [package-published]
  schedule:
    - cron: '0 6 * * 1'    # Weekly Monday

jobs:
  check:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Configure pip for GitHub Packages
        run: |
          pip config set global.extra-index-url \
            https://${{ github.actor }}:${{ secrets.GITHUB_TOKEN }}@nuget.pkg.github.com/MagnetDB/simple/

      - name: Install latest package versions
        run: pip install python-magnetgeo python-magnetsetup python-magnetapi

      - name: Run integration tests against pre-built image
        run: |
          docker compose -f docker-compose.test.yml up --abort-on-container-exit
        env:
          MAGNETDB_IMAGE: ghcr.io/magnetdb/python_magnetdb:latest
```

## Student docker-compose.yml

Students pull pre-built images. No `build:` sections, no depot access, no VPN needed
for `docker compose up`:

```yaml
# docker-compose.student.yml
services:
  api:
    image: ghcr.io/magnetdb/python_magnetdb:${MAGNETDB_VERSION:-latest}
    environment:
      - DATABASE_URL=postgresql://magnetdb:magnetdb@postgres/magnetdb
      - REDIS_URL=redis://redis:6379
      - MINIO_URL=http://minio:9000

  jupyter:
    image: ghcr.io/magnetdb/magnetdb-jupyter:${MAGNETDB_VERSION:-latest}
    ports:
      - "8888:8888"

  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: magnetdb
      POSTGRES_USER: magnetdb
      POSTGRES_PASSWORD: magnetdb

  redis:
    image: redis:7-alpine

  minio:
    image: minio/minio
    command: server /data
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin

# No apt depot service — it's a baremetal external dependency
# Only needed during CI image builds, not at runtime
```

## Secrets to configure

### GitHub Secrets (repository or organization level)

| Secret | Used in | Description |
|---|---|---|
| `APT_SIGNING_KEY` | magnettools deb workflow | GPG armor export of DD signing subkey (`--export-secret-subkeys <FPR>!`) |
| `APT_DEPLOY_KEY` | magnettools deb workflow | SSH private key for `apt-ci@depot` |
| `APT_DEPOT_HOST` | magnettools deb + base image workflows | Hostname of the baremetal depot (e.g. `apt.lncmi.cnrs.fr`) |
| `APT_DEPOT_INCOMING` | magnettools deb workflow | Path to the pool incoming dir on the depot |
| `DOCKERHUB_USERNAME` | magnettools base image workflow | DockerHub account name for `feelpp/magnettools` |
| `DOCKERHUB_TOKEN` | magnettools base image workflow | DockerHub access token (not password) — write access to `feelpp/magnettools` |
| `MAGNETDB_DISPATCH_TOKEN` | upstream package repos | GitHub PAT with `repo` scope for triggering downstream checks |

`GITHUB_TOKEN` is automatic — no configuration needed for GHCR or GitHub Packages uploads.

### Self-hosted runner requirements

The runner machine needs:
- On LNCMI network (satisfies depot access constraint automatically)
- Docker with buildx plugin
- `dpkg-dev devscripts dupload` installed
- The `apt-ci` SSH public key registered on the baremetal depot (one-time setup)
- No stored credentials — all secrets injected per-job from GitHub Secrets

## pip/Poetry configuration for consuming GitHub Packages

### For developers

```bash
pip config set global.extra-index-url \
  https://<your-github-username>:<your-github-pat>@nuget.pkg.github.com/MagnetDB/simple/
```

### pyproject.toml (after migration from local paths)

```toml
# python_magnetdb/pyproject.toml — after migration

[tool.poetry.dependencies]
python = ">=3.11"
# magnettools is installed as a system .deb — NOT declared here
# It is available in the Python environment via the system site-packages
python-magnetsetup = ">=0.1.0,<1.0.0"
python-magnetgeo   = ">=1.0.0,<2.0.0"
python-magnetapi   = ">=0.1.0,<1.0.0"

[[tool.poetry.source]]
name     = "lncmi-github"
url      = "https://nuget.pkg.github.com/MagnetDB/simple/"
priority = "supplemental"
```

Note: `magnettools` is NOT declared as a Poetry dependency — it's a system package
installed via `apt-get` in the Dockerfile. Poetry only manages pure Python packages.
The C++ bindings are available because the system Python path includes the depot-installed
package.

## Versioning conventions

- All packages use semantic versioning: `vMAJOR.MINOR.PATCH`
- Tags are created on each package's own repo, not on `python_magnetdb`
- Docker images are tagged with the `python_magnetdb` version: `ghcr.io/magnetdb/python_magnetdb:v1.2.3`
- The `latest` tag always points to the most recent stable release
- `magnettools` Debian package version tracks the C++ library version independently

## Definition of done

- Tagging `v1.x.x` on `python_magnetgeo` → wheel published to GitHub Packages,
  integration check triggered on `python_magnetdb`
- Tagging `v1.x.x` on `magnettools` → wheel published to GitHub Packages (manylinux),
  `.deb` uploaded to baremetal depot via `dupload`, depot index rebuilt and re-signed
  with CI subkey
- Tagging `v1.x.x` on `python_magnetdb` → Docker images built (self-hosted runner,
  `apt-get install magnettools` succeeds) and pushed to GHCR
- Student `docker compose up` works with no VPN, no build step, no depot access
- `python_magnetdb/pyproject.toml` has no `{path = ...}` dependencies
- Integration test workflow passes on GitHub-hosted runner using GHCR images
- All secrets documented, rotation procedures written, calendar reminders set
