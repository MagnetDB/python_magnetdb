# Prompt: Private PyPI Server Setup for MagnetDB

## Context

You are helping set up a private PyPI server for the LNCMI (Laboratoire National des Champs Magnétiques Intenses) MagnetDB project. The goal is to distribute internally developed Python packages to developers and students without relying on local path installs or git submodules.

## Infrastructure context

- All services run on Docker Compose with Traefik 3.x handling SSL termination
- Existing services: Django/FastAPI backend, PostgreSQL, Redis, MinIO, LemonLDAP::NG (OIDC/SSO)
- The PyPI server is **internal to LNCMI** — not publicly exposed by default
- Students and external collaborators access it via VPN **or** via GitHub Packages (see CI/CD prompt)
- The stack already has a working Traefik configuration with ACME certificates

## Packages to distribute

| Package | Type | Source |
|---|---|---|
| `python-magnetgeo` | Pure Python | Git submodule → GitHub repo |
| `python-magnetsetup` | Pure Python | Git submodule → GitHub repo |
| `python-magnetapi` | Pure Python | Git submodule → GitHub repo |
| `python-magnetrun` | Pure Python | GitHub repo |
| `magnettools` | C++ extension (pybind11) | Pre-built `.whl` via multistage Docker |

## Chosen solution: pypiserver

Use `pypiserver` (not Devpi, not Gitea) for simplicity. It is a single-container solution,
pip-compatible, and trivial to back with MinIO (S3) for package storage.

## Tasks to accomplish

### 1. Docker Compose service

Add `pypiserver` to the existing `docker-compose.yml`. Requirements:
- Use the official `pypiserver/pypiserver` image
- Back package storage with MinIO (already present) using the `--backend` S3 option,
  OR mount a local volume if S3 backend proves complex
- Expose via Traefik with a hostname like `pypi.magnetdb-dev.local` (dev) or
  `pypi.lncmi.cnrs.fr` (production)
- Authentication: htpasswd-based write access (upload requires credentials),
  unauthenticated read (install requires no auth for internal users on VPN)

### 2. Traefik routing

Add the appropriate Traefik labels to the pypiserver container so that:
- HTTPS is handled by Traefik (existing ACME setup)
- The service is reachable at `https://pypi.magnetdb-dev.local` in dev
- Middleware is applied consistently with other services in the stack

### 3. pip/Poetry client configuration

Show how to configure:
- `pip` to use the private index: `pip install --extra-index-url https://pypi.magnetdb-dev.local python-magnetgeo`
- `pyproject.toml` (Poetry/UV) to declare the private source:
  ```toml
  [[tool.poetry.source]]
  name = "lncmi"
  url = "https://pypi.magnetdb-dev.local/simple/"
  priority = "supplemental"
  ```
- `.env` / environment variable approach for CI credentials

### 4. Package upload workflow

Show how to upload a built wheel using `twine`:
```bash
twine upload \
  --repository-url https://pypi.magnetdb-dev.local \
  --username $PYPI_USER \
  --password $PYPI_TOKEN \
  dist/python_magnetgeo-1.0.0-py3-none-any.whl
```

### 5. pyproject.toml migration

Migrate the current `pyproject.toml` from local path dependencies to versioned package references:

**Before:**
```toml
python-magnetsetup = {path = "./python_magnetsetup"}
python-magnetgeo = {path = "./python_magnetgeo"}
magnettools = {path = "/home/feelpp/magnettools-1.1.0-cp311-cp311-linux_x86_64.whl"}
```

**After:**
```toml
python-magnetsetup = ">=0.1.0,<1.0.0"
python-magnetgeo = ">=1.0.0,<2.0.0"
magnettools = ">=1.1.0,<2.0.0"
```

With the private source declared so Poetry/pip knows where to find them.

## Constraints and decisions already made

- Do NOT use Devpi (too complex for a small team)
- Do NOT use Gitea package registry (not currently deployed)
- MinIO is already running — prefer using it as the storage backend if pypiserver supports it cleanly; fall back to a volume mount if the S3 integration adds significant complexity
- Authentication must be simple: a single service account for CI upload, read access open on VPN
- The server must survive a container restart without losing packages (persistent storage)

## Open questions to resolve during the session

1. Does `pypiserver` S3 backend work reliably with MinIO (path-style addressing)?
2. Should the pypiserver instance be shared between dev and production, or separate?
3. How to handle the `magnettools` wheel which is Python-version-specific (cp311)?
   Multiple wheels for cp311/cp312 may need to coexist.

## Definition of done

- `pypiserver` container running and reachable via Traefik
- All five packages installable with `pip install --extra-index-url ...`
- `pyproject.toml` updated to use version references instead of local paths
- Upload tested with `twine` for at least one package
- README section added explaining how to configure pip/Poetry for new developers
