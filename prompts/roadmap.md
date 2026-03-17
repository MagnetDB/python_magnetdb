# MagnetDB Package Distribution — Implementation Roadmap

## Overview

This roadmap covers the full implementation of the MagnetDB package distribution
infrastructure: private PyPI server, apt depot CI integration, Docker image pipeline,
and GitHub Actions automation. It is structured so that each phase delivers a
standalone usable result and unblocks the next phase.

**Estimated total effort**: 6–10 days of focused work, spread over 3–4 weeks to allow
for testing and iteration.

**Team**: Christophe + Rémi. Most phases can be parallelised between the two.

---

## Phase 0 — Prerequisites (1 day)

*Before any CI/CD work, establish the foundations that everything else depends on.*

### 0.1 — Self-hosted GitHub runner (half day)

See `prompt-github-runner.md`.

- [ ] Choose the host machine (existing LNCMI server or VM)
- [ ] Install runner dependencies: Docker, `dpkg-dev`, `devscripts`, `dupload`
- [ ] Register runner at org level with labels `self-hosted,lncmi,trixie`
- [ ] Install as systemd service, verify auto-start
- [ ] Confirm Docker access from `github-runner` user
- [ ] Run smoke-test workflow (hostname + depot reachability + Docker)
- [ ] Set up weekly Docker prune cron

**Exit criterion**: A workflow with `runs-on: [self-hosted, lncmi, trixie]` completes
successfully and can reach `apt.lncmi.cnrs.fr`.

### 0.2 — GPG subkey for CI signing (half day)

See `prompt-apt-depot.md`, section "DD subkey for CI".

- [ ] Create a signing-only subkey of the DD key
  (`gpg --expert --edit-key` → `addkey` → RSA sign-only, 4096, 2y expiry)
- [ ] Export only the subkey private material (`--export-secret-subkeys <FPR>!`)
- [ ] Add as `APT_SIGNING_KEY` GitHub org secret
- [ ] Verify import on a clean machine (subkey imports, primary shows as `[stub]`,
  signing works with `gpg -u <FPR>! ...`)
- [ ] Set calendar reminder for subkey rotation (2 years)

**Exit criterion**: `echo "$APT_SIGNING_KEY" | gpg --import` on the runner produces
a working signing key.

### 0.3 — SSH deploy key for depot (1 hour)

- [ ] Generate a dedicated ed25519 key pair (`magnettools-ci-deploy`)
- [ ] Create `apt-ci` system user on the baremetal depot machine
- [ ] Grant `apt-ci` write access to depot pool and dists directories
- [ ] Add deploy key public key to `apt-ci`'s `authorized_keys` with `command=`
  restriction (see `prompt-apt-depot.md`)
- [ ] Add private key as `APT_DEPLOY_KEY` GitHub org secret
- [ ] Add `APT_DEPOT_HOST` and `APT_DEPOT_INCOMING` as GitHub org secrets

**Exit criterion**: `ssh -i deploy_key apt-ci@apt.lncmi.cnrs.fr` runs the restricted
post-upload script and exits cleanly.

---

## Phase 1 — magnettools C++ packaging (2 days)

*Automate the `.deb` and `.whl` builds for `magnettools`. This is the most complex
phase technically — do it first so everything downstream can depend on it.*

### 1.1 — Debian package structure (1 day)

See `prompt-apt-depot.md`, section "Debian package structure".

- [ ] Verify or create the `debian/` directory in the `magnettools` repo:
  `control`, `rules`, `changelog`, `copyright`, `install`
- [ ] Test manual build: `dpkg-buildpackage -us -uc -b`
- [ ] Verify `.deb` installs cleanly on a trixie machine:
  `dpkg -i magnettools_*.deb && python3 -c "import magnettools"`
- [ ] Test manual `dupload --to lncmi magnettools_*.changes`
- [ ] Verify `apt-ftparchive` index rebuild and GPG re-signing via `postupload` hook

**Exit criterion**: Manual `dupload` uploads the `.deb`, rebuilds the index, and
`apt-get install magnettools` on a clean trixie machine works.

### 1.2 — Multistage Docker + auditwheel wheel (1 day)

See `prompt-auditwheel.md`.

- [ ] Identify the existing Dockerfile structure (cmake vs pip build path,
  base image, C++ dependencies)
- [ ] Extend into multistage build:
  Stage 1 (manylinux_2_28 builder) → Stage 2 (auditwheel repair) → Stage 3 (export)
- [ ] Verify with `auditwheel show`: tag is `manylinux_2_28_x86_64`
- [ ] Run `ldd` on all `.so` files in the repaired wheel — no unresolved externals
- [ ] Smoke test: `docker run debian:trixie pip install /dist/magnettools-*.whl &&
  python3 -c "import magnettools"`
- [ ] Add `make wheel` target that triggers the Docker build and copies output to `dist/`

**Exit criterion**: A self-contained wheel tagged `manylinux_2_28_x86_64` installs
on a clean trixie container with no system packages.

### 1.3 — CI workflows for magnettools (half day)

See `prompt-cicd.md`, Workflows 2 and 3.

- [ ] Add `publish-deb.yml`: self-hosted runner, `dpkg-buildpackage` + `dupload`,
  `.deb` also attached to GitHub Release
- [ ] Add `publish-wheel.yml`: GitHub-hosted runner, multistage Docker build,
  publish to GitHub Packages (PyPI registry)
- [ ] Test both workflows with `workflow_dispatch` + `dry_run: true`
- [ ] Test end-to-end with a real tag push

**Exit criterion**: Pushing `v1.1.1` tag to `magnettools` triggers both workflows;
`.deb` appears in the apt depot and wheel appears in GitHub Packages.

---

## Phase 2 — Private PyPI server (1 day)

*Distribute pure Python packages via a standard pip-compatible index.*

See `prompt-private-pypi.md`.

### 2.1 — pypiserver Docker Compose service (half day)

- [ ] Add `pypiserver` container to the existing `docker-compose.yml`
- [ ] Configure MinIO as the storage backend (test S3 path-style with MinIO first;
  fall back to volume mount if S3 integration is unstable)
- [ ] Add Traefik labels: `https://pypi.magnetdb-dev.local`
- [ ] Configure htpasswd authentication for write access; open read for internal users
- [ ] Test: `pip install --extra-index-url https://pypi.magnetdb-dev.local/simple/ python-magnetgeo`

### 2.2 — Pure Python package CI workflows (half day)

See `prompt-cicd.md`, Workflow 1.

- [ ] Add `publish.yml` to `python_magnetgeo`, `python_magnetsetup`,
  `python_magnetapi`, `python_magnetrun`
  (GitHub-hosted runner, `python -m build`, `twine upload` to GitHub Packages)
- [ ] Test with `workflow_dispatch` + `dry_run: true`
- [ ] Add downstream dispatch trigger to `python_magnetdb`

**Exit criterion**: All four pure Python packages installable with
`pip install --extra-index-url https://nuget.pkg.github.com/MagnetDB/simple/ python-magnetgeo`.

---

## Phase 3 — pyproject.toml migration (half day)

*Remove all local path dependencies from `python_magnetdb`.*

- [ ] Confirm all packages from Phases 1 and 2 are published and installable
- [ ] Update `pyproject.toml`:
  - Remove `{path = "./python_magnetgeo"}` → `python-magnetgeo = ">=1.0.0,<2.0.0"`
  - Remove `{path = "./python_magnetsetup"}` → `python-magnetsetup = ">=0.1.0,<1.0.0"`
  - Remove `{path = "/home/feelpp/magnettools-1.1.0...whl"}` entirely
    (magnettools is a system package, not a Poetry dep — see note below)
  - Add `[[tool.poetry.source]]` for GitHub Packages
- [ ] Note on `magnettools`: it is installed via `apt-get` in the Dockerfile and
  is available in the system Python path. Do NOT add it as a Poetry dependency.
  Add a comment in `pyproject.toml` explaining this:
  ```toml
  # magnettools is installed as a system .deb via apt-get in the Dockerfile.
  # It is NOT declared here. See Dockerfile and prompt-apt-depot.md.
  ```
- [ ] Run `poetry lock` and verify the new lockfile resolves correctly
- [ ] Run the test suite to confirm nothing is broken

**Exit criterion**: `poetry install` succeeds with no local path deps; all imports work.

---

## Phase 4 — Docker image pipeline (1–2 days)

*Automate building and pushing the pre-built images that students and CI use.*

### 4.1 — Update the magnettools DockerHub base image workflow (half day)

The base image (`feelpp/magnettools` on DockerHub) is already being built and pushed.
This phase automates it via GitHub Actions rather than a manual process.

- [ ] Confirm the existing Dockerfile for the DockerHub base image
- [ ] Add `publish-image-base.yml` to the `magnettools` repo:
  self-hosted runner, `apt-get install magnettools` (from depot), push to DockerHub
- [ ] Tag strategy: `feelpp/magnettools:1.1.0` and `feelpp/magnettools:latest`
- [ ] Add `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` as GitHub org secrets
- [ ] Enable BuildKit layer caching on the self-hosted runner

### 4.2 — python_magnetdb and Jupyter image workflows (1 day)

See `prompt-cicd.md`, Workflow 4.

- [ ] Update `python_magnetdb` Dockerfile to `FROM feelpp/magnettools:X.Y.Z`
  (no `apt-get install magnettools` — it's in the base)
- [ ] Add `publish-image.yml` to `python_magnetdb`:
  GitHub-hosted runner (base image is on DockerHub, no depot contact needed),
  build api + jupyter images, push to GHCR
- [ ] Tag strategy: `ghcr.io/magnetdb/python_magnetdb:1.2.3` + `latest`
- [ ] Update student `docker-compose.yml` to use `image: ghcr.io/magnetdb/...`
  with no `build:` sections

**Exit criterion**: `docker compose up` from the student Compose file works with
no VPN and no build step.

---

## Phase 5 — Documentation and integration test (1 day)

*Tie everything together, validate end-to-end, and document for new team members.*

### 5.1 — DEPLOYMENT.md

- [ ] External dependencies section: baremetal apt depot, LemonLDAP, GHCR, DockerHub
- [ ] First-time setup instructions for developers (VPN config, pip config, GitHub PAT)
- [ ] First-time setup instructions for students (just `docker compose up`)
- [ ] Runner maintenance procedures (update, disk cleanup)
- [ ] GPG subkey rotation procedure

### 5.2 — Integration test workflow

See `prompt-cicd.md`, Workflow 5.

- [ ] Add `integration-check.yml` to `python_magnetdb`:
  GitHub-hosted runner, pull GHCR images, run `docker compose -f docker-compose.test.yml up`
- [ ] Trigger: `repository_dispatch` from upstream packages + weekly cron

### 5.3 — End-to-end smoke test

Run the full pipeline manually to validate all phases together:

```
1. Tag magnettools v1.2.0
   → .deb uploaded to baremetal depot ✓
   → manylinux wheel on GitHub Packages ✓
   → feelpp/magnettools:1.2.0 pushed to DockerHub ✓

2. Tag python_magnetgeo v1.1.0
   → wheel on GitHub Packages ✓
   → integration check triggered on python_magnetdb ✓

3. Tag python_magnetdb v0.5.0
   → ghcr.io/magnetdb/python_magnetdb:0.5.0 built (FROM feelpp/magnettools:1.2.0) ✓
   → ghcr.io/magnetdb/magnetdb-jupyter:0.5.0 pushed ✓

4. Student docker compose up (no VPN, fresh machine)
   → pulls ghcr.io/magnetdb/python_magnetdb:0.5.0 ✓
   → import magnettools works ✓
```

---

## Dependency graph

```
Phase 0 (Runner + GPG + SSH keys)
    │
    ├──→ Phase 1 (magnettools .deb + wheel + CI)
    │        │
    │        └──→ Phase 4.1 (DockerHub base image CI)
    │                  │
    │                  └──→ Phase 4.2 (api + jupyter images)
    │
    ├──→ Phase 2 (pypiserver + pure Python CI)
    │        │
    │        └──→ Phase 3 (pyproject.toml migration)
    │
    └──→ Phase 5 (docs + integration tests) ← depends on all above
```

Phases 1 and 2 are independent and can be worked in parallel (one person each).
Phase 3 requires Phase 2 complete. Phase 4.2 requires Phase 4.1 complete.
Phase 5 is the capstone.

---

## Risks and mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| manylinux_2_28 base can't build magnettools C++ deps | Medium | Phase 1.2 blocked | Fall back to `debian:bookworm` base, accept `manylinux_2_36` tag |
| pypiserver S3/MinIO backend unstable | Low–Medium | Phase 2 delayed | Fall back to volume mount; S3 can be added later |
| Baremetal depot `postupload` hook not yet configured | Unknown | Phase 1.3 blocked | Clarify with Christophe before Phase 1.1 |
| magnettools `debian/` directory does not exist yet | Unknown | Phase 1.1 + 1 day | Create from scratch using `dh_make`; document template |
| DockerHub rate limits on GitHub-hosted runners | Low | Phase 4.2 slowed | Use GHCR mirror or authenticated DockerHub pull |
| GPG subkey approach rejected by lab policy | Low | Phase 0.2 redesign | Discuss with IT; alternative: full DD key in hardware token (YubiKey) |

---

## Effort summary

| Phase | Effort | Assignee suggestion |
|---|---|---|
| 0 — Prerequisites | 1 day | Christophe (GPG subkey), Rémi (runner setup) |
| 1 — magnettools packaging | 2 days | Christophe (Debian packaging expertise) |
| 2 — Private PyPI | 1 day | Rémi (Docker Compose familiarity) |
| 3 — pyproject.toml migration | 0.5 day | Rémi |
| 4 — Docker image pipeline | 1.5 days | Both |
| 5 — Docs + integration tests | 1 day | Both |
| **Total** | **~7 days** | |
