# Pre-Work: Preparing the Student Project Environment

## Purpose

This document details every preparation task required before M1 students can begin working on their projects. Each task includes a description of what needs to be done, open questions that may require investigation, verification criteria (how to know it's done), and estimated effort.

The guiding principle: **on day one, a student should be able to run a Docker container, open Jupyter, execute a starter notebook, and see a meaningful plot.** Every task below serves this goal.

---

## Task 1: Audit and Prepare python_magnetrun

### Context

`python_magnetrun` is referenced in MagnetDB documentation for retrieving operational data from the LNCMI control and monitoring website. It is used via CLI (`python_magnetrun.requests.cli`) and presumably provides parsing capabilities for record files. However, it is **not a submodule** of magnetdb — it lives in a separate repository and its current state, API surface, and standalone installability are uncertain.

Projects A and C depend on it directly. Project B can work without it (it only needs parsed DataFrames), but having it available makes the workflow cleaner.

### What needs to be investigated

**1.1 Repository and packaging state**

- Where is the repository? (GitHub/GitLab, public/private?)
- Does it have a `pyproject.toml` or `setup.py`?
- What build backend does it use? (Hatchling, Poetry, setuptools?)
- What are its declared dependencies? Does it pull in Django, requests, or anything heavy?
- Is it Python 3.11 compatible?

**Action**: Clone the repository. Attempt `pip install .` in a clean virtual environment (no Django, no MagnetDB). Record what happens.

**1.2 Core parsing API**

The critical question: is there a function that takes a file path (or file-like object) and returns a pandas DataFrame?

Investigate the module structure:

```
python_magnetrun/
├── __init__.py
├── requests/        # CLI for downloading data — students don't need this
│   └── cli.py
├── parsers/         # ? — this is what we need
│   ├── monitoring.py
│   ├── transient.py
│   └── ...
└── ...
```

What we need to find or create:

```python
# Desired API for students
from python_magnetrun import load_record

df = load_record("path/to/record.tsv")
# Returns a pandas DataFrame with columns: t, timestamp, Field, Icoil1, ..., Tin1, ...
```

If this doesn't exist, we need to know:

- How does MagnetDB currently parse records? (Answer: inline in `routes/api/records.py` `/visualize` endpoint, using raw pandas `read_csv`)
- Does python_magnetrun add value beyond this simple parsing? (Different file formats? Metadata extraction? Multiple record types?)
- Is the new record structure (multiple types: monitoring, transient, calibration) already implemented in python_magnetrun, or is it planned?

**1.3 Record file format documentation**

Currently the `/visualize` endpoint parses TSV files with whitespace separation, skipping the first row. The columns are defined in `record_visualization.py`:

```
Date, Time, Field, Tin1, Tin2, Tout, TAlimout, HP1, HP2, BP, 
Flow1, Flow2, Rpm1, Rpm2, Idcct1-4, Pmagnet, Ptot, teb, tsb, 
debitbrut, Q, t, timestamp, Icoil1-16, Ucoil1-16, DRcoil1-16, Tcal1-16
```

Questions:

- Are there other record formats beyond this monitoring format?
- Does the format vary by site or magnet configuration?
- Are the column names always the same, or do older records use different naming?
- Is the first-row skip always correct, or do some files have multi-line headers?
- What is the typical file size? (Affects whether we can bundle 10-20 records)

**Action**: Examine 10-15 actual record files from different sites and time periods. Document format variations.

### What needs to be built (if python_magnetrun is not ready)

If `python_magnetrun` cannot be installed standalone or doesn't provide a clean parsing API, create a minimal standalone parsing module:

```python
# student_helpers/record_parser.py
"""
Standalone record parser for student projects.
Extracted from MagnetDB /visualize endpoint logic.
"""

import pandas as pd
from datetime import datetime

# Column definitions with units
MONITORING_COLUMNS = {
    'Date': "acquisition date",
    'Time': "acquisition time",
    'Field': 'T',
    'Tin1': "°C",
    # ... (from record_visualization.py)
}

def load_monitoring_record(filepath: str) -> pd.DataFrame:
    """Load a monitoring record TSV file into a clean DataFrame.
    
    Args:
        filepath: Path to the TSV record file
        
    Returns:
        DataFrame with columns including 't' (seconds from start)
        and 'timestamp' (absolute datetime). Zero-only columns are removed.
    """
    time_format = "%Y.%m.%d %H:%M:%S"
    data = pd.read_csv(filepath, sep=r'\s+', skiprows=1)
    
    # Remove zero-only columns
    data = data.loc[:, (data != 0.0).any(axis=0)]
    
    # Compute time columns
    t0 = datetime.strptime(
        data['Date'].iloc[0] + " " + data['Time'].iloc[0], 
        time_format
    )
    data["t"] = data.apply(
        lambda row: (datetime.strptime(
            row.Date + " " + row.Time, time_format
        ) - t0).total_seconds(),
        axis=1
    )
    data["timestamp"] = data.apply(
        lambda row: datetime.strptime(
            row.Date + " " + row.Time, time_format
        ),
        axis=1
    )
    
    return data

def get_column_info() -> dict:
    """Return column name → unit mapping for monitoring records."""
    return MONITORING_COLUMNS.copy()

def get_record_metadata(df: pd.DataFrame) -> dict:
    """Extract metadata from a parsed record DataFrame."""
    return {
        'started_at': df['timestamp'].iloc[0].isoformat(),
        'ended_at': df['timestamp'].iloc[-1].isoformat(),
        'duration_seconds': float(df['t'].iloc[-1]),
        'num_points': len(df),
        'sampling_period_seconds': float(df['t'].diff().median()),
        'available_columns': list(df.columns),
        'non_zero_coils': [
            col for col in df.columns 
            if col.startswith('Icoil') and df[col].abs().max() > 0
        ],
    }
```

This fallback module is also useful pedagogically: students can see exactly how the parsing works.

### Verification criteria

- [ ] `python_magnetrun` installs in a clean Python 3.11 venv without Django
- [ ] OR: `student_helpers/record_parser.py` loads all sample records correctly
- [ ] Parsing produces a DataFrame with `t`, `timestamp`, and physical columns
- [ ] Column units are documented
- [ ] At least two record types (monitoring + one other) can be parsed, OR scope is limited to monitoring only

### Estimated effort

- Audit python_magnetrun: 1 day
- Fix/package if needed: 1–2 days
- Write fallback parser if needed: 0.5 day
- **Total: 1.5–3.5 days**

---

## Task 2: Extract the Geometry → MagnetTools Bridge

### Context

MagnetTools operates on C++ objects (Tubes, Helices, BMagnets, UMagnets, OHelices, Shims) exposed via Python bindings. MagnetDB constructs these objects somewhere in its pipeline — the `compute_bmap_chart.py` and `compute_stress_map_chart.py` actions receive them as a tuple `(Tubes, Helices, OHelices, BMagnets, UMagnets, Shims) = data`.

Students need a function: **given a magnet geometry YAML file (and associated helix/ring YAML files), produce MagnetTools objects they can call `mt.MagneticField()` and `bmap.getHoop()` on.**

### What needs to be investigated

**2.1 How does MagnetDB currently build the MagnetTools tuple?**

Trace the code path:

- The frontend calls an API endpoint (e.g., `/api/magnets/{id}/bmap`)
- The endpoint loads the magnet model, builds a configuration, and calls `compute_bmap_chart(data, ...)`
- But where is `data` constructed? There must be a function like `load_magnetcfg(magnet)` or similar that:
  1. Reads geometry YAML files via python_magnetgeo
  2. Converts them to MagnetTools objects
  3. Returns the tuple

**Action**: Search the codebase for:

```bash
grep -r "Tubes" python_magnetdb/actions/ python_magnetdb/routes/
grep -r "load_mag" python_magnetdb/
grep -r "mt.Tube\|mt.Helix\|mt.Bitter" python_magnetdb/
```

Identify the function that performs this conversion. It may be in:

- `python_magnetdb/actions/` — a dedicated action
- `python_magnetsetup/` — the setup module
- `magnettools` itself — a loader function

**2.2 What is the minimal input?**

For an Insert magnet (the most common type), the MagnetTools construction likely needs:

- Per-helix: inner/outer radius, height, number of turns, pitch, conductor dimensions, material conductivity
- Per-ring: inner/outer radius, height
- Assembly: bore dimensions, helix ordering

This information is in the geometry YAML files. The question is whether MagnetTools has a direct YAML loader or whether the conversion goes through python_magnetgeo objects first.

**2.3 Does MagnetTools have a `load_cfg` function?**

Check the MagnetTools Python API:

```python
import magnettools.magnettools as mt
dir(mt)
# Look for: load_cfg, load_config, from_yaml, from_json, ...
```

Also check if there's a higher-level loader:

```python
import magnettools
dir(magnettools)
# Look for any module beyond magnettools.magnettools and magnettools.Bmap
```

**2.4 What is the python_magnetsetup role?**

`python_magnetsetup` is a submodule with dependencies on `python_magnetgeo`, `chevron`, `fabric`, `Pint`. It seems oriented toward simulation setup (templating, remote execution). Does it contain geometry → MagnetTools conversion logic?

Check:

```bash
grep -r "Tube\|Helix\|magnettools" python_magnetsetup/
```

### What needs to be built

A standalone bridge function, documented and tested:

```python
# student_helpers/magnettools_bridge.py
"""
Bridge between python_magnetgeo YAML files and MagnetTools objects.

Usage:
    from magnettools_bridge import load_insert_from_yaml
    
    data = load_insert_from_yaml("path/to/HL-31.yaml", "path/to/geometries/")
    (Tubes, Helices, OHelices, BMagnets, UMagnets, Shims) = data
    
    # Now use MagnetTools
    import magnettools.magnettools as mt
    Bz0 = mt.MagneticField(Tubes, Helices, BMagnets, UMagnets, 0, 0)[1]
"""

import magnettools.magnettools as mt
import python_magnetgeo as pmg

def load_insert_from_yaml(
    insert_yaml_path: str,
    geometries_dir: str,
    materials: dict = None
) -> tuple:
    """Load an Insert magnet geometry and return MagnetTools objects.
    
    Args:
        insert_yaml_path: Path to the Insert YAML file (e.g., HL-31.yaml)
        geometries_dir: Directory containing individual helix/ring YAML files
        materials: Optional dict of material properties keyed by part name.
                   If None, uses default values from the YAML files.
    
    Returns:
        Tuple of (Tubes, Helices, OHelices, BMagnets, UMagnets, Shims)
    """
    # Step 1: Load geometry with python_magnetgeo
    insert = pmg.load(insert_yaml_path)
    
    # Step 2: Convert to MagnetTools objects
    # ... THIS IS THE UNKNOWN PART ...
    
    # Step 3: Return the standard tuple
    return (Tubes, Helices, OHelices, BMagnets, UMagnets, Shims)


def compute_hoop_stress(
    data: tuple,
    currents: list[float],
    magnet_type: str = "H"
) -> dict:
    """Compute hoop stress for all helices at given currents.
    
    Args:
        data: MagnetTools tuple from load_insert_from_yaml()
        currents: List of currents [I_helix, I_bitter, I_supra]
        magnet_type: "H" for helix, "B" for bitter
        
    Returns:
        dict with keys:
            'helix_numbers': list of helix indices
            'hoop_stress_MPa': list of hoop stress values
            'currents_used': the actual currents set
            'Bz0': central field in Tesla
    """
    import magnettools.Bmap as bmap
    
    (Tubes, Helices, OHelices, BMagnets, UMagnets, Shims) = data
    
    # Set currents
    vcurrents = mt.DoubleVector(currents)
    mt.set_currents(Tubes, Helices, BMagnets, UMagnets, OHelices, vcurrents)
    
    # Compute field
    Bz0 = mt.MagneticField(Tubes, Helices, BMagnets, UMagnets, 0, 0)[1]
    
    # Compute hoop stress
    mdata = {"H": Helices, "B": BMagnets, "S": UMagnets}
    Magnets = mdata[magnet_type]
    (headers, values) = bmap.getHoop(
        Magnets, Tubes, Helices, BMagnets, UMagnets, magnet_type
    )
    
    import pandas as pd
    df = pd.DataFrame.from_records(values)
    df.columns = headers
    
    return {
        'helix_numbers': df['num'].tolist(),
        'hoop_stress_MPa': df['Hoop[MPa]'].tolist(),
        'currents_used': currents,
        'Bz0': Bz0,
    }
```

The critical unknown is the body of `load_insert_from_yaml()`. This is the piece you need to extract from the existing codebase or write from scratch based on MagnetTools API knowledge.

### Verification criteria

- [ ] `load_insert_from_yaml("HL-31.yaml", "geometries/")` returns a valid MagnetTools tuple
- [ ] `mt.MagneticField(Tubes, Helices, BMagnets, UMagnets, 0, 0)` returns a non-zero field
- [ ] `compute_hoop_stress(data, [24000.0])` returns sensible hoop stress values
- [ ] The function works with at least 2 different magnet geometries (e.g., HL-31 and H12-phi50)
- [ ] No Django imports anywhere in the bridge module

### Estimated effort

- Trace the code path in MagnetDB: 0.5 day
- Investigate MagnetTools Python API: 0.5 day
- Write and test the bridge function: 1–2 days
- **Total: 2–3 days**

---

## Task 3: Curate the Sample Dataset

### Context

Students cannot access the sshfs operational data directory or the production MagnetDB database. They need a self-contained data package with representative records, geometry files, and material properties.

### Data selection criteria

**3.1 Record files**

Select 15–20 records covering:

- At least 2 different sites/magnet configurations (e.g., M9_M19061901 and M9_M20022001 or M10_M19071101)
- Different operating conditions: nominal steady-state, ramp-up, ramp-down, high-field runs
- At least one record with a thermal anomaly or current instability (for anomaly detection work in Project C)
- A range of durations: short runs (minutes), long runs (hours)
- Records from different time periods (for lifetime analysis)

**Size estimate**: A typical monitoring record with 500 data points and ~70 columns is roughly 50–100 KB as TSV. 20 records ≈ 1–2 MB total. Very manageable.

**3.2 Geometry YAML files**

For each magnet configuration used in the selected records, provide:

- The top-level Insert YAML (e.g., `HL-31.yaml`)
- All referenced per-helix YAML files (e.g., `HL-31_H1.yaml` through `HL-31_H14.yaml`)
- All referenced per-ring YAML files
- All referenced current lead YAML files (if applicable)

These are already in `python_magnetsetup/data/geometries/`. Check that they are self-consistent and up to date.

**3.3 Material properties**

Create a standalone JSON file with material properties for all parts referenced in the sample records:

```json
{
  "MA15101601": {
    "name": "MA15101601",
    "description": "H1",
    "nuance": "CuAg5.5",
    "t_ref": 293,
    "volumic_mass": 9000,
    "specific_heat": 380,
    "alpha": 3.6e-3,
    "electrical_conductivity": 52.4e6,
    "thermal_conductivity": 380,
    "young": 117e9,
    "poisson": 0.33,
    "expansion_coefficient": 18e-6,
    "rpe": 481
  }
}
```

This can be extracted from the seed files (e.g., `seed-M19061901.py`).

**3.4 Configuration files**

For each site represented in the sample records, create a standalone JSON describing the hierarchy:

```json
{
  "site": "M9_M19061901",
  "magnet": {
    "name": "M19061901",
    "type": "insert",
    "geometry_file": "HL-31.yaml",
    "inner_bore": 18.8,
    "outer_bore": 31.2,
    "parts": [
      {
        "name": "H15101601",
        "type": "helix",
        "geometry_file": "HL-31_H1.yaml",
        "material": "MA15101601",
        "coil_index": 1
      },
      {
        "name": "H15061703",
        "type": "helix",
        "geometry_file": "HL-31_H2.yaml",
        "material": "MA15061703",
        "coil_index": 2
      }
    ]
  },
  "records": [
    "M9_M19061901_2023-03-15.tsv",
    "M9_M19061901_2023-06-22.tsv"
  ]
}
```

The **`coil_index` mapping** is critical: it tells the student which `Icoil_N` column in the record corresponds to which physical helix. This mapping may not be explicit anywhere in the current codebase — it may be implicit in the ordering of helices in the geometry YAML. You need to document it.

### Anonymization considerations

**What to check with hierarchy/colleagues**:

- Can TSV operational records (currents, temperatures, fields, pressures) be shared with M1 students under NDA or university internship agreement?
- Should experimenter names be stripped from records? (If the record files contain experimenter info, replace with pseudonyms)
- Are magnet geometry YAML files shareable? (They describe dimensions, not proprietary manufacturing processes — likely fine)
- Are material properties (conductivity, Rpe, nuance) shareable? (These are typically published in the material supplier datasheets)

**Recommendation**: Most of this data is scientific/engineering data, not proprietary. An internship confidentiality clause (standard in French M1 conventions de stage) should be sufficient. But verify with your hierarchy for any export control or IP concerns.

### What to build

**3.5 Data README**

A comprehensive README explaining the physics context, data format, column meanings, and units. This is the single most important document for student onboarding:

```markdown
# Sample Operational Data — LNCMI High-Field Magnets

## Physical context
LNCMI operates resistive high-field magnets producing fields up to 36 T...
Water-cooled polyhelix insert magnets...

## Record format
Each record file is a TSV (tab-separated values) file capturing
one experimental session...

## Column reference
| Column | Unit | Description |
|--------|------|-------------|
| Field  | T    | Central magnetic field measured by Hall probe |
| Icoil1 | A   | Current in power supply 1 (feeds helix H1) |
| ...    |      |             |

## Coil-to-helix mapping
For the HL-31 insert geometry:
| Icoil column | Helix part | Geometry file |
|-------------|------------|---------------|
| Icoil1      | H15101601  | HL-31_H1.yaml |
| Icoil2      | H15061703  | HL-31_H2.yaml |
| ...         |            |               |

## Magnet configurations included
...
```

### Verification criteria

- [ ] All 15–20 record files parse correctly with the record parser
- [ ] All geometry YAML files load correctly with `python_magnetgeo`
- [ ] All materials referenced in configs exist in `materials.json`
- [ ] Coil-to-helix mapping is documented and verified for each site configuration
- [ ] Data README is complete and reviewed by someone unfamiliar with the system
- [ ] No confidential or personal information in the dataset

### Estimated effort

- Select and copy records: 0.5 day
- Extract materials and configs from seeds: 0.5 day
- Investigate and document coil-to-helix mapping: 0.5–1 day
- Write data README: 0.5 day
- Verify anonymization: 0.5 day
- **Total: 2.5–3 days**

---

## Task 4: Build and Test the Student Docker Image

### Context

MagnetTools requires Linux x86_64 + Python 3.11 + system libraries. The Docker image must provide a complete, reproducible environment with Jupyter access.

### Image design

Base: `trophime/magnettools:bookworm-poetry-2.2.1` (already used for MagnetDB)

Additional requirements:

- MagnetTools Debian package (`magnettools`, `libmagnettools-dev`)
- Python scientific stack: pandas, numpy, scipy, matplotlib, pyarrow, seaborn
- Jupyter: jupyterlab
- python_magnetgeo (installed from source)
- python_magnetrun (if available, otherwise the fallback parser)
- magnettools Python bindings (the `.whl` file)
- Student helper modules (bridge, parser)
- Sample data

### Open questions

**4.1 Base image availability**

- Is `trophime/magnettools:bookworm-poetry-2.2.1` published on Docker Hub or a private registry?
- Can students pull it, or do they need access credentials?
- If private: should we build a self-contained image from Debian bookworm instead?

**4.2 MagnetTools Debian package availability**

- The Dockerfile installs `magnettools` and `libmagnettools-dev` via apt. Which repository are these in?
- Is the repository accessible from outside LNCMI? If not, include the `.deb` files in the Docker build context.

**4.3 Python version pinning**

- The base image provides Python 3.11. The magnettools wheel is `cp311`. This must match exactly.
- Verify: `python3 --version` in the base image returns 3.11.x

**4.4 Student machine requirements**

- Docker Desktop on macOS (Apple Silicon): x86_emulation via Rosetta works but is slow. Test performance.
- Docker Desktop on Windows: WSL2 backend required. Verify it works.
- Alternative: provide a pre-built VM image (VirtualBox) as fallback.
- Or: host a JupyterHub instance at LNCMI that students can access remotely.

**Recommendation**: Hosting a JupyterHub (even a simple `docker compose` with JupyterHub + the student image) at LNCMI would eliminate all student-side installation issues. This is worth the setup effort if more than 2 students are involved.

### Dockerfile

```dockerfile
FROM trophime/magnettools:bookworm-poetry-2.2.1

USER root

# System dependencies
RUN apt-get update && apt-get install -y \
    magnettools libmagnettools-dev \
    && rm -rf /var/lib/apt/lists/*

ENV LD_LIBRARY_PATH="/usr/lib/x86_64-linux-gnu/MagnetTools/:$LD_LIBRARY_PATH"

# Python scientific stack (no Poetry — keep it simple for students)
RUN pip install --break-system-packages \
    pandas>=2.2 pyarrow>=17.0 numpy>=2.0 scipy>=1.14 \
    matplotlib>=3.8 seaborn \
    jupyterlab ipywidgets \
    pyyaml pint tabulate scikit-learn

# MagnetTools Python bindings
COPY magnettools-1.1.0-cp311-cp311-linux_x86_64.whl /tmp/
RUN pip install --break-system-packages /tmp/magnettools-1.1.0-cp311-cp311-linux_x86_64.whl \
    && rm /tmp/*.whl

# python_magnetgeo
COPY python_magnetgeo/ /opt/python_magnetgeo/
RUN pip install --break-system-packages /opt/python_magnetgeo/

# python_magnetrun (if available)
# COPY python_magnetrun/ /opt/python_magnetrun/
# RUN pip install --break-system-packages /opt/python_magnetrun/

# Student helpers and sample data
COPY student_helpers/ /opt/student_helpers/
RUN pip install --break-system-packages /opt/student_helpers/
COPY sample_data/ /home/student/sample_data/
COPY notebooks/ /home/student/notebooks/

# Student user
ARG STUDENT_UID=1000
ARG STUDENT_GID=1000
RUN groupadd -g ${STUDENT_GID} student || true \
    && useradd -m -u ${STUDENT_UID} -g ${STUDENT_GID} student || true \
    && chown -R student:student /home/student

USER student
WORKDIR /home/student
EXPOSE 8888

CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser"]
```

With a `docker-compose.yml` for easy startup:

```yaml
services:
  jupyter:
    build: .
    ports:
      - "8888:8888"
    volumes:
      - ./student_work:/home/student/work  # persistent workspace
```

### Verification criteria

- [ ] Image builds successfully
- [ ] `docker compose up` starts Jupyter, accessible at localhost:8888
- [ ] `import magnettools.magnettools as mt` works
- [ ] `import python_magnetgeo as pmg` works
- [ ] `import student_helpers.record_parser as rp` works
- [ ] Starter notebooks run without errors
- [ ] Image tested on macOS (Apple Silicon via Rosetta) if students may use Macs
- [ ] Image size is reasonable (< 5 GB)

### Estimated effort

- Write Dockerfile and docker-compose: 0.5 day
- Debug build issues: 0.5–1 day
- Test on different platforms: 0.5 day
- **Total: 1.5–2 days**

---

## Task 5: Write Starter Jupyter Notebooks

### Context

Starter notebooks are the primary onboarding tool. They must be self-contained, well-commented, and run without errors in the Docker environment.

### Notebook 00: Load and Explore a Record

**Purpose**: Familiarize students with the data format and basic pandas operations.

**Contents**:

1. Load a single record file using the parser
2. Display the DataFrame shape, columns, dtypes
3. Show the column reference table with units
4. Plot Field vs t (basic time series)
5. Plot multiple coil currents on the same axes
6. Plot temperature channels
7. Compute basic statistics (min, max, mean, std) per column
8. Compute the sampling period and check for irregularities
9. Show the record metadata (duration, start/end time, active coils)

**Estimated writing time**: 2–3 hours

### Notebook 01: MagnetTools Basics

**Purpose**: Show students how to use MagnetTools to compute physical quantities from geometry.

**Contents**:

1. Load a magnet geometry YAML with python_magnetgeo
2. Display the geometry structure (list helices, rings, dimensions)
3. Convert to MagnetTools objects using the bridge function
4. Set nominal currents
5. Compute Bz at the center (0, 0)
6. Compute Bz along the z-axis (1D profile)
7. Plot the field profile
8. Compute hoop stress for all helices
9. Plot hoop stress vs helix number
10. Compare with material Rpe (elastic limit)

**Estimated writing time**: 3–4 hours

### Notebook 02: Multi-Record Analysis

**Purpose**: Show students how to work with multiple records and extract cross-record information.

**Contents**:

1. Load the site configuration JSON
2. Load all records for a given site
3. Extract per-record summaries: max field, max current, duration, max temperature
4. Plot the evolution of max field across records (rudimentary lifetime view)
5. Show how operating conditions vary between records
6. Demonstrate the concept of stitching: create a long-term time series from per-record max values
7. Introduce the coil-to-helix mapping: for a specific part, extract "its" current channel across all records
8. Discuss what statistics would be meaningful at site, magnet, and part level

**Estimated writing time**: 3–4 hours

### Verification criteria

- [ ] Each notebook runs cell-by-cell without errors in the Docker image
- [ ] Each notebook runs top-to-bottom with "Restart & Run All" without errors
- [ ] Plots are readable and labeled (axis labels, units, legends)
- [ ] Comments explain the physics, not just the code
- [ ] Each notebook has a "Your turn" section with exercises/questions

### Estimated effort

- Write 3 notebooks: 1–1.5 days
- Test in Docker: 0.5 day
- **Total: 1.5–2 days**

---

## Task 6: Package the Student Helpers Module

### Context

The bridge function, record parser, and any other utility code should be packaged as an installable Python module so students can import it cleanly.

### Structure

```
student_helpers/
├── pyproject.toml
├── README.md
├── student_helpers/
│   ├── __init__.py
│   ├── record_parser.py        # Task 1 deliverable
│   ├── magnettools_bridge.py   # Task 2 deliverable
│   ├── visualization.py        # Common plotting helpers
│   └── config_loader.py        # Load site/magnet config JSON files
└── tests/
    ├── test_record_parser.py
    ├── test_bridge.py
    └── conftest.py              # pytest fixtures with sample data paths
```

With a minimal `pyproject.toml`:

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "student-helpers"
version = "0.1.0"
dependencies = ["pandas", "numpy", "pyyaml"]

[project.optional-dependencies]
magnettools = []  # magnettools must be installed separately (system package)
```

### Verification criteria

- [ ] `pip install .` works in the Docker image
- [ ] `from student_helpers import record_parser, magnettools_bridge` works
- [ ] `pytest tests/` passes (at least for record_parser; bridge tests require MagnetTools)

### Estimated effort

- Package structure: 0.5 day
- Write tests: 0.5 day
- **Total: 1 day**

---

## Task 7: Create Project-Specific Input/Output Specifications

### Context

Each project needs a clear "contract": what the student's module receives as input and what it must produce as output. This is what you will later integrate into MagnetDB.

### For Project A (Statistical Characterization)

**Input**: 
```python
def compute_record_stats(
    df: pd.DataFrame,           # parsed record (from record_parser)
    site_config: dict,          # site configuration (from config_loader)
    column_info: dict           # column name → unit mapping
) -> dict:
```

**Output**: A nested dict matching the RecordStats.data JSON schema defined in the roadmap.

### For Project B (Hoop Stress)

**Input**:
```python
def compute_stress_timeseries(
    df: pd.DataFrame,           # parsed record
    mt_data: tuple,             # MagnetTools objects (from bridge)
    parts: list[dict],          # part info: name, coil_index, material (rpe)
) -> pd.DataFrame:
```

**Output**: A DataFrame with columns `t`, `hoop_{part_name}`, `ratio_rpe_{part_name}` for each part.

### For Project C (Time Series Processing)

**Input**:
```python
def process_record(
    df: pd.DataFrame,           # raw parsed record
    target_points: int = 1000,  # downsampling target
    algorithm: str = 'lttb'     # downsampling algorithm
) -> pd.DataFrame:

def stitch_records(
    records: list[pd.DataFrame], # list of parsed records, chronologically ordered
    field: str = 'Field',        # column to stitch
    aggregation: str = 'max'     # how to summarize each record
) -> pd.DataFrame:
```

**Output**: Processed DataFrames ready for storage as Parquet.

**Action**: Write these specifications as part of each project description. Include example inputs and expected outputs.

### Estimated effort

- Write I/O specs for 3 projects: 0.5 day
- Create example input/output fixtures: 0.5 day
- **Total: 1 day**

---

## Summary and Timeline

| Task | Effort | Depends on | Priority |
|------|--------|-----------|----------|
| 1. Audit python_magnetrun | 1.5–3.5 days | — | Critical |
| 2. Geometry → MagnetTools bridge | 2–3 days | — | Critical (for Project B) |
| 3. Curate sample dataset | 2.5–3 days | Task 1 (to verify records parse) | Critical |
| 4. Build Docker image | 1.5–2 days | Tasks 1, 2, 3 | Critical |
| 5. Write starter notebooks | 1.5–2 days | Tasks 1, 2, 3, 4 | High |
| 6. Package student_helpers | 1 day | Tasks 1, 2 | High |
| 7. I/O specifications | 1 day | — | High |

**Total: 11.5–15.5 working days** (~3 weeks)

**Recommended execution order**:

1. Week 1: Tasks 1 and 2 in parallel (the two investigations)
2. Week 2: Tasks 3 and 6 (dataset curation + packaging, using results from week 1)
3. Week 3: Tasks 4, 5, and 7 (Docker image, notebooks, specs — integration week)

**Critical path**: Task 2 (MagnetTools bridge) is the highest-risk item. If the code path from YAML → MagnetTools objects turns out to be deeply entangled with Django or MagnetDB internals, it may take longer to extract. Start this investigation first.
