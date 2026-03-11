# Phase 3: Cumulative Stats & Lifetime Views

## Goal

Aggregate per-experiment statistics into lifetime summaries per site/magnet/part.
Provide trend endpoints returning ordered per-experiment stats over time for plotting.
Build stitched time series for long-term drift analysis.

**Duration**: 3–4 weeks
**Dependencies**: Phase 1 (ExperimentStats populated)
**Delivers**: CumulativeStats populated, history/trend API endpoints, stitched time series

> **Migration note from original design**: Originally written against `Record` and
> `RecordStats`. Updated to target `Experiment` and `ExperimentStats`. The aggregation
> math is unchanged. All ORM filter traversals, related field names, and API serializer
> fields have been updated:
>
> - `RecordStats.objects.filter(record__site_id=...)` →
>   `ExperimentStats.objects.filter(experiment__site_id=...)`
> - `s.record_id` / `s.record.name` → `s.experiment_id` / `s.experiment.name`
> - `records_count` field on `CumulativeStats` → `experiments_count`
>   (rename in migration or document as semantic alias)
>
> The stitched series builder is also updated: it now sources its data from
> `ExperimentStats` and links the resulting `ProcessedTimeSeries` to
> `source_curated_data` (M2M, added in Phase 2) instead of `record`.

---

## Prerequisites Checklist

- [ ] Phase 1 complete: ExperimentStats exist for all experiments at all scope levels
- [ ] Phase 2 at least partially done (ProcessedTimeSeries raw exist) — helpful for
      stitched series but not strictly required

---

## Week 1: Aggregation Service

### 1.1 Cumulative stats computation

**File: `python_magnetdb/actions/compute_cumulative_stats.py`**

```python
"""
Aggregate ExperimentStats into CumulativeStats for entity lifetimes.

Supports two modes:
- Full recompute: query all ExperimentStats, aggregate from scratch
- Incremental update: add a new experiment's contribution (triggered by ingest)
"""

import numpy as np
from python_magnetdb.models import ExperimentStats, CumulativeStats


def aggregate_field_stats(all_values: list[dict]) -> dict:
    """Aggregate a list of per-experiment field stats into a cumulative summary."""
    if not all_values:
        return {}
    maxes = [v['max'] for v in all_values if 'max' in v and v['max'] is not None]
    means = [v['mean'] for v in all_values if 'mean' in v and v['mean'] is not None]
    result = {'num_experiments': len(all_values)}
    if maxes:
        result['global_max'] = float(max(maxes))
        result['global_max_experiment_index'] = int(np.argmax(maxes))
    if means:
        result['lifetime_mean'] = float(np.mean(means))
        result['lifetime_std'] = float(np.std(means))
    if 'unit' in all_values[0]:
        result['unit'] = all_values[0]['unit']
    return result


def compute_cumulative_for_site(site_id: int, category: str = 'raw'):
    """Full recompute of CumulativeStats for a site."""
    stats = ExperimentStats.objects.filter(
        experiment__site_id=site_id,
        magnet__isnull=True,
        part__isnull=True,
        category=category,
    ).order_by('started_at')

    if not stats.exists():
        return None

    all_data = list(stats.values_list('data', flat=True))
    durations = list(stats.values_list('duration_seconds', flat=True))
    start_dates = list(stats.values_list('started_at', flat=True))
    end_dates = list(stats.values_list('ended_at', flat=True))

    cumulative_data = {}
    for key in (all_data[0].keys() if all_data else []):
        values = [d.get(key) for d in all_data if key in d]
        if values and isinstance(values[0], dict) and 'max' in values[0]:
            cumulative_data[key] = aggregate_field_stats(values)

    valid_durations = [d for d in durations if d is not None]
    valid_starts = [d for d in start_dates if d is not None]
    valid_ends = [d for d in end_dates if d is not None]

    obj, _ = CumulativeStats.objects.update_or_create(
        site_id=site_id, magnet=None, part=None, category=category,
        defaults={
            'data': cumulative_data,
            'experiments_count': len(all_data),
            'total_operating_seconds': sum(valid_durations) if valid_durations else 0,
            'time_range_start': min(valid_starts) if valid_starts else None,
            'time_range_end': max(valid_ends) if valid_ends else None,
        }
    )
    return obj


def compute_cumulative_for_magnet(magnet_id: int, category: str = 'raw'):
    """Full recompute of CumulativeStats for a magnet."""
    stats = ExperimentStats.objects.filter(
        magnet_id=magnet_id,
        part__isnull=True,
        category=category,
    ).order_by('started_at')

    if not stats.exists():
        return None

    all_data = list(stats.values_list('data', flat=True))
    durations = list(stats.values_list('duration_seconds', flat=True))
    start_dates = list(stats.values_list('started_at', flat=True))
    end_dates = list(stats.values_list('ended_at', flat=True))

    cumulative_data = {}
    for key in (all_data[0].keys() if all_data else []):
        values = [d.get(key) for d in all_data if key in d]
        if values and isinstance(values[0], dict) and 'max' in values[0]:
            cumulative_data[key] = aggregate_field_stats(values)

    valid_durations = [d for d in durations if d is not None]
    valid_starts = [d for d in start_dates if d is not None]
    valid_ends = [d for d in end_dates if d is not None]

    obj, _ = CumulativeStats.objects.update_or_create(
        site=None, magnet_id=magnet_id, part=None, category=category,
        defaults={
            'data': cumulative_data,
            'experiments_count': len(all_data),
            'total_operating_seconds': sum(valid_durations) if valid_durations else 0,
            'time_range_start': min(valid_starts) if valid_starts else None,
            'time_range_end': max(valid_ends) if valid_ends else None,
        }
    )
    return obj


def compute_cumulative_for_part(part_id: int, category: str = 'raw'):
    """Full recompute of CumulativeStats for a part.

    A part may have been in multiple magnets across multiple sites.
    This aggregates across all of them.
    """
    stats = ExperimentStats.objects.filter(
        part_id=part_id,
        category=category,
    ).order_by('started_at')

    if not stats.exists():
        return None

    all_data = list(stats.values_list('data', flat=True))
    durations = list(stats.values_list('duration_seconds', flat=True))
    start_dates = list(stats.values_list('started_at', flat=True))
    end_dates = list(stats.values_list('ended_at', flat=True))
    magnet_ids = list(stats.values_list('magnet_id', flat=True).distinct())

    cumulative_data = {}
    for key in (all_data[0].keys() if all_data else []):
        values = [d.get(key) for d in all_data if key in d]
        if values and isinstance(values[0], dict) and 'max' in values[0]:
            cumulative_data[key] = aggregate_field_stats(values)

    from python_magnetdb.models.magnet import Magnet
    magnet_names = list(
        Magnet.objects.filter(id__in=magnet_ids).values_list('name', flat=True)
    )
    cumulative_data['magnets_served'] = magnet_names

    valid_durations = [d for d in durations if d is not None]
    valid_starts = [d for d in start_dates if d is not None]
    valid_ends = [d for d in end_dates if d is not None]

    obj, _ = CumulativeStats.objects.update_or_create(
        site=None, magnet=None, part_id=part_id, category=category,
        defaults={
            'data': cumulative_data,
            'experiments_count': len(all_data),
            'total_operating_seconds': sum(valid_durations) if valid_durations else 0,
            'time_range_start': min(valid_starts) if valid_starts else None,
            'time_range_end': max(valid_ends) if valid_ends else None,
        }
    )
    return obj


def refresh_all_cumulative_stats(category: str = 'raw'):
    """Recompute CumulativeStats for all entities."""
    from python_magnetdb.models import Site, Magnet, Part
    for site in Site.objects.all():
        compute_cumulative_for_site(site.id, category)
    for magnet in Magnet.objects.all():
        compute_cumulative_for_magnet(magnet.id, category)
    for part in Part.objects.all():
        compute_cumulative_for_part(part.id, category)
```

### 1.2 Celery task for refresh

Add to `python_magnetdb/tasks/compute_stats.py`:

```python
@app.task
def refresh_cumulative_stats_task(
    site_id: int = None,
    magnet_id: int = None,
    part_id: int = None,
):
    """Refresh cumulative stats after a new experiment is processed."""
    from python_magnetdb.actions.compute_cumulative_stats import (
        compute_cumulative_for_site,
        compute_cumulative_for_magnet,
        compute_cumulative_for_part,
    )
    for category in ['raw', 'computed']:
        if site_id:
            compute_cumulative_for_site(site_id, category)
        if magnet_id:
            compute_cumulative_for_magnet(magnet_id, category)
        if part_id:
            compute_cumulative_for_part(part_id, category)
```

### 1.3 CumulativeStats model field update

The `records_count` field on `CumulativeStats` should be renamed (or aliased) to
`experiments_count` to reflect the new terminology. Choose one of:

- **Option A** (clean): Rename field in a migration. Update all references.
- **Option B** (compat): Add a `@property` alias `experiments_count` that returns
  `records_count`, then migrate the field name in a follow-up sprint.

For Phase 3, use Option B to avoid blocking on a database rename:

```python
# In python_magnetdb/models/cumulative_stats.py
@property
def experiments_count(self):
    return self.records_count

@experiments_count.setter
def experiments_count(self, value):
    self.records_count = value
```

---

## Week 2–3: API Endpoints

### 2.1 Summary endpoints

**File: `python_magnetdb/routes/api/cumulative_stats.py`**

```python
"""API endpoints for cumulative (lifetime) statistics."""

from fastapi import APIRouter, Query, Depends

from python_magnetdb.dependencies import get_user, get_user_experiment_queryset
from python_magnetdb.models import CumulativeStats, ExperimentStats

router = APIRouter()


@router.get("/api/sites/{id}/stats")
def site_stats(id: int, user=Depends(get_user('read')), category: str = Query(None)):
    qs = CumulativeStats.objects.filter(
        site_id=id, magnet__isnull=True, part__isnull=True
    )
    if category:
        qs = qs.filter(category=category)
    return {"site_id": id, "stats": [_serialize_cs(cs) for cs in qs]}


@router.get("/api/magnets/{id}/stats")
def magnet_stats(id: int, user=Depends(get_user('read')), category: str = Query(None)):
    qs = CumulativeStats.objects.filter(
        magnet_id=id, site__isnull=True, part__isnull=True
    )
    if category:
        qs = qs.filter(category=category)
    return {"magnet_id": id, "stats": [_serialize_cs(cs) for cs in qs]}


@router.get("/api/parts/{id}/stats")
def part_stats(id: int, user=Depends(get_user('read')), category: str = Query(None)):
    qs = CumulativeStats.objects.filter(
        part_id=id, site__isnull=True, magnet__isnull=True
    )
    if category:
        qs = qs.filter(category=category)
    return {"part_id": id, "stats": [_serialize_cs(cs) for cs in qs]}


@router.get("/api/sites/{id}/stats/history")
def site_stats_history(
    id: int,
    user=Depends(get_user('read')),
    category: str = Query('raw'),
    field: str = Query(None, description="Specific data field, e.g. 'field'"),
):
    """Return per-experiment stats over time for trend visualization."""
    accessible_experiments = get_user_experiment_queryset(user)
    return _build_history(
        ExperimentStats.objects.filter(
            experiment__site_id=id,
            experiment__in=accessible_experiments,
            magnet__isnull=True,
            part__isnull=True,
            category=category,
        ),
        field,
    )


@router.get("/api/magnets/{id}/stats/history")
def magnet_stats_history(
    id: int,
    user=Depends(get_user('read')),
    category: str = Query('raw'),
    field: str = Query(None),
):
    accessible_experiments = get_user_experiment_queryset(user)
    return _build_history(
        ExperimentStats.objects.filter(
            magnet_id=id,
            experiment__in=accessible_experiments,
            part__isnull=True,
            category=category,
        ),
        field,
    )


@router.get("/api/parts/{id}/stats/history")
def part_stats_history(
    id: int,
    user=Depends(get_user('read')),
    category: str = Query('raw'),
    field: str = Query(None),
):
    accessible_experiments = get_user_experiment_queryset(user)
    return _build_history(
        ExperimentStats.objects.filter(
            part_id=id,
            experiment__in=accessible_experiments,
            category=category,
        ),
        field,
    )


def _build_history(qs, field: str = None) -> dict:
    """Build a time-ordered series from ExperimentStats for trend charts."""
    qs = qs.select_related('experiment').order_by('started_at')
    points = []
    for s in qs:
        point = {
            "experiment_id": s.experiment_id,
            "experiment_name": s.experiment.name,
            "started_at": s.started_at.isoformat() if s.started_at else None,
            "duration_seconds": s.duration_seconds,
        }
        if field and field in s.data:
            point["value"] = s.data[field]
        else:
            point["data"] = s.data
        points.append(point)
    return {"history": points, "count": len(points)}


def _serialize_cs(cs: CumulativeStats) -> dict:
    return {
        "id": cs.id,
        "category": cs.category,
        "data": cs.data,
        "experiments_count": cs.experiments_count,
        "total_operating_seconds": cs.total_operating_seconds,
        "total_operating_hours": (
            cs.total_operating_seconds / 3600
            if cs.total_operating_seconds else None
        ),
        "time_range_start": (
            cs.time_range_start.isoformat() if cs.time_range_start else None
        ),
        "time_range_end": (
            cs.time_range_end.isoformat() if cs.time_range_end else None
        ),
        "computed_at": cs.computed_at.isoformat(),
        "version": cs.version,
    }
```

---

## Week 3–4: Stitched Series and Auto-Refresh

### 3.1 Stitched time series builder

**File: `python_magnetdb/actions/build_stitched_series.py`**

```python
"""Build stitched (cross-experiment) time series from ExperimentStats."""

import pandas as pd
from python_magnetdb.models import ExperimentStats, ProcessedTimeSeries
from python_magnetdb.actions.parquet_helpers import store_dataframe_as_parquet


def build_stitched_series(
    entity_type: str,
    entity_id: int,
    field: str,
    category: str = 'raw',
) -> ProcessedTimeSeries:
    """Build a lifetime series from ExperimentStats: one point per experiment.

    Args:
        entity_type: 'site', 'magnet', or 'part'
        entity_id: ID of the entity
        field: Data field to extract (e.g., 'field', 'hoop_stress_at_max_current')
        category: 'raw' or 'computed'

    Returns:
        ProcessedTimeSeries of origin='stitched', or None if no data.
    """
    if entity_type == 'site':
        qs = ExperimentStats.objects.filter(
            experiment__site_id=entity_id,
            magnet__isnull=True,
            part__isnull=True,
            category=category,
        )
    elif entity_type == 'magnet':
        qs = ExperimentStats.objects.filter(
            magnet_id=entity_id,
            part__isnull=True,
            category=category,
        )
    elif entity_type == 'part':
        qs = ExperimentStats.objects.filter(
            part_id=entity_id,
            category=category,
        )
    else:
        raise ValueError(f"Unknown entity_type: {entity_type}")

    stats = qs.select_related('experiment').order_by('started_at')
    if not stats.exists():
        return None

    rows = []
    curated_data_ids = set()

    for s in stats:
        value_data = s.data.get(field, {})
        row = {
            'timestamp': s.started_at,
            'experiment_id': s.experiment_id,
            'experiment_name': s.experiment.name,
            'duration_seconds': s.duration_seconds,
        }
        if isinstance(value_data, dict):
            for k, v in value_data.items():
                if isinstance(v, (int, float)):
                    row[f'{field}_{k}'] = v
        elif isinstance(value_data, (int, float)):
            row[field] = value_data
        rows.append(row)

        # Collect all CuratedData IDs contributing to this stitched series
        experiment = s.experiment
        for rel in ('pupitre_data', 'pigbrother_data', 'hybrid_data'):
            for sub in getattr(experiment, rel).all():
                curated_data_ids.update(
                    sub.curated_data.values_list('id', flat=True)
                )

    df = pd.DataFrame(rows)
    if df.empty:
        return None

    parquet_att = store_dataframe_as_parquet(
        df,
        f"stitched_{entity_type}_{entity_id}_{field}_{category}.parquet"
    )
    catalog = {
        col: {'dtype': str(df[col].dtype), 'role': 'stitched'}
        for col in df.columns
    }

    fk_kwargs = {
        'site_id': entity_id if entity_type == 'site' else None,
        'magnet_id': entity_id if entity_type == 'magnet' else None,
        'part_id': entity_id if entity_type == 'part' else None,
    }

    ts, _ = ProcessedTimeSeries.objects.update_or_create(
        scope=entity_type,
        origin='stitched',
        processing_params={'field': field, 'category': category},
        **{k: v for k, v in fk_kwargs.items() if v is not None},
        defaults={
            'attachment': parquet_att,
            'columns': catalog,
            'num_points': len(df),
            'started_at': df['timestamp'].iloc[0] if 'timestamp' in df.columns else None,
            'ended_at': df['timestamp'].iloc[-1] if 'timestamp' in df.columns else None,
        }
    )

    # Link contributing CuratedData (Phase 2 M2M field)
    from python_magnetdb.models.curated_data import CuratedData
    if curated_data_ids:
        ts.source_curated_data.set(
            CuratedData.objects.filter(id__in=curated_data_ids)
        )

    return ts
```

### 3.2 Wire auto-refresh into experiment ingest

When a new experiment's stats are computed, refresh the relevant cumulative stats:

```python
# In the ingest chain (used by Phase 4, but wire the logic now)
from celery import chain

def trigger_full_stats_pipeline(experiment_id: int, site_id: int):
    """Trigger the complete stats pipeline for a new experiment."""
    chain(
        compute_experiment_raw_stats_task.s(experiment_id),
        compute_experiment_computed_stats_task.si(experiment_id),
        refresh_cumulative_stats_task.si(site_id=site_id),
    ).apply_async()
```

---

## Verification Checklist

- [ ] CumulativeStats computed for all sites, magnets, and parts
- [ ] `GET /api/sites/{id}/stats` returns cumulative data with operating hours
- [ ] `GET /api/parts/{id}/stats` spans multiple magnets if applicable
- [ ] `GET /api/parts/{id}/stats/history` returns chronological per-experiment stats
- [ ] History endpoint uses `experiment_id` / `experiment_name` (not `record_id`)
- [ ] History respects `get_user_experiment_queryset()` scoping
- [ ] Stitched series created as ProcessedTimeSeries with origin='stitched'
- [ ] Stitched series has `source_curated_data` M2M populated
- [ ] Auto-refresh chain works: new ExperimentStats triggers CumulativeStats update
- [ ] Backfill command recomputes all cumulative stats
