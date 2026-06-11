# MagnetDB Operational Data & Statistics — Implementation Roadmap

## Context & Constraints

- **Team**: Christophe (lead) + Rémi, effectively 1.5 FTE on MagnetDB
- **Parallel work**: Frontend migration (5 phases) is planned — **Vue 3 or React, decision pending** (see comparison below)
- **Production stability**: LNCMI research operations depend on the platform
- **Principle**: Incremental delivery — each phase delivers standalone value

### Frontend prerequisite status (as of 2026-05-06) ✅

The following build tooling work is complete on the `eslint` branch. It is a prerequisite for both migration paths:

| Task | Status | Relevance |
|------|--------|-----------|
| Vue CLI 4 → 5 (Webpack 4 → 5) | ✅ Done | Vue 3: unblocks compat build; React: useful if keeping Webpack, but Vite is preferred |
| Node 18 → 22 (`node:22-trixie`) | ✅ Done | Both paths |
| ESLint 6 → 9 with flat config | ✅ Done | Both paths |
| `Vue.filter` → `Vue.prototype.$filters` | ✅ Done | Vue 3: required (Vue.filter removed); React: irrelevant |

---

## Frontend Migration Decision: Vue 3 vs React

The current frontend is **Vue 2** (Options API SFCs, Vuex 3, Vue Router 3, TailwindCSS, chart.js, plotly.js, Monaco editor). Vue 2 reached end-of-life on **2023-12-31**.

### Vue 3 migration

**Approach**: Incremental upgrade using the [Vue 2 migration build](https://v3-migration.vuejs.org/migration-build.html) (`@vue/compat`), then progressively opt components into Vue 3 mode. Vuex → Pinia, Vue Router 3 → 4.

| Pros | Cons |
|------|------|
| Most existing Options API SFCs are Vue 3-compatible with minimal changes | Vue ecosystem is smaller than React — fewer community packages, fewer developers available |
| Incremental migration: one component at a time, no big-bang rewrite | Vue 2 → 3 still has breaking changes: `v-model`, slots, `$attrs/$listeners`, global API (`Vue.use`, `Vue.set`) all changed |
| Vuex → Pinia is a simple, mechanical migration | Vetur IDE plugin must be replaced by Volar |
| Vue Router 3 → 4 requires minimal changes | Vue CLI 5 should be replaced by Vite for the full benefit of Vue 3 (separate effort) |
| TailwindCSS, chart.js, plotly.js, axios, Monaco editor: all unchanged | Long-term: smaller hiring pool |
| No paradigm shift — team already knows Vue | |
| `Vue.filter` already removed (one blocker already cleared) | |
| **Estimated effort**: 6–10 weeks (Christophe + Rémi part-time) | |

**Recommended if**: production stability and migration speed are the top priorities, and the team plans to stay primarily Vue-oriented.

---

### React migration

**Approach**: Full rewrite. All Vue SFCs become React components (JSX/TSX). Vuex → Zustand or TanStack Query. Vue Router → React Router v6. Build tool: Vite + React.

| Pros | Cons |
|------|------|
| Largest frontend ecosystem — most packages have React-first support | **Complete rewrite** — every `.vue` file must be reimplemented |
| Largest hiring pool — easier to onboard new developers | No incremental path: requires a parallel app or a big-bang cutover |
| React 18+ concurrent features (Suspense, transitions) | Team must learn React (JSX, hooks, different component model) — steep ramp for 1.5 FTE |
| First-class TypeScript support across the ecosystem | Much higher risk to production stability during migration |
| TanStack Query / React Query is excellent for the API-heavy data patterns in MagnetDB | chart.js, plotly.js, Monaco editor need React wrapper components (exist, but add indirection) |
| Vite + React is a very modern, fast build stack | Vuex mental model does not map directly to React — Redux/Zustand/Jotai are different paradigms |
| Better long-term community momentum | **Estimated effort**: 4–6 months (Christophe + Rémi part-time) |

**Recommended if**: long-term maintainability, team growth, and ecosystem breadth outweigh migration cost.

---

### Decision matrix

| Factor | Vue 3 | React |
|--------|-------|-------|
| Migration effort | Low–Medium (incremental) | High (full rewrite) |
| Risk to production | Low | Medium–High |
| Team ramp-up | None | Medium (JSX, hooks) |
| Ecosystem breadth | Medium | Large |
| Hiring pool | Medium | Large |
| Existing code reuse | High (~80% of template logic reusable) | Low (~20% logic reusable) |
| Time to first deployable result | 2–3 weeks | 6–8 weeks |
| Long-term community momentum | Good (Vue 3 is actively developed) | Excellent |

**Recommended path for this team and codebase**: **Vue 3**, unless there is a specific long-term plan to grow the team beyond 3–4 people or to consolidate with other React-based internal tools. The incremental migration approach and the work already done (Vue.filter removal, Vue CLI 5) give a meaningful head start that would be discarded in a React rewrite.

`Vue.filter` is removed from `src/main.js` and all 12 template files updated. The codebase now has no Vue 3 blockers in the build or filter layer.

This roadmap covers the backend evolution for operational data statistics, pre-processed time series, ingestion automation, streaming readiness, and user role/access refinements. It is designed to interleave with the Vue 3 migration without blocking it.

---

## Overview: 6 Phases, ~12 months

| Phase | Name | Duration | Dependencies | Key Deliverable |
|-------|------|----------|-------------|-----------------|
| 0 | Foundation: Record & User model evolution | 3–4 weeks | None | Extended models, migrations, backward-compatible API |
| 1 | Per-record statistics (RecordStats) | 4–5 weeks | Phase 0 | Stats computed per record, per entity; API endpoints |
| 2 | Pre-processed time series (ETL) | 5–6 weeks | Phase 1 | Parquet-based ProcessedTimeSeries; replaces `/visualize` |
| 3 | Cumulative stats & lifetime views | 3–4 weeks | Phase 1 | CumulativeStats model; trend endpoints |
| 4 | Automated ingestion (offline) | 3–4 weeks | Phase 2 | Celery Beat directory watcher; ingest pipeline |
| 5 | Streaming readiness & online data | 6–8 weeks | Phase 4 | Redis Streams buffer; window manager; WebSocket (optional) |

**Total estimated effort**: 24–31 working weeks (~6–8 months of calendar time, accounting for parallel React migration work and operational duties).

**Recommended cadence**: Alternate between backend phases (this roadmap) and Vue 3 migration phases. For example: Vue 3 Phase 1 → Stats Phase 0 → Vue 3 Phase 2 → Stats Phase 1 → etc.

---

## Phase 0: Foundation — Model Evolution (3–4 weeks)

**Goal**: Extend Record and User models to support everything downstream, without breaking existing functionality.

**Why first**: Every subsequent phase depends on these model changes. They are low-risk (additive fields, backward-compatible) and can be deployed immediately.

> **Terminology note.** The MagnetDB entity called `Record` represents an **operational run** — the set of control-system recordings produced during a magnet operation period (Pupitre, PigBrother, or Hybrid). This is *not* what the EMFL/ISABEL DMP calls an "experiment" (which is the scientist's user campaign and is governed by a separate DMP). The two share a time window and possibly a proposal reference, but contain different data under different policies. The `Record` name is kept throughout this roadmap; the word "experiment" is reserved for the EMFL context.

### 0.1 Record model redesign (Week 1)

Add fields to the existing Record model and introduce the D1/D2 data layer split:

- `record_type` (CharField with choices: monitoring, transient, calibration, maintenance) — default "monitoring" for all existing records
- `source` (CharField: offline, stream, database) — default "offline"
- `sources` (JSONField) — list of raw MCS filenames / NAS paths (D1 references, immutable after acquisition)
- `curated` (M2M to StorageAttachment) — curated full-resolution Parquet files in RustFS S3 (D2 layer); one per `(source_type, group)` pair
- `experimenter` (CharField, nullable, indexed) — the operator identity from the control system (not the scientist — see terminology note above)
- `experimenter_user` (FK to User, nullable) — resolved MagnetDB user link
- `started_at`, `ended_at` (DateTimeField, nullable) — time bounds
- `duration_seconds` (FloatField, nullable)
- `stream_id` (CharField, nullable) — for future streaming
- `window_index` (IntegerField, nullable) — for future streaming

Create and apply migration. All new fields are nullable or have defaults, so existing data is unaffected.

**Validation**: Existing record CRUD and `/visualize` endpoint still work unchanged.

### 0.2 User model & roles extension (Week 2)

Extend the User model:

- `data_scope` (CharField: own, site, all) — default "all" for existing users (preserves current behavior)
- `accessible_sites` (M2M to Site, blank=True)

New model: `ExternalIdentity`

- `user` (FK to User)
- `provider` (CharField) — e.g. "lncmi_monitoring", "ldap"
- `external_id` (CharField)
- unique_together on (provider, external_id)

Extend the role choices in `is_authorize()`:

- Add `experimenter` role (read-only, scoped to own data)
- Add `exploit` role (read + update on all operational data)

Create migration. Set all existing users to `data_scope='all'` so nothing changes until you explicitly configure scoping.

**Validation**: All existing API endpoints behave identically. Admin can now set `data_scope` on users.

### 0.3 Scoped query layer (Week 3)

Implement `get_user_record_queryset(user)`, `get_user_site_queryset(user)`, and similar functions in `dependencies.py`. Wire them into:

- `GET /api/records` (list)
- `GET /api/records/{id}` (show — check access)
- `GET /api/sites/{id}/records`
- `GET /api/parts/{id}/records`

**Validation**: With all users still set to `data_scope='all'`, behavior is unchanged. Test with a dedicated test user set to `data_scope='own'` + an ExternalIdentity mapping.

### 0.4 OIDC claim mapping (Week 3–4)

Extend `routes/api/sessions.py` to:

- Request additional OIDC scopes/claims from LemonLDAP (e.g., `monitoring_id`)
- Auto-create ExternalIdentity on login if the claim is present
- Configure LemonLDAP Manager to export the relevant LDAP attribute as an OIDC claim

**Validation**: Login flow still works. Users with the LDAP attribute get an ExternalIdentity record created automatically.

### Deliverables

- [ ] Migration: Record model extension
- [ ] Migration: User model + ExternalIdentity
- [ ] Scoped query functions in dependencies.py
- [ ] Updated session creation with claim mapping
- [ ] Updated admin UI (later, in React) to manage user data_scope and external identities

---

## Phase 1: Per-Record Statistics (4–5 weeks)

**Goal**: For each record, compute and store statistics at site, magnet, and part level — both raw (extracted from data) and computed (via MagnetTools).

### 1.1 RecordStats model (Week 1)

Create the `RecordStats` model:

- `record` (FK to Record)
- `magnet` (FK to Magnet, nullable)
- `part` (FK to Part, nullable)
- `category` (CharField: raw, computed)
- `data` (JSONField) — the stats payload
- `duration_seconds`, `started_at`, `ended_at`
- `computed_at`, `version`
- unique_together on (record, magnet, part, category)

Create migration.

### 1.2 Raw stats computation service (Weeks 2–3)

Implement `compute_record_raw_stats(record_id)`:

- Parse the record attachment using python_magnetrun (or the current pandas-based parser as fallback)
- Compute per-column min/max/mean/std
- Create RecordStats at site level (magnet=null, part=null)
- For each active magnet (via SiteMagnet.commissioned_at/decommissioned_at):
  - Create RecordStats at magnet level with magnet-relevant columns
- For each active part within each magnet:
  - Create RecordStats at part level with the part's coil-specific columns

Register as a Celery task.

### 1.3 Computed stats service (Weeks 3–4)

Implement `compute_record_computed_stats(record_id)`:

- Load MagnetTools data for each active magnet
- For each timestep (or sampled subset), compute hoop stress per part
- Store per-part computed RecordStats with hoop stress, ratio_to_rpe, etc.

This depends on the existing `compute_stress_map_chart` infrastructure — refactor to extract the computation logic into a reusable function.

### 1.4 API endpoints (Week 4–5)

- `GET /api/records/{id}/stats` — all RecordStats for a record
- `GET /api/records/{id}/stats?magnet_id=X` — filtered
- `GET /api/records/{id}/stats?part_id=X` — filtered
- `GET /api/magnets/{id}/record-stats` — all RecordStats for a magnet across records
- `GET /api/parts/{id}/record-stats` — all RecordStats for a part across records

Apply data scoping: use `get_user_record_queryset()` to filter accessible records before returning stats.

### 1.5 Backfill script (Week 5)

Management command to compute RecordStats for all existing records:

```
poetry run python manage.py compute_all_record_stats [--site=X] [--force]
```

### Deliverables

- [ ] Migration: RecordStats model
- [ ] Celery task: raw stats computation
- [ ] Celery task: computed stats (MagnetTools)
- [ ] API endpoints for per-record stats
- [ ] Backfill management command
- [ ] Data scoping applied to stats endpoints

---

## Phase 2: Pre-Processed Time Series / ETL (5–6 weeks)

**Goal**: Replace the on-the-fly `/visualize` endpoint with pre-computed, Parquet-stored time series that support columnar projection, efficient downsampling, and derived columns.

### 2.1 ProcessedTimeSeries model (Week 1)

Create the model:

- `record` (FK, nullable — null for stitched series)
- `site`, `magnet`, `part` (FKs, nullable)
- `scope` (site/magnet/part), `origin` (raw/derived/stitched)
- `attachment` (FK to StorageAttachment — the Parquet file)
- `columns` (JSONField — catalog of available columns with units and roles)
- `started_at`, `ended_at`, `num_points`, `sampling_period_seconds`
- `computed_at`, `version`, `parser_class`, `processing_params`

Create migration.

### 2.2 Parquet infrastructure (Week 1–2)

- Add `pyarrow` to dependencies (for Parquet read/write)
- Implement `store_as_parquet(df, name) -> StorageAttachment` helper
- Implement `read_parquet_columns(attachment, columns, t_min, t_max) -> DataFrame`
- Implement LTTB downsampling function (or add `lttbc` dependency)

### 2.3 Raw ETL pipeline (Weeks 2–3)

Implement `process_record_raw(record_id)`:

- Parse record attachment via python_magnetrun
- Clean DataFrame (remove zero columns, compute t/timestamp — same logic as current `/visualize`)
- Write to Parquet → StorageAttachment
- Create ProcessedTimeSeries with column catalog
- Extract and update Record.started_at/ended_at

Register as Celery task.

### 2.4 Derived ETL pipeline (Weeks 3–4)

Implement `process_record_derived(record_id)`:

- Read raw ProcessedTimeSeries for this record
- For each active magnet, compute derived columns (hoop stress per timestep per part)
- Write magnet-scoped and part-scoped Parquet files
- Create ProcessedTimeSeries entries

### 2.5 New API endpoints (Weeks 4–5)

Catalog endpoints:

- `GET /api/records/{id}/timeseries` — list available series for a record
- `GET /api/sites/{id}/timeseries`
- `GET /api/magnets/{id}/timeseries`
- `GET /api/parts/{id}/timeseries`

Data endpoint:

- `GET /api/timeseries/{id}/data?columns=Field,Icoil1&max_points=1000&t_min=0&t_max=600`

This replaces the current `/api/records/{id}/visualize` endpoint. Keep the old endpoint working (deprecated) during transition.

### 2.6 Backfill & validation (Week 5–6)

- Management command: `compute_all_timeseries [--site=X] [--force]`
- Validate that the new `/timeseries/{id}/data` endpoint produces equivalent results to the old `/visualize` for existing records
- Deprecate old endpoint (keep functional, add deprecation header)

### Deliverables

- [ ] Migration: ProcessedTimeSeries model
- [ ] pyarrow dependency + Parquet helpers
- [ ] LTTB downsampling implementation
- [ ] Celery tasks: raw and derived ETL
- [ ] Catalog + data API endpoints
- [ ] Backfill command
- [ ] Old `/visualize` endpoint deprecated but still functional

---

## Phase 3: Cumulative Stats & Lifetime Views (3–4 weeks)

**Goal**: Aggregate per-record stats into lifetime summaries per entity, and provide time-series-of-stats for trend visualization.

### 3.1 CumulativeStats model (Week 1)

Create the model:

- `site`, `magnet`, `part` (FKs, nullable — exactly one non-null)
- `category` (raw/computed)
- `data` (JSONField — aggregated payload)
- `records_count`, `total_operating_seconds`
- `time_range_start`, `time_range_end`
- `computed_at`, `version`
- unique_together on (site, magnet, part, category)

### 3.2 Aggregation service (Weeks 2–3)

Implement `refresh_cumulative_stats(entity_type, entity_id)`:

- Query all RecordStats for the entity
- Compute global min/max/mean/std across all records
- Count records, sum operating hours
- Track which record holds the global max for key metrics
- Support incremental update (add a new record's contribution) and full recompute

Implement stitched time series builder:

- `build_stitched_series(entity_type, entity_id, field)` — creates a ProcessedTimeSeries of type "stitched" from RecordStats, one point per record

### 3.3 API endpoints (Weeks 3–4)

Summary endpoints:

- `GET /api/sites/{id}/stats` → CumulativeStats
- `GET /api/magnets/{id}/stats` → CumulativeStats
- `GET /api/parts/{id}/stats` → CumulativeStats

History/trend endpoints:

- `GET /api/sites/{id}/stats/history?field=Field&category=raw`
- `GET /api/magnets/{id}/stats/history?field=hoop_stress&category=computed`
- `GET /api/parts/{id}/stats/history?field=hoop_stress`

These return ordered per-record stats over time — plottable as trend lines.

### 3.4 Auto-refresh on new records (Week 4)

Wire the cumulative stats refresh into the record ingest chain:

```
ingest → RecordStats → ProcessedTimeSeries → refresh CumulativeStats
```

### Deliverables

- [ ] Migration: CumulativeStats model
- [ ] Aggregation service (incremental + full recompute)
- [ ] Stitched series builder
- [ ] Summary + history API endpoints
- [ ] Auto-refresh wired into ingest chain
- [ ] Backfill command for cumulative stats

---

## Phase 4: Automated Offline Ingestion (3–4 weeks)

**Goal**: Automatically detect new record files on the sshfs directory and run the full ingest pipeline (Record → ProcessedTimeSeries → RecordStats → CumulativeStats).

### 4.1 Celery Beat setup (Week 1)

- Add `celery-beat` container to docker-compose (same image as worker, different command)
- Configure beat schedule in `worker.py`
- Add environment variables: `INCOMING_RECORDS_DIR`, `PROCESSED_RECORDS_DIR`

### 4.2 Directory scanner task (Weeks 1–2)

Implement `scan_incoming_directory()`:

- List files in INCOMING_RECORDS_DIR
- Skip already-ingested files (check Record.name)
- Resolve site from filename pattern or subdirectory structure
- Extract experimenter from filename or file content (via python_magnetrun)
- Trigger `ingest_record_file.delay()` for each new file

### 4.3 Ingest pipeline orchestration (Weeks 2–3)

Implement `ingest_record_file(filepath, site_id, source)` as a Celery chain:

```python
chain(
    create_record_from_file.s(filepath, site_id),
    process_record_raw.s(),
    process_record_derived.s(),
    compute_record_stats.s(),
    refresh_cumulative_stats.s(),
).apply_async()
```

Handle errors gracefully: if MagnetTools computation fails for a record, still keep raw stats and time series.

### 4.4 Monitoring & admin (Weeks 3–4)

- Add `IngestLog` model or use AuditLog to track ingestion events (file seen, record created, stats computed, errors)
- API endpoint: `GET /api/admin/ingest-status` — show recent ingestion activity
- Admin notification on ingestion errors (optional: simple email or log alert)

### Deliverables

- [ ] Celery Beat container in docker-compose
- [ ] Directory scanner Celery task
- [ ] Ingest pipeline chain
- [ ] IngestLog or AuditLog integration
- [ ] Admin status endpoint
- [ ] Documentation: directory structure conventions, filename patterns

---

## Phase 5: Streaming Readiness & Online Data (6–8 weeks)

**Goal**: Accept live streaming data from NI hardware or external databases, buffer in Redis Streams, and feed into the same pipeline as offline records.

**Note**: This phase can be deferred until the NI streaming or external DB integration is concretely planned. Phases 0–4 provide full value without it.

### 5.1 Redis Streams infrastructure (Weeks 1–2)

- Define stream key convention: `magnetdb:stream:{stream_id}`
- Define stream state key: `magnetdb:stream_state:{stream_id}`
- Implement `StreamConfig` model or configuration for known streams (which site, expected channels, window duration)

### 5.2 Stream adapter framework (Weeks 2–3)

- Abstract `BaseStreamAdapter` class with `push_sample(timestamp, channels)` method
- `DatabasePollAdapter` — polls an external SQL database for new rows
- `NIStreamAdapter` — skeleton for NI DAQmx integration (to be completed when hardware is available)
- Each adapter pushes to a Redis Stream with `XADD`

### 5.3 Window manager (Weeks 3–5)

Implement `close_stream_window(stream_id)`:

- Read messages from Redis Stream since last window close
- Convert to DataFrame
- Write as Parquet → StorageAttachment → Record (with source=STREAM)
- Update stream state (last processed message ID)
- Trigger the same ingest chain as offline records

Add Celery Beat schedule entry for each active stream (configurable window duration, typically 5 minutes).

### 5.4 Live data endpoint (Weeks 5–6, optional)

- WebSocket endpoint: `WS /api/streams/{stream_id}/live`
- Reads from Redis Stream with XREAD block
- Pushes new data points to connected WebSocket clients
- This is a bonus for real-time dashboards; the windowed pipeline is the primary path

### 5.5 Stream management API (Weeks 6–8)

- `GET /api/admin/streams` — list configured streams
- `POST /api/admin/streams` — configure a new stream
- `GET /api/admin/streams/{id}/status` — current state, lag, last window, errors
- `DELETE /api/admin/streams/{id}` — decommission a stream

### Deliverables

- [ ] Redis Streams infrastructure + conventions
- [ ] Stream adapter framework + DatabasePollAdapter
- [ ] NIStreamAdapter skeleton
- [ ] Window manager Celery task
- [ ] Live WebSocket endpoint (optional)
- [ ] Stream management admin API
- [ ] Documentation: how to add a new stream source

---

## Interleaving with the Frontend Migration

The frontend migration (Vue 3 or React) and this backend roadmap are largely independent. The suggested interleaving below is the same regardless of which path is chosen — only the effort column differs.

```
Month 1–2:   Frontend Phase 1 (preparation/audit) ← build tooling prereqs already done
             Stats Phase 0 (model foundations)    ← backend, no UI needed

Month 3–4:   Frontend Phase 2 (core infrastructure)
             Stats Phase 1 (RecordStats)          ← API-only, test via Swagger/curl

Month 4–5:   Stats Phase 2 (ETL/time series)      ← replaces existing /visualize

Month 5–7:   Frontend Phase 3 (component migration)
             Stats Phase 3 (cumulative stats)
             → New frontend components can consume new stats/timeseries endpoints

Month 7–8:   Stats Phase 4 (automated ingestion)  ← pure backend

Month 8–10:  Frontend Phase 4–5 (polish, cleanup)
             → Build stats dashboard, trend charts, experimenter views
             → Admin UI for user roles, data scoping, external identities

Month 10–12: Stats Phase 5 (streaming)            ← when NI/DB integration is ready
             → Real-time dashboard components (if WebSocket path chosen)
```

This interleaving ensures:

- Backend APIs are stable before new frontend components consume them
- The `/visualize` replacement (Phase 2) is ready before the VisualisationCard is migrated
- The user role/scoping system (Phase 0) is in place before external access is enabled
- Streaming (Phase 5) is deferred until actually needed

---

## Risk Mitigation

**MagnetTools dependency**: Phases 1 and 2 depend on MagnetTools for computed stats. If MagnetTools is unavailable or fails for certain magnet configurations, the pipeline must degrade gracefully — store raw stats, skip computed stats, log the error. Never block the entire ingest on a single computation failure.

**python_magnetrun evolution**: Phase 2 depends on python_magnetrun for parsing different record types. If the new record type structure isn't ready, fall back to the current pandas-based parser. The `parser_class` field on ProcessedTimeSeries tracks which parser was used, enabling reprocessing when the parser evolves.

**Parquet storage growth**: Each ProcessedTimeSeries creates a Parquet file in MinIO. For a rough estimate: a typical 500-point monitoring record → ~20KB Parquet file. 1000 records × 3 scope levels × 2 origins ≈ 120MB. Manageable, but monitor MinIO storage and add compression parameters to `processing_params` if needed.

**Data migration safety**: Phase 0 only adds nullable fields and new tables — zero risk to existing data. Each subsequent phase creates new models and data; existing functionality is never removed, only deprecated.

---

## Quick-Start Checklist for Phase 0

If you want to begin immediately:

1. Create a branch: `feature/operational-stats-foundation`
2. Edit `python_magnetdb/models/record.py` — add the new fields
3. Create `python_magnetdb/models/external_identity.py`
4. Edit `python_magnetdb/models/user.py` — add data_scope, roles
5. `poetry run python manage.py makemigrations`
6. Review the migration
7. `poetry run python manage.py migrate`
8. Update `dependencies.py` with scoped query functions
9. Update `routes/api/sessions.py` for OIDC claim mapping
10. Test: all existing functionality works, new fields are accessible

**Estimated time to first deployable result**: 2 weeks for steps 1–8.
