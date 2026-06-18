# Django Database Routing — MagnetDB

**Status:** Reference note  
**Context:** `python_magnetdb` Django app — Django 5.0, PostgreSQL primary, optional MySQL operational databases

---

## 1. Current state

`python_magnetdb/settings.py` declares a single database:

```python
DATABASES = {
    'default': {
        "ENGINE": "django.db.backends.postgresql",
        'HOST': getenv('DATABASE_HOST') or 'localhost',
        'NAME': getenv('DATABASE_NAME') or 'magnetdb',
        'USER': getenv('DATABASE_USER') or 'magnetdb',
        'PASSWORD': getenv('DATABASE_PASSWORD') or 'magnetdb',
    }
}
```

Since there is only one key (`"default"`), **every model** in `python_magnetdb` uses it automatically. No router is needed and none is configured. This covers all core models:

- `Site`, `Magnet`, `Part`, `Material`, `User`, `Server`
- `Experiment`, `PupitreData`, `PigBrotherData`, `HybridData`, `CuratedData`
- `ExperimentStats`, `ProcessedTimeSeries`, `CumulativeStats`
- `StorageAttachment`, `MeshAttachment`, `CadAttachment`, `Simulation`

---

## 2. How Django picks a database (default behaviour)

When no `DATABASE_ROUTERS` is set:

| Operation | Database used |
|---|---|
| `Model.objects.all()` | `"default"` |
| `Model.objects.using("default").all()` | explicit, same result |
| `manage.py migrate` | `"default"` |
| `manage.py migrate --database=other` | explicit target |

The `"default"` key is Django's built-in fallback for every queryset, migration, and raw SQL call that does not specify a target explicitly.

---

## 3. When would a router be needed in MagnetDB?

The most likely scenario is connecting to the **external operational MySQL databases** at LNCMI as read-only sources. For example:

| Alias | Source system | Data |
|---|---|---|
| `supervision` | SUPERVISION MySQL DB | Pupitre run files metadata |
| `pigbrother` | PIG_BROTHER MySQL DB | PigBrother acquisition data |
| `hybrid` | HYBRIDE MySQL DB | Hybrid magnet data |

These are **read-only reference sources** — MagnetDB never writes to them. All writes go to `"default"` (PostgreSQL).

---

## 4. Adding the MySQL backends

### 4.1 Install drivers (with fallback)

```python
# manage.py  — top of file, before django.setup()
try:
    import MySQLdb          # preferred: mysqlclient (C extension, faster)
except ImportError:
    import pymysql
    pymysql.install_as_MySQLdb()   # pure-Python fallback
```

```bash
pip install mysqlclient   # preferred
# or
pip install pymysql       # fallback if mysqlclient won't compile
```

### 4.2 Extend `settings.py`

```python
DATABASES = {
    # --- Primary store (all writes, all MagnetDB models) ---
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': getenv('DATABASE_HOST') or 'localhost',
        'NAME': getenv('DATABASE_NAME') or 'magnetdb',
        'USER': getenv('DATABASE_USER') or 'magnetdb',
        'PASSWORD': getenv('DATABASE_PASSWORD') or 'magnetdb',
    },

    # --- External operational sources (read-only) ---
    'supervision': {
        'ENGINE': 'django.db.backends.mysql',
        'HOST': getenv('SUPERVISION_DB_HOST') or 'localhost',
        'NAME': getenv('SUPERVISION_DB_NAME') or 'SUPERVISION',
        'USER': getenv('SUPERVISION_DB_USER') or 'readonly',
        'PASSWORD': getenv('SUPERVISION_DB_PASSWORD') or '',
        'PORT': getenv('SUPERVISION_DB_PORT') or '3306',
        'OPTIONS': {'charset': 'utf8mb4'},
    },

    'pigbrother': {
        'ENGINE': 'django.db.backends.mysql',
        'HOST': getenv('PIGBROTHER_DB_HOST') or 'localhost',
        'NAME': getenv('PIGBROTHER_DB_NAME') or 'PIG_BROTHER',
        'USER': getenv('PIGBROTHER_DB_USER') or 'readonly',
        'PASSWORD': getenv('PIGBROTHER_DB_PASSWORD') or '',
        'OPTIONS': {'charset': 'utf8mb4'},
    },

    'hybrid': {
        'ENGINE': 'django.db.backends.mysql',
        'HOST': getenv('HYBRID_DB_HOST') or 'localhost',
        'NAME': getenv('HYBRID_DB_NAME') or 'HYBRIDE',
        'USER': getenv('HYBRID_DB_USER') or 'readonly',
        'PASSWORD': getenv('HYBRID_DB_PASSWORD') or '',
        'OPTIONS': {'charset': 'utf8mb4'},
    },
}
```

Add the corresponding env vars to `.envrc.example`:

```bash
export SUPERVISION_DB_HOST=supervision-db.lncmi.local
export SUPERVISION_DB_NAME=SUPERVISION
export SUPERVISION_DB_USER=readonly
export SUPERVISION_DB_PASSWORD=
```

---

## 5. Router implementation

### 5.1 Create `python_magnetdb/routers.py`

```python
# python_magnetdb/routers.py

OPERATIONAL_DB_APPS = {
    'supervision': 'supervision',
    'pigbrother':  'pigbrother',
    'hybrid':      'hybrid',
}


class MagnetDBRouter:
    """
    Route queries for operational MySQL models to their respective databases.
    All writes and all core MagnetDB models always go to 'default' (PostgreSQL).
    """

    def db_for_read(self, model, **hints):
        db = OPERATIONAL_DB_APPS.get(model._meta.app_label)
        return db if db else 'default'

    def db_for_write(self, model, **hints):
        # Operational databases are read-only from MagnetDB's perspective.
        if model._meta.app_label in OPERATIONAL_DB_APPS:
            raise ValueError(
                f"Write to operational database '{model._meta.app_label}' is not allowed."
            )
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        # Allow relations only within the same database family.
        db1 = OPERATIONAL_DB_APPS.get(obj1._meta.app_label, 'default')
        db2 = OPERATIONAL_DB_APPS.get(obj2._meta.app_label, 'default')
        return db1 == db2

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label in OPERATIONAL_DB_APPS:
            # Never run migrations on the external operational databases.
            return False
        # Only run MagnetDB migrations on the default PostgreSQL database.
        return db == 'default'
```

### 5.2 Register the router in `settings.py`

```python
DATABASE_ROUTERS = ['python_magnetdb.routers.MagnetDBRouter']
```

---

## 6. Django apps layout for operational models

Each operational database needs its own Django app so the `app_label` routing works.

```
python_magnetdb/          ← app_label = 'python_magnetdb' → 'default' (PostgreSQL)
operational/
  supervision/            ← app_label = 'supervision'     → 'supervision' (MySQL)
    apps.py
    models.py             ← read-only mirror models, db_table = existing table names
  pigbrother/             ← app_label = 'pigbrother'      → 'pigbrother' (MySQL)
    apps.py
    models.py
  hybrid/                 ← app_label = 'hybrid'          → 'hybrid' (MySQL)
    apps.py
    models.py
```

Example `apps.py`:

```python
# operational/supervision/apps.py
from django.apps import AppConfig

class SupervisionConfig(AppConfig):
    name = 'operational.supervision'
    label = 'supervision'          # must match key in OPERATIONAL_DB_APPS
    managed = False                # Django will not create/alter these tables
```

Example model (mirrors an existing MySQL table):

```python
# operational/supervision/models.py
from django.db import models

class SupervisionRun(models.Model):
    """Read-only mirror of the SUPERVISION.runs table."""
    run_id    = models.IntegerField(primary_key=True)
    site_name = models.CharField(max_length=128)
    started   = models.DateTimeField()
    stopped   = models.DateTimeField(null=True)

    class Meta:
        app_label  = 'supervision'
        db_table   = 'runs'
        managed    = False    # never touch the real schema
```

Register them in `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    'django.contrib.postgres',
    'django.contrib.contenttypes',
    'python_magnetdb',
    'operational.supervision',
    'operational.pigbrother',
    'operational.hybrid',
]
```

---

## 7. Querying across databases

The router makes everything transparent. No `.using()` is needed in normal code:

```python
# Routed automatically to PostgreSQL via router
experiments = Experiment.objects.filter(site__name="M10")

# Routed automatically to MySQL SUPERVISION via router
runs = SupervisionRun.objects.filter(site_name="M10")
```

Use `.using()` only when you need to override explicitly:

```python
# Force a specific database regardless of routing
SupervisionRun.objects.using('supervision').filter(site_name="M10")
```

Cross-database joins are **not possible** via ORM (different servers). Combine in Python:

```python
experiment_names = set(Experiment.objects.values_list('name', flat=True))
matching_runs = SupervisionRun.objects.filter(site_name__in=experiment_names)
```

---

## 8. Migration behaviour with the router

| Command | Effect |
|---|---|
| `manage.py migrate` | Runs only on `"default"` (PostgreSQL) — operational DBs blocked by `allow_migrate` |
| `manage.py migrate --database=supervision` | Still blocked by `allow_migrate` returning `False` for that app |
| `manage.py inspectdb --database=supervision` | Generates model stubs from the live MySQL schema — useful to bootstrap operational models |

To bootstrap models from the real MySQL schema:

```bash
python manage.py inspectdb --database=supervision > operational/supervision/models.py
```

Then clean up the generated file: add `managed = False`, set correct `app_label`, remove unwanted fields.

---

## 9. Environment variables summary

Add to `.envrc.example` (team reference) and `.envrc` (local values):

```bash
# PostgreSQL — primary MagnetDB store
export DATABASE_HOST=postgres
export DATABASE_NAME=magnetdb
export DATABASE_USER=magnetdb
export DATABASE_PASSWORD=magnetdb

# MySQL — SUPERVISION (read-only)
export SUPERVISION_DB_HOST=supervision-db.lncmi.local
export SUPERVISION_DB_NAME=SUPERVISION
export SUPERVISION_DB_USER=readonly
export SUPERVISION_DB_PASSWORD=

# MySQL — PIGBROTHER (read-only)
export PIGBROTHER_DB_HOST=pigbrother-db.lncmi.local
export PIGBROTHER_DB_NAME=PIG_BROTHER
export PIGBROTHER_DB_USER=readonly
export PIGBROTHER_DB_PASSWORD=

# MySQL — HYBRIDE (read-only)
export HYBRID_DB_HOST=hybrid-db.lncmi.local
export HYBRID_DB_NAME=HYBRIDE
export HYBRID_DB_USER=readonly
export HYBRID_DB_PASSWORD=
```

---

## 10. Key design decisions

- **`python_magnetdb` always uses `default`** — no change to existing models or queries.
- **Operational databases are read-only** — the router raises on write attempts as a safety guard.
- **`managed = False` on all operational models** — Django never touches the MySQL schemas.
- **`allow_migrate` returns `False` for operational apps** — `manage.py migrate` is safe to run with no risk of touching SUPERVISION/PIGBROTHER/HYBRID.
- **`mysqlclient` preferred over `PyMySQL`** — the try/except in `manage.py` provides a silent fallback with no code changes elsewhere.
