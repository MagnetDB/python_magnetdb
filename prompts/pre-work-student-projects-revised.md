# Pre-Work: Preparing the Student Project Environment (Revised)

## Approach: Minimalist MagnetDB Stack

**Revision rationale**: Rather than building standalone student helpers that duplicate existing functionality, students will work against a **minimalist MagnetDB instance** — the real stack (postgres, redis, minio, api) with a curated seed dataset, no lemonldap/traefik/frontend. Students interact via Swagger UI and Jupyter notebooks that call the API or import modules directly.

This approach is better because:

- Students work with the real data model, real API, real attachments
- Their code integrates directly into MagnetDB — no translation layer needed afterward
- The existing `python_magnetsetup.ana.magnet_setup()` bridge already converts JSON configs to MagnetTools objects — no need to rewrite it
- The existing seed infrastructure creates realistic test data

---

## Architecture of the Student Environment

```
┌──────────────────────────────────────────────────────┐
│  docker-compose-student.yml                          │
│                                                      │
│  ┌──────────┐  ┌───────┐  ┌───────┐  ┌───────────┐ │
│  │ postgres  │  │ redis │  │ minio │  │ api       │ │
│  │          │  │       │  │       │  │ (FastAPI) │ │
│  └──────────┘  └───────┘  └───────┘  └─────┬─────┘ │
│                                             │       │
│  ┌──────────────────────────────────────────┼─────┐ │
│  │ jupyter                                  │     │ │
│  │  - notebooks/                            │     │ │
│  │  - can import python_magnetdb modules    │     │ │
│  │  - can call API via requests             │     │ │
│  │  - has python_magnetrun installed        │     │ │
│  │  - has magnettools installed             │     │ │
│  └────────────────────────────────────────────────┘ │
│                                                      │
│  NOT included: lemonldap, traefik, web-app           │
└──────────────────────────────────────────────────────┘
```

Students access:
- **Swagger UI** at `http://localhost:8000/docs` for exploring the API
- **JupyterLab** at `http://localhost:8888` for notebooks and development
- **PgAdmin** at `http://localhost:5050` (optional, for inspecting the database)

Authentication is bypassed or simplified (fixed API token) since this is a local development environment.

---

## Task 1: Audit and Prepare python_magnetrun (1.5–3.5 days)

### Objective

Ensure `python_magnetrun` installs cleanly and provides a usable Python API for parsing operational records into DataFrames. This module is needed by all three projects.

### 1.1 Repository and packaging audit

```bash
git clone <python_magnetrun_repo_url>
cd python_magnetrun

# Check packaging
cat pyproject.toml
ls -la

# Check for Django dependencies (must have NONE)
grep -r "django" python_magnetrun/ --include="*.py"

# Attempt install in the magnetdb-api container
docker exec -it magnetdb-api bash
pip install /path/to/python_magnetrun --break-system-packages
```

**Document**:
- [ ] Repository location and access method
- [ ] Build backend (hatchling, poetry, setuptools?)
- [ ] Dependencies list — flag any problematic ones (Django, heavy GUI libs)
- [ ] Python 3.11 compatibility confirmed

### 1.2 Discover and document the parsing API

```python
import python_magnetrun
import pkgutil

# Explore module structure
for importer, modname, ispkg in pkgutil.walk_packages(python_magnetrun.__path__):
    print(f"  {'[pkg]' if ispkg else '     '} {modname}")

# Find the parsing entry point
# Look for: load, parse, read, MagnetRun, MRecord, ...
print(dir(python_magnetrun))
```

**What we need**: a function that takes a file path and returns a pandas DataFrame with at minimum columns `t` (seconds), `timestamp` (datetime), `Field`, `Icoil1`...`IcoilN`, temperature channels, and pressure channels.

**Document**:
- [ ] Parsing function signature and module path
- [ ] Return type (DataFrame, custom object?)
- [ ] Supported record formats/types
- [ ] Whether it handles timestamp computation internally
- [ ] Whether it removes zero-only columns

### 1.3 Test with real record files

Test against 3+ records from different sites and time periods. Verify column names match the `record_visualization.py` definitions.

### 1.4 Fallback plan

If `python_magnetrun` is not ready for standalone use, extract the parsing logic from the existing `/visualize` endpoint into a minimal module. The code already exists in `python_magnetdb/routes/api/records.py` — it's ~15 lines of pandas operations. This fallback is documented in the verification prompt file.

### Verification criteria

- [ ] `python_magnetrun` installs without Django in the api container
- [ ] OR: fallback parser module is written and tested
- [ ] At least 5 record files from 2+ sites parse successfully
- [ ] Output DataFrames have consistent column structure

---

## Task 2: Verify python_magnetsetup → MagnetTools Bridge (2–3 days)

### Objective

Confirm that the existing code path `JSON config + YAML files → magnet_setup() → MagnetTools objects → field + hoop stress` works without Django model access.

This is the critical path for Project B (hoop stress). The verification prompt file (`prompt-verify-magnetrun-magnettools.md`) provides the detailed step-by-step procedure.

### 2.1 Extract reference data from running MagnetDB

From inside the `magnetdb-api` container with seeds loaded:

```python
import os, json
os.environ['DJANGO_SETTINGS_MODULE'] = 'python_magnetdb.settings'
import django; django.setup()

from python_magnetdb.actions.generate_magnet_directory import generate_magnet_directory
from python_magnetdb.actions.generate_simulation_config import generate_magnet_config

# Export for 2-3 magnet configurations
for magnet_id in [1, 2, 3]:  # adjust IDs based on your seed data
    config = generate_magnet_directory(magnet_id, f'/tmp/magnet_{magnet_id}')
    print(f"Magnet {magnet_id}: {json.dumps(config, indent=2)[:200]}...")
```

This produces directories with `config.json` + `data/geometries/*.yaml` — exactly what `magnet_setup()` needs.

### 2.2 Test magnet_setup() without Django

```python
from python_magnetsetup.ana import magnet_setup
from python_magnetsetup.config import appenv
import json

test_dir = "/tmp/magnet_1"
data_dir = f"{test_dir}/data"
env = appenv(
    envfile=None, url_api=data_dir,
    yaml_repo=f"{data_dir}/geometries", cad_repo=f"{data_dir}/cad",
    mesh_repo=data_dir, simage_repo=data_dir,
    mrecord_repo=data_dir, optim_repo=data_dir,
)
with open(f"{test_dir}/config.json") as f:
    config_data = json.load(f)

data = magnet_setup(env, config_data, True)
(Tubes, Helices, OHelices, BMagnets, UMagnets, Shims) = data
```

### 2.3 Test field computation and hoop stress

Follow the steps in Part 2 of the verification prompt. Confirm that `mt.MagneticField()` and `bmap.getHoop()` produce plausible values.

### 2.4 Known issue: MAT_ISOLANT

`generate_magnet_config()` fetches the insulator material from the database (`Material.objects.get(name="MAT_ISOLANT")`). For standalone use, the insulator properties must be embedded in the JSON config. Two options:

**Option A** (quick): Modify `generate_magnet_config()` to always include insulator data in the exported JSON (it already does — verify the exported config.json contains the `"insulator"` key in each Helix/Ring entry).

**Option B** (if needed): Add a default insulator dict as a fallback when the JSON doesn't contain one.

### 2.5 Document the current mapping

**Critical for Project B**: Determine how `Icoil1`...`Icoil16` columns in records map to MagnetTools current inputs. Investigate:

- Is there one power supply current per `Tube` in MagnetTools?
- Does `Icoil1` correspond to the first helix or the first power supply?
- Does this mapping vary by magnet type (Insert vs. Bitter)?

Document this in a `coil_mapping.md` file per magnet configuration.

### Verification criteria

- [ ] `magnet_setup()` returns MagnetTools objects from JSON config + YAML files
- [ ] No Django import in the `magnet_setup()` call chain
- [ ] Field computation produces plausible values (compare with known magnet performance)
- [ ] Hoop stress computation produces plausible values
- [ ] Insulator material is handled correctly in exported configs
- [ ] Icoil → MagnetTools current mapping documented for at least 2 magnet configurations
- [ ] Tested with at least 2 different magnet geometries (e.g., HL-31 and H12-phi50)

---

## Task 3: Curate the Seed Dataset (2–3 days)

### Objective

Prepare a reduced but realistic seed dataset that populates the minimalist MagnetDB with enough data for all three projects.

### 3.1 Select magnet configurations

Choose 2–3 configurations that:
- Cover different magnet types (at least 2 Insert configurations with different helix counts)
- Have existing geometry YAML files in `python_magnetsetup/data/`
- Have operational records available

Recommended: M9_M19061901 (HL-31, 14 helices + rings) and M10_M19071101 (H12-phi50, 12 helices + rings).

### 3.2 Select operational records

Choose 15–20 records covering:
- Both selected magnet configurations
- Different operating conditions (nominal, high-field, short runs, long runs)
- At least one record with a thermal or current anomaly
- Records from different time periods (for lifetime analysis)

### 3.3 Create a student seed script

Create `python_magnetdb/seeds/seed-student.py` that:
- Creates materials for the selected configurations
- Creates parts (helices, rings) with geometry configs
- Creates magnets and sites
- Imports the selected record files
- Creates a test user with a known API token

```python
"""
Student project seed data.
Creates a minimalist dataset for M1 project work.

Usage:
    export DATA_DIR=/data
    poetry run python3 -m python_magnetdb.seeds.seed-student
"""

from .crud import create_material, create_part, create_site, create_magnet, create_record
from ..models.magnet import MagnetType

# Reuse existing seed definitions for selected configurations
# Import from seed-M19061901 and seed-M19071101

# ... materials, parts, magnets, sites ...

# Import selected records
RECORDS = [
    {"file": "record_file_1.tsv", "site": site_1},
    {"file": "record_file_2.tsv", "site": site_1},
    # ... 15-20 records
]

for rec in RECORDS:
    create_record(rec)

# Create student user with fixed API token
from ..models.user import User
student_user, _ = User.objects.get_or_create(
    username="student",
    defaults={
        "email": "student@lncmi.cnrs.fr",
        "name": "Student Project",
        "role": "designer",
        "api_key": "student-project-api-key-2025",
    }
)
```

### 3.4 Anonymization

- Replace experimenter names in record files with generic IDs
- Verify that geometry YAML and material data are shareable under internship NDA
- Remove any operational comments or notes that reference specific people

### 3.5 Export reference JSON configs

Using the code from Task 2.1, export `config.json` + geometry YAMLs for each selected magnet. Store these in a `reference_data/` directory that ships with the student environment.

### Verification criteria

- [ ] `seed-student.py` runs successfully against a fresh database
- [ ] 2–3 magnet configurations created with full part hierarchy
- [ ] 15–20 records imported and accessible via API
- [ ] Student user can authenticate with fixed API token
- [ ] Reference JSON configs exported for each magnet configuration
- [ ] No personal/confidential data in the seed dataset

---

## Task 4: Build the Student Docker Compose (1.5–2 days)

### Objective

Create a `docker-compose-student.yml` that starts the minimalist MagnetDB stack plus a Jupyter container.

### 4.1 Docker compose file

```yaml
# docker-compose-student.yml
# Minimalist MagnetDB stack for student projects
# No lemonldap, no traefik, no web frontend

services:
  postgres:
    container_name: magnetdb-student-postgres
    image: postgres:17
    environment:
      POSTGRES_USER: magnetdb
      POSTGRES_PASSWORD: magnetdb
      TZ: 'Europe/Paris'
    volumes:
      - student-postgres-data:/var/lib/postgresql/data

  redis:
    container_name: magnetdb-student-redis
    image: redis

  minio:
    container_name: magnetdb-student-minio
    image: minio/minio
    command: server /data --console-address ":9080"
    environment:
      MINIO_ROOT_USER: minio
      MINIO_ROOT_PASSWORD: minio123
    ports:
      - 9080:9080
    volumes:
      - student-minio-data:/data

  api:
    container_name: magnetdb-student-api
    build:
      context: .
      dockerfile: Dockerfile
    command: >
      bash -c "
        poetry install --no-root &&
        poetry run python manage.py migrate &&
        poetry run python -m python_magnetdb.seeds.seed-student &&
        poetry run uvicorn python_magnetdb.web:app --host 0.0.0.0 --port 8000
      "
    ports:
      - 8000:8000
    volumes:
      - .:/home/feelpp/test
      - ./data:/data
    environment:
      S3_ENDPOINT: minio:9000
      S3_ACCESS_KEY: minio
      S3_SECRET_KEY: minio123
      S3_BUCKET: magnetdb
      REDIS_ADDR: redis://redis:6379/0
      DATABASE_HOST: postgres
      DATA_DIR: /data
      # Bypass OIDC — use direct token auth
      SECRET: student-secret-key
    depends_on:
      - postgres
      - redis
      - minio

  jupyter:
    container_name: magnetdb-student-jupyter
    build:
      context: .
      dockerfile: Dockerfile-student-jupyter
    ports:
      - 8888:8888
    volumes:
      - .:/home/feelpp/magnetdb
      - ./student_notebooks:/home/feelpp/notebooks
      - ./reference_data:/home/feelpp/reference_data
    environment:
      MAGNETDB_API_URL: http://api:8000
      MAGNETDB_API_TOKEN: student-project-api-key-2025
      DATA_DIR: /data
    depends_on:
      - api

volumes:
  student-postgres-data:
  student-minio-data:
```

### 4.2 Jupyter Dockerfile

```dockerfile
# Dockerfile-student-jupyter
FROM trophime/magnettools:bookworm-poetry-2.2.1

USER root
RUN apt-get update && apt-get install -y magnettools libmagnettools-dev \
    && rm -rf /var/lib/apt/lists/*
ENV LD_LIBRARY_PATH="/usr/lib/x86_64-linux-gnu/MagnetTools/:$LD_LIBRARY_PATH"

RUN pip install --break-system-packages \
    jupyterlab ipywidgets \
    pandas pyarrow numpy scipy \
    matplotlib seaborn scikit-learn \
    requests

# Install magnettools Python bindings
COPY magnettools-1.1.0-cp311-cp311-linux_x86_64.whl /tmp/
RUN pip install --break-system-packages /tmp/magnettools-1.1.0-cp311-cp311-linux_x86_64.whl

# Install python_magnetgeo and python_magnetsetup
COPY python_magnetgeo/ /opt/python_magnetgeo/
RUN pip install --break-system-packages /opt/python_magnetgeo/
COPY python_magnetsetup/ /opt/python_magnetsetup/
RUN pip install --break-system-packages /opt/python_magnetsetup/

# Install python_magnetrun (if available)
# COPY python_magnetrun/ /opt/python_magnetrun/
# RUN pip install --break-system-packages /opt/python_magnetrun/

USER feelpp
WORKDIR /home/feelpp
EXPOSE 8888
CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", \
     "--NotebookApp.token=''", "--NotebookApp.password=''"]
```

### 4.3 First-run script

```bash
#!/bin/bash
# setup-student-env.sh
# Run once to initialize the student environment

echo "Starting student MagnetDB environment..."
docker compose -f docker-compose-student.yml up -d

echo "Waiting for services to be ready..."
sleep 15

echo "Verifying API..."
curl -s -H "Authorization: student-project-api-key-2025" \
  http://localhost:8000/api/sites | python3 -m json.tool

echo ""
echo "Environment ready!"
echo "  API + Swagger UI: http://localhost:8000/docs"
echo "  JupyterLab:       http://localhost:8888"
echo "  MinIO Console:    http://localhost:9080"
```

### Verification criteria

- [ ] `docker compose -f docker-compose-student.yml up` starts all services
- [ ] API responds at localhost:8000/docs
- [ ] Jupyter responds at localhost:8888
- [ ] Student API token works for all read endpoints
- [ ] Seeds are loaded (sites, magnets, parts, records visible via API)
- [ ] Jupyter can `import magnettools.magnettools as mt`
- [ ] Jupyter can `import python_magnetgeo as pmg`
- [ ] Jupyter can call the API via `requests.get("http://api:8000/api/sites", ...)`

---

## Task 5: Write Starter Notebooks (1.5–2 days)

### Objective

Create 3 Jupyter notebooks that run in the student environment, verified to work end-to-end.

### Notebook 00: Explore MagnetDB Data

- Connect to the API, list sites, magnets, parts
- Fetch a record's visualization data via API
- Load record data into a DataFrame, plot channels
- Navigate the site → magnet → part hierarchy
- Show the column reference with units

### Notebook 01: MagnetTools from JSON Config

- Load a reference `config.json` and geometry YAML files
- Call `magnet_setup()` to create MagnetTools objects
- Compute field at origin, plot field profile along z-axis
- Compute hoop stress, display per-helix table
- Compare with material Rpe values from the config

### Notebook 02: Multi-Record Analysis

- Fetch all records for a site via API
- Parse each record, extract per-record summary (max field, max current, duration)
- Plot lifetime evolution of key metrics
- Demonstrate the coil-to-helix mapping
- Show what cross-record statistics would look like

### Verification criteria

- [ ] Each notebook runs with "Restart & Run All" without errors
- [ ] Each notebook produces readable, labeled plots
- [ ] Comments explain the physics, not just the code
- [ ] Each notebook has a "Your turn" section with exercises

---

## Task 6: Document the Coil Mapping and JSON Schema (1 day)

### Objective

Produce reference documentation that students (and future developers) need.

### 6.1 Coil-to-helix mapping per magnet configuration

For each seeded magnet configuration, document:

| Icoil column | Part name | Part type | Geometry file | Material | Rpe (MPa) |
|-------------|-----------|-----------|---------------|----------|-----------|
| Icoil1 | H15101601 | helix | HL-31_H1.yaml | CuAg5.5 | 481 |
| Icoil2 | H15061703 | helix | HL-31_H2.yaml | CuAg5.5 | 482 |
| ... | ... | ... | ... | ... | ... |

### 6.2 JSON config schema documentation

Document the `config.json` structure with:
- All keys and their types
- Material property keys with units
- How the ordering maps to MagnetTools indices
- Examples for Insert, Bitter, and Hybrid configurations

### 6.3 Input/Output specifications per project

The contract between student code and MagnetDB integration:
- Project A: `compute_record_stats(df, site_config) → dict`
- Project B: `compute_stress_timeseries(df, mt_data, parts) → DataFrame`
- Project C: `process_record(df, config) → (DataFrame, metadata)`

---

## Task 7: Create Project-Specific README Files (0.5 day)

For each project, a short README in the notebook directory:

```
student_notebooks/
├── README.md                    # Overview, how to start
├── project_A/
│   ├── README.md               # Project A specific instructions
│   ├── 00_explore_data.ipynb
│   └── 01_your_work.ipynb      # Empty template with sections
├── project_B/
│   ├── README.md
│   ├── 00_magnettools_basics.ipynb
│   └── 01_your_work.ipynb
└── project_C/
    ├── README.md
    ├── 00_explore_timeseries.ipynb
    └── 01_your_work.ipynb
```

---

## Summary and Timeline

| Task | Effort | Depends on | Priority |
|------|--------|-----------|----------|
| 1. Audit python_magnetrun | 1.5–3.5 days | — | Critical |
| 2. Verify magnetsetup + magnettools bridge | 2–3 days | — | Critical (Project B) |
| 3. Curate seed dataset | 2–3 days | Tasks 1, 2 | Critical |
| 4. Build docker-compose-student.yml | 1.5–2 days | Task 3 | Critical |
| 5. Write starter notebooks | 1.5–2 days | Tasks 1–4 | High |
| 6. Document coil mapping + JSON schema | 1 day | Task 2 | High |
| 7. Project README files | 0.5 day | Tasks 5, 6 | Medium |

**Total: 10.5–15 working days** (~2.5–3 weeks)

**Execution order**:

1. **Week 1**: Tasks 1 and 2 in parallel (the two investigations) — use the verification prompt
2. **Week 2**: Tasks 3 and 6 (seed data + documentation, using results from week 1)
3. **Week 3**: Tasks 4, 5, and 7 (compose, notebooks, READMEs — integration week)

**Critical path**: Tasks 1 and 2 are the highest risk. Start there. Everything else is assembly.
