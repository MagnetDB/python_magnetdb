# Phase 1: Per-Record Statistics (RecordStats)

## Goal

For each record, compute and store statistical summaries at site, magnet, and part level — both raw (extracted directly from operational data) and computed (derived via MagnetTools). These are the atomic building blocks for all downstream analytics.

**Duration**: 4–5 weeks
**Dependencies**: Phase 0 (models must be migrated)
**Delivers**: RecordStats populated for all existing records, API endpoints, Celery tasks

---

## Prerequisites Checklist

Before starting Phase 1, verify:

- [ ] Phase 0 migration applied: `RecordStats` table exists and is empty
- [ ] `python_magnetrun` parsing works (or fallback parser available)
- [ ] `python_magnetsetup.ana.magnet_setup()` works from JSON config + YAML files (for computed stats)
- [ ] At least 2 magnet configurations have exported reference JSON configs
- [ ] Coil-to-helix mapping documented for each magnet configuration

---

## Week 1: Raw Stats Computation Service

### 1.1 Create the computation module

**File: `python_magnetdb/actions/compute_record_stats.py`**

```python
"""
Compute per-record statistics at site, magnet, and part level.

This module is the core of Phase 1. It takes a parsed DataFrame
and a site configuration, and produces RecordStats entries.
"""

import pandas as pd
import numpy as np
from typing import Optional


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
    """Compute site-level raw statistics from a parsed record DataFrame.
    
    Args:
        df: Parsed record with 't', 'Field', 'Icoil*', temperature, pressure columns.
        column_info: Column name → unit mapping.
    
    Returns:
        dict suitable for RecordStats.data JSONField.
    """
    stats = {}
    
    # Field statistics
    if 'Field' in df.columns:
        stats['field'] = {**compute_column_stats(df['Field']), 'unit': 'T'}
    
    # Power statistics
    for col in ['Pmagnet', 'Ptot']:
        if col in df.columns:
            stats[col.lower()] = {**compute_column_stats(df[col]), 'unit': column_info.get(col, '')}
    
    # Temperature statistics
    temp_cols = [c for c in df.columns if c.startswith('T') and c in column_info]
    if temp_cols:
        stats['temperatures'] = {}
        for col in temp_cols:
            stats['temperatures'][col] = {
                **compute_column_stats(df[col]),
                'unit': column_info.get(col, '°C')
            }
        # Cooling performance: delta T
        if 'Tin1' in df.columns and 'Tout' in df.columns:
            delta_t = df['Tout'] - df['Tin1']
            stats['cooling'] = {
                'delta_T': compute_column_stats(delta_t),
                'unit': '°C',
            }
    
    # Pressure statistics
    pressure_cols = [c for c in df.columns if c.startswith(('HP', 'BP'))]
    if pressure_cols:
        stats['pressures'] = {}
        for col in pressure_cols:
            stats['pressures'][col] = {
                **compute_column_stats(df[col]),
                'unit': column_info.get(col, 'bar')
            }
    
    # Flow statistics
    flow_cols = [c for c in df.columns if c.startswith('Flow')]
    if flow_cols:
        stats['flows'] = {}
        for col in flow_cols:
            stats['flows'][col] = {
                **compute_column_stats(df[col]),
                'unit': column_info.get(col, 'l/s')
            }
    
    # Aggregate current statistics
    icoil_cols = [c for c in df.columns if c.startswith('Icoil')]
    if icoil_cols:
        stats['currents_summary'] = {
            'active_coils': len(icoil_cols),
            'total_current_max': float(sum(df[c].max() for c in icoil_cols)),
        }
    
    return stats


def compute_magnet_raw_stats(
    df: pd.DataFrame,
    magnet_config: dict,
    column_info: dict
) -> dict:
    """Compute magnet-level raw statistics.
    
    Args:
        magnet_config: Magnet configuration with parts and coil indices.
        
    Returns:
        dict for RecordStats.data.
    """
    stats = {'currents': {}, 'voltages': {}, 'resistance_variations': {}}
    
    parts = magnet_config.get('parts', [])
    for part in parts:
        coil_idx = part.get('coil_index')
        if coil_idx is None:
            continue
        
        # Current
        icol = f'Icoil{coil_idx}'
        if icol in df.columns:
            stats['currents'][icol] = {
                **compute_column_stats(df[icol]),
                'unit': 'A',
                'part_name': part['name'],
            }
        
        # Voltage
        ucol = f'Ucoil{coil_idx}'
        if ucol in df.columns:
            stats['voltages'][ucol] = {
                **compute_column_stats(df[ucol]),
                'unit': 'V',
                'part_name': part['name'],
            }
        
        # Resistance variation
        drcol = f'DRcoil{coil_idx}'
        if drcol in df.columns:
            stats['resistance_variations'][drcol] = {
                **compute_column_stats(df[drcol]),
                'unit': '%',
                'part_name': part['name'],
            }
    
    return stats


def compute_part_raw_stats(
    df: pd.DataFrame,
    part_config: dict,
    column_info: dict
) -> dict:
    """Compute part-level raw statistics for a single part.
    
    Args:
        part_config: Part descriptor with coil_index, material info.
        
    Returns:
        dict for RecordStats.data.
    """
    coil_idx = part_config.get('coil_index')
    if coil_idx is None:
        return {}
    
    stats = {}
    
    for prefix, key, unit in [
        ('Icoil', 'current', 'A'),
        ('Ucoil', 'voltage', 'V'),
        ('DRcoil', 'resistance_variation', '%'),
        ('Tcal', 'temperature_cal', '°C'),
    ]:
        col = f'{prefix}{coil_idx}'
        if col in df.columns:
            stats[key] = {**compute_column_stats(df[col]), 'unit': unit}
    
    # Compute power for this part: P = U * I
    icol = f'Icoil{coil_idx}'
    ucol = f'Ucoil{coil_idx}'
    if icol in df.columns and ucol in df.columns:
        power = df[icol] * df[ucol]
        stats['power'] = {**compute_column_stats(power), 'unit': 'W'}
    
    return stats
```

### 1.2 Create the record parsing utility

**File: `python_magnetdb/actions/parse_record.py`**

```python
"""
Parse a record attachment into a DataFrame.

Wraps python_magnetrun (preferred) or falls back to inline parsing
(same logic as the current /visualize endpoint).
"""

import pandas as pd
from datetime import datetime


def parse_record_attachment(attachment) -> pd.DataFrame:
    """Parse a record's StorageAttachment into a cleaned DataFrame.
    
    Args:
        attachment: StorageAttachment instance with a download() method.
    
    Returns:
        DataFrame with 't' (seconds), 'timestamp' (datetime), and data columns.
        Zero-only columns removed.
    """
    # Try python_magnetrun first
    try:
        import python_magnetrun
        # Adjust API call based on audit findings (Task 1 of pre-work)
        df = python_magnetrun.load_record(attachment.download())
        if 't' in df.columns:
            return df
    except (ImportError, Exception):
        pass
    
    # Fallback: inline parsing (from current /visualize endpoint)
    time_format = "%Y.%m.%d %H:%M:%S"
    data = pd.read_csv(attachment.download(), sep=r'\s+', skiprows=1)
    data = data.loc[:, (data != 0.0).any(axis=0)]
    
    if 'Date' in data.columns and 'Time' in data.columns:
        t0 = datetime.strptime(
            data['Date'].iloc[0] + " " + data['Time'].iloc[0],
            time_format
        )
        data["t"] = data.apply(
            lambda row: (datetime.strptime(
                row.Date + " " + row.Time, time_format
            ) - t0).total_seconds(), axis=1
        )
        data["timestamp"] = data.apply(
            lambda row: datetime.strptime(
                row.Date + " " + row.Time, time_format
            ), axis=1
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

### 1.3 Wire into a Celery task

**File: `python_magnetdb/tasks/compute_stats.py`**

```python
"""
Celery tasks for computing record statistics.
"""

from python_magnetdb.worker import app
from python_magnetdb.models import Record, RecordStats
from python_magnetdb.models.magnet import Magnet
from python_magnetdb.models.site_magnet import SiteMagnet
from python_magnetdb.actions.parse_record import parse_record_attachment, extract_time_bounds
from python_magnetdb.actions.compute_record_stats import (
    compute_site_raw_stats,
    compute_magnet_raw_stats,
    compute_part_raw_stats,
)
from python_magnetdb.utils.record_visualization import columns as column_info


def get_active_magnets(site, record_started_at):
    """Get magnets that were active at the time of the record."""
    site_magnets = SiteMagnet.objects.filter(site=site).select_related('magnet')
    active = []
    for sm in site_magnets:
        # If no commissioned_at, assume always active
        if sm.commissioned_at and record_started_at and sm.commissioned_at > record_started_at:
            continue
        if sm.decommissioned_at and record_started_at and sm.decommissioned_at < record_started_at:
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
            'coil_index': idx + 1,  # TODO: verify this mapping per magnet type
            'material': {
                'rpe': mp.part.material.rpe,
                'young': mp.part.material.young,
                'nuance': mp.part.material.nuance,
            } if mp.part.material else {},
        })
    return {
        'name': magnet.name,
        'type': magnet.type,
        'parts': parts,
    }


@app.task(bind=True, max_retries=3)
def compute_record_raw_stats_task(self, record_id: int):
    """Compute raw statistics for a single record at all scope levels."""
    try:
        record = Record.objects.select_related('site', 'attachment').get(id=record_id)
        
        # Parse the record
        df = parse_record_attachment(record.attachment)
        
        # Update record time bounds if not set
        time_bounds = extract_time_bounds(df)
        updated = False
        if record.started_at is None and 'started_at' in time_bounds:
            record.started_at = time_bounds['started_at']
            updated = True
        if record.ended_at is None and 'ended_at' in time_bounds:
            record.ended_at = time_bounds['ended_at']
            updated = True
        if record.duration_seconds is None and 'duration_seconds' in time_bounds:
            record.duration_seconds = time_bounds['duration_seconds']
            updated = True
        if updated:
            record.save(update_fields=[
                f for f in ['started_at', 'ended_at', 'duration_seconds']
                if getattr(record, f) is not None
            ])
        
        # Site-level raw stats
        site_stats = compute_site_raw_stats(df, column_info)
        RecordStats.objects.update_or_create(
            record=record, magnet=None, part=None, category='raw',
            defaults={
                'data': site_stats,
                'started_at': record.started_at,
                'ended_at': record.ended_at,
                'duration_seconds': record.duration_seconds,
            }
        )
        
        # Magnet-level and part-level raw stats
        active_magnets = get_active_magnets(record.site, record.started_at)
        for sm in active_magnets:
            magnet = sm.magnet
            magnet_config = build_magnet_config(magnet)
            
            # Magnet-level
            magnet_stats = compute_magnet_raw_stats(df, magnet_config, column_info)
            RecordStats.objects.update_or_create(
                record=record, magnet=magnet, part=None, category='raw',
                defaults={
                    'data': magnet_stats,
                    'started_at': record.started_at,
                    'ended_at': record.ended_at,
                    'duration_seconds': record.duration_seconds,
                }
            )
            
            # Part-level
            for part_config in magnet_config['parts']:
                from python_magnetdb.models.part import Part
                try:
                    part = Part.objects.get(name=part_config['name'])
                except Part.DoesNotExist:
                    continue
                
                part_stats = compute_part_raw_stats(df, part_config, column_info)
                if part_stats:
                    RecordStats.objects.update_or_create(
                        record=record, magnet=magnet, part=part, category='raw',
                        defaults={
                            'data': part_stats,
                            'started_at': record.started_at,
                            'ended_at': record.ended_at,
                            'duration_seconds': record.duration_seconds,
                        }
                    )
        
        return {'status': 'success', 'record_id': record_id}
    
    except Exception as exc:
        print(f"Error computing raw stats for record {record_id}: {exc}")
        raise self.retry(exc=exc, countdown=60)
```

---

## Week 2–3: Computed Stats (MagnetTools)

### 2.1 Create the computed stats service

**File: `python_magnetdb/actions/compute_record_computed_stats.py`**

```python
"""
Compute derived statistics using MagnetTools (hoop stress, field at bore, etc.).
"""

import pandas as pd
import numpy as np
from python_magnetdb.actions.object_geometries import get_magnet_data


def compute_hoop_at_currents(mt_data, currents: list, magnet_type: str = "H") -> dict:
    """Compute hoop stress for all helices at given currents.
    
    Args:
        mt_data: Tuple (Tubes, Helices, OHelices, BMagnets, UMagnets, Shims)
        currents: List of current values for each power supply
        magnet_type: "H" for helix, "B" for bitter
    
    Returns:
        dict with helix numbers and hoop stress values
    """
    import magnettools.magnettools as mt
    import magnettools.Bmap as bmap
    
    (Tubes, Helices, OHelices, BMagnets, UMagnets, Shims) = mt_data
    
    # Set currents
    vcurrents = mt.DoubleVector(currents)
    mt.set_currents(Tubes, Helices, BMagnets, UMagnets, OHelices, vcurrents)
    
    # Compute central field
    Bz0 = mt.MagneticField(Tubes, Helices, BMagnets, UMagnets, 0, 0)[1]
    
    # Compute hoop stress
    mdata = {"H": Helices, "B": BMagnets, "S": UMagnets}
    Magnets = mdata.get(magnet_type, Helices)
    (headers, values) = bmap.getHoop(
        Magnets, Tubes, Helices, BMagnets, UMagnets, magnet_type
    )
    
    df_hoop = pd.DataFrame.from_records(values)
    df_hoop.columns = headers
    
    return {
        'Bz0': float(Bz0),
        'helix_numbers': df_hoop['num'].tolist(),
        'hoop_MPa': df_hoop['Hoop[MPa]'].tolist(),
    }


def compute_magnet_computed_stats(
    df: pd.DataFrame,
    magnet_id: int,
    magnet_config: dict,
) -> dict:
    """Compute MagnetTools-derived statistics for a magnet across a record.
    
    Samples key timesteps (max current, min current, a few intermediate)
    rather than computing at every timestep (that's Phase 2 ETL territory).
    
    Returns:
        dict for RecordStats.data with category='computed'
    """
    try:
        mt_data = get_magnet_data(magnet_id)
    except Exception as e:
        print(f"Failed to load MagnetTools data for magnet {magnet_id}: {e}")
        return {'error': str(e)}
    
    import magnettools.magnettools as mt
    (Tubes, Helices, OHelices, BMagnets, UMagnets, Shims) = mt_data
    icurrents = mt.get_currents(Tubes, Helices, BMagnets, UMagnets)
    
    # Find the timestep with max total current
    icoil_cols = [c for c in df.columns if c.startswith('Icoil')]
    if not icoil_cols:
        return {'error': 'no Icoil columns found'}
    
    # Use first Icoil column as proxy for helix supply current
    # TODO: refine based on documented coil mapping
    primary_col = icoil_cols[0]
    idx_max = df[primary_col].idxmax()
    
    # Compute at max current
    max_current = float(df.loc[idx_max, primary_col])
    vcurrents = list(icurrents)
    vcurrents[0] = max_current
    
    hoop_at_max = compute_hoop_at_currents(mt_data, vcurrents)
    
    # Build per-part computed stats
    parts_stats = {}
    parts = magnet_config.get('parts', [])
    for i, hoop_val in enumerate(hoop_at_max['hoop_MPa']):
        if i < len(parts):
            part = parts[i]
            rpe = float(part.get('material', {}).get('rpe', 0)) if part.get('material', {}).get('rpe') else None
            parts_stats[part['name']] = {
                'hoop_stress_at_max_current': {
                    'value': hoop_val,
                    'unit': 'MPa',
                    'at_current_A': max_current,
                },
                'ratio_to_rpe': hoop_val / rpe if rpe else None,
            }
    
    return {
        'Bz0_at_max_current': hoop_at_max['Bz0'],
        'max_current_used': max_current,
        'parts': parts_stats,
    }
```

### 2.2 Add computed stats Celery task

Add to `python_magnetdb/tasks/compute_stats.py`:

```python
@app.task(bind=True, max_retries=2)
def compute_record_computed_stats_task(self, record_id: int):
    """Compute MagnetTools-derived statistics for a record."""
    try:
        record = Record.objects.select_related('site', 'attachment').get(id=record_id)
        df = parse_record_attachment(record.attachment)
        
        active_magnets = get_active_magnets(record.site, record.started_at)
        for sm in active_magnets:
            magnet = sm.magnet
            magnet_config = build_magnet_config(magnet)
            
            computed_stats = compute_magnet_computed_stats(
                df, magnet.id, magnet_config
            )
            
            if 'error' not in computed_stats:
                RecordStats.objects.update_or_create(
                    record=record, magnet=magnet, part=None, category='computed',
                    defaults={
                        'data': computed_stats,
                        'started_at': record.started_at,
                        'ended_at': record.ended_at,
                        'duration_seconds': record.duration_seconds,
                    }
                )
                
                # Per-part computed stats
                for part_name, part_data in computed_stats.get('parts', {}).items():
                    from python_magnetdb.models.part import Part
                    try:
                        part = Part.objects.get(name=part_name)
                    except Part.DoesNotExist:
                        continue
                    
                    RecordStats.objects.update_or_create(
                        record=record, magnet=magnet, part=part, category='computed',
                        defaults={
                            'data': part_data,
                            'started_at': record.started_at,
                            'ended_at': record.ended_at,
                            'duration_seconds': record.duration_seconds,
                        }
                    )
            else:
                print(f"Skipping computed stats for magnet {magnet.name}: {computed_stats['error']}")
        
        return {'status': 'success', 'record_id': record_id}
    
    except Exception as exc:
        print(f"Error computing computed stats for record {record_id}: {exc}")
        raise self.retry(exc=exc, countdown=120)
```

---

## Week 4–5: API Endpoints and Backfill

### 3.1 Stats API endpoints

**File: `python_magnetdb/routes/api/stats.py`**

```python
"""
API endpoints for record statistics.
"""

from fastapi import APIRouter, Query, Depends, HTTPException

from python_magnetdb.dependencies import get_user, get_user_record_queryset
from python_magnetdb.models import RecordStats, Record
from python_magnetdb.routes.api.serializers import model_serializer

router = APIRouter()


@router.get("/api/records/{id}/stats")
def record_stats(
    id: int,
    user=Depends(get_user('read')),
    category: str = Query(None),
    magnet_id: int = Query(None),
    part_id: int = Query(None),
):
    """Get statistics for a specific record."""
    # Check record access
    record_qs = get_user_record_queryset(user)
    try:
        record = record_qs.get(id=id)
    except Record.DoesNotExist:
        raise HTTPException(status_code=404, detail="Record not found")
    
    qs = RecordStats.objects.filter(record=record)
    if category:
        qs = qs.filter(category=category)
    if magnet_id is not None:
        qs = qs.filter(magnet_id=magnet_id)
    if part_id is not None:
        qs = qs.filter(part_id=part_id)
    
    return {
        "record_id": id,
        "stats": [
            {
                "id": s.id,
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
            for s in qs.all()
        ]
    }


@router.get("/api/magnets/{id}/record-stats")
def magnet_record_stats(
    id: int,
    user=Depends(get_user('read')),
    category: str = Query(None),
):
    """Get all per-record stats for a magnet (across all its records)."""
    qs = RecordStats.objects.filter(
        magnet_id=id
    ).select_related('record').order_by('started_at')
    
    if category:
        qs = qs.filter(category=category)
    
    # Apply record-level data scoping
    accessible_records = get_user_record_queryset(user)
    qs = qs.filter(record__in=accessible_records)
    
    return {
        "magnet_id": id,
        "stats": [
            {
                "id": s.id,
                "record_id": s.record_id,
                "record_name": s.record.name,
                "category": s.category,
                "part_id": s.part_id,
                "data": s.data,
                "started_at": s.started_at.isoformat() if s.started_at else None,
                "duration_seconds": s.duration_seconds,
                "version": s.version,
            }
            for s in qs.all()
        ]
    }


@router.get("/api/parts/{id}/record-stats")
def part_record_stats(
    id: int,
    user=Depends(get_user('read')),
    category: str = Query(None),
):
    """Get all per-record stats for a part (across all its records)."""
    qs = RecordStats.objects.filter(
        part_id=id
    ).select_related('record').order_by('started_at')
    
    if category:
        qs = qs.filter(category=category)
    
    accessible_records = get_user_record_queryset(user)
    qs = qs.filter(record__in=accessible_records)
    
    return {
        "part_id": id,
        "stats": [
            {
                "id": s.id,
                "record_id": s.record_id,
                "record_name": s.record.name,
                "category": s.category,
                "magnet_id": s.magnet_id,
                "data": s.data,
                "started_at": s.started_at.isoformat() if s.started_at else None,
                "duration_seconds": s.duration_seconds,
                "version": s.version,
            }
            for s in qs.all()
        ]
    }
```

Register the router in `python_magnetdb/web.py`:

```python
from python_magnetdb.routes.api.stats import router as stats_router
app.include_router(stats_router)
```

### 3.2 Backfill management command

**File: `python_magnetdb/management/commands/compute_all_record_stats.py`**

```python
from django.core.management.base import BaseCommand
from python_magnetdb.models import Record
from python_magnetdb.tasks.compute_stats import (
    compute_record_raw_stats_task,
    compute_record_computed_stats_task,
)


class Command(BaseCommand):
    help = 'Compute statistics for all existing records'

    def add_arguments(self, parser):
        parser.add_argument('--site', type=int, help='Only process records for this site ID')
        parser.add_argument('--record', type=int, help='Only process this specific record ID')
        parser.add_argument('--force', action='store_true', help='Recompute even if stats exist')
        parser.add_argument('--raw-only', action='store_true', help='Skip computed (MagnetTools) stats')
        parser.add_argument('--sync', action='store_true', help='Run synchronously (no Celery)')

    def handle(self, *args, **options):
        qs = Record.objects.all()
        
        if options['site']:
            qs = qs.filter(site_id=options['site'])
        if options['record']:
            qs = qs.filter(id=options['record'])
        if not options['force']:
            # Skip records that already have stats
            from python_magnetdb.models.record_stats import RecordStats
            existing = RecordStats.objects.values_list('record_id', flat=True).distinct()
            qs = qs.exclude(id__in=existing)
        
        records = list(qs.values_list('id', flat=True))
        self.stdout.write(f"Processing {len(records)} records...")
        
        for i, record_id in enumerate(records):
            self.stdout.write(f"  [{i+1}/{len(records)}] Record {record_id}...")
            
            if options['sync']:
                compute_record_raw_stats_task(record_id)
                if not options['raw_only']:
                    compute_record_computed_stats_task(record_id)
            else:
                compute_record_raw_stats_task.delay(record_id)
                if not options['raw_only']:
                    compute_record_computed_stats_task.delay(record_id)
        
        self.stdout.write(self.style.SUCCESS(f"Done. {len(records)} records queued."))
```

Usage:

```bash
# Compute all stats synchronously (for testing)
poetry run python manage.py compute_all_record_stats --sync

# Compute only raw stats for site 1
poetry run python manage.py compute_all_record_stats --site=1 --raw-only --sync

# Queue all stats via Celery (production)
poetry run python manage.py compute_all_record_stats

# Force recompute for a specific record
poetry run python manage.py compute_all_record_stats --record=42 --force --sync
```

---

## Verification Checklist

### Week 1

- [ ] `parse_record_attachment()` works for all existing records
- [ ] `compute_site_raw_stats()` produces reasonable output for a sample record
- [ ] `compute_magnet_raw_stats()` correctly maps Icoil columns to parts
- [ ] `compute_part_raw_stats()` produces per-part stats

### Week 2–3

- [ ] `compute_hoop_at_currents()` matches output of existing `compute_stress_map_chart()`
- [ ] `compute_magnet_computed_stats()` runs without error on at least 2 magnet configs
- [ ] Graceful degradation: if MagnetTools fails for a record, raw stats are still stored

### Week 4–5

- [ ] `GET /api/records/{id}/stats` returns correct stats
- [ ] `GET /api/magnets/{id}/record-stats` returns stats across records, respects data scoping
- [ ] `GET /api/parts/{id}/record-stats` returns part-level stats across records
- [ ] Backfill command processes all existing records without errors
- [ ] RecordStats count matches expected: records × (1 site + N magnets + M parts) × (1 raw + 1 computed)

---

## Known Risks and Mitigations

**Risk**: MagnetTools computation fails for certain magnet configurations.
**Mitigation**: Computed stats task catches exceptions, logs them, and stores raw stats regardless. The `data` field can contain `{"error": "..."}` for debugging.

**Risk**: Coil-to-helix mapping is wrong for some configurations.
**Mitigation**: The `build_magnet_config()` function uses sequential indexing (`idx + 1`). This must be verified against the actual mapping documented in Task 6 of the pre-work. Mark with a TODO and validate during backfill by comparing computed field values with known experimental results.

**Risk**: Large records (5000+ points) make the computed stats task slow.
**Mitigation**: Phase 1 only computes hoop stress at the max-current timestep, not at every timestep. Full time series computation is Phase 2 (ETL). This keeps the per-record computation under 10 seconds.
