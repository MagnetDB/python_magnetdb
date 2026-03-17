# Prompt: Self-Hosted GitHub Actions Runner Setup for LNCMI

## Context

You are helping set up a self-hosted GitHub Actions runner on an LNCMI machine.
This runner is required for jobs that must run inside the LNCMI network:
- Building the `magnettools` DockerHub base image (`apt-get install magnettools`
  contacts the internal baremetal apt depot)
- Uploading `.deb` packages to the baremetal depot via `dupload`
- Any future job requiring internal network access

All other CI jobs (pure Python wheel builds, downstream image builds using the
DockerHub base, integration tests) run on GitHub-hosted runners and do not need
the self-hosted runner.

## Runner scope: organization vs repository

Register the runner at the **organization level** (`MagnetDB` org), not per-repository.
This allows all repos (`magnettools`, `python_magnetdb`, etc.) to share the same runner
without re-registering it for each repo.

```
GitHub: MagnetDB org → Settings → Actions → Runners → New self-hosted runner
```

Registration token is single-use and expires after 1 hour. Generate it immediately
before running `./config.sh`.

## Host machine requirements

The runner can be installed on any existing LNCMI machine — it does not need to be
dedicated. A VM or an existing development server works fine. Requirements:

- OS: Debian trixie (consistent with the build target)
- RAM: ≥ 4 GB (Docker builds are memory-hungry; 8 GB preferred)
- Disk: ≥ 20 GB free (Docker image layers cache accumulates)
- Network: LNCMI internal network (obviously) + outbound HTTPS to GitHub and DockerHub
- CPU: ≥ 2 cores (parallelism in `make -j`)

Packages to install before runner setup:
```bash
sudo apt-get update
sudo apt-get install -y \
    curl git \
    docker.io docker-buildx \
    dpkg-dev devscripts dupload \
    apt-utils reprepro \
    gpg gpg-agent
sudo usermod -aG docker $RUNNER_USER
```

## Installation

```bash
# Create a dedicated system user for the runner (do not run as root)
sudo adduser --system --no-create-home --shell /bin/bash --group github-runner
sudo usermod -aG docker github-runner

# Create runner directory
sudo mkdir -p /opt/actions-runner
sudo chown github-runner:github-runner /opt/actions-runner

# Switch to runner user for the rest
sudo -u github-runner bash

cd /opt/actions-runner

# Download the runner (check https://github.com/actions/runner/releases for latest)
curl -o actions-runner-linux-x64.tar.gz -L \
  https://github.com/actions/runner/releases/download/v2.321.0/actions-runner-linux-x64-2.321.0.tar.gz

# Verify checksum (value from the GitHub releases page)
echo "EXPECTED_SHA256  actions-runner-linux-x64.tar.gz" | sha256sum -c

tar xzf actions-runner-linux-x64.tar.gz
```

## Registration

```bash
# Run as github-runner user
./config.sh \
  --url https://github.com/MagnetDB \
  --token <ORG_REGISTRATION_TOKEN> \
  --name lncmi-trixie-01 \
  --labels self-hosted,lncmi,trixie,linux,x64 \
  --runnergroup Default \
  --work /opt/actions-runner/_work \
  --unattended
```

Labels explained:
- `self-hosted` — required, identifies it as a self-hosted runner
- `lncmi` — used in workflow `runs-on:` to target LNCMI-network jobs
- `trixie` — used to target Debian trixie-specific builds
- `linux`, `x64` — standard labels for cross-platform awareness

## systemd service (persistent, auto-restart)

```bash
# Still as github-runner user, install the service
exit  # back to sudo-capable user

cd /opt/actions-runner
sudo ./svc.sh install github-runner
sudo ./svc.sh start

# Verify
sudo systemctl status actions.runner.MagnetDB.lncmi-trixie-01.service
```

The service file is installed at:
`/etc/systemd/system/actions.runner.MagnetDB.lncmi-trixie-01.service`

To enable auto-start on boot (already done by `svc.sh install`, verify with):
```bash
sudo systemctl is-enabled actions.runner.MagnetDB.lncmi-trixie-01.service
```

## Docker configuration for the runner

The runner user needs Docker access without sudo, and Docker BuildKit must be enabled:

```bash
# /etc/docker/daemon.json
{
  "features": {
    "buildkit": true
  },
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "50m",
    "max-file": "3"
  }
}
```

```bash
sudo systemctl restart docker

# Test Docker access from runner user
sudo -u github-runner docker run --rm hello-world
```

## GitHub Actions cache configuration

The runner caches Docker layers locally. Configure the cache directory to be on
a disk with sufficient space:

```bash
# In the runner's environment file
# /opt/actions-runner/.env
DOCKER_BUILDKIT=1
BUILDKIT_PROGRESS=plain

# Optional: point Docker cache to a larger disk if /opt is small
# DOCKER_CONFIG=/mnt/data/docker-runner-config
```

In workflow YAML, use the `gha` cache backend to share Docker layer cache across
workflow runs:
```yaml
- uses: docker/build-push-action@v6
  with:
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

This is critical for the `magnettools` base image build — the `apt-get install magnettools`
layer should be cached and only rebuilt when the `magnettools` version changes.

## Security hardening

### Restrict what the runner can do

Self-hosted runners should be treated as semi-trusted infrastructure. Mitigations:

```bash
# Runner user has no sudo access (verify)
sudo -l -U github-runner  # should show "no sudo"

# Docker group membership is the only elevated privilege
# Acceptable because all builds run in containers

# Restrict the runner to specific repositories (set in GitHub org settings)
# Settings → Actions → Runner groups → Default → Repository access:
# → "Selected repositories" → add magnettools, python_magnetdb only
```

### Secrets are injected per-job, never stored on the runner

The runner itself stores no secrets. All credentials (`APT_SIGNING_KEY`, `APT_DEPLOY_KEY`,
`DOCKERHUB_TOKEN`, etc.) are injected as environment variables per job by GitHub Actions
and are zeroed after the job completes.

Each workflow that uses secrets should clean up after itself:
```yaml
- name: Cleanup secrets from runner disk
  if: always()   # runs even if previous steps failed
  run: |
    rm -f ~/.ssh/apt_deploy_key ~/.dupload.conf
    gpg --batch --yes --delete-secret-and-public-key \
      $(gpg --list-secret-keys --with-colons 2>/dev/null \
        | grep '^fpr' | cut -d: -f10) 2>/dev/null || true
```

### Ephemeral runner option (advanced)

For higher security, configure the runner in ephemeral mode: each job gets a fresh
runner instance, which is destroyed after the job completes. This prevents job-to-job
contamination at the cost of slower startup (Docker layer cache is lost between runs
unless using an external cache backend).

```bash
./config.sh ... --ephemeral
```

For your use case (small team, internal infra, no untrusted PRs triggering builds),
the persistent runner is sufficient.

## DockerHub credentials on the runner

The runner needs to push to DockerHub for the `magnettools` base image. Configure
via a GitHub Secret (`DOCKERHUB_TOKEN`) injected per-job:

```yaml
- uses: docker/login-action@v3
  with:
    username: ${{ secrets.DOCKERHUB_USERNAME }}
    password: ${{ secrets.DOCKERHUB_TOKEN }}
```

Never `docker login` manually on the runner machine — credentials stored in
`~/.docker/config.json` would persist across jobs.

## Monitoring and maintenance

### Check runner status
```bash
sudo systemctl status actions.runner.MagnetDB.lncmi-trixie-01.service
journalctl -u actions.runner.MagnetDB.lncmi-trixie-01.service -f
```

### Update the runner

GitHub will warn in the UI when the runner version is outdated. Update procedure:
```bash
sudo systemctl stop actions.runner.MagnetDB.lncmi-trixie-01.service
cd /opt/actions-runner
sudo -u github-runner ./config.sh remove --token <REMOVAL_TOKEN>
# Re-download and re-register as in the Installation section above
```

### Disk cleanup

Docker layer cache accumulates over time. Add a weekly cleanup cron:
```bash
# As github-runner user, crontab -e
0 3 * * 0 docker system prune -f --filter "until=168h" >> /var/log/docker-prune.log 2>&1
```

This prunes images and containers older than 7 days, preserving recently used cache.

### Runner offline alerting

If the runner goes offline (machine reboots, service crash), GitHub marks it as
"offline" in the org settings and jobs queue indefinitely rather than failing fast.
Add a monitoring check:
```bash
# Simple systemd watchdog — already handled by svc.sh install
# For external alerting, check the GitHub API:
# GET /orgs/MagnetDB/actions/runners → look for runner with status != "online"
```

Consider adding a health check to your existing monitoring stack (if any).

## Multiple runners (future scaling)

If CI queue times become a problem (e.g. multiple tag pushes queued), add a second
runner on another LNCMI machine using the same labels. GitHub distributes jobs
across available runners with matching labels automatically. Each runner needs its
own registration token but shares the same secrets (stored at org level).

## Definition of done

- Runner registered at org level with labels `self-hosted,lncmi,trixie`
- Running as a systemd service, auto-starts on boot
- Docker access confirmed for `github-runner` user
- Test workflow runs successfully:
  ```yaml
  jobs:
    test:
      runs-on: [self-hosted, lncmi, trixie]
      steps:
        - run: |
            echo "Runner hostname: $(hostname)"
            echo "Network: $(curl -s --max-time 5 https://apt.lncmi.cnrs.fr/apt/dists/trixie/Release | head -3)"
            docker run --rm debian:trixie echo "Docker works"
  ```
- No secrets stored on the runner machine between jobs
- Weekly Docker prune cron installed
- Runner hostname and location documented in DEPLOYMENT.md
