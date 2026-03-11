# Phase 4: Automated Offline Ingestion

## Goal

Automatically detect new data files on the sshfs directory and run the full pipeline:
files detected → `Experiment` created → sub-model rows (`PupitreData` / `PigBrotherData` /
`HybridData`) created → `CuratedData` produced in S3 → `ExperimentStats` computed →
`ProcessedTimeSeries` populated → `CumulativeStats` refreshed.

No manual import needed.

**Duration**: 3–4 weeks
**Dependencies**: Phases 1–3 (full stats pipeline must work end-to-end)
**Delivers**: Celery Beat directory watcher, ingest pipeline chain, admin monitoring

> **Migration note from original design**: Originally written to ingest by uploading a
> file to `StorageAttachment` and creating a `Record`. The new flow is fundamentally
> different:
>
> - Files are **not uploaded** to S3 at ingest time. MagnetDB records the sshfs path
>   and file list in the appropriate sub-model (`PupitreData`, `PigBrotherData`, or
>   `HybridData`).
> - A separate `produce_curated_data` Celery task (service account) reads from sshfs
>   and writes a cleaned Parquet to S3. This separation keeps the ingestion step fast;
>   curated output is produced asynchronously.
> - `ingest_record_file` is **fully replaced** by `ingest_experiment`.
> - The site resolver, filename parser, file stability check, and experimenter extractor
>   from the original design are reused unchanged.
> - The duplicate check changes: instead of `Record.objects.filter(name=filename)`,
>   check `Experiment.objects.filter(name=session_name)`.

---

## Prerequisites Checklist

- [ ] Phases 1–3 complete: stats + timeseries + cumulative pipeline works end-to-end
- [ ] sshfs directory is mounted in the worker container (read-only)
- [ ] Service account (`magnetdb-svc`) has sshfs read access and S3 write access
- [ ] Filename and directory conventions documented (PupitreData vs PigBrotherData vs
      Hybrid, base_path per environment)
- [ ] `python_magnetrun` parsing works for all expected file formats

---

## Week 1: Celery Beat Setup

### 1.1 Add Celery Beat to docker-compose

```yaml
  celery-beat:
    container_name: magnetdb-celery-beat
    build:
      context: .
      dockerfile: Dockerfile
      args:
        USER_UID: "${UUID:-1000}"
        USER_GID: "${GID:-1000}"
    command: >
      bash -c "
        poetry install --no-root &&
        poetry run celery -A python_magnetdb.worker beat
          --loglevel=info
          --scheduler django_celery_beat.schedulers:DatabaseScheduler
      "
    working_dir: /home/feelpp/test
    volumes:
      - .:/home/feelpp/test
      - ../magnetdb-data/django/poetry-cache:/home/feelpp/.cache/pypoetry
      - ${SSHFS_MOUNT:-./data/sshfs}:/mnt/sshfs:ro
    links:
      - redis
      - postgres
    environment:
      S3_ENDPOINT: minio:9000
      S3_ACCESS_KEY: minio
      S3_SECRET_KEY: minio123
      S3_BUCKET: magnetdb
      REDIS_ADDR: redis://redis:6379/0
      DATABASE_HOST: postgres
      SSHFS_BASE_PATH: /mnt/sshfs
```

### 1.2 Configure beat schedule

**File: `python_magnetdb/worker.py`** — add to `app.conf.beat_schedule`:

```python
app.conf.beat_schedule = {
    'scan-incoming-experiments': {
        'task': 'python_magnetdb.tasks.ingest.scan_incoming_directory',
        'schedule': crontab(minute='*/5'),
    },
}
app.conf.timezone = 'Europe/Paris'
```

### 1.3 Environment configuration

Add to `.envrc.example`:

```bash
export SSHFS_BASE_PATH="/mnt/sshfs"
```

---

## Week 1–2: Directory Scanner

### 2.1 Site resolution from filename

**File: `python_magnetdb/actions/resolve_record_site.py`**

Reused unchanged from original Phase 4 design. Key functions:
- `resolve_site_from_filename(filename)` → `Site | None`
- `resolve_site_from_path(filepath)` → `Site | None`
- `extract_experimenter_from_filename(filename)` → `str | None`

### 2.2 Detect sub-model type from path

**File: `python_magnetdb/actions/detect_experiment_source.py`**

```python
"""Determine which sub-model to create from a directory structure."""

import os
from enum import Enum


class DataLayout(str, Enum):
    PUPITRE = 'pupitre'
    PIGBROTHER = 'pigbrother'
    HYBRID = 'hybrid'
    UNKNOWN = 'unknown'


def detect_data_layout(dirpath: str) -> DataLayout:
    """Detect the data layout for a session directory."""
    try:
        entries = set(os.listdir(dirpath))
    except OSError:
        return DataLayout.UNKNOWN
    if {'overview', 'archive'} & entries:
        return DataLayout.PIGBROTHER
    if {'rms', '1khz', 'vprocess'} & entries:
        return DataLayout.HYBRID
    return DataLayout.PUPITRE


def list_files_for_layout(base_path: str, layout: DataLayout) -> dict:
    """List files for a session directory.

    Returns:
        PUPITRE: {'files': [rel_path, ...]}
        PIGBROTHER: {'files': {'overview': [...], 'archive': [...]}, 'defaults': {}}
        HYBRID: {'files': {'rms': [...], '1khz': [...], 'vprocess': [...]}, 'defaults': {}}
    """
    if layout == DataLayout.PUPITRE:
        files = sorted([
            f for f in os.listdir(base_path)
            if os.path.isfile(os.path.join(base_path, f))
            and f.endswith(('.txt', '.tsv', '.csv'))
        ])
        return {'files': files}

    subtypes = {
        DataLayout.PIGBROTHER: ('overview', 'archive'),
        DataLayout.HYBRID: ('rms', '1khz', 'vprocess'),
    }.get(layout, ())

    result = {}
    for subtype in subtypes:
        subpath = os.path.join(base_path, subtype)
        if os.path.isdir(subpath):
            result[subtype] = sorted([
                os.path.join(subtype, f)
                for f in os.listdir(subpath)
                if os.path.isfile(os.path.join(subpath, f))
            ])
    return {'files': result, 'defaults': {}}
```

### 2.3 Ingest tasks

**File: `python_magnetdb/tasks/ingest.py`**

```python
"""Celery tasks for automated experiment ingestion."""

import os
from celery import chain
from python_magnetdb.worker import app
from python_magnetdb.models import AuditLog
from python_magnetdb.models.experiment import Experiment, ExperimentType, ExperimentSource
from python_magnetdb.actions.resolve_record_site import (
    resolve_site_from_path,
    extract_experimenter_from_filename,
)
from python_magnetdb.actions.detect_experiment_source import (
    detect_data_layout,
    list_files_for_layout,
    DataLayout,
)
from python_magnetdb.tasks.compute_stats import (
    compute_experiment_raw_stats_task,
    compute_experiment_computed_stats_task,
    refresh_cumulative_stats_task,
)
from python_magnetdb.tasks.process_timeseries import (
    process_experiment_raw_timeseries,
    process_experiment_derived_timeseries,
)


@app.task
def scan_incoming_directory():
    """Scan the sshfs directory for new session directories."""
    base_path = os.getenv('SSHFS_BASE_PATH')
    if not base_path or not os.path.isdir(base_path):
        return {'status': 'skipped', 'reason': 'SSHFS_BASE_PATH not set or missing'}

    new_experiments, skipped, errors = 0, 0, []

    for session_name in sorted(os.listdir(base_path)):
        session_path = os.path.join(base_path, session_name)
        if not os.path.isdir(session_path):
            continue

        if Experiment.objects.filter(name=session_name).exists():
            skipped += 1
            continue

        site = resolve_site_from_path(session_path)
        if site is None:
            errors.append(f"Cannot resolve site for {session_name}")
            continue

        if not _directory_is_stable(session_path):
            continue

        ingest_experiment.delay(session_path, site.id)
        new_experiments += 1

    return {
        'status': 'success',
        'new_experiments': new_experiments,
        'skipped': skipped,
        'errors': errors,
    }


def _directory_is_stable(dirpath: str, wait_seconds: int = 5) -> bool:
    """Check a session directory has stopped being written to."""
    import time
    try:
        def _total_size(path):
            return sum(
                os.path.getsize(os.path.join(r, f))
                for r, _, files in os.walk(path)
                for f in files
            )
        size1 = _total_size(dirpath)
        time.sleep(wait_seconds)
        return size1 == _total_size(dirpath) and size1 > 0
    except OSError:
        return False


@app.task(bind=True, max_retries=3)
def ingest_experiment(self, session_path: str, site_id: int):
    """Ingest a session directory: create Experiment + sub-model, then trigger pipeline.

    Replaces the original ingest_record_file task.
    """
    try:
        session_name = os.path.basename(session_path)

        if Experiment.objects.filter(name=session_name).exists():
            return {'status': 'already_exists', 'name': session_name}

        layout = detect_data_layout(session_path)
        file_info = list_files_for_layout(session_path, layout)

        if not file_info.get('files'):
            return {'status': 'skipped', 'reason': 'no data files found'}

        experimenter = extract_experimenter_from_filename(session_name)

        experiment = Experiment.objects.create(
            name=session_name,
            site_id=site_id,
            experiment_type=ExperimentType.MONITORING,
            source=ExperimentSource.OFFLINE,
            experimenter=experimenter or '',
        )

        if layout == DataLayout.PUPITRE:
            from python_magnetdb.models.pupitre_data import PupitreData
            PupitreData.objects.create(
                experiment=experiment,
                base_path=session_path,
                files=file_info['files'],
                signatures={},
            )
        elif layout == DataLayout.PIGBROTHER:
            from python_magnetdb.models.pigbrother_data import PigBrotherData
            PigBrotherData.objects.create(
                experiment=experiment,
                base_path=session_path,
                files=file_info['files'],
                defaults=file_info.get('defaults', {}),
                signatures={},
            )
        elif layout == DataLayout.HYBRID:
            from python_magnetdb.models.hybrid_data import HybridData
            HybridData.objects.create(
                experiment=experiment,
                base_path=session_path,
                files=file_info['files'],
                defaults=file_info.get('defaults', {}),
                signatures={},
            )
        else:
            experiment.delete()
            return {'status': 'skipped', 'reason': f'Unknown layout: {layout}'}

        AuditLog.log(
            None, f"Experiment auto-ingested: {session_name}", resource=experiment
        )

        # Pipeline:
        # 1. Produce CuratedData (sshfs → S3 Parquet, service account)
        # 2. Compute raw stats
        # 3. Compute computed stats (MagnetTools)
        # 4. Process raw timeseries
        # 5. Process derived timeseries
        # 6. Refresh cumulative stats
        chain(
            produce_curated_data.si(experiment.id),
            compute_experiment_raw_stats_task.si(experiment.id),
            compute_experiment_computed_stats_task.si(experiment.id),
            process_experiment_raw_timeseries.si(experiment.id),
            process_experiment_derived_timeseries.si(experiment.id),
            refresh_cumulative_stats_task.si(site_id=site_id),
        ).apply_async()

        return {
            'status': 'success',
            'experiment_id': experiment.id,
            'name': session_name,
            'layout': layout,
        }

    except Exception as exc:
        print(f"Error ingesting {session_path}: {exc}")
        raise self.retry(exc=exc, countdown=120)


@app.task(bind=True, max_retries=3)
def produce_curated_data(self, experiment_id: int):
    """Service account task: read sshfs → write cleaned Parquet to S3.

    This is the only pipeline step requiring active sshfs access.
    After this task completes, all downstream steps use S3 only.
    Non-fatal: if it fails, downstream tasks fall back to sshfs directly.
    """
    try:
        from python_magnetdb.models.experiment import Experiment
        from python_magnetdb.models.curated_data import CuratedData
        from python_magnetdb.actions.parse_experiment import _parse_from_sshfs
        from python_magnetdb.actions.parquet_helpers import (
            store_dataframe_as_parquet, build_column_catalog
        )
        from python_magnetdb.utils.signature_serializer import signatures_to_json
        from django.utils import timezone

        experiment = Experiment.objects.select_related('site').get(id=experiment_id)

        for rel in ('pupitre_data', 'pigbrother_data', 'hybrid_data'):
            for sub in getattr(experiment, rel).all():
                if sub.curated_data.filter(format='parquet').exists():
                    continue
                try:
                    df = _parse_from_sshfs(experiment)

                    # Compute signatures
                    try:
                        import python_magnetrun
                        sigs = python_magnetrun.compute_signatures(df)
                        sub.signatures = signatures_to_json(sigs)
                    except Exception:
                        sub.signatures = {}
                    sub.save(update_fields=['signatures'])

                    parquet_att = store_dataframe_as_parquet(
                        df, f"experiment_{experiment_id}_curated.parquet"
                    )

                    # CuratedData FK: set the right sub-model FK
                    sub_fk = {rel: sub}
                    CuratedData.objects.create(
                        **sub_fk,
                        attachment=parquet_att,
                        format='parquet',
                        columns=build_column_catalog(df),
                        provenance={
                            'source': 'sshfs',
                            'base_path': sub.base_path,
                            'ingested_at': timezone.now().isoformat(),
                        },
                    )
                except Exception as e:
                    # Non-fatal: downstream tasks fall back to sshfs
                    print(
                        f"Warning: CuratedData production failed for {rel} "
                        f"{sub.id}: {e}"
                    )

        return {'status': 'success', 'experiment_id': experiment_id}

    except Exception as exc:
        print(f"Error producing CuratedData for experiment {experiment_id}: {exc}")
        raise self.retry(exc=exc, countdown=60)
```

---

## Week 3: Monitoring and Admin

### 3.1 Admin status endpoint

**File: `python_magnetdb/routes/api/admin/ingest.py`**

```python
from fastapi import APIRouter, Depends
from python_magnetdb.dependencies import get_user
from python_magnetdb.models import AuditLog
from python_magnetdb.models.experiment import Experiment, ExperimentSource
from django.utils import timezone
from datetime import timedelta

router = APIRouter()


@router.get("/api/admin/ingest-status")
def ingest_status(user=Depends(get_user('admin'))):
    last_24h = timezone.now() - timedelta(hours=24)
    last_week = timezone.now() - timedelta(days=7)

    return {
        'experiments_last_24h': Experiment.objects.filter(
            source=ExperimentSource.OFFLINE, created_at__gte=last_24h,
        ).count(),
        'experiments_last_week': Experiment.objects.filter(
            source=ExperimentSource.OFFLINE, created_at__gte=last_week,
        ).count(),
        'recent_activity': [
            {
                'action': log.action,
                'created_at': log.created_at.isoformat(),
                'resource_type': log.resource_type,
                'resource_id': log.resource_id,
            }
            for log in AuditLog.objects.filter(
                action__icontains='ingest', created_at__gte=last_24h,
            ).order_by('-created_at')[:20]
        ],
    }
```

---

## Week 3–4: Testing and Hardening

### 4.1 Test scenarios

1. **Happy path**: Place a new session directory in the sshfs mount. Wait 5 minutes.
   Verify `Experiment`, sub-model, `CuratedData`, `ExperimentStats`,
   `ProcessedTimeSeries`, and `CumulativeStats` all created.

2. **Duplicate detection**: Place the same directory again. Verify skipped.

3. **Unresolvable site**: Directory with unknown site name → logged, not dropped.

4. **Incomplete directory**: Start copying a large session → stability check prevents
   premature ingestion.

5. **sshfs unavailable**: `produce_curated_data` retries gracefully; downstream stats
   tasks fall back to sshfs (or fail cleanly if sshfs also unavailable).

6. **MagnetTools failure**: Raw stats and CuratedData succeed; computed stats skipped.

7. **PigBrother layout**: `overview/`/`archive/` detected → `PigBrotherData` created.

8. **Hybrid layout**: `rms/`/`1khz/`/`vprocess/` detected → `HybridData` created.

---

## Verification Checklist

- [ ] Celery Beat starts and runs `scan_incoming_directory` every 5 minutes
- [ ] Scanner correctly identifies new session directories
- [ ] `ingest_experiment` creates `Experiment` + correct sub-model for each layout
- [ ] `produce_curated_data` reads sshfs and writes Parquet to S3
- [ ] `produce_curated_data` failure is non-fatal (downstream falls back)
- [ ] Duplicate sessions skipped (idempotent on `Experiment.name`)
- [ ] Sessions with unresolvable sites are logged with detail
- [ ] Directory stability check prevents partial-write ingestion
- [ ] Full pipeline completes: `ExperimentStats` + `ProcessedTimeSeries` +
      `CumulativeStats` all created for a new session
- [ ] Admin endpoint reports `experiments_last_24h` (not `records_last_24h`)
- [ ] End-to-end: session appears → all artifacts created in < 10 minutes
