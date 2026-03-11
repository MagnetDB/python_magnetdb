# MagnetDB — Computed Data & Reproducibility Migration Guide

**Status:** Draft — design document for discussion  
**Author:** Christophe Trophime / Claude  
**Last updated:** 2026-03-09  
**Scope:** New `ComputedData` model, reproducibility metadata for `MeshAttachment` and `CadAttachment`

---

## 1. Motivation

MagnetDB currently stores raw inputs (geometry configs, CAD files, mesh files) and simulation results (output archives, logs). What's missing is a layer of **derived/computed data** that sits between raw inputs and full simulation outputs — lightweight, structured results that are frequently queried and displayed:

- **R(I) tables** — resistance as a function of current for a magnet
- **Mutual inductance matrices** — coupling between magnets in a site configuration
- Future candidates: B-field maps, thermal profiles, stress distributions, optimization results

Additionally, the existing `MeshAttachment` and `CadAttachment` models lack **provenance metadata** — there is no record of which command, tool version, or parameters produced a given mesh or CAD file. For scientific reproducibility, this lineage must be captured.

---

## 2. Current Attachment Pattern in MagnetDB

All file-bearing models in MagnetDB follow the same structural pattern:

```
┌─────────────────┐       FK        ┌─────────────────────┐
│  Domain Model    │───────────────▶│  StorageAttachment   │
│  (CadAttachment, │                │  - filename          │
│   MeshAttachment)│                │  - content_type      │
│  - type (enum)   │                │  - key (SHA256 hash) │
│  - magnet FK     │                │  - S3 storage        │
│  - site FK       │                └─────────────────────┘
│  - part FK       │
│  - created_at    │
└─────────────────┘
```

**Key characteristics:**
- The domain model owns the semantic metadata (type, parent resource FKs)
- `StorageAttachment` is a generic, content-addressed file store (deduplication via SHA256)
- Upload uses `StorageAttachment.upload(file)` for HTTP uploads or `StorageAttachment.raw_upload(filename, content_type, filepath)` for programmatic creation
- Download via `/api/attachments/{id}/download` streaming endpoint

**Existing models following this pattern:**

| Model | Table | Parent FKs | Type enum | Metadata |
|-------|-------|-----------|-----------|----------|
| `CadAttachment` | `cad_attachments` | magnet, part, site | axi, 3d | — |
| `MeshAttachment` | `mesh_attachments` | magnet, site | axi, 3d | — |

**Models using direct attachment FKs (no intermediate model):**

| Parent model | Field | Purpose |
|-------------|-------|---------|
| `Part` | `hts_attachment` | HTS material data file |
| `Part` | `shape_attachment` | Shape definition file |
| `Part` | `modelaxi_attachment` | Axisymmetric model file |
| `Site` | `config_attachment` | Site configuration file |
| `Simulation` | `setup_output_attachment` | Setup archive |
| `Simulation` | `output_attachment` | Result archive |
| `Simulation` | `log_attachment` | Debug log |
| `Simulation` | `mesh_attachment` | Mesh used for simulation |

---

## 3. Proposed Design: `ComputedData` Model

### 3.1 Rationale: Separate Model + StorageAttachment

A single `ComputedData` model that references `StorageAttachment` for the actual data file. This combines:

- **From the separate model approach:** provenance tracking (which simulation produced it, source type, timestamps), ability to store multiple versions, queryable metadata
- **From the file-based approach:** downloadable files via the existing S3/attachment infrastructure, no PostgreSQL row bloat, external tool compatibility (CSV/JSON files)

### 3.2 Model Definition

```python
# python_magnetdb/models/computed_data.py
import enum
from django.db import models


class ComputedDataType(str, enum.Enum):
    """What kind of computed result this is."""
    RESISTANCE_TABLE = "resistance_table"       # R(I) curve for a Magnet
    INDUCTANCE_MATRIX = "inductance_matrix"     # Mutual inductance for a Site
    # Future types — add here without schema changes:
    # BFIELD_MAP = "bfield_map"
    # THERMAL_PROFILE = "thermal_profile"
    # STRESS_DISTRIBUTION = "stress_distribution"

    @classmethod
    def choices(cls):
        return [(item.value, item.name) for item in cls]


class ComputedDataSource(str, enum.Enum):
    """How this data was produced."""
    SIMULATION = "simulation"       # Output of a FEM simulation
    MEASUREMENT = "measurement"     # Experimental measurement
    ANALYTICAL = "analytical"       # Analytical/semi-analytical computation

    @classmethod
    def choices(cls):
        return [(item.value, item.name) for item in cls]


class ComputedData(models.Model):
    class Meta:
        db_table = "computed_data"

    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255, null=True)
    type = models.CharField(max_length=255, choices=ComputedDataType.choices())
    source = models.CharField(max_length=255, choices=ComputedDataSource.choices())
    description = models.TextField(null=True)

    # ---- Parent resource (polymorphic, one is set) ----
    magnet = models.ForeignKey("Magnet", on_delete=models.CASCADE, null=True)
    site = models.ForeignKey("Site", on_delete=models.CASCADE, null=True)

    # ---- The actual data file (CSV or JSON in S3) ----
    attachment = models.ForeignKey("StorageAttachment", on_delete=models.CASCADE)

    # ---- Provenance ----
    simulation = models.ForeignKey("Simulation", on_delete=models.SET_NULL, null=True)

    # ---- Lightweight summary for frontend display without downloading ----
    metadata = models.JSONField(default=dict)

    # ---- Reproducibility: how was this data generated? ----
    # See Section 5 for the provenance schema
    provenance = models.JSONField(default=dict)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### 3.3 Type-specific Constraints

The `type` field determines which parent FK is valid:

| `type` | Valid parent | File format |
|--------|-------------|-------------|
| `resistance_table` | `magnet` (required) | CSV or JSON |
| `inductance_matrix` | `site` (required) | JSON |

This validation should be enforced at the API level (route handler), not as a database constraint, to keep the model flexible for future types that may attach to either parent.

### 3.4 Metadata Schema Conventions

The `metadata` JSONField stores a lightweight summary so the frontend can render a preview table/card without downloading the full file:

```jsonc
// For resistance_table
{
    "columns": ["I", "R"],
    "units": {"I": "A", "R": "Ohm"},
    "row_count": 42,
    "I_range": [0, 30000],
    "R_range": [0.105, 0.250]
}

// For inductance_matrix
{
    "magnets": ["M9_Bi", "M9_Bo", "M10"],
    "units": "H",
    "dimension": [3, 3],
    "symmetric": true
}
```

### 3.5 File Format Conventions

**Resistance table (CSV):**
```csv
I,R
0,0.105
100,0.112
200,0.128
...
```

**Resistance table (JSON):**
```json
{
    "columns": ["I", "R"],
    "units": {"I": "A", "R": "Ohm"},
    "data": [[0, 0.105], [100, 0.112], [200, 0.128]]
}
```

**Inductance matrix (JSON):**
```json
{
    "magnets": ["M9_Bi", "M9_Bo"],
    "units": "H",
    "matrix": [[0.0045, 0.0012], [0.0012, 0.0038]]
}
```

> **Open question:** Should we enforce a canonical format (JSON only, or CSV only), or support both and distinguish via `StorageAttachment.content_type`? JSON is self-describing and easier to parse in the frontend; CSV is more familiar for external tools and spreadsheets.

---

## 4. Reproducibility Enhancement for Existing Models

### 4.1 Problem Statement

`MeshAttachment` and `CadAttachment` currently store only the file and a type enum. There is no record of:

- Which tool and version generated the mesh/CAD (e.g., `gmsh 4.12.2`, `salome_meca 2024.1`)
- The command line used (e.g., `gmsh -2 -order 2 -clmax 0.5 input.geo`)
- The algorithmic parameters (mesh size, refinement criteria, element order)
- Which input geometry or configuration was used as source
- Whether the result is reproducible given the same inputs

### 4.2 Proposed Solution: `provenance` JSONField

Add a `provenance` JSONField to `MeshAttachment` and `CadAttachment` (and use the same field on `ComputedData`). This is consistent with the existing `metadata` JSONField pattern already present on most models.

**Why JSONField rather than structured columns:**

- The provenance schema varies significantly by tool (gmsh vs. salome vs. MeshGems vs. custom scripts)
- New tools and parameters are added over time — a JSONField avoids constant schema migrations
- The data is primarily for display and audit, not for relational queries
- Consistent with MagnetDB's existing extensibility strategy (cf. `metadata` on Magnet, Part, Site, etc.)

### 4.3 Provenance Schema Convention

A common structure for all provenance-bearing models:

```jsonc
{
    // What tool produced this artifact
    "tool": {
        "name": "gmsh",
        "version": "4.12.2",
        "image": "docker.io/lncmi/gmsh:4.12.2"  // optional: container image
    },

    // The exact command line (for full reproducibility)
    "command": "gmsh -2 -order 2 -clmax 0.5 -clmin 0.01 M9_Bi.geo",

    // Structured parameters (for querying/display, independent of command format)
    "parameters": {
        "dimension": 2,
        "order": 2,
        "clmax": 0.5,
        "clmin": 0.01,
        "algorithm": "Frontal-Delaunay"
    },

    // Input lineage — what was this derived from?
    "inputs": {
        "geometry_source": "cad_attachment:42",   // FK reference as string
        "config_file": "M9_Bi.yaml"
    },

    // Execution environment (optional, for HPC traceability)
    "environment": {
        "hostname": "lncmi-calc01",
        "date": "2026-03-09T14:30:00Z",
        "duration_seconds": 123
    },

    // Free-form notes
    "notes": "Refined mesh near inner bore for thermal gradient resolution"
}
```

### 4.4 Migration for Existing Models

```python
# Migration 0022 (example number)
migrations.AddField(
    model_name='meshattachment',
    name='provenance',
    field=models.JSONField(default=dict),
),
migrations.AddField(
    model_name='cadattachment',
    name='provenance',
    field=models.JSONField(default=dict),
),
```

This is non-breaking: existing records get an empty dict, and no existing code needs to change. The provenance data is populated going forward, either manually via the UI or automatically from simulation workflows.

### 4.5 Automatic Provenance Capture

In `run_simulation.py` and `run_ssh_simulation.py`, the command generation already exists via `setup_cmds()`. The provenance can be captured at mesh/CAD generation time:

```python
# After generating a mesh in the simulation workflow
mesh_attachment = MeshAttachment(
    type=MeshAttachmentType.AXI,
    magnet=magnet,
    attachment=StorageAttachment.raw_upload(...),
    provenance={
        "tool": {"name": "gmsh", "version": gmsh_version},
        "command": cmds.get("Mesh", ""),
        "parameters": extract_mesh_params(args),
        "inputs": {"config": simulation.setup_state.get("cfgfile")},
        "environment": {
            "hostname": server.host if server else "local",
            "date": datetime.utcnow().isoformat() + "Z",
        }
    }
)
```

---

## 5. Combined Migration Plan

### 5.1 Migration Sequence

All changes can be done in a single migration or split for clarity:

| Step | Migration | Description |
|------|-----------|-------------|
| 1 | `0022_computed_data.py` | Create `ComputedData` model with all fields |
| 2 | `0023_attachment_provenance.py` | Add `provenance` JSONField to `MeshAttachment` and `CadAttachment` |

Alternatively, combine into a single migration if done at the same time.

### 5.2 API Routes to Add

| Endpoint | Method | Description |
|----------|--------|-------------|
| `POST /api/computed_data` | Create | Upload a computed data file (form: resource_type, resource_id, type, source, file, metadata, provenance) |
| `GET /api/computed_data?magnet_id=X` | List | List computed data for a magnet |
| `GET /api/computed_data?site_id=X` | List | List computed data for a site |
| `GET /api/computed_data/{id}` | Read | Get computed data details (metadata without file) |
| `DELETE /api/computed_data/{id}` | Delete | Remove computed data entry and attachment |
| `PATCH /api/mesh_attachments/{id}/provenance` | Update | Set/update provenance on existing mesh |
| `PATCH /api/cad_attachments/{id}/provenance` | Update | Set/update provenance on existing CAD |

The create/delete routes follow the exact pattern of `mesh_attachments.py` and `cad_attachments.py`.

### 5.3 Serializer Updates

Add post-processors in `serializers.py`:

```python
def _magnet_post_processor(model, res):
    # ... existing code ...
    if 'computeddata_set' in res:
        res['computed_data'] = res['computeddata_set']
        del res['computeddata_set']
    return res

def _site_post_processor(model, res):
    # ... existing code ...
    if 'computeddata_set' in res:
        res['computed_data'] = res['computeddata_set']
        del res['computeddata_set']
    return res
```

Add `computeddata_set__attachment` to `prefetch_related` calls in magnet and site routes.

### 5.4 Frontend Component

A `ComputedDataEditor.vue` component (or React equivalent post-migration) following the same pattern as `MeshAttachmentEditor.vue`:

- List existing computed data with type badge, source badge, row count / dimension
- Upload new computed data (file + type + source + optional description)
- Download the file via attachment endpoint
- Delete entry
- Display metadata summary inline (column names, units, ranges)

---

## 6. Open Questions for Future Discussion

### 6.1 Data Model

- **Single `ComputedData` vs. separate models per type?** Current proposal uses a single model with a `type` enum. If resistance tables and inductance matrices diverge significantly in their metadata structure or behavior, separate models (`MagnetResistanceTable`, `SiteInductanceMatrix`) may be cleaner. Decision point: when we know more about additional computed data types.

- **Should `ComputedData` also reference `Part`?** Some computed results may be part-level (e.g., resistance of a single helix). Adding a nullable `part` FK keeps the door open.

- **Version management:** If multiple R(I) tables exist for the same magnet (computed vs. measured, or from different simulations), should there be an `is_active` / `is_default` flag? Or is the most recent one always preferred?

### 6.2 Provenance

- **Provenance schema validation:** Should we enforce the provenance JSON structure via a JSON Schema, or keep it free-form? A JSON Schema could be stored as a project-level constant and validated at the API layer.

- **Provenance for `Simulation` itself?** The simulation model already stores `setup_state`, method, geometry, model, etc. Should there be a unified provenance format that also covers simulations, or is the existing approach sufficient?

- **Retroactive provenance:** For existing meshes and CAD files, is it worth building a backfill mechanism (e.g., parsing log files to reconstruct command lines)?

### 6.3 File Formats

- **Canonical format:** JSON vs. CSV vs. both. JSON is self-describing and frontend-friendly. CSV is familiar for external tools. HDF5 could be relevant for large datasets but adds a dependency.

- **Streaming large results:** If computed data files become large (e.g., 3D field maps), should the API support partial reads or pagination, or is download-only sufficient?

### 6.4 Reproducibility Scope

- **What guarantees "reproducible"?** Storing the command line and parameters is necessary but may not be sufficient. Should we also store input file checksums, environment variables, or container image digests?

- **REANA integration:** When REANA is adopted for workflow orchestration, its built-in provenance tracking (Yadage/CWL workflow definitions, run IDs) could supersede or complement the `provenance` JSONField. The current design should be compatible with a future migration to REANA-managed provenance.

---

## 7. Summary of Changes

```
Existing schema (migration 0021)          Proposed additions
─────────────────────────────             ──────────────────────

Magnet ◄──── CadAttachment ──► SA        CadAttachment + provenance JSONField
       ◄──── MeshAttachment ──► SA       MeshAttachment + provenance JSONField
       ◄──── Probe
                                          Magnet ◄──── ComputedData ──► SA
Site   ◄──── CadAttachment ──► SA                      (resistance_table)
       ◄──── MeshAttachment ──► SA
                                          Site   ◄──── ComputedData ──► SA
                                                        (inductance_matrix)

SA = StorageAttachment (unchanged)
```

**Total new tables:** 1 (`computed_data`)  
**Modified tables:** 2 (`mesh_attachments` + `cad_attachments`, adding `provenance` column)  
**New API routes:** ~5  
**Breaking changes:** None — all additions are nullable or have defaults
