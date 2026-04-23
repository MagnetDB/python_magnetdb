# Phase 1: Per-Experiment Statistics (ExperimentStats)

## Goal

For each experiment, compute and store statistical summaries at site, magnet, and part
level — both raw (extracted directly from operational data) and computed (derived via
MagnetTools). These are the atomic building blocks for all downstream analytics.

**Duration**: 4–5 weeks
**Dependencies**: Phase 0 (models must be migrated, CuratedData pipeline operational)
**Delivers**: ExperimentStats populated for all experiments, API endpoints, Celery tasks

> **Migration note from original design**: This phase targets `Experiment` /
> `ExperimentStats` instead of `Record` / `RecordStats`. Raw data is read from sshfs
> paths stored in `PupitreData`, `PigBrotherData`, and `HybridData` sub-models rather
> than from a `StorageAttachment`. The parsing entry point is therefore different, but
> all DataFrame-level computation logic is unchanged.

---

## Prerequisites Checklist

Before starting Phase 1, verify:

- [ ] Phase 0 migration applied: `experiment_stats` table exists and is empty
- [ ] `experiments`, `pupitre_data`, `pigbrother_data`, `hybrid_data` tables exist
- [ ] At least one `Experiment` with at least one sub-model row exists for testing
- [ ] sshfs mount is accessible from the worker container at the expected path
- [ ] `python_magnetrun` can parse files at the sshfs paths
- [ ] `python_magnetsetup.ana.magnet_setup()` works from JSON config + YAML files
- [ ] At least 2 magnet configurations have exported reference JSON configs
- [ ] Coil-to-helix mapping documented for each magnet configuration

---

## Week 1: Raw Stats Computation Service

### 1.1 Create the sshfs parsing entry point

**File: `python_magnetdb/actions/parse_experiment.py`**

This replaces `parse_record_attachment()` from the original design.
Instead of reading from a `StorageAttachment`, it resolves sshfs paths
from the sub-model instances and loads via `python_magnetrun`.

```python
"""
Parse raw experiment data from sshfs paths into a DataFrame.

Each Experiment has one or more sub-model rows (PupitreData, PigBrotherData,
HybridData). Each sub-model stores a base_path + relative file paths.
This module resolves the full paths and delegates to python_magnetrun.
"""

import os
import pandas as pd
from datetime import datetime
from typing import Optional

from python_magnetdb.models.experiment import Experiment
from python_magnetdb.models.pupitre_data import PupitreData
from python_magnetdb.models.pigbrother_data import PigBrotherData
from python_magnetdb.models.hybrid_data import HybridData


def resolve_full_path(base_path: str, relative_path: str) -> str:
    """Resolve a relative sshfs path to an absolute path."""
    return os.path.join(base_path, relative_path)


def parse_pupitre_data(pupitre: PupitreData) -> Optional[pd.DataFrame]:
    """Parse a PupitreData row into a DataFrame using python_magnetrun."""
    if not pupitre.files:
        return None
    for relative_path in pupitre.files:
        full_path = resolve_full_path(pupitre.base_path, relative_path)
        if not os.path.exists(full_path):
            print(f"Warning: sshfs path not found: {full_path}")
            continue
        try:
            return _load_via_magnetrun(full_path)
        except Exception as e:
            print(f"Warning: failed to parse {full_path}: {e}")
    return None


def parse_pigbrother_data(
    pigbrother: PigBrotherData,
    subtype: str = "overview",
) -> Optional[pd.DataFrame]:
    """Parse a PigBrotherData row for a given sub-format.

    Args:
        pigbrother: PigBrotherData instance.
        subtype: One of 'overview', 'archive'. Defaults to 'overview'.
    """
    files = pigbrother.files.get(subtype, [])
    if not files:
        for fallback in PigBrotherData.VALID_SUBTYPES:
            files = pigbrother.files.get(fallback, [])
            if files:
                break
    if not files:
        return None
    for relative_path in files:
        full_path = resolve_full_path(pigbrother.base_path, relative_path)
        if not os.path.exists(full_path):
            print(f"Warning: sshfs path not found: {full_path}")
            continue
        try:
            return _load_via_magnetrun(full_path)
        except Exception as e:
            print(f"Warning: failed to parse {full_path}: {e}")
    return None


def parse_hybrid_data(
    hybrid: HybridData,
    subtype: str = "rms",
) -> Optional[pd.DataFrame]:
    """Parse a HybridData row for a given sub-format.

    Args:
        hybrid: HybridData instance.
        subtype: One of 'rms', '1khz', 'vprocess'. Defaults to 'rms'.
    """
    files = hybrid.files.get(subtype, [])
    if not files:
        for fallback in HybridData.VALID_SUBTYPES:
            files = hybrid.files.get(fallback, [])
            if files:
                break
    if not files:
        return None
    for relative_path in files:
        full_path = resolve_full_path(hybrid.base_path, relative_path)
        if not os.path.exists(full_path):
            print(f"Warning: sshfs path not found: {full_path}")
            continue
        try:
            return _load_via_magnetrun(full_path)
        except Exception as e:
            print(f"Warning: failed to parse {full_path}: {e}")
    return None


def parse_experiment(experiment: Experiment) -> Optional[pd.DataFrame]:
    """Parse an Experiment into a DataFrame.

    Tries sub-models in priority order: PigBrother (overview) → Hybrid (rms)
    → Pupitre. Returns the first successfully parsed DataFrame.

    For stats computation a single representative DataFrame per experiment
    is sufficient. Full multi-source merging is a Phase 2 concern.
    """
    for pb in experiment.pigbrother_data.all():
        df = parse_pigbrother_data(pb, subtype="overview")
        if df is not None:
            return df
    for hy in experiment.hybrid_data.all():
        df = parse_hybrid_data(hy, subtype="rms")
        if df is not None:
            return df
    for pu in experiment.pupitre_data.all():
        df = parse_pupitre_data(pu)
        if df is not None:
            return df
    return None


def _load_via_magnetrun(filepath: str) -> pd.DataFrame:
    """Load a raw data file via python_magnetrun, with inline fallback."""
    try:
        from python_magnetrun.magnetdata import MagnetData
        mdata = MagnetData(filepath)
        df = mdata.getData()
        if df is not None and not df.empty:
            return df
    except (ImportError, Exception):
        pass

    # Fallback: inline CSV/TSV parsing (same logic as legacy /visualize endpoint)
    time_format = "%Y.%m.%d %H:%M:%S"
    data = pd.read_csv(filepath, sep=r'\s+', skiprows=1)
    data = data.loc[:, (data != 0.0).any(axis=0)]
    if 'Date' in data.columns and 'Time' in data.columns:
        t0 = datetime.strptime(
            data['Date'].iloc[0] + " " + data['Time'].iloc[0], time_format
        )
        data["t"] = data.apply(
            lambda row: (datetime.strptime(
                row.Date + " " + row.Time, time_format
            ) - t0).total_seconds(), axis=1
        )
        data["timestamp"] = data.apply(
            lambda row: datetime.strptime(row.Date + " " + row.Time, time_format),
            axis=1
        )
    return data


def extract_time_bounds(df: pd.DataFrame) -> dict:
    """Extract time bounds from a parsed DataFrame."""
    result = {}
    if 'timestamp' in df.columns:
        result['started_at'] = df['timestamp'].iloc[0]
        result['ended_at'] = df['timestamp'].iloc[-1]
    if 't' in df.columns:
        result['duration_seconds'] = float(df['t'].iloc[-1] - df['t'].iloc[0])
    return result
```

### 1.2 Create the computation module

**File: `python_magnetdb/actions/compute_experiment_stats.py`**

All DataFrame-level computation is unchanged from the original design.
Only the module name and docstring are updated.

```python
"""
Compute per-experiment statistics at site, magnet, and part level.

All computation operates on pandas DataFrames and is independent of
how the data was loaded (sshfs, StorageAttachment, stream window, etc.).
"""

import pandas as pd
import numpy as np


def compute_column_stats(series: pd.Series) -> dict:
    """Compute standard statistics for a single column."""
    valid = series.dropna()
    if len(valid) == 0:
        return {"count": 0}
    return {
        "min": float(valid.min()),
        "max": float(valid.max()),
        "mean": float(valid.mean()),
        "std": float(valid.std()),
        "median": float(valid.median()),
        "count": int(len(valid)),
    }


def compute_site_raw_stats(df: pd.DataFrame, column_info: dict) -> dict:
    """Compute site-level raw statistics from a parsed experiment DataFrame."""
    stats = {}

    if 'Field' in df.columns:
        stats['field'] = {**compute_column_stats(df['Field']), 'unit': 'T'}

    for col in ['Pmagnet', 'Ptot']:
        if col in df.columns:
            stats[col.lower()] = {**compute_column_stats(df[col]), 'unit': column_info.get(col, '')}

    temp_cols = [c for c in df.columns if c.startswith('T') and c in column_info]
    if temp_cols:
        stats['temperatures'] = {}
        for col in temp_cols:
            stats['temperatures'][col] = {
                **compute_column_stats(df[col]),
                'unit': column_info.get(col, '°C')
            }
        if 'Tin1' in df.columns and 'Tout' in df.columns:
            delta_t = df['Tout'] - df['Tin1']
            stats['cooling'] = {'delta_T': compute_column_stats(delta_t), 'unit': '°C'}

    pressure_cols = [c for c in df.columns if c.startswith(('HP', 'BP'))]
    if pressure_cols:
        stats['pressures'] = {}
        for col in pressure_cols:
            stats['pressures'][col] = {**compute_column_stats(df[col]), 'unit': column_info.get(col, 'bar')}

    flow_cols = [c for c in df.columns if c.startswith('Flow')]
    if flow_cols:
        stats['flows'] = {}
        for col in flow_cols:
            stats['flows'][col] = {**compute_column_stats(df[col]), 'unit': column_info.get(col, 'l/s')}

    icoil_cols = [c for c in df.columns if c.startswith('Icoil')]
    if icoil_cols:
        stats['currents_summary'] = {
            'active_coils': len(icoil_cols),
            'total_current_max': float(sum(df[c].max() for c in icoil_cols)),
        }

    return stats


def compute_magnet_raw_stats(df: pd.DataFrame, magnet_config: dict, column_info: dict) -> dict:
    """Compute magnet-level raw statistics."""
    stats = {'currents': {}, 'voltages': {}, 'resistance_variations': {}}
    for part in magnet_config.get('parts', []):
        coil_idx = part.get('coil_index')
        if coil_idx is None:
            continue
        for prefix, key, unit in [('Icoil', 'currents', 'A'), ('Ucoil', 'voltages', 'V'), ('DRcoil', 'resistance_variations', '%')]:
            col = f'{prefix}{coil_idx}'
            if col in df.columns:
                stats[key][col] = {**compute_column_stats(df[col]), 'unit': unit, 'part_name': part['name']}
    return stats


def compute_part_raw_stats(df: pd.DataFrame, part_config: dict, column_info: dict) -> dict:
    """Compute part-level raw statistics for a single part."""
    coil_idx = part_config.get('coil_index')
    if coil_idx is None:
        return {}
    stats = {}
    for prefix, key, unit in [('Icoil', 'current', 'A'), ('Ucoil', 'voltage', 'V'), ('DRcoil', 'resistance_variation', '%'), ('Tcal', 'temperature_cal', '°C')]:
        col = f'{prefix}{coil_idx}'
        if col in df.columns:
            stats[key] = {**compute_column_stats(df[col]), 'unit': unit}
    icol, ucol = f'Icoil{coil_idx}', f'Ucoil{coil_idx}'
    if icol in df.columns and ucol in df.columns:
        stats['power'] = {**compute_column_stats(df[icol] * df[ucol]), 'unit': 'W'}
    return stats
```

### 1.3 Wire into Celery tasks

**File: `python_magnetdb/tasks/compute_stats.py`**

```python
"""Celery tasks for computing experiment statistics."""

from python_magnetdb.worker import app
from python_magnetdb.models import ExperimentStats
from python_magnetdb.models.experiment import Experiment
from python_magnetdb.models.site_magnet import SiteMagnet
from python_magnetdb.actions.parse_experiment import parse_experiment, extract_time_bounds
from python_magnetdb.actions.compute_experiment_stats import (
    compute_site_raw_stats, compute_magnet_raw_stats, compute_part_raw_stats,
)
from python_magnetdb.actions.compute_experiment_computed_stats import compute_magnet_computed_stats
from python_magnetdb.utils.record_visualization import columns as column_info


def get_active_magnets(site, experiment_started_at):
    """Get magnets active at the time of the experiment."""
    site_magnets = SiteMagnet.objects.filter(site=site).select_related('magnet')
    active = []
    for sm in site_magnets:
        if sm.commissioned_at and experiment_started_at and sm.commissioned_at > experiment_started_at:
            continue
        if sm.decommissioned_at and experiment_started_at and sm.decommissioned_at < experiment_started_at:
            continue
        active.append(sm)
    return active


def build_magnet_config(magnet):
    """Build a magnet config dict from the Django model, including coil mapping."""
    parts = []
    for idx, mp in enumerate(magnet.magnetpart_set.select_related('part', 'part__material').all()):
        parts.append({
            'name': mp.part.name,
            'type': mp.part.type,
            'coil_index': idx + 1,  # TODO: verify mapping per magnet type
            'material': {
                'rpe': mp.part.material.rpe,
                'young': mp.part.material.young,
                'nuance': mp.part.material.nuance,
            } if mp.part.material else {},
        })
    return {'name': magnet.name, 'type': magnet.type, 'parts': parts}


@app.task(bind=True, max_retries=3)
def compute_experiment_raw_stats_task(self, experiment_id: int):
    """Compute raw statistics for a single experiment at all scope levels.

    Reads raw data from sshfs via parse_experiment(). Retries up to 3 times
    to tolerate transient sshfs mount issues.
    """
    try:
        experiment = Experiment.objects.select_related('site').get(id=experiment_id)
        df = parse_experiment(experiment)
        if df is None:
            print(f"Warning: no parseable data for experiment {experiment_id}")
            return {'status': 'no_data', 'experiment_id': experiment_id}

        # Update time bounds if not set
        time_bounds = extract_time_bounds(df)
        updated_fields = []
        for field in ('started_at', 'ended_at', 'duration_seconds'):
            if getattr(experiment, field) is None and field in time_bounds:
                setattr(experiment, field, time_bounds[field])
                updated_fields.append(field)
        if updated_fields:
            experiment.save(update_fields=updated_fields)

        # Site-level
        ExperimentStats.objects.update_or_create(
            experiment=experiment, magnet=None, part=None, category='raw',
            defaults={
                'data': compute_site_raw_stats(df, column_info),
                'started_at': experiment.started_at,
                'ended_at': experiment.ended_at,
                'duration_seconds': experiment.duration_seconds,
            }
        )

        # Magnet-level and part-level
        for sm in get_active_magnets(experiment.site, experiment.started_at):
            magnet = sm.magnet
            magnet_config = build_magnet_config(magnet)

            ExperimentStats.objects.update_or_create(
                experiment=experiment, magnet=magnet, part=None, category='raw',
                defaults={
                    'data': compute_magnet_raw_stats(df, magnet_config, column_info),
                    'started_at': experiment.started_at,
                    'ended_at': experiment.ended_at,
                    'duration_seconds': experiment.duration_seconds,
                }
            )

            for part_config in magnet_config['parts']:
                from python_magnetdb.models.part import Part
                try:
                    part = Part.objects.get(name=part_config['name'])
                except Part.DoesNotExist:
                    continue
                part_stats = compute_part_raw_stats(df, part_config, column_info)
                if part_stats:
                    ExperimentStats.objects.update_or_create(
                        experiment=experiment, magnet=magnet, part=part, category='raw',
                        defaults={
                            'data': part_stats,
                            'started_at': experiment.started_at,
                            'ended_at': experiment.ended_at,
                            'duration_seconds': experiment.duration_seconds,
                        }
                    )

        return {'status': 'success', 'experiment_id': experiment_id}

    except Exception as exc:
        print(f"Error computing raw stats for experiment {experiment_id}: {exc}")
        raise self.retry(exc=exc, countdown=60)


@app.task(bind=True, max_retries=2)
def compute_experiment_computed_stats_task(self, experiment_id: int):
    """Compute MagnetTools-derived statistics for an experiment."""
    try:
        experiment = Experiment.objects.select_related('site').get(id=experiment_id)
        df = parse_experiment(experiment)
        if df is None:
            return {'status': 'no_data', 'experiment_id': experiment_id}

        for sm in get_active_magnets(experiment.site, experiment.started_at):
            magnet = sm.magnet
            magnet_config = build_magnet_config(magnet)
            computed_stats = compute_magnet_computed_stats(df, magnet.id, magnet_config)

            if 'error' not in computed_stats:
                ExperimentStats.objects.update_or_create(
                    experiment=experiment, magnet=magnet, part=None, category='computed',
                    defaults={
                        'data': computed_stats,
                        'started_at': experiment.started_at,
                        'ended_at': experiment.ended_at,
                        'duration_seconds': experiment.duration_seconds,
                    }
                )
                for part_name, part_data in computed_stats.get('parts', {}).items():
                    from python_magnetdb.models.part import Part
                    try:
                        part = Part.objects.get(name=part_name)
                    except Part.DoesNotExist:
                        continue
                    ExperimentStats.objects.update_or_create(
                        experiment=experiment, magnet=magnet, part=part, category='computed',
                        defaults={
                            'data': part_data,
                            'started_at': experiment.started_at,
                            'ended_at': experiment.ended_at,
                            'duration_seconds': experiment.duration_seconds,
                        }
                    )
            else:
                print(f"Skipping computed stats for magnet {magnet.name}: {computed_stats['error']}")

        return {'status': 'success', 'experiment_id': experiment_id}

    except Exception as exc:
        print(f"Error computing computed stats for experiment {experiment_id}: {exc}")
        raise self.retry(exc=exc, countdown=120)
```

---

## Week 4–5: API Endpoints and Backfill

### 3.1 Stats API endpoints

**File: `python_magnetdb/routes/api/stats.py`**

```python
"""API endpoints for experiment statistics."""

from fastapi import APIRouter, Query, Depends, HTTPException
from python_magnetdb.dependencies import get_user
from python_magnetdb.models import ExperimentStats
from python_magnetdb.models.experiment import Experiment

router = APIRouter()


@router.get("/api/experiments/{id}/stats")
def experiment_stats(
    id: int,
    user=Depends(get_user('read')),
    category: str = Query(None),
    magnet_id: int = Query(None),
    part_id: int = Query(None),
):
    """Get statistics for a specific experiment."""
    try:
        experiment = Experiment.objects.get(id=id)
    except Experiment.DoesNotExist:
        raise HTTPException(status_code=404, detail="Experiment not found")

    qs = ExperimentStats.objects.filter(experiment=experiment)
    if category:
        qs = qs.filter(category=category)
    if magnet_id is not None:
        qs = qs.filter(magnet_id=magnet_id)
    if part_id is not None:
        qs = qs.filter(part_id=part_id)

    return {
        "experiment_id": id,
        "stats": [_serialize_stat(s) for s in qs.all()]
    }


@router.get("/api/magnets/{id}/experiment-stats")
def magnet_experiment_stats(
    id: int,
    user=Depends(get_user('read')),
    category: str = Query(None),
):
    """Get all per-experiment stats for a magnet (across all experiments)."""
    qs = ExperimentStats.objects.filter(
        magnet_id=id
    ).select_related('experiment').order_by('started_at')
    if category:
        qs = qs.filter(category=category)
    return {"magnet_id": id, "stats": [_serialize_stat(s) for s in qs.all()]}


@router.get("/api/parts/{id}/experiment-stats")
def part_experiment_stats(
    id: int,
    user=Depends(get_user('read')),
    category: str = Query(None),
):
    """Get all per-experiment stats for a part (across all experiments)."""
    qs = ExperimentStats.objects.filter(
        part_id=id
    ).select_related('experiment').order_by('started_at')
    if category:
        qs = qs.filter(category=category)
    return {"part_id": id, "stats": [_serialize_stat(s) for s in qs.all()]}


def _serialize_stat(s: ExperimentStats) -> dict:
    return {
        "id": s.id,
        "experiment_id": s.experiment_id,
        "experiment_name": s.experiment.name,
        "category": s.category,
        "magnet_id": s.magnet_id,
        "part_id": s.part_id,
        "data": s.data,
        "started_at": s.started_at.isoformat() if s.started_at else None,
        "ended_at": s.ended_at.isoformat() if s.ended_at else None,
        "duration_seconds": s.duration_seconds,
        "computed_at": s.computed_at.isoformat(),
        "version": s.version,
    }
```

Register in `python_magnetdb/web.py`:

```python
from python_magnetdb.routes.api.stats import router as stats_router
app.include_router(stats_router)
```

### 3.2 Backfill management command

**File: `python_magnetdb/management/commands/compute_all_experiment_stats.py`**

```python
from django.core.management.base import BaseCommand
from python_magnetdb.models.experiment import Experiment
from python_magnetdb.tasks.compute_stats import (
    compute_experiment_raw_stats_task,
    compute_experiment_computed_stats_task,
)


class Command(BaseCommand):
    help = 'Compute statistics for all existing experiments'

    def add_arguments(self, parser):
        parser.add_argument('--site', type=int, help='Only process experiments for this site ID')
        parser.add_argument('--experiment', type=int, help='Only process this specific experiment ID')
        parser.add_argument('--force', action='store_true', help='Recompute even if stats exist')
        parser.add_argument('--raw-only', action='store_true', help='Skip computed (MagnetTools) stats')
        parser.add_argument('--sync', action='store_true', help='Run synchronously (no Celery)')

    def handle(self, *args, **options):
        qs = Experiment.objects.all()
        if options['site']:
            qs = qs.filter(site_id=options['site']))
        if options['experiment']:
            qs = qs.filter(id=options['experiment'])
        if not options['force']:
            from python_magnetdb.models import ExperimentStats
            existing = ExperimentStats.objects.values_list('experiment_id', flat=True).distinct()
            qs = qs.exclude(id__in=existing)

        experiments = list(qs.values_list('id', flat=True))
        self.stdout.write(f"Processing {len(experiments)} experiments...")

        for i, experiment_id in enumerate(experiments):
            self.stdout.write(f"  [{i+1}/{len(experiments)}] Experiment {experiment_id}...")
            if options['sync']:
                compute_experiment_raw_stats_task(experiment_id)
                if not options['raw_only']:
                    compute_experiment_computed_stats_task(experiment_id)
            else:
                compute_experiment_raw_stats_task.delay(experiment_id)
                if not options['raw_only']:
                    compute_experiment_computed_stats_task.delay(experiment_id)

        self.stdout.write(self.style.SUCCESS(f"Done. {len(experiments)} experiments queued."))
```

Usage:

```bash
# Compute all stats synchronously (for testing)
poetry run python manage.py compute_all_experiment_stats --sync

# Compute only raw stats for site 1
poetry run python manage.py compute_all_experiment_stats --site=1 --raw-only --sync

# Queue all stats via Celery (production)
poetry run python manage.py compute_all_experiment_stats

# Force recompute for a specific experiment
poetry run python manage.py compute_all_experiment_stats --experiment=42 --force --sync
```

---

## Verification Checklist

### Week 1

- [ ] `parse_experiment()` resolves sshfs paths and returns a DataFrame for at least one experiment
- [ ] `parse_experiment()` falls back gracefully when a subtype file is missing
- [ ] `compute_site_raw_stats()` produces reasonable output for a sample experiment
- [ ] `compute_magnet_raw_stats()` correctly maps Icoil columns to parts
- [ ] `compute_part_raw_stats()` produces per-part stats
- [ ] `ExperimentStats` rows created with correct `experiment` FK (not `record`)

### Week 2–3

- [ ] `compute_hoop_at_currents()` matches output of existing `compute_stress_map_chart()`
- [ ] `compute_magnet_computed_stats()` runs without error on at least 2 magnet configs
- [ ] Graceful degradation: if MagnetTools fails, raw stats are still stored

### Week 4–5

- [ ] `GET /api/experiments/{id}/stats` returns correct stats
- [ ] `GET /api/magnets/{id}/experiment-stats` returns stats across experiments
- [ ] `GET /api/parts/{id}/experiment-stats` returns part-level stats across experiments
- [ ] Backfill command processes all existing experiments without errors
- [ ] ExperimentStats count matches expected: experiments × (1 site + N magnets + M parts) × (raw + computed)

---

## Known Risks and Mitigations

**Risk**: sshfs mount unavailable in worker container at stats computation time.
**Mitigation**: Task retries up to 3 times with 60-second backoff. `parse_experiment()`
logs missing paths clearly. Consider a health-check task that verifies sshfs
accessibility before triggering the backfill command.

**Risk**: MagnetTools fails for certain magnet configurations.
**Mitigation**: Computed stats task catches exceptions per-magnet; raw stats are stored
regardless. `data` field may contain `{"error": "..."}` for debugging.

**Risk**: Coil-to-helix mapping wrong for some configurations.
**Mitigation**: `build_magnet_config()` uses sequential indexing. Validate during
backfill by comparing computed field values with known experimental results.

**Risk**: Large files (5000+ points) make the computed stats task slow.
**Mitigation**: Phase 1 only computes at the max-current timestep. Full time series is Phase 2.
