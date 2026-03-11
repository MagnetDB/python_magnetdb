# Phase 5: Streaming Readiness & Online Data

## Goal

Accept live streaming data from NI hardware or external databases, buffer in Redis
Streams, window into `Experiment` rows, and feed the same pipeline as offline data.
Optionally expose live data via WebSocket.

**Duration**: 6–8 weeks
**Dependencies**: Phase 4 (automated ingest pipeline working)
**Delivers**: Redis Streams infrastructure, stream adapters, window manager,
optional live WebSocket

**Note**: This phase can be deferred until NI streaming or external DB integration is
concretely planned. Phases 0–4 provide full value without it.

> **Migration note from original design**: Originally written to create `Record` rows
> from stream windows. Updated to target `Experiment`.
>
> ### ⚠️ Architecture decision required before starting Phase 5
>
> There are two valid approaches for where streaming data lives:
>
> **Option A — Streaming through `Experiment`** (recommended)
>
> Each streaming window becomes an `Experiment` with a new `StreamData` sub-model
> (parallel to `PupitreData` / `PigBrotherData` / `HybridData`). This gives a single
> consistent data model and reuses the entire Phase 1–4 pipeline unchanged.
>
> - Window manager creates `Experiment(source=STREAM, stream_id=..., window_index=...)`
> - Creates `StreamData(experiment=..., redis_key=..., window_start=..., window_end=...)`
> - Stores the window as a Parquet in S3, sets `CuratedData` directly (no sshfs step)
> - Triggers the same stats pipeline as Phase 4
>
> **Option B — Keep streaming as `Record`** (minimal Phase 5 disruption)
>
> Streaming windows stay as `Record` rows. The `Record` model still exists (never
> dropped). The window manager creates `Record(source=STREAM, ...)` and triggers the
> legacy `compute_record_*_stats_task` pipeline separately. Two diverging pipelines
> are maintained.
>
> **This phase documents Option A (Experiment path).** Option B is easier to
> implement but creates long-term technical debt. Decide before starting Phase 5;
> the `StreamData` model needs a Sprint 0 / Phase 5 migration.

---

## Prerequisites Checklist

- [ ] Architecture decision made: Option A (Experiment) vs Option B (Record)
- [ ] Phase 4 complete: `ingest_experiment` pipeline works end-to-end
- [ ] Redis is available in the Docker stack
- [ ] NI hardware interface specified OR external database connection details known
- [ ] `Experiment` model has `stream_id` and `window_index` fields (added in Phase 0)
- [ ] (Option A only) `StreamData` sub-model created and migrated

---

## Pre-Phase: StreamData sub-model (Option A)

If Option A is chosen, add this model before starting Phase 5 tasks.

**File: `python_magnetdb/models/stream_data.py`**

```python
from django.db import models


class StreamData(models.Model):
    """Sub-model for streaming data windows.

    Parallel to PupitreData / PigBrotherData / HybridData.
    Represents a single time window from a live Redis stream.
    """
    class Meta:
        db_table = 'stream_data'

    id = models.BigAutoField(primary_key=True)
    experiment = models.ForeignKey(
        'Experiment', on_delete=models.CASCADE,
        related_name='stream_data',
    )
    # Redis stream info for traceability
    redis_stream_key = models.CharField(max_length=255, blank=True)
    redis_first_id = models.CharField(max_length=64, blank=True)
    redis_last_id = models.CharField(max_length=64, blank=True)
    # Stream config FK for back-reference
    stream_config = models.ForeignKey(
        'StreamConfig', on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='stream_data_windows',
    )
    created_at = models.DateTimeField(auto_now_add=True)
```

Register and migrate:

```bash
poetry run python manage.py makemigrations
poetry run python manage.py migrate
```

---

## Architecture Overview

```
              Data Sources                    MagnetDB

┌─────────────┐  ┌──────────────┐    ┌──────────────────┐
│ NI DAQmx    │  │ External DB  │    │ Redis Stream     │
│ hardware    │  │ (polling)    │    │ magnetdb:stream: │
└──────┬──────┘  └──────┬───────┘    │  {stream_id}     │
       │                │            └────────┬─────────┘
       ▼                ▼                     │
┌──────────────────────────────┐              │
│      Stream Adapters         │   XADD       │
│  (push samples to Redis)     │─────────────►│
└──────────────────────────────┘              │
                                    ┌─────────▼──────────┐
                                    │   Window Manager   │
                                    │   (Celery Beat)    │
                                    │   every N minutes  │
                                    └─────────┬──────────┘
                                              │
                                   XRANGE → DataFrame
                                   → CuratedData (S3)
                                   → Experiment + StreamData
                                              │
                                    ┌─────────▼──────────┐
                                    │   Same pipeline    │
                                    │   as Phase 4:      │
                                    │   Experiment → TS  │
                                    │   → Stats → Cumul. │
                                    └────────────────────┘

                     OPTIONAL:

┌─────────────┐     XREAD        ┌─────────────────────┐
│  Browser    │◄──── WebSocket──│  /api/streams/      │
│  (live)     │                  │    {id}/live        │
└─────────────┘                  └─────────────────────┘
```

---

## Week 1–2: Redis Streams Infrastructure

### 1.1 StreamConfig model

**File: `python_magnetdb/models/stream_config.py`**

```python
from django.db import models


class StreamConfig(models.Model):
    """Configuration for a live data stream."""
    class Meta:
        db_table = 'stream_configs'

    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(null=True, blank=True)
    site = models.ForeignKey('Site', on_delete=models.CASCADE)
    adapter_type = models.CharField(
        max_length=50,
        choices=[
            ('ni_daq', 'NI DAQmx'),
            ('database', 'Database Polling'),
            ('mqtt', 'MQTT'),
            ('custom', 'Custom'),
        ],
    )
    adapter_config = models.JSONField(default=dict)
    window_duration_seconds = models.IntegerField(default=300)
    active = models.BooleanField(default=False)
    last_window_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def stream_key(self) -> str:
        return f"magnetdb:stream:{self.id}"

    @property
    def state_key(self) -> str:
        return f"magnetdb:stream_state:{self.id}"
```

### 1.2 Redis Stream utilities

**File: `python_magnetdb/actions/stream_utils.py`**

Unchanged from original Phase 5 design — see original document for full code.
Key functions: `push_sample()`, `read_window()`, `update_window_state()`, `get_stream_info()`.

---

## Week 2–3: Stream Adapters

Adapters are unchanged from the original Phase 5 design. They push samples to Redis
Streams; the window manager converts them to `Experiment` rows.

- `python_magnetdb/adapters/base.py` — `BaseStreamAdapter` (abstract)
- `python_magnetdb/adapters/database_poll.py` — `DatabasePollAdapter`
- `python_magnetdb/adapters/ni_daq.py` — `NIStreamAdapter` (skeleton)

See original Phase 5 document for full adapter code. No changes needed.

---

## Week 3–5: Window Manager

### 3.1 Window close task (Option A — Experiment path)

**File: `python_magnetdb/tasks/stream_window.py`**

```python
"""Celery task to close stream windows and create Experiments."""

import pandas as pd
from datetime import datetime

from python_magnetdb.worker import app
from python_magnetdb.models.stream_config import StreamConfig
from python_magnetdb.models.experiment import Experiment, ExperimentType, ExperimentSource
from python_magnetdb.models.stream_data import StreamData
from python_magnetdb.models.curated_data import CuratedData
from python_magnetdb.actions.stream_utils import read_window, update_window_state
from python_magnetdb.actions.parquet_helpers import store_dataframe_as_parquet, build_column_catalog
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
def close_all_stream_windows():
    """Close windows for all active streams. Run by Celery Beat."""
    for config in StreamConfig.objects.filter(active=True):
        close_stream_window.delay(config.id)


@app.task(bind=True, max_retries=3)
def close_stream_window(self, stream_config_id: int):
    """Close the current time window for a stream and create an Experiment."""
    try:
        config = StreamConfig.objects.select_related('site').get(id=stream_config_id)
        messages, last_msg_id = read_window(config.stream_key, config.state_key)

        if not messages:
            return {'status': 'empty', 'stream': config.name}

        # Convert to DataFrame
        rows = []
        for msg_id, fields in messages:
            row = {}
            for k, v in fields.items():
                key = k.decode() if isinstance(k, bytes) else k
                val = v.decode() if isinstance(v, bytes) else v
                try:
                    row[key] = float(val)
                except ValueError:
                    row[key] = val
            rows.append(row)

        df = pd.DataFrame(rows)
        if df.empty:
            return {'status': 'empty_df', 'stream': config.name}

        # Determine time bounds
        now = datetime.utcnow()
        started_at, ended_at, duration = None, None, None
        if 't' in df.columns:
            started_at = datetime.fromtimestamp(float(df['t'].iloc[0]))
            ended_at = datetime.fromtimestamp(float(df['t'].iloc[-1]))
            duration = float(df['t'].iloc[-1] - df['t'].iloc[0])

        window_name = f"{config.name}_{now.strftime('%Y%m%d_%H%M%S')}"

        # Count existing windows for this stream
        window_index = Experiment.objects.filter(
            stream_id=str(config.id),
            source=ExperimentSource.STREAM,
        ).count() + 1

        # Create Experiment
        experiment = Experiment.objects.create(
            name=window_name,
            site=config.site,
            experiment_type=ExperimentType.MONITORING,
            source=ExperimentSource.STREAM,
            stream_id=str(config.id),
            window_index=window_index,
            started_at=started_at,
            ended_at=ended_at,
            duration_seconds=duration,
        )

        # Store window as Parquet in S3 (no sshfs step — data is already in memory)
        parquet_att = store_dataframe_as_parquet(
            df, f"{window_name}.parquet"
        )
        catalog = build_column_catalog(df)

        # Create StreamData sub-model
        first_id = messages[0][0]
        first_id = first_id.decode() if isinstance(first_id, bytes) else first_id
        stream_sub = StreamData.objects.create(
            experiment=experiment,
            redis_stream_key=config.stream_key,
            redis_first_id=first_id,
            redis_last_id=last_msg_id,
            stream_config=config,
        )

        # Create CuratedData directly (stream windows are already curated)
        CuratedData.objects.create(
            stream_data=stream_sub,
            attachment=parquet_att,
            format='parquet',
            columns=catalog,
            provenance={
                'source': 'redis_stream',
                'stream_key': config.stream_key,
                'window_index': window_index,
                'closed_at': now.isoformat(),
            },
        )

        # Update stream state
        update_window_state(config.state_key, last_msg_id)
        config.last_window_at = now
        config.last_error = None
        config.save(update_fields=['last_window_at', 'last_error', 'updated_at'])

        # Trigger the same pipeline as Phase 4 offline experiments.
        # produce_curated_data step is SKIPPED — CuratedData already created above.
        from celery import chain
        chain(
            compute_experiment_raw_stats_task.si(experiment.id),
            compute_experiment_computed_stats_task.si(experiment.id),
            process_experiment_raw_timeseries.si(experiment.id),
            process_experiment_derived_timeseries.si(experiment.id),
            refresh_cumulative_stats_task.si(site_id=config.site_id),
        ).apply_async()

        return {
            'status': 'success',
            'stream': config.name,
            'experiment_id': experiment.id,
            'num_points': len(df),
        }

    except Exception as exc:
        try:
            config = StreamConfig.objects.get(id=stream_config_id)
            config.last_error = str(exc)
            config.save(update_fields=['last_error', 'updated_at'])
        except Exception:
            pass
        raise self.retry(exc=exc, countdown=60)
```

**Note**: `CuratedData.stream_data` FK requires `CuratedData` to accept a
`stream_data` source alongside `pupitre_data`, `pigbrother_data`, and `hybrid_data`.
Add `stream_data` FK to `CuratedData` in the Phase 5 migration:

```python
# In python_magnetdb/models/curated_data.py — add alongside existing sub-model FKs:
stream_data = models.ForeignKey(
    'StreamData', on_delete=models.CASCADE,
    null=True, blank=True,
    related_name='curated_data',
)
```

Update `CuratedData.clean()` to accept exactly one of the four sub-model FKs.

### 3.2 Add to Celery Beat schedule

In `worker.py`, extend the beat schedule:

```python
app.conf.beat_schedule = {
    'scan-incoming-experiments': {
        'task': 'python_magnetdb.tasks.ingest.scan_incoming_directory',
        'schedule': crontab(minute='*/5'),
    },
    'close-stream-windows': {
        'task': 'python_magnetdb.tasks.stream_window.close_all_stream_windows',
        'schedule': 300.0,  # every 5 minutes
    },
}
```

---

## Week 5–6: Live WebSocket Endpoint (Optional)

### 4.1 WebSocket and admin endpoints

**File: `python_magnetdb/routes/api/streams.py`**

Largely unchanged from original Phase 5 design. Key updates:
- `list_streams` response references `Experiment` windows, not `Record` windows
- Window count query: `Experiment.objects.filter(stream_id=..., source=STREAM).count()`

```python
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
import redis.asyncio as aioredis
import os
from python_magnetdb.dependencies import get_user
from python_magnetdb.models.stream_config import StreamConfig
from python_magnetdb.models.experiment import Experiment, ExperimentSource
from python_magnetdb.actions.stream_utils import get_stream_info

router = APIRouter()


@router.websocket("/api/streams/{stream_id}/live")
async def stream_live(websocket: WebSocket, stream_id: int):
    """WebSocket for live streaming data (pre-windowing)."""
    await websocket.accept()
    try:
        config = StreamConfig.objects.get(id=stream_id, active=True)
    except StreamConfig.DoesNotExist:
        await websocket.close(code=4004, reason="Stream not found or inactive")
        return

    r = aioredis.from_url(os.getenv('REDIS_ADDR', 'redis://localhost:6379/0'))
    last_id = '$'
    try:
        while True:
            results = await r.xread(
                {config.stream_key: last_id}, block=2000, count=50
            )
            if results:
                for _, messages in results:
                    for msg_id, fields in messages:
                        last_id = msg_id
                        await websocket.send_json({
                            k.decode(): v.decode()
                            for k, v in fields.items()
                        })
    except WebSocketDisconnect:
        pass
    finally:
        await r.close()


@router.get("/api/admin/streams")
def list_streams(user=Depends(get_user('admin'))):
    return {"streams": [
        {
            "id": c.id,
            "name": c.name,
            "site": c.site.name,
            "adapter_type": c.adapter_type,
            "active": c.active,
            "window_duration_seconds": c.window_duration_seconds,
            "windows_created": Experiment.objects.filter(
                stream_id=str(c.id), source=ExperimentSource.STREAM
            ).count(),
            "last_window_at": c.last_window_at.isoformat() if c.last_window_at else None,
            "last_error": c.last_error,
            "redis_info": get_stream_info(c.stream_key),
        }
        for c in StreamConfig.objects.select_related('site').all()
    ]}


@router.post("/api/admin/streams/{id}/activate")
def activate_stream(id: int, user=Depends(get_user('admin'))):
    config = StreamConfig.objects.get(id=id)
    config.active = True
    config.save()
    return {"status": "activated", "stream": config.name}


@router.post("/api/admin/streams/{id}/deactivate")
def deactivate_stream(id: int, user=Depends(get_user('admin'))):
    config = StreamConfig.objects.get(id=id)
    config.active = False
    config.save()
    return {"status": "deactivated", "stream": config.name}
```

---

## Verification Checklist

- [ ] Architecture decision made and documented (Option A chosen)
- [ ] `StreamData` model created and migrated
- [ ] `CuratedData.stream_data` FK added and `clean()` updated
- [ ] `StreamConfig` model created and migrated
- [ ] Redis Stream push/read utilities work
- [ ] Database poll adapter connects and pushes data
- [ ] NI adapter skeleton works in simulation mode
- [ ] Window manager creates `Experiment` + `StreamData` + `CuratedData` per window
- [ ] Created `Experiment` rows have `source=STREAM`, `stream_id`, `window_index` set
- [ ] Full pipeline runs: stream → window → Experiment → CuratedData → ExperimentStats
      → ProcessedTimeSeries → CumulativeStats
- [ ] `produce_curated_data` step is SKIPPED for streaming Experiments (already done)
- [ ] WebSocket endpoint delivers live data (optional)
- [ ] Admin endpoints show stream status, window count, and Redis info
- [ ] Stream errors captured in `StreamConfig.last_error`

---

## Future Considerations

- **Adapter deployment**: Stream adapters should run as separate containers, close
  to the data source. For NI hardware, the adapter container runs on the machine
  connected to the NI crate.
- **Backpressure**: Redis Stream `maxlen` prevents unbounded growth. Monitor stream
  length via the admin endpoint.
- **Data quality**: Stream data may have gaps or duplicates. The window manager
  should sort by timestamp and deduplicate before creating the Experiment.
- **Stitching streaming + offline data**: Once both Experiment sources (offline and
  streaming) share the same model, stitched series (Phase 3) automatically span both
  without special handling.
