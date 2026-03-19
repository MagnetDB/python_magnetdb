# Geometry API Usage Guide

This guide explains how to add geometry configuration to parts, including the important constraint around file references.

## Overview

Parts support three types of geometry-related data:

1. **geometry_config** (YAML/JSON): The main geometry configuration (stored as JSON in database)
2. **geometry_shape** (CSV file): Shape data for HELIX type parts
3. **geometry_modelaxi** (JSON file): ModelAxi data for HELIX and BITTER type parts

## Important: File References in YAML

### The Problem

YAML geometry files can reference other YAML files like this:

```yaml
!<Helix>
name: MyHelix
r: [19.3, 24.2]
z: []
modelaxi: "modelaxi_file"  # References modelaxi_file.yaml
shape: "shape_file"        # References shape_file.yaml
```

When the YAML is loaded, it tries to load these referenced files from the file system. This works during **seeding** (where we have access to all files), but **fails at runtime** via the API (where referenced files don't exist).

### The Solution

**Option 1: Use Fully Expanded Inline YAML** (Recommended for API)

Provide the complete YAML structure inline without file references:

```yaml
!<Helix>
name: MyHelix
r: [19.3, 24.2]
z: []
cutwidth: 0.2
odd: true
dble: true
modelaxi: !<ModelAxi>
  name: MyHelix
  h: 0.0
  turns: []
  pitch: []
model3d: !<Model3D>
  cad: MyHelix
shape: !<Shape>
  name: ''
  file: ''
```

**Option 2: Pre-expand During Seeding** (Automatic)

During database seeding, file references are automatically expanded and stored as complete, self-contained JSON. This means:
- Seed data can use file references
- The database stores fully expanded geometry
- API consumers get complete geometry without file dependencies

## API Usage Examples

### Using curl

```bash
curl -X PATCH "http://magnetdb-api.grenoble.lncmi.local:8000/api/parts/1" \
  -H "Authorization: YOUR_API_KEY" \
  -F "name=MyHelix" \
  -F "description=Test helix part" \
  -F "type=helix" \
  -F "material_id=1" \
  -F "geometry_yaml_config=---
!<Helix>
name: MyHelix
r: [19.3, 24.2]
z: []
cutwidth: 0.2
odd: true
dble: true
modelaxi: !<ModelAxi>
  name: MyHelix
  h: 0.0
  turns: []
  pitch: []
model3d: !<Model3D>
  cad: MyHelix
shape: !<Shape>
  name: ''
  file: ''" \
  -F "geometry_shape=@path/to/shape.csv" \
  -F "geometry_modelaxi=@path/to/modelaxi.json"
```

### Using Python requests

```python
import requests
import os

api_server = os.getenv('MAGNETDB_API_SERVER') or "http://magnetdb-api.grenoble.lncmi.local:8000"
api_key = os.getenv('MAGNETDB_API_KEY')

# Fully expanded YAML (no file references)
geometry_yaml = """---
!Helix
name: MyHelix
r: [19.3, 24.2]
z: []
cutwidth: 0.2
odd: true
dble: true
modelaxi: !ModelAxi
  name: MyHelix
  h: 0.0
  turns: []
  pitch: []
model3d: !Model3D
  cad: MyHelix
  with_shapes: false
  with_channels: false
shape: !Shape
  name: ''
  file: ''
"""

data = {
    'name': 'MyHelix',
    'description': 'Test helix part',
    'type': 'helix',
    'material_id': '1',
    'geometry_yaml_config': geometry_yaml
}

files = {}
if os.path.exists('path/to/shape.csv'):
    files['geometry_shape'] = open('path/to/shape.csv', 'rb')

if os.path.exists('path/to/modelaxi.json'):
    files['geometry_modelaxi'] = open('path/to/modelaxi.json', 'rb')

response = requests.patch(
    f"{api_server}/api/parts/1",
    data=data,
    files=files,
    headers={'Authorization': api_key}
)

for f in files.values():
    f.close()

if response.status_code == 200:
    print("Success:", response.json())
else:
    print(f"Error {response.status_code}:", response.text)
```

## Error Handling

If you try to use YAML with file references via the API, you'll get an error:

```json
{
  "detail": "YAML contains file references that cannot be resolved: [Errno 2] No such file or directory: 'modelaxi_file.yaml'. Please provide fully expanded inline YAML without file references, or upload the complete geometry including all referenced files."
}
```

**Solution**: Replace string references with inline object definitions as shown in the examples above.

## For Developers: How Seeding Works

The seeding process (in `python_magnetdb/seeds/crud.py`) handles file references correctly:

```python
# In create_part():
geometry_dir = path.join(data_directory, "geometries")
geometry_file = path.join(geometry_dir, f"{geometry}.yaml")
with open(geometry_file) as file:
    # Pass geometry_dir as base_dir so referenced YAML files are resolved
    part.geometry_config = json.loads(yaml_to_json(file.read(), base_dir=geometry_dir))
```

This:
1. Changes to the geometries directory before loading YAML
2. Resolves all file references (modelaxi.yaml, shape.yaml, etc.)
3. Expands everything into a complete JSON structure
4. Stores the expanded JSON in the database

Result: The database contains fully self-contained geometry configurations that don't require external files.

## Field Constraints

- **geometry_shape**: Only allowed for `helix` type parts
- **geometry_modelaxi**: Only allowed for `helix` and `bitter` type parts
- **geometry_config**: Allowed for all part types

These constraints are enforced by the Part model's `allow_hts_file`, `allow_shape_file`, and `allow_modelaxi_file` properties.
