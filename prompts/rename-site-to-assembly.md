# Migration Plan: Rename `site` → `assembly`

## Motivation

The name "site" is ambiguous — it conflates a physical installation location with a logical grouping of magnets. "Assembly" more accurately describes the concept: a named configuration of one or more magnets that can be put in operation, shut down, and simulated as a unit.

---

## Scope

This rename touches: Python model layer, database schema, API routes, frontend, CLI, actions, seeds, and tests. It should be done in a single branch to avoid drift.

---

## Phase 1 — Python Model Layer

**Files to rename:**

| Old | New |
|-----|-----|
| `python_magnetdb/models/site.py` | `assembly.py` |
| `python_magnetdb/models/site_magnet.py` | `assembly_magnet.py` |

**Changes inside those files:**
- `class Site` → `class Assembly`, `db_table = "assemblies"`
- `class SiteMagnet` → `class AssemblyMagnet`, `db_table = "assembly_magnets"`
- FK field name on `AssemblyMagnet`: `site` → `assembly`

**`python_magnetdb/models/__init__.py`:**
- Import `Assembly` from `assembly`, `AssemblyMagnet` from `assembly_magnet`; remove old imports.

**Models with foreign keys to Site** — update field name `site` → `assembly` and string ref `'Site'` → `'Assembly'` in:
- `python_magnetdb/models/record.py`
- `python_magnetdb/models/simulation.py`
- `python_magnetdb/models/cad_attachment.py`
- `python_magnetdb/models/mesh_attachment.py`

---

## Phase 2 — Database Migration

Create a new migration file (e.g. `0010_rename_site_to_assembly.py`) that:
1. Renames table `sites` → `assemblies`
2. Renames table `site_magnets` → `assembly_magnets`
3. Renames FK columns `site_id` → `assembly_id` on Record, Simulation, CadAttachment, MeshAttachment

Do **not** modify existing migrations — only add a new one.

---

## Phase 3 — API Routes

**Files to rename:**

| Old | New |
|-----|-----|
| `python_magnetdb/routes/api/sites.py` | `assemblies.py` |
| `python_magnetdb/routes/api/site_magnets.py` | `assembly_magnets.py` |

**URL paths:** `/api/sites` → `/api/assemblies`, `/api/site_magnets` → `/api/assembly_magnets`

**`python_magnetdb/routes/api/serializers.py`:**
- `_site_post_processor` → `_assembly_post_processor`
- `sitemagnet_set` → `assemblymagnet_set`
- Update the post-processor mapping key.

**`python_magnetdb/routes/api/home.py`:**
- Update `Site` import and any `"site"` resource-type string.

**`python_magnetdb/routes/api/visualisations.py`:**
- `resource_type == "site"` → `resource_type == "assembly"` (3 occurrences).

Register the new route files in the app router; remove old registrations.

---

## Phase 4 — Actions & Business Logic

**Files to rename:**

| Old | New |
|-----|-----|
| `python_magnetdb/actions/generate_site_directory.py` | `generate_assembly_directory.py` |

**Function renames:**
- `generate_site_directory` → `generate_assembly_directory`
- `generate_site_config` → `generate_assembly_config`
- `get_site_data` → `get_assembly_data`
- All `site_id` parameter names → `assembly_id`

**Update call sites in:**
- `python_magnetdb/actions/generate_simulation_config.py`
- `python_magnetdb/actions/object_geometries.py`
- `python_magnetdb/actions/run_simulation_setup.py`

---

## Phase 5 — Seeds & CRUD

**`python_magnetdb/seeds/crud.py`:**
- `create_site` → `create_assembly`, `query_site` → `query_assembly`
- Update `Site` import.

**All seed files** (`seed-Hybrid.py`, `seed-M*.py`, `seeds.py`):
- Update import of `create_site` → `create_assembly`
- Rename all call sites.

---

## Phase 6 — Frontend

**Files/directories to rename:**

| Old | New |
|-----|-----|
| `web/src/services/siteService.js` | `assemblyService.js` |
| `web/src/views/sites/` | `assemblies/` |
| `AttachMagnetToSiteModal.vue` | `AttachMagnetToAssemblyModal.vue` |

**`web/src/router.js`:**
- Route names: `'sites'` → `'assemblies'`, `'new_site'` → `'new_assembly'`, `'site'` → `'assembly'`
- Route paths: `/sites` → `/assemblies`

**`web/src/App.vue`:**
- Update nav link text and route name.

**Inside all Vue components:**
- Update all references to `siteService` → `assemblyService`, API URLs, route names.

---

## Phase 7 — CLI (`python_magnetapi`)

**`python_magnetapi/python_magnetapi/site.py`** → rename to `assembly.py`:
- Update internal API URL strings (`/api/sites` → `/api/assemblies`)
- `site_create` → `assembly_create`

**`python_magnetapi/python_magnetapi/cli.py`:**
- Import `assembly_create` instead of `site_create`
- Update `--site` CLI arguments and help strings.

**`python_magnetapi/python_magnetapi/utils.py`:**
- Update `"site"` resource type strings → `"assembly"`.

---

## Phase 8 — Tests

| Old | New |
|-----|-----|
| `tests/test_site_geometry_config.py` | `test_assembly_geometry_config.py` |

- Update all imports (`Site` → `Assembly`) and variable names.
- Update `python_magnetapi/tests/test_list.py` for new CLI command names.

---

## Phase 9 — Verification

1. Run `python manage.py migrate` — confirm migration applies cleanly.
2. Run the full test suite.
3. Start the dev server and manually verify: list assemblies, create, attach magnet, run simulation.
4. Check the CLI: `magnetapi assembly create ...`

---

## Key Risks

- **String literals for `resource_type`** — `"site"` appears as a runtime string in visualisations and migrations; missing even one will silently break queries.
- **Existing data** — if the DB has live data, the rename migration must be tested on a snapshot first.
- **Frontend route-name references** — any `router.push({ name: 'site' })` call not caught by search will 404 silently.
- **`python_magnetapi` submodule** — it is a separate package (possibly a git submodule); changes there need their own commit.
