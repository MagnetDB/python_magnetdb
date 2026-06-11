# RustFS Migration, Parquet Storage & Frontend Display

*Created: 2026-05-06 — architectural decisions made during Track D / DMP review*

---

## 1. MinIO → RustFS migration

### Why

RustFS is the planned replacement for MinIO as the S3 object store backing MagnetDB (curated
data D2, derived statistics D3, simulation outputs D5, mesh attachments). The switch is
motivated by operational and licensing considerations; it is transparent to all application code.

### What does not change

RustFS exposes the **same S3-compatible API** as MinIO. Consequently:

| Component | Status |
|-----------|--------|
| `boto3` / `botocore` client code | Unchanged |
| `django-storages` S3 backend | Unchanged — only `AWS_S3_ENDPOINT_URL` env var updated |
| Pre-signed URL generation | Unchanged |
| `StorageAttachment` model | Unchanged |
| `python_magnetrun` S3 helpers (`save_to_s3` / `load_from_s3`) | Unchanged |
| CI/CD workflows that push artifacts to S3 | Unchanged — only endpoint/credentials rotated |

### What changes

| Item | Change |
|------|--------|
| `MINIO_ENDPOINT` env var | Renamed / replaced by `S3_ENDPOINT_URL` pointing to RustFS |
| `MINIO_ACCESS_KEY` / `MINIO_SECRET_KEY` | Replaced by RustFS service-account credentials |
| CORS configuration | Reconfigured in RustFS admin UI (same rules as MinIO) |
| Bucket creation / lifecycle policies | Recreated in RustFS |
| `docker-compose*.yml` | Replace `minio:` service block with `rustfs:` (or `ghcr.io/rustfs/rustfs:latest`) |
| `pypiserver` backend (Track A, A2) | Update to use RustFS endpoint instead of MinIO |

### Migration procedure (one-time)

1. Stand up the RustFS container alongside the existing MinIO instance.
2. Create the same bucket structure in RustFS (`magnetdb-attachments`, `magnetdb-parquet`, etc.).
3. Use `mc mirror` (MinIO client, compatible with any S3 endpoint) to copy all objects:
   ```bash
   mc alias set src  http://minio:9000   MINIO_ACCESS_KEY MINIO_SECRET_KEY
   mc alias set dst  http://rustfs:9000  RUSTFS_ACCESS_KEY RUSTFS_SECRET_KEY
   mc mirror src/magnetdb-attachments dst/magnetdb-attachments
   mc mirror src/magnetdb-parquet     dst/magnetdb-parquet
   ```
4. Flip the environment variables in `.envrc` / Docker secrets.
5. Restart the API and worker containers; run the smoke-test suite.
6. Decommission the MinIO container once all services are verified.

### CORS configuration in RustFS

The curated data bucket must allow cross-origin `GET` requests so that the frontend can fetch
Parquet files via pre-signed URLs. Set the following CORS rule on the bucket (equivalent to the
current MinIO policy):

```json
{
  "CORSRules": [{
    "AllowedOrigins": ["https://magnetdb.lncmi.cnrs.fr", "https://magnetdb-dev.local"],
    "AllowedMethods": ["GET"],
    "AllowedHeaders": ["*"],
    "ExposeHeaders": ["Content-Length", "Content-Range"],
    "MaxAgeSeconds": 3600
  }]
}
```

`Content-Range` must be exposed because HTTP range requests are used by client-side Parquet
readers for columnar projection (reading only the columns the user selected without downloading
the full file).

---

## 2. Parquet in the data architecture

### Layer mapping

| DMP label | Format | Location | Description |
|-----------|--------|----------|-------------|
| D1 | Native MCS binary / text | NAS (sshfs, LNCMI-internal only) | Raw acquisition files — immutable after capture |
| D2 | **Apache Parquet** | **RustFS S3** | Curated, full-resolution — the canonical processed layer |
| D3 | PostgreSQL JSONB + tiny Parquet | RustFS S3 + PostgreSQL | Derived statistics; stitched trend series (one point per record) |

### Record model redesign

The `Record` model (or its successor `Experiment`) carries:

```
sources     : list of raw filenames / NAS paths   → D1 references
curated     : list of StorageAttachment FKs        → D2 Parquet files in RustFS
```

One curated Parquet per `(source_type, group)` pair:
- Pupitre → one file (single group)
- PigBrother (TDMS) → one file per TDMS group
- Hybrid → one file per stream identifier

The S3 key convention for curated files:

```
curated/{housing}/{record_id}/{source_type}-{group_or_stream}.parquet
```

This key is derivable from the Parquet file-level metadata (`magnetrun.housing`,
`magnetrun.source_type`, `magnetrun.group`) enabling orphan recovery without a DB query.

### Derived columns (hoop stress, etc.)

Physics-computed columns (hoop stress per part per timestep via MagnetTools) do not exist in the
raw data and are expensive to recompute. They are stored as a separate derived Parquet, also in
RustFS, referenced from the redesigned Record / a `DerivedTimeSeries` attachment:

```
derived/{housing}/{record_id}/{magnet_id}-computed.parquet
```

These derived Parquet files follow the same `python_magnetrun` metadata schema (field-level
`magnetrun.category`, `magnetrun.unit`, etc.) so they are self-describing.

### Downsampling policy

**Downsampling (LTTB) is applied at display time only. No pre-stored downsampled files.**

Rationale:
- D2 files at typical Pupitre 1 Hz / 60 min are 200 KB–2 MB — small enough that on-the-fly
  LTTB from the full-res Parquet is fast (pyarrow columnar read + in-memory LTTB).
- Pre-storing downsampled artifacts adds storage management overhead (invalidation on reprocess,
  multiple resolution tiers) for no current gain.
- The API contract is already forward-compatible: if a future profiling run shows that on-the-fly
  LTTB on large PigBrother kHz records is too slow, the backend can transparently switch to
  serving a pre-stored downsampled Parquet without any frontend or API signature change.

The `max_points` query parameter on the data endpoint acts as the single control knob:

```
GET /api/records/{id}/timeseries/data?columns=B,t&max_points=1000&t_min=0&t_max=600
```

- `max_points` absent or 0 → return full-resolution data (for export / CEMOSIS notebooks)
- `max_points` set → apply LTTB server-side before returning JSON

---

## 3. Parquet display in the JS frontend

The plotly.js and chart.js libraries used in the frontend consume JSON arrays. Neither reads
Parquet natively. An intermediary layer is always needed: either the backend converts Parquet →
JSON (server-side), or a JS library does it in the browser (client-side).

### Option A — Server-side (recommended for initial implementation)

```
frontend  → GET /api/records/{id}/timeseries/data?columns=B,t&max_points=1000
backend   → opens D2 Parquet from RustFS (pyarrow, columnar projection)
          → applies LTTB if max_points set
          → returns JSON
frontend  → plotly.js / chart.js (unchanged)
```

**Pros**: zero frontend change; works immediately in both Vue 3 and React paths.  
**Cons**: server CPU and memory for every visualization request.

This is the right choice for Track D Phase D2 — it replaces the current `/visualize` endpoint
with no frontend migration cost.

### Option B — Client-side with pre-signed URL (recommended for the new TimeseriesViewer component)

```
frontend  → GET /api/records/{id}/timeseries/presigned-url
backend   → generates pre-signed RustFS URL (boto3, unchanged from MinIO)
          → returns { url, columns_catalog, started_at, ... }
frontend  → hyparquet.parquetRead(url, { columns: ['B', 't'] })
          → applies LTTB in JS if needed
          → plotly.js / chart.js (unchanged)
```

**Pros**:
- Zero server load for visualization after the pre-signed URL is issued.
- Columnar projection via HTTP range requests: only the requested columns are downloaded,
  not the full file. Critical for wide PigBrother files.
- The **same pre-signed URL** can be handed to CEMOSIS researchers for direct use in
  Python notebooks (`pd.read_parquet(url)` or `pyarrow.parquet.read_table(url)`).
- Works in any browser without a backend change when columns or time range change.

**Cons**: requires CORS configuration on the RustFS bucket (see Section 1).

**Library**: [`hyparquet`](https://github.com/hyparam/hyparquet) — pure JS, no WebAssembly,
~10 KB, supports HTTP range requests and async column projection. Suitable for browser use.
No additional bundler configuration needed.

```js
import { parquetRead, parquetMetadata } from 'hyparquet'

// fetch metadata to get column catalog (cheap — reads only the Parquet footer)
const meta = await parquetMetadata(presignedUrl)

// read only the columns needed for display
await parquetRead({
  url: presignedUrl,
  columns: ['t', 'B'],
  onComplete: (rows) => {
    // rows is an array of objects [{ t: 0.0, B: 0.0 }, ...]
    // apply LTTB here if needed, then feed to plotly.js
  }
})
```

### Option C — DuckDB-WASM (future, interactive exploration)

[DuckDB-WASM](https://duckdb.org/docs/api/wasm/overview.html) can execute SQL against a Parquet
file via HTTPS URL, including pre-signed S3 URLs, with columnar projection and predicate
pushdown running in the browser via WebAssembly. Suitable for a future interactive query panel.
Not needed for the standard timeseries viewer.

```js
import * as duckdb from '@duckdb/duckdb-wasm'
// SELECT t, B FROM read_parquet('presigned-url') WHERE t BETWEEN 100 AND 600
```

### Recommended rollout

| Phase | Approach | Rationale |
|-------|----------|-----------|
| Track D Phase D2 (short term) | Option A (server-side) | Drop-in replacement for `/visualize`; no frontend change |
| New `TimeseriesViewer` component (Vue 3 E-A4 / React E-B3) | Option B (`hyparquet` + pre-signed URL) | Columnar projection; same URL usable in CEMOSIS notebooks |
| Future interactive exploration panel | Option C (DuckDB-WASM) | Only if SQL-style querying is needed |

---

## 4. Impact on Track D Phase D2 scope

The combination of (a) downsampling at display time only and (b) curated refs living directly on
`Record` rather than in a separate `ProcessedTimeSeries` model simplifies Phase D2:

| Sub-phase | Original scope | Revised scope |
|-----------|----------------|---------------|
| D2.1 ProcessedTimeSeries model | Full model (scope, origin, columns catalog, Parquet FK) | **Drops** — curated ref lives on `Record.curated` |
| D2.2 Parquet infrastructure | `store_as_parquet` helper + `read_parquet_columns` + LTTB storage | `read_parquet_columns` (pyarrow) + LTTB at query time; write via `python_magnetrun.saveParquet()` |
| D2.3 Raw ETL | parse → clean → write Parquet → create ProcessedTimeSeries row | parse → `mdata.saveParquet()` → `Record.curated.add(attachment)` |
| D2.4 Derived ETL | hoop stress → separate Parquet per scope | Unchanged — derived columns still worth pre-computing |
| D2.5 API endpoints | catalog endpoints + data endpoint | Data endpoint only; catalog is `Record.curated` list via existing Record show endpoint |
| D2.6 Backfill + validation | management command + deprecate `/visualize` | Unchanged |

**Revised D2 duration estimate**: 3–4 weeks (down from 5–6 weeks).

### Forward-compatibility note

When (if) pre-stored downsampled Parquet becomes worth it:
- Add a `downsampled_attachments` field to Record (or a small `DownsampledCache` model).
- The data endpoint checks for a cached artifact before running LTTB.
- No API signature change, no frontend change.
