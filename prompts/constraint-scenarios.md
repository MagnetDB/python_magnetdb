# Baremetal apt Depot — Constraint Analysis and Mitigations

## The constraint

The LNCMI apt depot runs on a baremetal machine accessible only from inside the LNCMI
network (or via VPN). Any `docker build` step containing `apt-get install magnettools`
fails if the build runs somewhere that cannot reach that machine.

This is an accepted architectural constraint, not a problem to fix. The mitigations below
are designed to make it invisible in normal workflows and manageable when it surfaces.

---

## Important: the DockerHub base image

`magnettools` is already distributed as a Docker base image on DockerHub
(e.g. `feelpp/magnettools:latest` or similar). This is a first-class mitigation
that changes the constraint picture significantly:

- Images that `FROM` this base already have `magnettools` installed
- Those downstream builds have **no depot dependency at all**
- The depot contact is confined entirely to the job that builds and pushes the base image
- Any GitHub-hosted runner can build derivative images by pulling from DockerHub

The critical implication: **the self-hosted runner is only required for the base image
build itself** (the `magnettools` Docker image pushed to DockerHub). Everything downstream
— the `python_magnetdb` api image, the Jupyter image — can delegate to GitHub-hosted runners
by `FROM`-ing the DockerHub base.

```
Self-hosted runner (LNCMI network) — required only here:
  apt-get install magnettools → docker build → push feelpp/magnettools:X.Y.Z (DockerHub)

GitHub-hosted runner — sufficient for all of these:
  FROM feelpp/magnettools:X.Y.Z → add Python env → push ghcr.io/magnetdb/magnetdb-jupyter:X.Y.Z
  FROM feelpp/magnettools:X.Y.Z → add api code  → push ghcr.io/magnetdb/python_magnetdb:X.Y.Z
```

---

## Scenario 1 — Developer rebuilds the image locally, off-site (no VPN)

**Trigger**: Developer runs `docker compose build` from home without VPN.

**What happens**: The `RUN apt-get install magnettools` step in the api/jupyter Dockerfile
gets a connection timeout or DNS failure. The build fails with a generic error that is
confusing without context.

**Does the DockerHub base image help here?** Yes — if the api and jupyter Dockerfiles
`FROM feelpp/magnettools:X.Y.Z` (public DockerHub), the depot is never contacted.
The developer can rebuild these images from anywhere.

**Remaining exposure**: Only the base image build itself (which developers should
never need to run locally anyway — it's a CI artifact).

**Mitigations**:
- Document the constraint in README and DEPLOYMENT.md:
  *"Building the magnettools base image requires LNCMI network access or VPN.
  Building downstream images (api, jupyter) requires only DockerHub access."*
- Make the default `docker-compose.yml` use `image:` references (pull from GHCR/DockerHub),
  not `build:`. Provide a `docker-compose.override.yml.example` for developers who
  need local builds.
- Add a clear build arg comment in the base Dockerfile:
  ```dockerfile
  ARG APT_DEPOT_URL=https://apt.lncmi.cnrs.fr
  # ^ Requires LNCMI network or VPN. Not needed for downstream images.
  ```

---

## Scenario 2 — GitHub-hosted runner tries to build the base image

**Trigger**: A workflow using `ubuntu-latest` attempts to build the `magnettools`
DockerHub base image.

**What happens**: The `apt-get install magnettools` layer fails silently or with a
network error. If BuildKit cache happens to have a valid layer, the build succeeds on
that run and fails on the next cache miss — a non-deterministic failure.

**Mitigation**: The self-hosted runner label `[self-hosted, lncmi]` is the architectural
guard. It must be applied to the base image build job and only that job. All other
image build jobs use `ubuntu-latest` and `FROM feelpp/magnettools:X.Y.Z`.

The cache trap deserves explicit attention: in the workflow YAML, always pin the base
image to a specific version tag rather than `latest`. This makes cache invalidation
predictable and intentional:

```yaml
# Bad — cache behaves non-deterministically with :latest
FROM feelpp/magnettools:latest

# Good — cache invalidates only when you explicitly bump the version
FROM feelpp/magnettools:1.1.0
```

---

## Scenario 3 — New developer sets up their workstation

**Trigger**: Developer clones the repo, instinctively runs `docker compose build`.

**What happens with DockerHub base**: If downstream Dockerfiles use the DockerHub
base, the build succeeds anywhere. The developer gets a working local build without
needing VPN.

**Remaining gap**: If the developer tries to build the `magnettools` base image itself
(e.g. by cloning the `magnettools` repo and running its Dockerfile), they hit the depot
constraint. This is unlikely for a typical developer but worth documenting.

**Mitigation**:
- The student/developer `docker-compose.yml` uses `image:` by default with no `build:`.
- README clearly distinguishes:
  - "Running the platform" → `docker compose pull && docker compose up` (zero constraints)
  - "Building downstream images" → requires DockerHub access only
  - "Building the magnettools base image" → requires LNCMI network / self-hosted runner

---

## Scenario 4 — The depot machine is temporarily down

**Trigger**: Baremetal depot goes offline. A CI tag push triggers the `magnettools`
`.deb` build and base image build.

**What happens**:
- `.deb` upload via `dupload` fails — the package is not added to the depot
- Base image build fails at `apt-get install magnettools` — the DockerHub base is not updated
- All downstream image builds (api, jupyter) that depend on the DockerHub base are blocked
  only if they explicitly rebuild from scratch; if they pin the previous base version tag,
  they continue to work

**Mitigations**:

Layer the Dockerfile so the `apt-get install magnettools` step is in its own early layer:
```dockerfile
# Layer 1 — changes only when magnettools version bumps
ARG MAGNETTOOLS_VERSION=1.1.0
RUN apt-get install -y magnettools=${MAGNETTOOLS_VERSION}

# Layer 2 — changes when Python deps change
COPY pyproject.toml .
RUN pip install ...

# Layer 3 — changes on every commit
COPY . .
```
With BuildKit layer caching on the self-hosted runner, the depot is not contacted
unless `MAGNETTOOLS_VERSION` changes. Most `python_magnetdb` tag pushes never
invalidate layer 1.

Keep the `.deb` as a GitHub Release asset (already in the CI/CD workflow). In an
emergency, the base image Dockerfile can temporarily install from the release asset:
```dockerfile
ARG MAGNETTOOLS_DEB_URL=https://github.com/MagnetDB/magnettools/releases/download/v1.1.0/magnettools_1.1.0-1_amd64.deb
RUN curl -fsSL ${MAGNETTOOLS_DEB_URL} -o /tmp/magnettools.deb \
    && dpkg -i /tmp/magnettools.deb \
    && rm /tmp/magnettools.deb
```
This is a break-glass fallback, not the default path.

---

## Scenario 5 — Student needs a custom Jupyter image variant

**Trigger**: A student working on Project A, B, or C needs to add a Python dependency
or modify the Jupyter configuration. They cannot push to GHCR (no write access) and
cannot run the self-hosted runner.

**What happens with DockerHub base**: The student can build a custom image locally
without any depot dependency:
```dockerfile
# Student's custom Dockerfile
FROM feelpp/magnettools:1.1.0
# or: FROM ghcr.io/magnetdb/magnetdb-jupyter:latest
# magnettools already installed — no depot contact needed

RUN pip install rainflow scipy-extra my-custom-lib
COPY notebooks/ /home/jovyan/work/
```

This builds and runs anywhere — laptop, university cluster, GitHub Codespace.

**For sharing the custom image**: students push to their own DockerHub account or a
shared LNCMI student namespace:
```bash
docker build -t myusername/magnetdb-project-a:v1 .
docker push myusername/magnetdb-project-a:v1
```

**Mitigation already in place**: The DockerHub base image strategy was chosen precisely
for this reason. Document it explicitly in the student onboarding guide as the standard
pattern for extending the environment.

---

## Summary matrix

| Scenario | Without DockerHub base | With DockerHub base | Residual constraint |
|---|---|---|---|
| Developer off-site rebuild | ❌ Fails (depot unreachable) | ✅ Works | Base image only — not needed locally |
| GitHub-hosted runner image build | ❌ Fails non-deterministically | ✅ Works | Base image build → self-hosted only |
| New developer onboarding | ❌ Fails on `compose build` | ✅ Works | Document base image rebuild as rare/CI-only |
| Depot temporarily down | ❌ All builds blocked | ⚠️ Partial — cached layers survive | Pin base version tags; keep .deb as release asset |
| Student custom image | ❌ Requires VPN | ✅ Works anywhere | None — full independence |

The DockerHub base image is not just a convenience — it is the structural solution that
reduces the self-hosted runner requirement to a single job (base image build + depot upload)
and removes the depot constraint from every other workflow.
