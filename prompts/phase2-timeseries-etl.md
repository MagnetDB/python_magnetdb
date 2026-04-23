# Phase 2: Pre-Processed Time Series / ETL Pipeline

## Goal

Replace the on-the-fly `/visualize` endpoint with pre-computed, Parquet-stored time
series. Support columnar projection, efficient LTTB downsampling, and derived columns
(hoop stress time series). Expose a catalog + data API for the frontend.

**Duration**: 5–6 weeks
**Dependencies**: Phase 1 (parse_experiment infrastructure, ExperimentStats computed)
**Delivers**: ProcessedTimeSeries populated, catalog + data API, deprecated `/visualize`

> **Migration notes from original design**:
>
> 1. **Raw ETL simplified for Experiment-sourced data**: `CuratedData` (created at
>    ingest time by the service account) is already a cleaned S3-backed file. For
>    experiments that have a `CuratedData` row, the raw ETL step links the existing
>    attachment into `ProcessedTimeSeries` rather than re-parsing from sshfs.
>
> 2. **`ProcessedTimeSeries.curated_data` FK lands here**: The Sprint 0 deferred
>    section planned to retarget `ProcessedTimeSeries` from `Record` to `CuratedData`.
>    Since Phase 2 is when new `ProcessedTimeSeries` rows are first created for
>    Experiment-sourced data, this is the right phase to add that FK. The existing
>    `record` FK is kept for legacy rows and streaming windows (Phase 5).

---

## Prerequisites Checklist

- [ ] Phase 1 complete: ExperimentStats exist for all experiments
- [ ] `pyarrow` in dependencies (`pyarrow = ">=17.0.0,<18.0.0"` in `pyproject.toml`)
- [ ] MinIO storage working
- [ ] At least one `CuratedData` row exists for testing the direct-link path
- [ ] MagnetTools bridge validated (for derived time series)

---

## Week 0 (pre-work): Add `curated_data` FK to ProcessedTimeSeries

**File: `python_magnetdb/models/processed_timeseries.py`** — add after existing fields:

```python
    # Phase 2 addition: source FK for Experiment-path rows.
    # Exactly one of `record` or `curated_data` is set per row.
    # `record` is kept for legacy rows and streaming windows (Phase 5).
    curated_data = models.ForeignKey(
        'CuratedData', on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='timeseries_set',
        help_text=(
            "For Experiment-sourced time series: the CuratedData this was derived from. "
            "Null for legacy Record-sourced rows and stream windows."
        )
    )
```

Update `Meta.indexes`:

```python
    class Meta:
        db_table = 'processed_timeseries'
        indexes = [
            models.Index(fields=['record', 'scope']),
            models.Index(fields=['curated_data']),          # new
            models.Index(fields=['site', 'origin']),
            models.Index(fields=['magnet', 'origin']),
            models.Index(fields=['part', 'origin']),
        ]
```

```bash
poetry run python manage.py makemigrations
poetry run python manage.py migrate
```

> **Future step**: once all `ProcessedTimeSeries` rows sourced from `Record` have been
> retired, the `record` FK can be dropped. For stitched series spanning multiple
> `CuratedData` rows, a `source_curated_data = ManyToManyField(CuratedData)` will be
> needed (Phase 3+).

---

## Week 1: Parquet Infrastructure

### 1.1 Parquet storage helpers

**File: `python_magnetdb/actions/parquet_helpers.py`**

Unchanged from original design.

```python
"""Helpers for storing and reading Parquet files via StorageAttachment."""

import io
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from python_magnetdb.models import StorageAttachment


def store_dataframe_as_parquet(df: pd.DataFrame, name: str) -> StorageAttachment:
    buf = io.BytesIO()
    pq.write_table(pa.Table.from_pandas(df), buf, compression='snappy')
    buf.seek(0)
    return StorageAttachment.raw_upload_bytes(name, 'application/octet-stream', buf.getvalue())


def read_parquet_columns(
    attachment: StorageAttachment,
    columns: list = None,
    t_min: float = None,
    t_max: float = None,
) -> pd.DataFrame:
    data = attachment.download()
    df = pd.read_parquet(data, columns=list(set(['t'] + columns)) if columns else None)
    if t_min is not None and 't' in df.columns:
        df = df[df['t'] >= t_min]
    if t_max is not None and 't' in df.columns:
        df = df[df['t'] <= t_max]
    return df


def build_column_catalog(df: pd.DataFrame, column_info: dict = None) -> dict:
    from python_magnetdb.utils.record_visualization import columns as default_info
    info = column_info or default_info
    return {
        col: {'unit': info.get(col, ''), 'dtype': str(df[col].dtype),
              'role': 'index' if col == 't' else 'raw'}
        for col in df.columns
    }
```

Add `raw_upload_bytes` to `StorageAttachment` if not already present:

```python
@classmethod
def raw_upload_bytes(cls, filename, content_type, data: bytes):
    import tempfile, os
    with tempfile.NamedTemporaryFile(delete=False, suffix=filename) as f:
        f.write(data)
        temp_path = f.name
    try:
        return cls.raw_upload(filename, content_type, temp_path)
    finally:
        os.unlink(temp_path)
```

### 1.2 LTTB downsampling

**File: `python_magnetdb/actions/downsample.py`** — unchanged from original design.

```python
"""LTTB (Largest-Triangle-Three-Buckets) downsampling."""

import numpy as np
import pandas as pd


def lttb_downsample(t: np.ndarray, values: np.ndarray, target_points: int):
    n = len(t)
    if target_points >= n or target_points < 3:
        return t.copy(), values.copy()
    out_t, out_v = np.empty(target_points), np.empty(target_points)
    out_t[0], out_v[0] = t[0], values[0]
    out_t[-1], out_v[-1] = t[-1], values[-1]
    bucket_size = (n - 2) / (target_points - 2)
    prev_selected = 0
    for bi in range(1, target_points - 1):
        bs = int((bi - 1) * bucket_size) + 1
        be = min(int(bi * bucket_size) + 1, n)
        ns = int(bi * bucket_size) + 1
        ne = min(int((bi + 1) * bucket_size) + 1, n)
        avg_t, avg_v = np.mean(t[ns:ne]), np.mean(values[ns:ne])
        max_area, max_idx = -1, bs
        for i in range(bs, be):
            area = abs(
                (t[prev_selected] - avg_t) * (values[i] - out_v[bi - 1]) -
                (t[prev_selected] - t[i]) * (avg_v - out_v[bi - 1])
            ) * 0.5
            if area > max_area:
                max_area, max_idx = area, i
        out_t[bi], out_v[bi] = t[max_idx], values[max_idx]
        prev_selected = max_idx
    return out_t, out_v


def downsample_dataframe(df, time_column, columns, target_points):
    if len(df) <= target_points:
        return df[[time_column] + columns].copy()
    t = df[time_column].values
    all_indices = {0, len(df) - 1}
    for col in columns:
        t_down, _ = lttb_downsample(t, df[col].values, target_points)
        for td in t_down:
            all_indices.add(min(np.searchsorted(t, td), len(t) - 1))
    return df.iloc[sorted(all_indices)][[time_column] + columns].reset_index(drop=True)
```

---

## Week 2–3: Raw and Derived ETL Pipelines

### 2.1 Raw ETL task

**File: `python_magnetdb/tasks/process_timeseries.py`**

Two code paths:
- **CuratedData path** (Experiment-sourced): link existing `CuratedData.attachment` directly, no re-parse.
- **sshfs fallback**: when no `CuratedData` row exists yet, parse from sshfs via `parse_experiment()`.
- **Legacy path**: `Record`-sourced rows parsed from `record.attachment` as before.

```python
"""Celery tasks for time series ETL."""

from django.db import models as db_models
from python_magnetdb.worker import app
from python_magnetdb.models import ProcessedTimeSeries
from python_magnetdb.actions.parquet_helpers import (
    store_dataframe_as_parquet, build_column_catalog, read_parquet_columns,
)


def _sampling_period(df):
    import pandas as pd
    if 't' in df.columns and len(df) > 1:
        return float(df['t'].diff().median())
    return None


@app.task(bind=True, max_retries=3)
def process_experiment_raw_timeseries(self, experiment_id: int):
    """Create a ProcessedTimeSeries for an Experiment.

    Prefers the CuratedData path (no re-parse). Falls back to sshfs if
    CuratedData is not yet available.
    """
    try:
        from python_magnetdb.models.experiment import Experiment
        from python_magnetdb.models.curated_data import CuratedData, CuratedDataFormat

        experiment = Experiment.objects.select_related('site').get(id=experiment_id)

        # Idempotency check
        already = ProcessedTimeSeries.objects.filter(
            db_models.Q(curated_data__pupitre_data__experiment=experiment) |
            db_models.Q(curated_data__pigbrother_data__experiment=experiment) |
            db_models.Q(curated_data__hybrid_data__experiment=experiment),
            scope='site', origin='raw', version='v1',
        ).exists()
        if already:
            return {'status': 'skipped', 'experiment_id': experiment_id}

        # CuratedData path (preferred)
        curated = CuratedData.objects.filter(
            db_models.Q(pupitre_data__experiment=experiment) |
            db_models.Q(pigbrother_data__experiment=experiment) |
            db_models.Q(hybrid_data__experiment=experiment),
            format__in=[CuratedDataFormat.PARQUET, CuratedDataFormat.CSV],
        ).select_related('attachment').first()

        if curated is not None:
            df = read_parquet_columns(curated.attachment)
            ProcessedTimeSeries.objects.create(
                curated_data=curated,
                site=experiment.site,
                scope='site',
                origin='raw',
                attachment=curated.attachment,   # reuse, no copy needed
                columns=build_column_catalog(df),
                started_at=experiment.started_at,
                ended_at=experiment.ended_at,
                num_points=len(df),
                sampling_period_seconds=_sampling_period(df),
                parser_class='curated_data',
            )
            return {'status': 'success', 'path': 'curated_data',
                    'experiment_id': experiment_id, 'num_points': len(df)}

        # sshfs fallback
        from python_magnetdb.actions.parse_experiment import parse_experiment, extract_time_bounds
        df = parse_experiment(experiment)
        if df is None:
            return {'status': 'no_data', 'experiment_id': experiment_id}

        att = store_dataframe_as_parquet(df, f"experiment_{experiment_id}_raw.parquet")
        time_bounds = extract_time_bounds(df)
        ProcessedTimeSeries.objects.create(
            site=experiment.site,
            scope='site', origin='raw',
            attachment=att,
            columns=build_column_catalog(df),
            started_at=time_bounds.get('started_at'),
            ended_at=time_bounds.get('ended_at'),
            num_points=len(df),
            sampling_period_seconds=_sampling_period(df),
            parser_class='sshfs_fallback',
        )
        return {'status': 'success', 'path': 'sshfs_fallback',
                'experiment_id': experiment_id, 'num_points': len(df)}

    except Exception as exc:
        print(f"Error processing raw timeseries for experiment {experiment_id}: {exc}")
        raise self.retry(exc=exc, countdown=60)


@app.task(bind=True, max_retries=3)
def process_record_raw_timeseries(self, record_id: int):
    """Legacy raw ETL for Record-sourced data. Unchanged from original design."""
    try:
        from python_magnetdb.models import Record
        from python_magnetdb.actions.parse_record import parse_record_attachment
        from python_magnetdb.actions.parse_experiment import extract_time_bounds

        record = Record.objects.select_related('site', 'attachment').get(id=record_id)
        if ProcessedTimeSeries.objects.filter(record=record, scope='site', origin='raw', version='v1').exists():
            return {'status': 'skipped', 'record_id': record_id}

        df = parse_record_attachment(record.attachment)
        att = store_dataframe_as_parquet(df, f"record_{record_id}_raw.parquet")
        time_bounds = extract_time_bounds(df)
        ProcessedTimeSeries.objects.create(
            record=record, site=record.site,
            scope='site', origin='raw',
            attachment=att,
            columns=build_column_catalog(df),
            started_at=time_bounds.get('started_at'),
            ended_at=time_bounds.get('ended_at'),
            num_points=len(df),
            sampling_period_seconds=_sampling_period(df),
            parser_class='legacy_attachment',
        )
        return {'status': 'success', 'record_id': record_id, 'num_points': len(df)}

    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


@app.task(bind=True, max_retries=2)
def process_experiment_derived_timeseries(self, experiment_id: int):
    """Compute derived time series (hoop stress) for an Experiment."""
    try:
        from python_magnetdb.models.experiment import Experiment
        from python_magnetdb.tasks.compute_stats import get_active_magnets, build_magnet_config
        from python_magnetdb.actions.compute_experiment_computed_stats import compute_hoop_at_currents
        from python_magnetdb.actions.object_geometries import get_magnet_data
        import magnettools.magnettools as mt
        import pandas as pd
        import numpy as np

        experiment = Experiment.objects.select_related('site').get(id=experiment_id)

        raw_ts = ProcessedTimeSeries.objects.filter(
            db_models.Q(curated_data__pupitre_data__experiment=experiment) |
            db_models.Q(curated_data__pigbrother_data__experiment=experiment) |
            db_models.Q(curated_data__hybrid_data__experiment=experiment),
            origin='raw',
        ).first()
        if not raw_ts:
            return {'status': 'skipped', 'reason': 'no raw timeseries'}

        df_raw = read_parquet_columns(raw_ts.attachment)

        for sm in get_active_magnets(experiment.site, experiment.started_at):
            magnet = sm.magnet
            magnet_config = build_magnet_config(magnet)
            try:
                mt_data = get_magnet_data(magnet.id)
            except Exception as e:
                print(f"Skipping derived TS for magnet {magnet.name}: {e}")
                continue

            (Tubes, Helices, OHelices, BMagnets, UMagnets, Shims) = mt_data
            icurrents = mt.get_currents(Tubes, Helices, BMagnets, UMagnets)
            icoil_cols = [c for c in df_raw.columns if c.startswith('Icoil')]
            if not icoil_cols:
                continue

            sample_indices = np.linspace(0, len(df_raw) - 1, min(100, len(df_raw)), dtype=int)
            results = []
            for idx in sample_indices:
                row = df_raw.iloc[idx]
                vcurrents = list(icurrents)
                vcurrents[0] = float(row[icoil_cols[0]])
                hoop = compute_hoop_at_currents(mt_data, vcurrents)
                result_row = {'t': float(row['t']), 'Bz0': hoop['Bz0']}
                for i, hv in enumerate(hoop['hoop_MPa']):
                    if i < len(magnet_config['parts']):
                        p = magnet_config['parts'][i]
                        result_row[f"hoop_{p['name']}"] = hv
                        rpe = p.get('material', {}).get('rpe')
                        if rpe:
                            result_row[f"ratio_rpe_{p['name']}"] = hv / float(rpe)
                results.append(result_row)

            df_d = pd.DataFrame(results)
            att = store_dataframe_as_parquet(df_d, f"experiment_{experiment_id}_magnet_{magnet.id}_derived.parquet")
            catalog = {
                col: {'unit': 'T' if col == 'Bz0' else ('MPa' if 'hoop' in col else ''),
                      'dtype': str(df_d[col].dtype),
                      'role': 'index' if col == 't' else 'derived'}
                for col in df_d.columns
            }
            ProcessedTimeSeries.objects.create(
                site=experiment.site, magnet=magnet,
                scope='magnet', origin='derived',
                attachment=att, columns=catalog,
                started_at=experiment.started_at,
                ended_at=experiment.ended_at,
                num_points=len(df_d),
            )

        return {'status': 'success', 'experiment_id': experiment_id}

    except Exception as exc:
        raise self.retry(exc=exc, countdown=120)
```

---

## Week 4–5: Catalog and Data API

### 3.1 Time series API endpoints

**File: `python_magnetdb/routes/api/timeseries.py`**

```python
"""API endpoints for pre-processed time series."""

from django.db import models as db_models
from fastapi import APIRouter, Query, Depends, HTTPException
from python_magnetdb.dependencies import get_user
from python_magnetdb.models import ProcessedTimeSeries
from python_magnetdb.actions.parquet_helpers import read_parquet_columns
from python_magnetdb.actions.downsample import downsample_dataframe

router = APIRouter()


@router.get("/api/experiments/{id}/timeseries")
def experiment_timeseries_catalog(id: int, user=Depends(get_user('read'))):
    """List all processed time series for an experiment."""
    from python_magnetdb.models.experiment import Experiment
    try:
        experiment = Experiment.objects.get(id=id)
    except Experiment.DoesNotExist:
        raise HTTPException(status_code=404, detail="Experiment not found")
    series = ProcessedTimeSeries.objects.filter(
        db_models.Q(curated_data__pupitre_data__experiment=experiment) |
        db_models.Q(curated_data__pigbrother_data__experiment=experiment) |
        db_models.Q(curated_data__hybrid_data__experiment=experiment)
    ).distinct()
    return {"experiment_id": id, "timeseries": [_serialize_ts(ts) for ts in series]}


@router.get("/api/records/{id}/timeseries")
def record_timeseries_catalog(id: int, user=Depends(get_user('read'))):
    """List all processed time series for a legacy Record."""
    from python_magnetdb.models import Record
    try:
        Record.objects.get(id=id)
    except Record.DoesNotExist:
        raise HTTPException(status_code=404, detail="Record not found")
    series = ProcessedTimeSeries.objects.filter(record_id=id)
    return {"record_id": id, "timeseries": [_serialize_ts(ts) for ts in series]}


@router.get("/api/sites/{id}/timeseries")
def site_timeseries_catalog(id: int, user=Depends(get_user('read'))):
    return {"site_id": id, "timeseries": [_serialize_ts(ts) for ts in ProcessedTimeSeries.objects.filter(site_id=id)]}


@router.get("/api/magnets/{id}/timeseries")
def magnet_timeseries_catalog(id: int, user=Depends(get_user('read'))):
    return {"magnet_id": id, "timeseries": [_serialize_ts(ts) for ts in ProcessedTimeSeries.objects.filter(magnet_id=id)]}


@router.get("/api/parts/{id}/timeseries")
def part_timeseries_catalog(id: int, user=Depends(get_user('read'))):
    return {"part_id": id, "timeseries": [_serialize_ts(ts) for ts in ProcessedTimeSeries.objects.filter(part_id=id)]}


@router.get("/api/timeseries/{id}/data")
def timeseries_data(
    id: int,
    user=Depends(get_user('read')),
    columns: str = Query(..., description="Comma-separated column names"),
    max_points: int = Query(1000, ge=10, le=10000),
    t_min: float = Query(None),
    t_max: float = Query(None),
):
    """Fetch data points from a processed time series with LTTB downsampling."""
    ts = ProcessedTimeSeries.objects.select_related('attachment').filter(id=id).first()
    if not ts:
        raise HTTPException(status_code=404, detail="Time series not found")

    requested_cols = [c.strip() for c in columns.split(',')]
    invalid = set(requested_cols) - set(ts.columns.keys())
    if invalid:
        raise HTTPException(status_code=400,
            detail=f"Unknown columns: {invalid}. Available: {sorted(ts.columns.keys())}")

    df = read_parquet_columns(ts.attachment, requested_cols, t_min, t_max)
    total_points = len(df)
    if len(df) > max_points and 't' in df.columns:
        df = downsample_dataframe(df, 't', requested_cols, max_points)

    response = {
        "timeseries_id": id,
        "total_points": total_points,
        "returned_points": len(df),
        "downsampled": len(df) < total_points,
    }
    if 't' in df.columns:
        response["t"] = df['t'].tolist()
    response["series"] = {col: df[col].tolist() for col in df.columns if col != 't'}
    return response


def _serialize_ts(ts: ProcessedTimeSeries) -> dict:
    return {
        "id": ts.id,
        "scope": ts.scope,
        "origin": ts.origin,
        "columns": ts.columns,
        "num_points": ts.num_points,
        "started_at": ts.started_at.isoformat() if ts.started_at else None,
        "ended_at": ts.ended_at.isoformat() if ts.ended_at else None,
        "record_id": ts.record_id,
        "curated_data_id": ts.curated_data_id,
        "magnet_id": ts.magnet_id,
        "part_id": ts.part_id,
        "version": ts.version,
    }
```

### 3.2 Deprecate `/visualize`

```python
# In routes/api/records.py, add to the existing visualize endpoint:
response.headers["Deprecation"] = "true"
response.headers["Link"] = '</api/experiments/{id}/timeseries>; rel="successor-version"'
```

---

## Verification Checklist

- [ ] `curated_data` FK added to `ProcessedTimeSeries` and migration applied
- [ ] `process_experiment_raw_timeseries` uses CuratedData path when available
- [ ] `process_experiment_raw_timeseries` falls back to sshfs when no CuratedData present
- [ ] Derived ETL task creates hoop stress time series for each magnet
- [ ] `GET /api/experiments/{id}/timeseries` returns series linked via curated_data
- [ ] `GET /api/records/{id}/timeseries` still works for legacy rows
- [ ] Catalog endpoints return correct column metadata including `curated_data_id`
- [ ] Data endpoint supports column projection, time range filtering, LTTB
- [ ] Backfill command processes all experiments
- [ ] Old `/visualize` still works with deprecation headers
- [ ] Response times: catalog < 50ms, data < 200ms for 1000 points
