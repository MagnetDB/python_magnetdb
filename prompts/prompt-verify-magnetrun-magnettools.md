# Prompt: Verify python_magnetrun and python_magnettools with JSON Site/Magnet/Part Data

## Objective

Verify and document that `python_magnetrun` and `python3-magnettools` (via `python_magnetsetup`) can operate **outside MagnetDB** using JSON structures that describe site/magnet/part configurations. The goal is a standalone, Django-free workflow that:

1. Parses operational record files into pandas DataFrames using `python_magnetrun`
2. Loads magnet geometry + materials from JSON config + YAML files using `python_magnetsetup`
3. Creates MagnetTools objects and computes field and hoop stress
4. Combines both: given a record and a magnet config, compute hoop stress time series

This is critical preparation for student projects and for decoupling computation from the web platform.

---

## Context: The Existing Code Path in MagnetDB

The current MagnetDB code path from database to MagnetTools objects is:

```
Django Model (Magnet)
    │
    ├── generate_magnet_config(magnet_id)        [generate_simulation_config.py]
    │   → JSON dict: {"geom": "HL-31.yaml", "Helix": [{...}], "Ring": [{...}]}
    │
    ├── generate_magnet_directory(magnet_id, dir) [generate_magnet_directory.py]
    │   → writes YAML files to dir/data/geometries/
    │   → writes config.json to dir/
    │
    ├── appenv(yaml_repo=..., ...)               [python_magnetsetup.config]
    │   → environment object pointing to file locations
    │
    └── magnet_setup(env, config_data, debug)    [python_magnetsetup.ana]
        → returns (Tubes, Helices, OHelices, BMagnets, UMagnets, Shims)
```

For sites, the equivalent path uses `generate_site_config()` → `msite_setup()`.

The JSON config structure produced by `generate_magnet_config()` looks like:

```json
{
  "geom": "M19061901.yaml",
  "Helix": [
    {
      "geom": "H15101601.yaml",
      "material": {
        "Tref": 293,
        "VolumicMass": 9000,
        "alpha": 0.0036,
        "ElectricalConductivity": 52400000.0,
        "MagnetPermeability": 1,
        "Poisson": 0.33,
        "Rpe": 481,
        "SpecificHeat": 380,
        "ThermalConductivity": 380,
        "Young": 117000000000.0,
        "CoefDilatation": 1.8e-05,
        "nuance": "CuAg5.5"
      },
      "insulator": {
        "Tref": 293,
        "VolumicMass": 2000,
        "...": "..."
      }
    }
  ],
  "Ring": [
    {
      "geom": "M19061901_R1.yaml",
      "material": {"...": "..."},
      "insulator": {"...": "..."}
    }
  ]
}
```

**The key insight**: if we can produce this JSON config + the YAML geometry files on disk, we can call `magnet_setup()` without Django.

---

## Part 1: Verify python_magnetrun

### Step 1.1 — Check repository and installation

```bash
# Clone the repository (adjust URL as needed)
git clone <python_magnetrun_repo_url>
cd python_magnetrun

# Check packaging
cat pyproject.toml   # or setup.py, setup.cfg
ls -la

# Attempt standalone install in a clean venv (no Django)
python3 -m venv /tmp/test_magnetrun
source /tmp/test_magnetrun/bin/activate
pip install .

# Check what was installed
pip list | grep magnet
python -c "import python_magnetrun; print(dir(python_magnetrun))"
```

**Document**:
- [ ] Does it install without errors?
- [ ] What dependencies does it pull in? (list them)
- [ ] Does it import Django or MagnetDB? (it must not)
- [ ] What is the module structure? (`find python_magnetrun -name "*.py" | head -30`)

### Step 1.2 — Discover the parsing API

```python
import python_magnetrun

# Explore the module
print(dir(python_magnetrun))

# Look for parsing functions
# Candidates: load, parse, read, load_record, MagnetRun, ...
# Check submodules
import pkgutil
for importer, modname, ispkg in pkgutil.walk_packages(python_magnetrun.__path__):
    print(f"  {'[pkg]' if ispkg else '     '} {modname}")
```

**What we need to find or establish**:

A function with this kind of signature:

```python
# Option A: file-based
df = python_magnetrun.load_record("path/to/record.tsv")

# Option B: class-based
run = python_magnetrun.MagnetRun("path/to/record.tsv")
df = run.to_dataframe()

# Option C: format-specific
from python_magnetrun.parsers import MonitoringParser
parser = MonitoringParser()
df = parser.parse("path/to/record.tsv")
```

**Document**:
- [ ] What is the actual API for parsing a record file?
- [ ] Does it return a pandas DataFrame?
- [ ] What record types/formats does it support?
- [ ] Does it handle the timestamp computation (Date + Time → t in seconds)?
- [ ] Does it clean/filter columns (remove zero-only columns)?
- [ ] Does it extract metadata (duration, sampling rate, etc.)?

### Step 1.3 — Test with a real record file

```python
# Use a record file from data/mrecords/ or from the sshfs directory
import python_magnetrun
import pandas as pd

# Try the API discovered in Step 1.2
# Adjust the call based on what you found
df = python_magnetrun.load_record("/data/mrecords/some_record.tsv")

# Verify the output
print(f"Shape: {df.shape}")
print(f"Columns: {list(df.columns)}")
print(f"Dtypes:\n{df.dtypes}")
print(f"\nFirst 3 rows:\n{df.head(3)}")
print(f"\nTime range: {df['t'].iloc[0]} to {df['t'].iloc[-1]} seconds")
print(f"Sampling period: {df['t'].diff().median():.2f} s")

# Check that key columns are present
required_columns = ['t', 'Field', 'Icoil1']
for col in required_columns:
    assert col in df.columns, f"Missing column: {col}"
    
print("\n✓ python_magnetrun record parsing works")
```

### Step 1.4 — Test with multiple record types (if applicable)

If `python_magnetrun` supports multiple record types:

```python
# Test each type
for record_file in [
    "monitoring_record.tsv",
    "transient_record.tsv",   # if available
    "calibration_record.tsv", # if available
]:
    try:
        df = python_magnetrun.load_record(f"/data/mrecords/{record_file}")
        print(f"✓ {record_file}: {df.shape[0]} rows, {df.shape[1]} columns")
    except Exception as e:
        print(f"✗ {record_file}: {e}")
```

### Step 1.5 — Fallback: if python_magnetrun is not ready

If `python_magnetrun` cannot be used standalone, create a minimal parser based on the existing MagnetDB `/visualize` endpoint logic:

```python
# minimal_record_parser.py
"""
Minimal record parser extracted from MagnetDB.
Fallback for when python_magnetrun is not available standalone.
"""
import pandas as pd
from datetime import datetime

def load_monitoring_record(filepath: str) -> pd.DataFrame:
    """Parse a monitoring record TSV file.
    
    This replicates the parsing logic from
    python_magnetdb/routes/api/records.py /visualize endpoint.
    """
    time_format = "%Y.%m.%d %H:%M:%S"
    data = pd.read_csv(filepath, sep=r'\s+', skiprows=1)
    data = data.loc[:, (data != 0.0).any(axis=0)]
    
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
```

**Document**:
- [ ] Is the fallback needed, or does python_magnetrun work?
- [ ] If fallback is used, which record types does it NOT handle?

---

## Part 2: Verify python_magnetsetup + MagnetTools with JSON Config

### Step 2.1 — Prepare a test directory with geometry files

You need a directory with the same structure that `generate_magnet_directory()` produces. Either:

**Option A**: Extract from the running MagnetDB container:

```bash
# Inside the magnetdb-api container
docker exec -it magnetdb-api bash

# Use the existing generate_magnet_directory to produce a test dataset
python3 -c "
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'python_magnetdb.settings'
import django; django.setup()

from python_magnetdb.actions.generate_magnet_directory import generate_magnet_directory
config = generate_magnet_directory(1, '/tmp/test_magnet')  # magnet_id=1
import json
print(json.dumps(config, indent=2))
"

# Copy the generated directory out of the container
docker cp magnetdb-api:/tmp/test_magnet ./test_magnet_data/
```

**Option B**: Build manually from seed data and geometry files:

```bash
# Create the directory structure
mkdir -p test_magnet_data/data/geometries
mkdir -p test_magnet_data/data/cad

# Copy geometry YAML files from python_magnetsetup/data/geometries/
cp python_magnetsetup/data/geometries/HL-31.yaml test_magnet_data/data/geometries/
cp python_magnetsetup/data/geometries/HL-31_H*.yaml test_magnet_data/data/geometries/
cp python_magnetsetup/data/geometries/Ring-*.yaml test_magnet_data/data/geometries/
```

Then create `test_magnet_data/config.json` manually, matching the structure from `generate_magnet_config()`:

```python
import json

config = {
    "geom": "HL-31.yaml",  # or the actual Insert geometry name
    "Helix": [
        {
            "geom": "HL-31_H1.yaml",
            "material": {
                "Tref": 293,
                "VolumicMass": 9000,
                "alpha": 0.0036,
                "ElectricalConductivity": 52.4e6,
                "MagnetPermeability": 1,
                "Poisson": 0.33,
                "Rpe": 481,
                "SpecificHeat": 380,
                "ThermalConductivity": 380,
                "Young": 117e9,
                "CoefDilatation": 18e-6,
                "nuance": "CuAg5.5"
            },
            "insulator": {
                "Tref": 293,
                "VolumicMass": 2000,
                "alpha": 0.0,
                "ElectricalConductivity": 0.0,
                "MagnetPermeability": 1,
                "Poisson": 0.3,
                "Rpe": 0,
                "SpecificHeat": 1000,
                "ThermalConductivity": 0.2,
                "Young": 3e9,
                "CoefDilatation": 0.0,
                "nuance": "Isolant"
            }
        },
        # ... add entries for H2, H3, ... H14
    ],
    "Ring": [
        {
            "geom": "Ring-H1H2.yaml",
            "material": {
                # ... ring material properties
            },
            "insulator": {
                # ... same insulator as above
            }
        },
        # ... add entries for all rings
    ]
}

with open("test_magnet_data/config.json", "w") as f:
    json.dump(config, f, indent=2)
```

**Document**:
- [ ] Which option was used (A or B)?
- [ ] List all geometry YAML files present
- [ ] Is the config.json complete (all helices, all rings, correct material values)?

### Step 2.2 — Call magnet_setup() without Django

This is the critical test. Can we go from JSON config + YAML files → MagnetTools objects?

```python
import json
import os

# These imports must work WITHOUT Django
from python_magnetsetup.ana import magnet_setup, msite_setup
from python_magnetsetup.config import appenv

# Point to the test directory
test_dir = "test_magnet_data"
data_dir = f"{test_dir}/data"

# Create the environment (same as object_geometries.py does)
env = appenv(
    envfile=None,
    url_api=data_dir,
    yaml_repo=f"{data_dir}/geometries",
    cad_repo=f"{data_dir}/cad",
    mesh_repo=data_dir,
    simage_repo=data_dir,
    mrecord_repo=data_dir,
    optim_repo=data_dir,
)

# Load the config
with open(f"{test_dir}/config.json") as f:
    config_data = json.load(f)

print(f"Config keys: {list(config_data.keys())}")
print(f"Number of helices: {len(config_data.get('Helix', []))}")
print(f"Number of rings: {len(config_data.get('Ring', []))}")

# THE CRITICAL CALL: convert JSON config → MagnetTools objects
data = magnet_setup(env, config_data, True)  # True = debug mode

(Tubes, Helices, OHelices, BMagnets, UMagnets, Shims) = data
print(f"\n✓ magnet_setup succeeded")
print(f"  Tubes:    {len(Tubes)}")
print(f"  Helices:  {len(Helices)}")
print(f"  OHelices: {len(OHelices)}")
print(f"  BMagnets: {len(BMagnets)}")
print(f"  UMagnets: {len(UMagnets)}")
print(f"  Shims:    {len(Shims)}")
```

**If this fails**, investigate:
- Does `python_magnetsetup` import Django? Check with `grep -r "django" python_magnetsetup/`
- Does `appenv` require an envfile? Can it work with `envfile=None`?
- Does `magnet_setup` need fields beyond what `config_data` provides?
- Are there missing YAML files that the geometry references?
- Check the error traceback carefully — it will indicate which module or function is the blocker

**Document**:
- [ ] Does `magnet_setup()` return successfully?
- [ ] If not, what is the error? What is missing?
- [ ] Does `python_magnetsetup` have any Django dependency?
- [ ] What does `appenv` actually need? (inspect its source)

### Step 2.3 — Compute magnetic field

```python
import magnettools.magnettools as mt

(Tubes, Helices, OHelices, BMagnets, UMagnets, Shims) = data

# Get default currents
icurrents = mt.get_currents(Tubes, Helices, BMagnets, UMagnets)
print(f"Default currents: {[c for c in icurrents]}")

# Compute central field
Bz0 = mt.MagneticField(Tubes, Helices, BMagnets, UMagnets, 0, 0)[1]
print(f"Central field Bz(0,0) = {Bz0:.4f} T")

# Set a specific current (e.g., 24000 A for helix supply)
vcurrents = list(icurrents)
vcurrents[0] = 24000.0  # helix current
currents = mt.DoubleVector(vcurrents)
mt.set_currents(Tubes, Helices, BMagnets, UMagnets, OHelices, currents)

Bz0_new = mt.MagneticField(Tubes, Helices, BMagnets, UMagnets, 0, 0)[1]
print(f"Central field at 24 kA: Bz(0,0) = {Bz0_new:.4f} T")

print("\n✓ MagnetTools field computation works")
```

### Step 2.4 — Compute hoop stress

```python
import magnettools.Bmap as bmap
import pandas as pd

(Tubes, Helices, OHelices, BMagnets, UMagnets, Shims) = data

# Set currents
icurrents = mt.get_currents(Tubes, Helices, BMagnets, UMagnets)
vcurrents = list(icurrents)
vcurrents[0] = 24000.0
currents = mt.DoubleVector(vcurrents)
mt.set_currents(Tubes, Helices, BMagnets, UMagnets, OHelices, currents)

# Compute hoop stress for helices
magnet_type = "H"
mdata = {"H": Helices, "B": BMagnets, "S": UMagnets}
Magnets = mdata[magnet_type]

(headers, values) = bmap.getHoop(
    Magnets, Tubes, Helices, BMagnets, UMagnets, magnet_type
)

df_hoop = pd.DataFrame.from_records(values)
df_hoop.columns = headers
print(f"\nHoop stress at 24 kA:")
print(df_hoop.to_string(index=False))

# Compare with material Rpe
# (You need the Rpe values from the config — extract them)
helix_configs = config_data.get("Helix", [])
for i, row in df_hoop.iterrows():
    if i < len(helix_configs):
        rpe = helix_configs[i]["material"].get("Rpe", None)
        hoop = row["Hoop[MPa]"]
        if rpe:
            ratio = hoop / float(rpe)
            print(f"  Helix {int(row['num'])}: {hoop:.1f} MPa, "
                  f"Rpe={rpe} MPa, ratio={ratio:.3f}")

print("\n✓ MagnetTools hoop stress computation works")
```

### Step 2.5 — Compute max hoop stress (at max current)

This replicates the `compute_max()` logic from `compute_stress_map_chart.py`:

```python
# Set currents to maximum (31 kA for helix supply)
vcurrents = list(icurrents)
num = 0
if len(Tubes) != 0:
    vcurrents[num] = 31.0e3
    num += 1
if len(BMagnets) != 0:
    vcurrents[num] = 31.0e3
    num += 1
if len(UMagnets) != 0:
    vcurrents[num] = 0
    num += 1

currents = mt.DoubleVector(vcurrents)
mt.set_currents(Tubes, Helices, BMagnets, UMagnets, OHelices, currents)

Bz0_max = mt.MagneticField(Tubes, Helices, BMagnets, UMagnets, 0, 0)[1]
print(f"\nAt max current (31 kA):")
print(f"  Bz(0,0) = {Bz0_max:.4f} T")

(headers, values) = bmap.getHoop(
    Magnets, Tubes, Helices, BMagnets, UMagnets, magnet_type
)
df_max = pd.DataFrame.from_records(values)
df_max.columns = headers
print(f"  Max hoop stress: {df_max['Hoop[MPa]'].max():.1f} MPa")
print(f"  Per helix:\n{df_max.to_string(index=False)}")

print("\n✓ Max hoop stress computation works")
```

---

## Part 3: Combined Workflow — Record + Config → Hoop Stress Time Series

### Step 3.1 — Load record and config together

```python
import pandas as pd
import numpy as np

# Load a record (using python_magnetrun or fallback parser)
# Adjust the import based on Part 1 findings
try:
    import python_magnetrun
    df = python_magnetrun.load_record("/data/mrecords/some_record.tsv")
except:
    from minimal_record_parser import load_monitoring_record
    df = load_monitoring_record("/data/mrecords/some_record.tsv")

# Load the MagnetTools data (from Part 2)
import json
from python_magnetsetup.ana import magnet_setup
from python_magnetsetup.config import appenv

test_dir = "test_magnet_data"
data_dir = f"{test_dir}/data"
env = appenv(
    envfile=None, url_api=data_dir,
    yaml_repo=f"{data_dir}/geometries", cad_repo=f"{data_dir}/cad",
    mesh_repo=data_dir, simage_repo=data_dir,
    mrecord_repo=data_dir, optim_repo=data_dir,
)
with open(f"{test_dir}/config.json") as f:
    config_data = json.load(f)
data = magnet_setup(env, config_data, False)

print(f"Record: {df.shape[0]} timesteps, {df.shape[1]} columns")
print(f"Active Icoil columns: {[c for c in df.columns if c.startswith('Icoil')]}")
```

### Step 3.2 — Compute hoop stress at each timestep

```python
import magnettools.magnettools as mt
import magnettools.Bmap as bmap
import time

(Tubes, Helices, OHelices, BMagnets, UMagnets, Shims) = data
icurrents = mt.get_currents(Tubes, Helices, BMagnets, UMagnets)

# Determine which Icoil columns map to MagnetTools current inputs
# For a pure helix insert: there's one current source feeding all helices
# The Icoil columns represent individual coil currents, but MagnetTools
# expects the power supply current.
#
# IMPORTANT: understand the mapping between Icoil columns in the record
# and the current inputs expected by MagnetTools.
# This may be: Icoil1 = total helix current (same for all helices in a tube)
# Or: each Icoil_i is independent.
# CHECK THIS WITH THE ACTUAL DATA AND MAGNET CONFIGURATION.

# For now, assume a single helix current source:
# Use the first non-zero Icoil as the helix supply current
helix_current_col = 'Icoil1'  # ADJUST BASED ON ACTUAL MAPPING

# Subsample for testing (compute every 10th timestep)
sample_indices = np.arange(0, len(df), max(1, len(df) // 50))
print(f"Computing hoop stress at {len(sample_indices)} timesteps "
      f"(out of {len(df)})...")

results = []
t_start = time.time()

for idx in sample_indices:
    row = df.iloc[idx]
    
    # Set current from record
    vcurrents = list(icurrents)
    vcurrents[0] = float(row[helix_current_col])
    # Add bitter/supra currents if applicable
    
    currents_vec = mt.DoubleVector(vcurrents)
    mt.set_currents(Tubes, Helices, BMagnets, UMagnets, OHelices, currents_vec)
    
    # Compute field
    Bz0 = mt.MagneticField(Tubes, Helices, BMagnets, UMagnets, 0, 0)[1]
    
    # Compute hoop stress
    magnet_type = "H"
    mdata_map = {"H": Helices, "B": BMagnets, "S": UMagnets}
    (headers, values) = bmap.getHoop(
        mdata_map[magnet_type], Tubes, Helices, BMagnets, UMagnets, magnet_type
    )
    df_hoop = pd.DataFrame.from_records(values)
    df_hoop.columns = headers
    
    result_row = {
        't': float(row['t']),
        'Bz0': Bz0,
        'I_helix': float(row[helix_current_col]),
    }
    for _, hoop_row in df_hoop.iterrows():
        helix_num = int(hoop_row['num'])
        result_row[f'hoop_H{helix_num}'] = float(hoop_row['Hoop[MPa]'])
    
    results.append(result_row)

elapsed = time.time() - t_start
print(f"Computed {len(results)} timesteps in {elapsed:.1f} s "
      f"({elapsed/len(results)*1000:.1f} ms per timestep)")

# Build result DataFrame
df_stress = pd.DataFrame(results)
print(f"\nStress time series shape: {df_stress.shape}")
print(f"Columns: {list(df_stress.columns)}")
print(f"\nFirst 5 rows:\n{df_stress.head()}")
print(f"\nMax hoop stress per helix:")
for col in df_stress.columns:
    if col.startswith('hoop_'):
        print(f"  {col}: {df_stress[col].max():.1f} MPa")

print("\n✓ Combined record + hoop stress computation works")
```

### Step 3.3 — Visualize the result

```python
import matplotlib.pyplot as plt

fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)

# Panel 1: Current
axes[0].plot(df_stress['t'], df_stress['I_helix'], 'b-')
axes[0].set_ylabel('Current [A]')
axes[0].set_title('Operational Record + Computed Hoop Stress')
axes[0].grid(True, alpha=0.3)

# Panel 2: Central field
axes[1].plot(df_stress['t'], df_stress['Bz0'], 'r-')
axes[1].set_ylabel('Bz(0,0) [T]')
axes[1].grid(True, alpha=0.3)

# Panel 3: Hoop stress for selected helices
hoop_cols = [c for c in df_stress.columns if c.startswith('hoop_')]
for col in hoop_cols[:5]:  # plot first 5 helices
    axes[2].plot(df_stress['t'], df_stress[col], label=col)
axes[2].set_ylabel('Hoop Stress [MPa]')
axes[2].set_xlabel('Time [s]')
axes[2].legend(fontsize=8)
axes[2].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('hoop_stress_timeseries.png', dpi=150)
plt.show()
print("\n✓ Visualization saved to hoop_stress_timeseries.png")
```

---

## Part 4: Document the JSON Config Schema

After successful validation, document the exact JSON structure that the pipeline expects. This becomes the interface contract for student projects and for any future code that creates MagnetTools objects from data.

### Step 4.1 — Export a complete reference config

```python
# From a working MagnetDB instance, export configs for 2-3 magnet configurations
import json

# Inside the magnetdb-api container:
# python3 -c "
# import os; os.environ['DJANGO_SETTINGS_MODULE']='python_magnetdb.settings'
# import django; django.setup()
# from python_magnetdb.actions.generate_simulation_config import generate_magnet_config
# config = generate_magnet_config(MAGNET_ID)
# import json; print(json.dumps(config, indent=2))
# "

# Save as reference files:
# - reference_config_HL31.json (HL-31 insert, ~14 helices)
# - reference_config_H12phi50.json (H12-phi50 insert, ~12 helices)
```

### Step 4.2 — Write the schema documentation

Create a `config_schema.md` documenting:

- Top-level keys: `geom`, `Helix`, `Ring`, `Lead` (optional), `Bitter` (optional), `Supra` (optional)
- Per-helix entry: `geom` (YAML filename), `material` (dict), `insulator` (dict)
- Material dict keys and units
- How the ordering of entries in the `Helix` list maps to MagnetTools helix indices
- How Icoil columns in records map to MagnetTools current inputs

---

## Part 5: Checklist Summary

### python_magnetrun
- [ ] Repository cloned and location documented
- [ ] Installs without Django dependency
- [ ] Parsing API identified and documented (function signature, return type)
- [ ] Tested on at least 3 record files from different sites
- [ ] Handles timestamp computation (Date+Time → t in seconds)
- [ ] Returns clean pandas DataFrame
- [ ] If not ready: fallback parser written and tested

### python_magnetsetup + MagnetTools
- [ ] `appenv()` works with `envfile=None` (no .env file needed)
- [ ] `magnet_setup(env, config_data, debug)` returns MagnetTools objects from JSON + YAML files
- [ ] No Django dependency in the call chain
- [ ] `mt.MagneticField()` computes correct field values
- [ ] `bmap.getHoop()` computes correct hoop stress values
- [ ] Tested with at least 2 different magnet configurations

### Combined workflow
- [ ] Record parsing + MagnetTools computation works end-to-end
- [ ] Performance measured: milliseconds per timestep documented
- [ ] Current mapping (Icoil columns → MagnetTools inputs) understood and documented
- [ ] Visualization produces correct-looking plots

### Reference data exported
- [ ] 2-3 complete config.json files exported from MagnetDB
- [ ] Matching geometry YAML files collected
- [ ] JSON config schema documented
- [ ] Coil-to-helix mapping documented per magnet configuration

---

## Open Questions to Resolve During This Session

1. **Current mapping**: How do Icoil1..Icoil16 columns map to MagnetTools current inputs? Is it one current source per Tube, or one per Helix? Does this vary by magnet type?

2. **python_magnetsetup Django dependency**: Does `appenv` or `magnet_setup` import Django anywhere? If yes, can the import be made conditional?

3. **python_magnetrun new record types**: Is the new record structure (monitoring, transient, calibration) already implemented, or is it still the single TSV format?

4. **Insulator material**: `generate_magnet_config()` loads `Material.objects.get(name="MAT_ISOLANT")` — this assumes a fixed insulator material in the database. For standalone use, we need to either include it in the config JSON or hardcode sensible defaults.

5. **Bitter and Supra magnets**: The current test focuses on Insert (helix) magnets. Do the same JSON config + `magnet_setup` patterns work for Bitter and Supra configurations?
