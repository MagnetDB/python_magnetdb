# MagnetDB — Global Development Plan

**Version 1.0 · May 2026**  
LNCMI — Laboratoire National des Champs Magnétiques Intenses

**Team**: Christophe + Rémi (1.5 FTE effective)  
**Horizon**: ~12–14 months of calendar time

---

## Overview

This document consolidates four parallel workstreams into a single coordinated plan:

| Track | Scope | Est. effort |
|-------|-------|-------------|
| **A — Infrastructure & Distribution** | Private PyPI, apt depot, Docker CI/CD | 7 days |
| **B — Core Data Model** | Lifecycle status overhaul + standalone Mesh model + standalone CAD model | ~11 days |
| **C — Authentication & Access** | LemonLDAP Combination auth, user scoping, OIDC claims | ~5 days |
| **D — Operational Statistics** | RecordStats, ETL pipeline, streaming | 24–31 weeks |
| **E — Frontend Migration** | Vue 2 → Vue 3 (recommended path) | 6–10 weeks |

Tracks A and B are largely independent and can begin immediately in parallel.  
Track C is a prerequisite for the data-scoping features in Track D (Phase D0.2–D0.4).  
Track E interleaves with Track D — see the suggested cadence in Section 5.

---

## Track A — Infrastructure & Distribution

> Source: `roadmap.md`  
> Goal: Replace manual packaging and deployment with a fully automated CI/CD pipeline.

### A0 — Prerequisites (1 day)

**A0.1 — Self-hosted GitHub runner (½ day)**
- [ ] Choose host machine (existing LNCMI server or VM)
- [ ] Install runner deps: Docker, `dpkg-dev`, `devscripts`, `dupload`
- [ ] Register runner at org level with labels `self-hosted,lncmi,trixie`
- [ ] Install as systemd service; set up weekly Docker prune cron
- [ ] Smoke-test: workflow with `runs-on: [self-hosted, lncmi, trixie]` reaches `apt.lncmi.cnrs.fr`

**A0.2 — GPG subkey for CI signing (½ day)**
- [ ] Create a signing-only subkey of the DD key (4096-bit RSA, 2y expiry)
- [ ] Export only the subkey private material; add as `APT_SIGNING_KEY` GitHub org secret
- [ ] Verify import on a clean machine; set calendar reminder for rotation

**A0.3 — SSH deploy key for depot (1 hour)**
- [ ] Generate dedicated ed25519 key pair `magnettools-ci-deploy`
- [ ] Create `apt-ci` system user on the baremetal depot; grant write access to pool/dists
- [ ] Add public key to `apt-ci`'s `authorized_keys` with `command=` restriction
- [ ] Add `APT_DEPLOY_KEY`, `APT_DEPOT_HOST`, `APT_DEPOT_INCOMING` as org secrets

### A1 — magnettools C++ packaging (2 days)

**A1.1 — Debian package structure (1 day)**
- [ ] Verify or create `debian/` directory: `control`, `rules`, `changelog`, `copyright`, `install`
- [ ] Test manual build: `dpkg-buildpackage -us -uc -b`
- [ ] Test manual `dupload --to lncmi magnettools_*.changes`
- [ ] Verify `apt-ftparchive` index rebuild and GPG re-signing via `postupload` hook

**A1.2 — Multistage Docker + auditwheel wheel (1 day)**
- [ ] Extend Dockerfile into multistage: manylinux_2_28 builder → auditwheel repair → export
- [ ] Verify tag `manylinux_2_28_x86_64` with `auditwheel show`
- [ ] Smoke test: install wheel on clean `debian:trixie` container; `import magnettools`
- [ ] Add `make wheel` target

**A1.3 — CI workflows for magnettools (½ day)**
- [ ] Add `publish-deb.yml` (self-hosted runner, `dpkg-buildpackage` + `dupload`)
- [ ] Add `publish-wheel.yml` (GitHub-hosted, multistage Docker, publish to GitHub Packages)
- [ ] Test both with `workflow_dispatch` + `dry_run: true`, then with a real tag

### A2 — Private PyPI server (1 day)

- [ ] Add `pypiserver` container to `docker-compose.yml` with RustFS S3 backend
- [ ] Traefik labels: `https://pypi.magnetdb-dev.local`; htpasswd auth for write
- [ ] Add `publish.yml` to `python_magnetgeo`, `python_magnetsetup`, `python_magnetapi`, `python_magnetrun`
- [ ] Test: `pip install --extra-index-url https://nuget.pkg.github.com/MagnetDB/simple/ python-magnetgeo`

### A3 — pyproject.toml migration (½ day)

- [ ] Replace local `{path = ...}` deps with versioned package refs
- [ ] Add `[[tool.poetry.source]]` for GitHub Packages
- [ ] Note in `pyproject.toml` that `magnettools` is a system `.deb`, not a Poetry dep
- [ ] `poetry lock` + full test suite pass

### A4 — Docker image pipeline (1½ days)

- [ ] Add `publish-image-base.yml` to `magnettools` repo: push `feelpp/magnettools:X.Y.Z` to DockerHub
- [ ] Update `python_magnetdb` Dockerfile to `FROM feelpp/magnettools:X.Y.Z`
- [ ] Add `publish-image.yml`: build api + jupyter images; push to GHCR
- [ ] Update student `docker-compose.yml`: `image: ghcr.io/magnetdb/...`, no `build:` sections

### A5 — Documentation & integration tests (1 day)

- [ ] Write `DEPLOYMENT.md` covering: external deps, first-time setup (dev + student), runner maintenance, GPG rotation
- [ ] Add `integration-check.yml`: pull GHCR images, run `docker compose -f docker-compose.test.yml up`
- [ ] Full end-to-end smoke test: tag `magnettools`, `python_magnetgeo`, `python_magnetdb` in sequence

### A6 — MinIO → RustFS migration (1–2 days)

> Reference: `rustfs-parquet-frontend-display.md` §1  
> Goal: Replace the MinIO S3 container with RustFS. RustFS exposes the same S3-compatible API so
> all application code (`boto3`, `django-storages`, `StorageAttachment`) is unchanged — only
> environment variables and the docker-compose service block are updated.

**A6.1 — Stand up RustFS alongside MinIO (½ day)**
- [ ] Add `rustfs` service to `docker-compose.yml` (e.g. `ghcr.io/rustfs/rustfs:latest`); keep `minio` running in parallel during migration
- [ ] Recreate the same bucket structure in RustFS (`magnetdb-attachments`, `magnetdb-parquet`, etc.)
- [ ] Configure CORS on the curated-data bucket — expose `Content-Range` for client-side Parquet columnar reads:
  ```json
  { "AllowedOrigins": ["https://magnetdb.lncmi.cnrs.fr"],
    "AllowedMethods": ["GET"],
    "AllowedHeaders": ["*"],
    "ExposeHeaders": ["Content-Length", "Content-Range"],
    "MaxAgeSeconds": 3600 }
  ```

**A6.2 — Mirror data and flip credentials (½ day)**
- [ ] Mirror all objects from MinIO to RustFS using `mc mirror`:
  ```bash
  mc alias set src  http://minio:9000   $MINIO_ACCESS_KEY   $MINIO_SECRET_KEY
  mc alias set dst  http://rustfs:9000  $RUSTFS_ACCESS_KEY  $RUSTFS_SECRET_KEY
  mc mirror src/magnetdb-attachments dst/magnetdb-attachments
  mc mirror src/magnetdb-parquet     dst/magnetdb-parquet
  ```
- [ ] Update `.envrc.example`: replace `MINIO_ENDPOINT` / `MINIO_ACCESS_KEY` / `MINIO_SECRET_KEY` with `S3_ENDPOINT_URL` / `S3_ACCESS_KEY` / `S3_SECRET_KEY` pointing to RustFS
- [ ] Update `settings.py` / `django-storages` config to read the new env var names
- [ ] Remove the `minio` service from `docker-compose.yml` once all services are verified

**A6.3 — Smoke test (½ day)**
- [ ] Restart API + worker containers; run the existing attachment upload/download test
- [ ] Verify pre-signed URL generation works (needed for client-side Parquet reads in Track E)
- [ ] Add A6 to `DEPLOYMENT.md` and `integration-check.yml`

**Track A dependency graph:**
```
A0 → A1 → A4.1 → A4.2
           A6 (can run after A2 — RustFS must be up before D2 Parquet ETL)
A0 → A2 → A3
A0 → A5 (capstone, depends on all above)
```
A1 and A2 are independent and can be parallelised.

---

## Track B — Core Data Model

> Sources: `magnetdb_lifecycle_migration_guide.md`, `MESH_MODEL_CREATION.md`, `CAD_MODEL_CREATION.md`  
> Goal: Modernise the status lifecycle and introduce first-class Mesh and CAD models. All three can proceed in parallel.

### B1 — Lifecycle Status Overhaul (~5 days)

> Source: `magnetdb_lifecycle_migration_guide.md`

#### Revised status model

| Entity | Added statuses | Terminal state |
|--------|---------------|----------------|
| Site | `stopped` | `stopped` (never `defunct`) |
| Magnet | `retired` | `retired` or `defunct` |
| Part | `retired` | `retired` or `defunct` |

#### Cascade rules (summary)
- `PUT /sites/{id}/put_in_operation`: accepts magnets in `in_study` **or** `in_stock` (not just `in_stock`)
- `POST /sites/{id}/shutdown`: site → `stopped`; per-magnet decision in request payload; at least 1 part must share the terminal status for `retired`/`defunct` magnets
- `POST /magnets/{id}/retire`: new standalone endpoint
- `POST /magnets/{id}/defunct`: updated to accept `defunct_parts` list (≥1 required)

#### Implementation phases

**B1.1 — Backend model & DB (~½ day)**
- [ ] `python_magnetdb/models/status.py`: add `RETIRED = 'retired'`, `STOPPED = 'stopped'`
- [ ] `python manage.py makemigrations` — only `choices` altered, no data migration yet
- [ ] Run migration in test env; confirm existing rows unaffected

**B1.2 — API endpoint updates (~1 day)**
- [ ] Rewrite `POST /sites/{id}/shutdown` with `ShutdownPayload` Pydantic model; wrap in `transaction.atomic()`
- [ ] Update `POST /sites/{id}/put_in_operation` guard to accept `in_study` magnets
- [ ] Add `POST /magnets/{id}/retire`
- [ ] Update `POST /magnets/{id}/defunct` (select `defunct_parts` list, rest → `in_stock`)

**B1.3 — Frontend: status display (~½ day)**
- [ ] `StatusBadge.vue`: `stopped` → amber/warning, `retired` → neutral amber
- [ ] `main.js`: add `stopped: 'Stopped'`, `retired: 'Retired'` to `statusName` filter
- [ ] Update filter dropdowns and table columns in site/magnet list views

**B1.4 — Frontend: shutdown workflow (~2 days)**
- [ ] Multi-step dialog: Step 1 — per-magnet status selector; Step 2 — per-part selector for `retired`/`defunct` magnets
- [ ] Enforce ≥1 part selection in UI before submit is enabled
- [ ] Confirmation summary before POST to `/sites/{id}/shutdown`
- [ ] Add **Reactivate** action on magnet detail view (`retired` → `in_stock`)

**B1.5 — Testing & data validation (~1 day)**
- [ ] Backend unit tests: all valid transitions, cascade correctness, payload validation errors, rollback
- [ ] Data audit: query for sites marked `defunct` (may need normalisation to `stopped`)
- [ ] Integration test in staging: mixed shutdown (in_stock + retired + defunct in one call)

### B2 — Standalone Mesh Model (~3 days)

> Source: `MESH_MODEL_CREATION.md`

**Goal**: Introduce a `Mesh` model with M2M ownership (Part, Magnet, Site), provenance metadata, and mesh sharing — while leaving `MeshAttachment` fully intact.

**B2.1 — Model & migration**
- [ ] Create `python_magnetdb/models/mesh.py` with `Mesh` and `MeshType` (axi/3d)
- [ ] Fields: `type`, `attachment` (FK StorageAttachment), `mesh_config` (JSON), `command`, `provenance` (JSON), `comment`, M2M to Part/Magnet/Site, timestamps
- [ ] Register in `python_magnetdb/models/__init__.py`
- [ ] `python manage.py makemigrations` → creates `meshes` table + M2M through tables
- [ ] Second data migration: backfill all existing `MeshAttachment` rows into `Mesh`

**B2.2 — FastAPI routes**
- [ ] `POST /api/meshes` — upload file, parse JSON fields, link to owner
- [ ] `GET /api/meshes/{id}` — single mesh with attachment
- [ ] `PATCH /api/meshes/{id}` — update `mesh_config`, `command`, `provenance`, `comment`
- [ ] `DELETE /api/meshes/{id}` — cascade-deletes `StorageAttachment`
- [ ] `POST /api/meshes/{id}/link` — add second owner
- [ ] `DELETE /api/meshes/{id}/unlink` — remove owner; delete row if no owners remain
- [ ] Register router in `web.py`

**B2.3 — Serializer & show endpoint updates**
- [ ] Verify `model_serializer` handles M2M reverse accessors correctly
- [ ] Add `'meshes__attachment'` to `prefetch_related` in `magnets.show`, `sites.show`, `parts.show`
- [ ] Expose both `meshes` (new) and `mesh_attachments` (old) in serialized responses
- [ ] Deferred: migrate `Simulation.mesh_attachment` FK to `Mesh` once new model is stable

**What must NOT be changed**: `mesh_attachment.py`, `mesh_attachments.py` router, `MeshAttachmentEditor.vue`, existing `meshattachment_set` prefetch calls.

### B3 — Standalone CAD Model (~3 days)

> Source: `CAD_MODEL_CREATION.md`

**Goal**: Introduce a `Cad` model with M2M ownership (Part, Magnet, Site), provenance metadata, and CAD file sharing — while leaving `CadAttachment` fully intact. Follows the same additive pattern as B2.

**B3.1 — Model & migration**
- [ ] Create `python_magnetdb/models/cad.py` with `Cad` and `CadType` (axi/3d)
- [ ] Fields: `type`, `attachment` (FK StorageAttachment), `cad_config` (JSON), `command`, `provenance` (JSON), `comment`, M2M to Part/Magnet/Site (`related_name='cad_set'`), timestamps
- [ ] Register in `python_magnetdb/models/__init__.py`: `from .cad import Cad, CadType`
- [ ] `python manage.py makemigrations` → creates `cad` table + M2M through tables (`cad_parts`, `cad_magnets`, `cad_sites`)
- [ ] Second data migration: backfill all existing `CadAttachment` rows into `Cad` (type + attachment + owner links; `cad_config`/`command`/`provenance`/`comment` left NULL — that information was never captured)

**B3.2 — FastAPI routes** (`python_magnetdb/routes/api/cad.py`)
- [ ] `POST /api/cad` — upload file (`.xao`, `.brep`, or other), parse JSON fields, link to one owner (`resource_type`/`resource_id`)
- [ ] `GET /api/cad/{id}` — single cad with attachment
- [ ] `PATCH /api/cad/{id}` — update `cad_config`, `command`, `provenance`, `comment` (type and attachment are immutable)
- [ ] `DELETE /api/cad/{id}` — cascade-deletes `StorageAttachment`
- [ ] `POST /api/cad/{id}/link` — add second owner
- [ ] `DELETE /api/cad/{id}/unlink` — remove owner; delete row if no owners remain
- [ ] Register router in `web.py`

**B3.3 — Serializer & show endpoint updates**
- [ ] Add `'cad_set__attachment'` to `prefetch_related` in `parts.show`, `magnets.show`, `sites.show` alongside existing `cadattachment_set` prefetch calls
- [ ] In `_part_post_processor`, `_magnet_post_processor`, `_site_post_processor`: rename `cad_set` → `cad_new`; keep `cadattachment_set` → `cad` (existing key, unchanged) so both old and new CAD relations are exposed
- [ ] Deferred: retire `CadAttachment` FK once `Cad` model is stable and frontend has been updated

**Note on CAD file pairs**: `.xao` + `.brep` produced by the same geometry invocation remain separate `Cad` rows (matching current `CadAttachment` behaviour). They are implicitly related by sharing the same owners and `command`/`provenance` fields. Explicit pairing via a `group_id` UUID is out of scope.

**What must NOT be changed**: `cad_attachment.py`, `cad_attachments.py` router, all existing `cadattachment_set` prefetch calls, frontend `CadAttachment` components.

---

## Track C — Authentication & Access

> Sources: `lemonldap-dbusers-gemini.md`, `roadmap-operational-stats.md` (Phase 0.2–0.4)  
> Goal: Enable multi-source authentication in LemonLDAP and map external identities to MagnetDB users for data scoping.

### C1 — LemonLDAP Combination Auth

**Use case**: Researchers log in via LDAP; external monitoring system users may log in via a DBI (database) module, or a future SAML provider. A single rule chain unifies these.

**C1.1 — Enable Combination module in Manager**
- [ ] Manager → General Parameters → Authentication modules → set Auth, UserDB, Password to **Combination**
- [ ] Define combination modules: `LDAP` (existing), `DBI` or `SAML` (new external)
- [ ] Set combination rule, e.g.:
  ```perl
  $_authChoice eq "LDAP" ? LDAP : ExternalDB
  ```
  or IP-based:
  ```perl
  inSubnet($ip, '192.168.x.0/24') ? LDAP : ExternalDB
  ```

**C1.2 — OIDC claim export**
- [ ] Configure LemonLDAP Manager to export the relevant LDAP attribute (e.g., `monitoring_id`) as a custom OIDC claim
- [ ] Validate with `lemonldap-ng-cli` or Manager test tool before applying to production

**C1.3 — Testing**
- [ ] Validate each auth path (LDAP user, external user) logs in and receives correct claims
- [ ] Verify OIDC token contains `monitoring_id` claim for users who have it in LDAP

### C2 — User Model & OIDC Claim Mapping (from Track D Phase 0.2–0.4)

These steps are logically part of Track D Phase 0 but depend on C1 being operational:

- [ ] Add `data_scope` field to User model (`own` / `site` / `all`, default `all`)
- [ ] Add `accessible_sites` M2M to Site
- [ ] Create `ExternalIdentity` model (`user`, `provider`, `external_id`)
- [ ] Extend role choices: `experimenter` (read-only, own data), `exploit` (read+update, all operational)
- [ ] Update `routes/api/sessions.py`: auto-create `ExternalIdentity` on login if `monitoring_id` claim present
- [ ] Implement `get_user_record_queryset(user)`, `get_user_site_queryset(user)` in `dependencies.py`
- [ ] Wire scoped queries into `GET /api/records`, `GET /api/sites/{id}/records`, `GET /api/parts/{id}/records`

---

## Track D — Operational Statistics Backend

> Sources: `roadmap-operational-stats.md`, `django-database-routing.md`, `rustfs-parquet-frontend-display.md`  
> ~12 months; interleaves with Track E. See detailed descriptions in `roadmap-operational-stats.md`.
>
> **Terminology.** The MagnetDB entity `Record` represents an **operational run** — the control-system recordings from a magnet operation period. This is distinct from what the EMFL/ISABEL DMP calls an "experiment" (the scientist's user campaign, governed by a separate DMP). The word "experiment" is not used in this track to avoid confusion. The `experimenter` field on `Record` is the *operator* identity from the control system, not the scientist.
>
> **UserDB**: term used in this plan for the external read-only operational databases at LNCMI (SUPERVISION, PIGBROTHER, HYBRID MySQL instances). These are the upstream data sources for the ingestion pipeline. See `django-database-routing.md` for the full implementation reference.

### D0 — Foundation: Model Evolution (3–4 weeks)

Extends Record, User models; implements scoped query layer; OIDC claim mapping.  
**Depends on**: Track C (C2 overlaps with D0.2–D0.4)

| Sub-phase | Deliverable |
|-----------|-------------|
| D0.0 | External DB connectivity — UserDB router (prerequisite for D1 ingestion) |
| D0.1 | Record model redesign (`record_type`, `sources`, `curated`, `experimenter`, time bounds, `stream_id`) |
| D0.2 | User model + `ExternalIdentity` model + new roles ← covered in Track C |
| D0.3 | Scoped query layer in `dependencies.py` |
| D0.4 | OIDC claim mapping in `sessions.py` ← covered in Track C |

#### D0.0 — External DB Connectivity / UserDB Router

> Reference: `django-database-routing.md`  
> Goal: Give MagnetDB read-only ORM access to the three operational MySQL databases so that D1–D4 ingest tasks can query them directly without bespoke connection code.

**D0.0.1 — Driver & settings (~½ day)**
- [ ] Add `mysqlclient` (or `pymysql` fallback) to `pyproject.toml`
- [ ] Extend `python_magnetdb/settings.py`: add `supervision`, `pigbrother`, `hybrid` database entries (all read-only MySQL; credentials via env vars)
- [ ] Add corresponding env vars to `.envrc.example` (`SUPERVISION_DB_HOST`, `PIGBROTHER_DB_HOST`, `HYBRID_DB_HOST`, …)

**D0.0.2 — Router (~½ day)**
- [ ] Create `python_magnetdb/routers.py` with `MagnetDBRouter`:
  - `db_for_read`: routes `supervision`/`pigbrother`/`hybrid` app_label to their MySQL DB; everything else → `default`
  - `db_for_write`: raises on any write attempt to operational DBs
  - `allow_migrate`: blocks migrations on operational DBs entirely
- [ ] Register in `settings.py`: `DATABASE_ROUTERS = ['python_magnetdb.routers.MagnetDBRouter']`

**D0.0.3 — Operational app skeletons (~1 day)**
- [ ] Create `operational/supervision/`, `operational/pigbrother/`, `operational/hybrid/` Django apps (each with `apps.py` setting `managed = False` and correct `label`)
- [ ] Bootstrap initial models via `manage.py inspectdb --database=<alias>`; clean up: set `managed = False`, correct `app_label`, drop unwanted fields
- [ ] Register apps in `INSTALLED_APPS`
- [ ] Smoke-test: `SupervisionRun.objects.using('supervision').count()` returns without error

**D0.0.4 — Verify migration safety (~15 min)**
- [ ] Confirm `manage.py migrate` (no `--database` flag) does not touch MySQL schemas
- [ ] Confirm `manage.py migrate --database=supervision` is also blocked by router

### D1 — Per-Record Statistics (4–5 weeks)

**Depends on**: D0  
Creates `RecordStats` model; raw and computed (MagnetTools) stats as Celery tasks; per-record and per-entity API endpoints; backfill management command.

Key models: `RecordStats(record, magnet, part, category, data JSON, computed_at)`  
Key tasks: `compute_record_raw_stats`, `compute_record_computed_stats`  
Key endpoints: `GET /api/records/{id}/stats`, `GET /api/magnets/{id}/record-stats`, `GET /api/parts/{id}/record-stats`

### D2 — Curated Parquet ETL (3–4 weeks)

> Reference: `rustfs-parquet-frontend-display.md` §2–3; `python-magnetrun-parquet-save-load.plan.md`  
> **Prerequisite**: python_magnetrun parquet Phases 1–6 (FieldMeta category, PandasMagnetData
> saveParquet/loadParquet, MagnetRun.fromparquet) must be complete or in active progress.  
> **Prerequisite**: Track A A6 (RustFS up and running).

**Depends on**: D1  
Replaces on-the-fly `/visualize` with curated Parquet files stored in RustFS. The `ProcessedTimeSeries`
model is dropped — curated file references live directly on the redesigned `Record` model.

**Data layer mapping**:
- `Record.sources` → D1: list of raw MCS filenames / NAS paths (immutable)
- `Record.curated` → D2: list of `StorageAttachment` FKs pointing to full-resolution Parquet files in RustFS
- One Parquet per `(source_type, group)`: Pupitre → one file; PigBrother/TDMS → one per group; Hybrid → one per stream
- S3 key convention: `curated/{housing}/{record_id}/{source_type}-{group}.parquet`

**Downsampling policy**: LTTB is applied **at display time only** — no pre-stored downsampled files.
The `max_points` query parameter is the single control knob. If future profiling shows on-the-fly
LTTB is too slow for large PigBrother kHz records, the backend can serve a pre-stored artifact
transparently without any API or frontend change (add a `downsampled_attachments` field).

**Derived columns** (hoop stress per part per timestep via MagnetTools): still pre-computed and
stored as a separate derived Parquet in RustFS, referenced via an additional `StorageAttachment`.

Key tasks: `process_record_raw(record_id)` — parse via python_magnetrun → `mdata.saveParquet()` →
attach to `Record.curated`; `process_record_derived(record_id)` — MagnetTools computation → store
derived Parquet.

Key endpoints:
- `GET /api/records/{id}/timeseries/data?columns=B,t&max_points=1000&t_min=…&t_max=…` — server-side
  LTTB from full-res Parquet (Option A, replaces `/visualize`; zero frontend change)
- `GET /api/records/{id}/timeseries/presigned-url` — returns a pre-signed RustFS URL + column catalog
  (Option B, used by `TimeseriesViewer` component and CEMOSIS Python notebooks)

Old `/visualize` kept functional (deprecated header added).

**Initial scope (Pupitre only)**: PigBrother and Hybrid Parquet curation follows when
`python_magnetrun` TDMS parquet (Phase 5) is complete (DMP Annex A open point 4).

### D3 — Cumulative Stats & Lifetime Views (3–4 weeks)

**Depends on**: D1  
`CumulativeStats` model aggregates per-record stats into lifetime summaries; stitched time series for trend plots; auto-refresh wired into ingest chain.

Key endpoints: `GET /api/sites/{id}/stats`, `GET /api/magnets/{id}/stats/history?field=…`

### D4 — Automated Offline Ingestion (3–4 weeks)

**Depends on**: D2, D3  
Celery Beat directory scanner; full ingest pipeline chain: file → Record (with curated Parquet) → RecordStats → CumulativeStats; `IngestLog`; admin status endpoint.

### D5 — Streaming Readiness & Online Data (6–8 weeks)

**Depends on**: D4 (can be deferred until NI/DB integration is concretely planned)  
Redis Streams buffer; `BaseStreamAdapter` + `DatabasePollAdapter` + `NIStreamAdapter` skeleton; window manager; optional WebSocket live endpoint; stream management admin API.

---

## Track E — Frontend Migration

> Sources: `vue-cli-4-to-5-migration.md`, `node-image-migration-bookworm-to-trixie.md`, `roadmap-operational-stats.md`

### E0 — Current baseline (complete on `node22` branch ✅)

The `node22` branch already delivers the following, ready to merge to `main`:

| Task | Details | Status |
|------|---------|--------|
| Node 18-bookworm → 22-trixie | Two-step via Node 20-trixie; both Dockerfiles updated | ✅ |
| Vue CLI 4 → 5 (Webpack 4 → 5) | `@vue/cli-*` bumped to `~5.0.0`; `--openssl-legacy-provider` removed | ✅ |
| TailwindCSS 2 → 3 (PostCSS 8) | `purge` → `content`; `@tailwindcss/forms` 0.3 → 0.5 | ✅ |
| `babel-eslint` → `@babel/eslint-parser` | Peer-dep forced ESLint 6 → 8 in the same step | ✅ |
| ESLint 8 → 9 flat config | `eslint.config.js`; `eslint-plugin-vue ^10`; `lint` script → `eslint src/` | ✅ |
| `Vue.filter` → `Vue.prototype.$filters` | `main.js` + all 12 templates updated | ✅ |
| Webpack 5 Node polyfill fallbacks | `resolve.fallback: { stream: false, assert: false }` in `vue.config.js` | ✅ |
| Full smoke test | All views, forms, charts, Monaco editor verified on Node 22 | ✅ |

**Immediate action**: merge `node22` → `main` before starting E1 on either path.

---

### Decision: Vue 3 vs React

The current frontend is **Vue 2** (Options API SFCs, Vuex 3, Vue Router 3, TailwindCSS 3, chart.js, plotly.js, Monaco editor). Vue 2 reached end-of-life on **2023-12-31**.

| Factor | Vue 3 | React |
|--------|-------|-------|
| Migration strategy | Incremental (`@vue/compat`) | Full rewrite |
| Existing code reuse | ~80% of template logic | ~20% (logic only) |
| Time to first deployable result | 2–3 weeks | 6–8 weeks |
| Total effort (1.5 FTE part-time) | 6–10 weeks | 4–6 months |
| Risk to production stability | Low | Medium–High |
| Team ramp-up | None (team already knows Vue) | Medium (JSX, hooks, different model) |
| Ecosystem breadth | Medium | Large |
| Hiring pool | Medium | Large |
| Long-term community momentum | Good (Vue 3 actively developed) | Excellent |

**Recommended path**: **Vue 3** — incremental migration, low production risk, work already done on the `node22` branch gives a meaningful head start. Choose React only if there is a concrete plan to grow the team beyond 3–4 people or to consolidate with other React-based internal tools.

Both paths are documented below so either can be started from the same E0 baseline.

---

### Path A — Vue 3 Migration (recommended, ~6–10 weeks)

#### E-A1 — Compatibility build & audit (1–2 weeks)

**Goal**: Get the app booting under `@vue/compat` without any functional regressions.

- [ ] Install `@vue/compat` (drop-in replacement for `vue`):
  ```bash
  npm install vue@^3 @vue/compat
  npm install -D @vue/compiler-sfc
  ```
- [ ] Configure `vue.config.js` to alias `vue` → `@vue/compat`:
  ```js
  config.resolve.alias.set('vue', '@vue/compat')
  ```
- [ ] Set global compat config in `main.js`:
  ```js
  import { createApp, configureCompat } from 'vue'
  configureCompat({ MODE: 2 })  // Vue 2 mode with Vue 3 warnings
  ```
- [ ] Boot the app; collect all `[Vue warn]: COMPAT` messages in the console
- [ ] Triage warnings into three buckets:
  - **Already fixed**: `Vue.filter` removal (done ✅)
  - **Breaking**: `v-model` argument change, `$attrs/$listeners` merge, slot unification, `Vue.set`/`Vue.delete`, `$children`
  - **Non-breaking / gradual**: `Vue.use` → `app.use`, global component registration

Exit criterion: app boots and all major routes are navigable without console errors.

#### E-A2 — Core infrastructure migration (1–2 weeks)

**Vue Router 3 → 4**

- [ ] `npm install vue-router@^4`
- [ ] Replace `new Router({...})` → `createRouter({ history: createWebHistory(), routes })`
- [ ] Replace `router.beforeEach` callback signature: `(to, from, next)` → `(to, from)` returning a value
- [ ] Update dynamic import syntax if using string-based lazy loading

**Vuex 3 → Pinia**

- [ ] `npm install pinia`
- [ ] Create one Pinia store per Vuex module (auth, magnets, sites, parts, records, visualisation)
- [ ] Each store: `defineStore('name', { state: () => ({...}), getters: {}, actions: {} })`
- [ ] Replace `this.$store.commit/dispatch` in components with store action calls
- [ ] Remove Vuex entirely once all modules are migrated

**Global API changes**

- [ ] Replace `new Vue({...}).$mount('#app')` → `createApp(App).use(router).use(pinia).mount('#app')`
- [ ] Replace `Vue.component(...)` (global) → `app.component(...)`
- [ ] Replace `Vue.use(...)` → `app.use(...)`
- [ ] Replace `Vue.prototype.$x = y` → `app.config.globalProperties.$x = y`

Exit criterion: app boots with Vue 3 proper (no `@vue/compat`), routing works, Pinia stores initialise.

#### E-A3 — Component migration (3–5 weeks)

Migrate one SFC at a time, starting with leaf components (no children) and working up to layout/page components.

**v-model changes** (most common breaking change)

- [ ] `v-model` on native inputs: unchanged
- [ ] `v-model` on custom components: `value` prop + `input` event → `modelValue` prop + `update:modelValue` event
- [ ] `v-model:propName` syntax for multiple bindings

**Slots**

- [ ] Replace `slot="name"` attribute → `v-slot:name` directive
- [ ] Replace `$slots.default` → `$slots.default()`
- [ ] Replace scoped slots `slot-scope` → `v-slot:name="{ prop }"`

**$attrs and $listeners**

- [ ] `$listeners` is removed; merged into `$attrs` in Vue 3
- [ ] Components using `v-bind="$listeners"` → `v-bind="$attrs"` (now includes event listeners)
- [ ] Components that use `inheritAttrs: false` may need `useAttrs()` composable

**Lifecycle hooks** (minimal changes in Options API)

- [ ] `beforeDestroy` → `beforeUnmount`
- [ ] `destroyed` → `unmounted`
- [ ] All other hooks unchanged in Options API

**Transition names**

- [ ] `v-enter` → `v-enter-from`
- [ ] `v-leave` → `v-leave-from`

**Priority order for migration (component categories)**:

1. Pure presentational components: `StatusBadge`, `Button`, `Card`, `Alert`, `Modal`, `Popover`
2. Form components: `Form`, field wrappers, `MeshAttachmentEditor`
3. Chart/visualisation components: `BmapChart`, `StressMapChart`, `TimeseriesChart`
4. List views: `Sites/Index`, `Magnets/Index`, `Parts/Index`, `Records/Index`
5. Detail/show views: `Sites/Show`, `Magnets/Show`, `Parts/Show`
6. Layout: `App.vue`, `Nav`, `Sidebar`

Exit criterion: all routes render without Vue compat warnings; ESLint `eslint-plugin-vue` v10 rules pass.

#### E-A4 — New feature components (1–2 weeks)

Build the new frontend components for Track D stats/timeseries endpoints (available from D1 onward):

- [ ] `RecordStatsCard.vue` — displays per-record stats (min/max/mean/std) for a given scope
- [ ] `CumulativeStatsPanel.vue` — lifetime summary for a site/magnet/part
- [ ] `TrendChart.vue` — per-record stats over time (stitched series, using existing chart.js or plotly.js)
- [ ] `TimeseriesViewer.vue` — replaces current `VisualisationCard`; two display modes:
  - **Phase D2 initial (Option A)**: calls `GET /api/records/{id}/timeseries/data?columns=…&max_points=1000` — server-side LTTB, no new JS dep
  - **Upgraded (Option B)**: calls `GET /api/records/{id}/timeseries/presigned-url`, then uses `hyparquet` (`npm install hyparquet`) for client-side columnar reads + LTTB; the same pre-signed URL is usable by CEMOSIS in Python notebooks (`pd.read_parquet(url)`)
- [ ] `ExperimenterRecordList.vue` — scoped record list for `experimenter` role
- [ ] Admin UI: `UserScopeEditor.vue` — manage `data_scope` and `accessible_sites` per user

#### E-A5 — Vue CLI → Vite (optional, 1 week)

Vue CLI 5 is fully functional and not end-of-life, but Vite offers substantially faster dev-server startup and HMR. This step is optional and can be deferred.

- [ ] `npm install -D vite @vitejs/plugin-vue`
- [ ] Create `vite.config.js` replacing `vue.config.js`
- [ ] Update `index.html` to be at the project root (Vite convention)
- [ ] Replace `process.env.VUE_APP_*` → `import.meta.env.VITE_*`
- [ ] Update `web/Dockerfile` build step: `npm run build` still works (Vite outputs to `dist/`)
- [ ] Remove `@vue/cli-service`, `webpack`, `@vue/cli-plugin-*`

Exit criterion: `vite build` and `vite dev` replace `vue-cli-service build/serve`; Docker images unchanged.

---

### Path B — React Migration (full rewrite, ~4–6 months)

> Choose this path only if the team plans to grow beyond 3–4 people or to consolidate with other React-based internal tools. All phases are sequential; no incremental deployment until E-B3.

#### E-B0 — Decision prerequisites

Before committing to React, resolve:
- [ ] Confirm team will learn React (JSX, hooks, `useEffect`, `useContext`) — budget 2–3 weeks ramp-up
- [ ] Choose state management: **TanStack Query** (server state, recommended for this API-heavy app) + **Zustand** (client state) — avoids Redux boilerplate
- [ ] Choose routing: **React Router v6** (file-based routing via `createBrowserRouter`)
- [ ] Confirm build tool: **Vite + React** (`@vitejs/plugin-react`) — replaces Vue CLI 5
- [ ] Decide on TypeScript: strongly recommended for a full rewrite (enables gradual adoption)

#### E-B1 — Parallel app skeleton (2–3 weeks)

Run in a separate directory (`web-react/`) until ready to cut over.

- [ ] `npm create vite@latest web-react -- --template react-ts`
- [ ] Install core deps:
  ```bash
  npm install @tanstack/react-query react-router-dom zustand axios
  npm install -D tailwindcss @tailwindcss/forms autoprefixer
  ```
- [ ] Configure TailwindCSS (same design tokens as current app — reuse `tailwind.config.js`)
- [ ] Set up `QueryClient`, `BrowserRouter`, and `ZustandStore` in `main.tsx`
- [ ] Implement the API client layer (`src/api/`) matching the existing FastAPI endpoints
- [ ] Set up `react-router-dom` routes matching the current Vue Router routes

#### E-B2 — Auth & layout shell (1–2 weeks)

- [ ] Implement OIDC login flow (replace `routes/api/sessions.py` integration):
  - Use `@tanstack/react-query` to fetch `/api/sessions/me`
  - Store auth state in Zustand
  - `<ProtectedRoute>` wrapper for role-gated pages
- [ ] Implement the main layout: nav bar, sidebar, content area (reuse TailwindCSS classes)
- [ ] Implement `StatusBadge` component (port colour mapping from `StatusBadge.vue`)
- [ ] Implement shared UI primitives: `Button`, `Card`, `Modal`, `Alert`, `Form`

#### E-B3 — Feature pages (6–10 weeks)

One route group at a time. Each group below is independently deployable behind a feature flag once complete.

**Sites** (1–1.5 weeks)
- [ ] `SiteList` — `useQuery(['sites'], fetchSites)` + table + status filter
- [ ] `SiteShow` — detail view with magnet list, mesh list, record list
- [ ] `SiteForm` — create/edit
- [ ] Shutdown workflow: multi-step dialog (reuse the B1 lifecycle model)

**Magnets** (1–1.5 weeks)
- [ ] `MagnetList`, `MagnetShow`, `MagnetForm`
- [ ] Retire / defunct actions (B1 lifecycle)

**Parts** (1 week)
- [ ] `PartList`, `PartShow`, `PartForm`
- [ ] Mesh attachment editor: `<MeshEditor>` using `react-dropzone` for file upload

**Records & Visualisation** (2–3 weeks)
- [ ] `RecordList` (with server-side pagination via TanStack Query)
- [ ] `RecordShow` with stats cards and time series viewer
- [ ] `TimeseriesChart` component — two display modes (mirror Vue path):
  - **Option A** (initial): `useQuery` → `GET /api/records/{id}/timeseries/data?columns=…&max_points=1000` → `react-plotly.js`
  - **Option B** (upgraded): `useQuery` → pre-signed URL → `hyparquet` columnar read + client-side LTTB → `react-plotly.js`; install: `npm install hyparquet`
- [ ] `BmapChart` and `StressMapChart`: wrap existing chart.js or plotly.js calls in React components
- [ ] Monaco editor: use `@monaco-editor/react` package

**Admin UI** (1–2 weeks)
- [ ] `UserList`, `UserShow`, `UserScopeEditor` (data_scope, accessible_sites, ExternalIdentity)
- [ ] `IngestStatusPage` — admin ingestion log (Track D Phase D4)
- [ ] `StreamStatusPage` — stream management (Track D Phase D5, deferred)

#### E-B4 — Cutover & cleanup (1–2 weeks)

- [ ] Move `web-react/` → `web/`; archive `web/src/` (keep in git history)
- [ ] Update `web/Dockerfile` and `web/Dockerfile-dev` to use the Vite build
- [ ] Update nginx config (`web/config/nginx.conf`) — path rewriting for SPA (same as current)
- [ ] Remove Vue CLI, Vue 2, Vuex, Vue Router 3 deps
- [ ] Update `docker-compose*.yml` — no `web/Dockerfile` changes needed (same `dist/` output path)

#### Library equivalences (Vue 2 → React)

| Vue 2 (current) | React equivalent |
|----------------|-----------------|
| Vuex 3 | Zustand (client state) + TanStack Query (server state) |
| Vue Router 3 | React Router v6 |
| `axios` + manual loading state | TanStack Query (`useQuery`, `useMutation`) |
| `chart.js` | `react-chartjs-2` wrapper |
| `plotly.js` | `react-plotly.js` wrapper |
| Monaco editor (CDN) | `@monaco-editor/react` |
| TailwindCSS 3 | TailwindCSS 3 (unchanged) |
| `vue-final-modal` | `headlessui` or custom portal |
| `@vue/compat` warnings | TypeScript strict mode |
| *(new)* client-side Parquet reads | `hyparquet` (pure JS, no WASM; HTTP range requests for columnar projection) |

---

### Shared considerations (both paths)

**Build tooling baseline** (already established on `node22` branch)

| Item | Current state |
|------|--------------|
| Node | 22-trixie ✅ |
| Base Docker image | `node:22-trixie` ✅ |
| ESLint | 9 flat config ✅ |
| TailwindCSS | 3.x ✅ |
| Build output | `web/dist/` served by `nginx:alpine` ✅ |

**nginx config** (`web/config/nginx.conf`) — keep as-is for both paths; it already handles SPA routing with `try_files $uri $uri/ /index.html`.

**API contract** — the FastAPI backend is path-stable. Both paths use the same endpoints. No backend changes are needed for E1–E5.

**Testing**
- Vue 3 path: add `@vue/test-utils@^2` + `vitest` (replaces Jest + `@vue/test-utils@^1`)
- React path: `@testing-library/react` + `vitest` (or Jest)
- Both: keep the existing backend pytest suite unchanged

---

## Section 5 — Interleaving & Recommended Cadence

```
Month 1:     Track A (A0–A1): runner, GPG, magnettools packaging
             Track B (B1.1–B1.2): lifecycle status backend
             Track C (C1): LemonLDAP Combination auth

Month 2:     Track A (A2–A3): PyPI server (RustFS backend), pyproject.toml
             Track A (A6): MinIO → RustFS migration (can run in parallel with A2)
             Track B (B1.3–B1.5): lifecycle frontend + tests
             Track B (B2): standalone Mesh model
             Track B (B3): standalone CAD model

Month 3:     Track A (A4–A5): Docker pipeline, integration tests
             Track D (D0.0): UserDB router — external DB connectivity (no C dependency)
             Track C (C2) / Track D (D0.1–D0.4): User model, OIDC mapping, scoped queries
             [Vue 3] Track E (E-A1): merge node22 branch; install @vue/compat; collect warnings
             [React]  Track E (E-B1): scaffold Vite+React app in web-react/; API client layer

Month 4:     Track D (D1): RecordStats — API-only, test via Swagger/curl
             [Vue 3] Track E (E-A2): Vue Router 4 + Pinia migration
             [React]  Track E (E-B2): Auth + layout shell; StatusBadge; shared UI primitives

Month 5–6:   Track D (D2): Curated Parquet ETL (replaces /visualize; RustFS must be live)
             [Vue 3] Track E (E-A3): component migration (leaf → layout)
             [React]  Track E (E-B3 start): Sites, Magnets, Parts pages
             → New frontend components can consume new stats/timeseries endpoints

Month 7–8:   Track D (D3): CumulativeStats
             [Vue 3] Track E (E-A3–E-A4): trend charts, experimenter views, admin UI
             [React]  Track E (E-B3 cont.): Records, Visualisation, Admin pages

Month 9:     Track D (D4): automated offline ingestion (pure backend)
             [Vue 3] Track E (E-A5): polish + optional Vue CLI → Vite
             [React]  Track E (E-B4): cutover; archive Vue source; update Dockerfiles

Month 10–12: Track D (D5): streaming (when NI/DB integration is ready)
             → Real-time dashboard components (WebSocket) whichever path was chosen
```

**Key sequencing rules:**
- A0 must complete before A1 and A2 (they share the runner and org secrets)
- A6 (RustFS migration) must complete before D2 Parquet ETL writes curated files; can run in parallel with A2–A3
- B1 backend phases (B1.1–B1.2) must deploy before frontend phases (B1.3–B1.4)
- C1 must be stable before C2/D0.4 (OIDC claim mapping depends on LemonLDAP exporting the claim)
- D0.0 (UserDB router) has no external dependency and can start in Month 2 alongside B/C work
- D0 must complete before D1; D1 before D2 and D3; D2+D3 before D4
- E-A1 / E-B1 can start as soon as `node22` branch merges; largely independent from D0–D2
- TimeseriesViewer Option B (`hyparquet`) requires A6 (RustFS CORS) and D2 (presigned-url endpoint)
- **Frontend path decision must be made before Month 3** — the two paths diverge immediately

---

## Section 6 — Effort Summary

| Track | Phase | Effort | Assignee |
|-------|-------|--------|----------|
| A | A0 Prerequisites | 1 day | Christophe (GPG), Rémi (runner) |
| A | A1 magnettools | 2 days | Christophe |
| A | A2 PyPI server | 1 day | Rémi |
| A | A3 pyproject.toml | ½ day | Rémi |
| A | A4 Docker pipeline | 1½ days | Both |
| A | A5 Docs + integration | 1 day | Both |
| A | A6 MinIO → RustFS migration | 1–2 days | Christophe |
| **A total** | | **~8–9 days** | |
| B | B1 Lifecycle status | 5 days | Both |
| B | B2 Mesh model | 3 days | Christophe |
| B | B3 CAD model | 3 days | Christophe |
| **B total** | | **~11 days** | |
| C | C1 LemonLDAP | 1–2 days | Christophe |
| C | C2 User/OIDC mapping | 2–3 days | Christophe |
| **C total** | | **~5 days** | |
| D | D0.0 UserDB router (ext. DB connectivity) | 2 days | Christophe |
| D | D0.1–D0.4 Foundation (model, scoped queries, OIDC) | 3–4 weeks | Both |
| D | D1 RecordStats | 4–5 weeks | Both |
| D | D2 Curated Parquet ETL | 3–4 weeks | Both |
| D | D3 CumulativeStats | 3–4 weeks | Both |
| D | D4 Ingestion | 3–4 weeks | Rémi |
| D | D5 Streaming | 6–8 weeks | Both |
| **D total** | | **~22–29 weeks** | |
| E (Vue 3 path) | E-A1 Compat build + audit | 1–2 weeks | Rémi |
| E (Vue 3 path) | E-A2 Router 4 + Pinia | 1–2 weeks | Rémi |
| E (Vue 3 path) | E-A3 Component migration | 3–5 weeks | Rémi |
| E (Vue 3 path) | E-A4 New stats/timeseries components | 1–2 weeks | Rémi |
| E (Vue 3 path) | E-A5 Vite (optional) | 1 week | Rémi |
| **E total (Vue 3)** | | **~6–10 weeks** | |
| — or — | | | |
| E (React path) | E-B1 Vite + React skeleton | 2–3 weeks | Both |
| E (React path) | E-B2 Auth + layout shell | 1–2 weeks | Both |
| E (React path) | E-B3 Feature pages | 6–10 weeks | Both |
| E (React path) | E-B4 Cutover + cleanup | 1–2 weeks | Both |
| **E total (React)** | | **~4–6 months** | |
| **Grand total (Vue 3 path)** | | **~11–13 months** | |
| **Grand total (React path)** | | **~15–19 months** | |

---

## Section 7 — Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| manylinux_2_28 base can't build magnettools C++ deps | Medium | A1.2 blocked | Fall back to `debian:bookworm` base |
| Baremetal depot `postupload` hook not yet configured | Unknown | A1.3 blocked | Clarify before A1.1 |
| LemonLDAP Combination module breaks existing LDAP login | Medium | C1 rollback | Test in staging with a shadow rule first |
| `monitoring_id` LDAP attribute not consistently populated | Medium | C2/D0.4 blocked | Make ExternalIdentity creation optional; log missing claims |
| MagnetTools fails for certain magnet configs | Medium | D1/D2 degraded | Degrade gracefully: keep raw stats, skip computed, log error |
| RustFS migration data loss or service interruption | Low | A6 blocked | Run `mc mirror` with `--overwrite=false`; keep MinIO live until full smoke-test passes |
| Parquet storage growth in RustFS | Low | D2 storage | Full-res D2 files are 200 KB–2 MB each; monitor bucket size; use zstd compression in `saveParquet()` |
| python_magnetrun parquet Phases 1–6 not ready when D2 starts | Medium | D2 delayed | Fall back to MagnetDB-internal pyarrow conversion for Pupitre; reprocess when python_magnetrun lands |
| RustFS CORS misconfiguration blocks client-side Parquet reads | Low | Option B unavailable | Start with Option A (server-side); Option B is an upgrade, not a blocker |
| Existing `defunct` site records need manual normalisation to `stopped` | Unknown | B1.5 audit | Run audit query before deploying B1; prepare targeted data migration |
| NI streaming hardware integration delayed | High | D5 deferred | D5 is designed to be deferrable — D0–D4 deliver full value without it |
| Vue 3 → Vite migration adds scope to Track E | Low | E-A5 extended | Keep Vite as optional; Vue CLI 5 is fully functional |
| Vue 3 compat warnings reveal hidden `$children`/`$listeners` usage | Low | E-A1 extended | Audit all components for `$children`; replace with `ref` or slot pattern |
| React rewrite scope creep (TypeScript, new test suite, full redesign) | High | E-B delayed | Timebox each feature page strictly; no design overhaul in E-B3 |
| React: plotly.js / chart.js wrapper libraries add indirection | Low | E-B3 rework | Evaluate `react-plotly.js` and `react-chartjs-2` early in E-B1 |

---

## Section 8 — Immediate Next Steps (Month 1)

1. **A0**: Provision GitHub runner; create GPG subkey; generate SSH deploy key
2. **B1.1**: Add `RETIRED`, `STOPPED` to `status.py`; generate and review migration; deploy to test env
3. **B2**: Create `mesh.py` model; generate migration; write backfill data migration
4. **B3**: Create `cad.py` model; generate migration; write backfill data migration (same pattern as B2, can run in parallel)
5. **C1**: Enable Combination module in LemonLDAP staging; validate existing LDAP login still works
6. **Decision**: Confirm Vue 3 or React path (see Track E decision matrix); communicate to Rémi; merge `node22` → `main` as the shared starting point for either path

**Quick-start for B1.1 (can start today):**
```bash
git checkout -b feature/lifecycle-status-retired-stopped
# Edit python_magnetdb/models/status.py — add RETIRED, STOPPED
python manage.py makemigrations
# Review generated migration
python manage.py migrate
# Run test suite
```

**Quick-start for B2 (parallel branch):**
```bash
git checkout -b feature/mesh-model
# Create python_magnetdb/models/mesh.py
# Register in __init__.py
python manage.py makemigrations
# Write backfill data migration
```

**Quick-start for B3 (parallel branch):**
```bash
git checkout -b feature/cad-model
# Create python_magnetdb/models/cad.py
# Register in __init__.py
python manage.py makemigrations
# Write backfill data migration (CadAttachment → Cad)
```
