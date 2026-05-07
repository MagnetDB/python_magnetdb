# Student DuckDB Tooling

Helper scripts for building and populating a standalone [DuckDB](https://duckdb.org/) database from MagnetDB data, intended for M1 student project work.

No Django, PostgreSQL, MinIO, or any other MagnetDB service needs to be running. The result is a single portable `.duckdb` file that students can query directly from Python or Jupyter notebooks.

These scripts are **teacher/admin tools** — they are not part of `python_magnetdb` and do not need to be shipped to students. Only the generated `.duckdb` file (and the TSV record files) are distributed.

---

## Location in the repository

```
magnetdb/                        ← repo root
├── python_magnetdb/             ← Django application (not needed here)
│   └── seeds/
│       ├── seed-M19061901.py
│       ├── seeds-Bitters.py
│       └── ...
└── to_duckdb/                   ← this directory
    ├── README.md
    ├── schema.py
    ├── crud.py
    ├── seeds_to_duckdb.py
    ├── magnetdb.py              ← unified CLI (use this)
    ├── add_magnet.py            ← DEPRECATED (kept for compatibility)
    ├── add_site.py              ← DEPRECATED (kept for compatibility)
    └── student_queries.py
```

---

## Files

| File | Purpose |
|------|---------|
| `schema.py` | Canonical DDL — single source of truth for all table definitions |
| `crud.py` | CRUD helpers for material, part, magnet, and site operations |
| `seeds_to_duckdb.py` | Build the DB from `python_magnetdb/seeds/` — creates materials, parts, and magnets |
| `magnetdb.py` | **Unified CLI** — single entry point for all add / view / delete / update operations |
| `add_magnet.py` | ~~Add a magnet from a JSON export~~ — **deprecated**, use `magnetdb.py magnet add` |
| `add_site.py` | ~~Manage sites~~ — **deprecated**, use `magnetdb.py site ...` |
| `student_queries.py` | Example queries to explore the DB — can be used as a notebook starting point |

---

## Requirements

### Virtualenv setup (recommended)

```bash
cd to_duckdb/
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

All scripts must be run from inside the activated virtualenv.

---

## Unified CLI — `magnetdb.py`

`magnetdb.py` is the single entry point for managing the DuckDB. It replaces the old `add_magnet.py` and `add_site.py` scripts.

```
python magnetdb.py <entity> <action> [arguments] [options]
```

### Quick reference

| Command | Description |
|---------|-------------|
| `magnet add <json>` | Add a magnet (parts + materials) from a JSON export |
| `magnet view [name]` | List all magnets, or show detail for one |
| `magnet delete <name>` | Delete a magnet and its part links |
| `site add <json>` | Add a site (magnet links + experiments) from a JSON export |
| `site view [name]` | List all sites, or show detail for one |
| `site delete <name>` | Delete a site, its magnet links, and its experiments |
| `site update-magnet <site> <magnet>` | Patch positional/temporal fields on a site–magnet link |

All subcommands accept `--db <path>` (default: `student_magnetdb.duckdb` in the current directory).

---

## Workflow

### Step 1 — Build the structural data

Run `seeds_to_duckdb.py` from the `to_duckdb/` directory. It reads the seed files in `../python_magnetdb/seeds/` and populates the DB with materials, parts, and magnets.

```bash
cd to_duckdb/

# Load all available seeds (repo root inferred as ../)
python seeds_to_duckdb.py --repo ..

# Load specific seeds only
python seeds_to_duckdb.py --repo .. --seeds bitters,M19061901,M19071101

# Custom output path
python seeds_to_duckdb.py --repo .. --output /path/to/student.duckdb
```

Available seed keys:

| Key | Seed file | Content |
|-----|-----------|---------|
| `bitters` | `seeds-Bitters.py` | M8, M9, M10 Bitter magnets |
| `M19061901` | `seed-M19061901.py` | HL-31 insert, 14 helices + rings |
| `M19071101` | `seed-M19071101.py` | H12-phi50 insert, 12 helices + rings |
| `M18110501` | `seed-M18110501.py` | Earlier HL-31 configuration |
| `M20022001` | `seed-M20022001.py` | Insert configuration |
| `M22011801` | `seed-M22011801.py` | Insert configuration |
| `records` | `seed-records.py` | Experiment records for M9/M10 sites |

### Step 1b — Add a magnet from a JSON export (alternative to seeds)

When a magnet is not covered by a seed file, load it directly from a MagnetDB magnet JSON export. The JSON embeds all part and material definitions, so no prior data in the DB is needed.

```bash
cd to_duckdb/

# Preview without writing
python magnetdb.py magnet add /path/to/M25032101.json --dry-run

# Write to the default DB (student_magnetdb.duckdb in current directory)
python magnetdb.py magnet add /path/to/M25032101.json

# Write to a specific DB
python magnetdb.py magnet add /path/to/M25032101.json --db /path/to/student.duckdb

# When part JSON files live in a separate directory
python magnetdb.py magnet add /path/to/M25032101.json --part-dir /path/to/parts/
```

The magnet type (`insert`, `bitters`, `hybrid`) is inferred automatically from the part types. The operation is **idempotent**: running it twice with the same JSON is safe — existing materials, parts, and magnets are skipped.

### Step 1c — Inspect and manage magnets

```bash
# List all magnets
python magnetdb.py magnet view

# Show detail for one magnet (parts, coil indices)
python magnetdb.py magnet view M25032101

# Delete a magnet and its part links
python magnetdb.py magnet delete M25032101
```

---

### Step 2 — Add sites

Sites reference magnets by name, so Step 1 (or Step 1b) must be completed first. Use `magnetdb.py site add` with a MagnetDB site JSON export to add a site with its magnet links and experiment records.

```bash
cd to_duckdb/

# Preview without writing
python magnetdb.py site add /path/to/M10_M19071101_13.json --dry-run

# Write to the default DB
python magnetdb.py site add /path/to/M10_M19071101_13.json

# Write to a specific DB
python magnetdb.py site add /path/to/M10_M19071101_13.json --db /path/to/student.duckdb

# Auto-load missing magnets from a separate directory
python magnetdb.py site add /path/to/M10_M19071101_13.json --magnet-dir /path/to/magnet/jsons
```

Magnets referenced in the JSON that are not yet in the DB are loaded automatically from a same-named JSON file (e.g. `M19071101.json`) found in the same directory as the site JSON (or the directory given by `--magnet-dir`). The script fails with a clear message if any magnet file cannot be found.

The operation is **idempotent**: running it twice with the same JSON is safe — existing sites, magnet links, and experiment records are skipped.

### Step 2b — Inspect and manage sites

```bash
# List all sites
python magnetdb.py site view

# Show detail for one site (magnets, experiment count)
python magnetdb.py site view M10_M19071101_13

# Delete a site (removes magnet links and experiments too)
python magnetdb.py site delete M10_M19071101_13
```

### Step 2c — Update SiteMagnet fields

After a site has been added, positional and temporal fields for a specific magnet within that site can be patched without re-importing the full JSON:

```bash
# Update positional offsets
python magnetdb.py site update-magnet M10_M19071101_13 M19071101 \
    --z-offset 12.5 --r-offset 0.0 --parallax 0.0

# Set commissioning / decommissioning dates
python magnetdb.py site update-magnet M10_M19071101_13 M19071101 \
    --commissioned-at "2025-11-12 00:00:00"

# Attach arbitrary metadata (JSON string)
python magnetdb.py site update-magnet M10_M19071101_13 M19071101 \
    --metadata '{"current_max_A": 26000}'

# Target a specific DB file
python magnetdb.py site update-magnet M10_M19071101_13 M19071101 \
    --z-offset 5.0 --db /path/to/student.duckdb
```

Only the fields explicitly passed are updated; all others are left unchanged.

---

## Database schema

```
materials        physical properties of conductor alloys (rpe in Pa)
parts            individual physical components (helix, ring, bitter, lead)
magnets          magnet assemblies (insert, bitters, hybrid, …)
magnet_parts     ordered parts within a magnet, with coil_index
sites            operational configurations (housing, commissioning dates)
site_magnets     magnets active in a site — positional & temporal metadata
experiments      operational records (TSV files) attached to a site
```

### site_magnets columns

| Column | Type | Default | Description |
|--------|------|---------|-------------|
| `site_name` | VARCHAR | — | FK → sites |
| `magnet_name` | VARCHAR | — | FK → magnets |
| `z_offset` | DOUBLE | 0.0 | Axial offset of the magnet in the site (m) |
| `r_offset` | DOUBLE | 0.0 | Radial offset of the magnet in the site (m) |
| `parallax` | DOUBLE | 0.0 | Parallax angle |
| `commissioned_at` | TIMESTAMP | NULL | When this magnet was commissioned in this site |
| `decommissioned_at` | TIMESTAMP | NULL | When removed (NULL = still active) |
| `metadata` | JSON | `{}` | Free-form key/value store |

### coil_index

The `magnet_parts.coil_index` column maps each helix or bitter part to its `Icoil_N` column in the operational TSV records:

- Assigned 1-based, in the order parts appear in the magnet definition
- Only `helix` and `bitter` parts receive a coil_index
- `ring` and `lead` parts get `NULL`

Example query to retrieve the mapping:

```python
import duckdb
con = duckdb.connect("student_magnetdb.duckdb", read_only=True)

con.execute("""
    SELECT 'Icoil' || mp.coil_index AS column,
           p.name AS part,
           p.type,
           mat.nuance,
           mat.rpe / 1e6 AS rpe_MPa
    FROM magnet_parts mp
    JOIN parts     p   ON p.name   = mp.part_name
    JOIN magnets   m   ON m.name   = mp.magnet_name
    LEFT JOIN materials mat ON mat.name = p.material_name
    WHERE m.name = 'M19061901'
      AND mp.coil_index IS NOT NULL
    ORDER BY mp.coil_index
""").df()
```

---

## Site JSON format

The JSON expected by `magnetdb.py site add` matches the format produced by `python_magnetapi`. The minimal required fields are:

```json
{
    "name":              "M10_M19071101_13",
    "status":            "in_operation",
    "housing":           "M10",
    "commissioned_at":   "2025-11-12 00:00:00",
    "decommissioned_at": "None",
    "magnets": [
        "M19071101",
        "M10Bitters"
    ],
    "records": [
        {
            "name":        "M10_2025.11.13---09:14:21.txt",
            "description": "",
            "file":        "M10_2025.11.13---09:14:21.txt"
        }
    ]
}
```

Each entry in `magnets` is either a **plain string** (name only — positional fields default to `0.0`, metadata to `{}`) or a **dict** with the full `SiteMagnet` fields:

```json
"magnets": [
    "M19071101",
    {
        "name":               "M10Bitters",
        "z_offset":           0.0,
        "r_offset":           0.0,
        "parallax":           0.0,
        "commissioned_at":    "2025-11-12 00:00:00",
        "decommissioned_at":  null,
        "metadata":           {"current_max_A": 26000}
    }
]
```

Notes:
- `magnets` contains magnet **names** — magnets must already be in the DB (or resolvable from a JSON file).
- `decommissioned_at` can be `"None"` or omitted for active sites.
- `records` can be an empty list `[]` if no experiment files are available yet.

---

## Example queries

`student_queries.py` contains ready-to-run examples covering:

1. Full site hierarchy (site → magnet → parts → materials)
2. `Icoil_N → part` mapping for a specific magnet
3. Experiment records for a site
4. Material comparison across all helices
5. Coil channel count per magnet
6. Parts shared across multiple magnets (reused helices/rings)

Run it directly or copy cells into a Jupyter notebook:

```bash
python student_queries.py
```

---

## Typical full setup

```bash
cd to_duckdb/

# 1a. Build structural data from seeds (when seed files are available)
python seeds_to_duckdb.py --repo .. --seeds bitters,M19061901,M19071101

# 1b. Or load a magnet directly from a MagnetDB JSON export (no seeds needed)
python magnetdb.py magnet add /path/to/M25032101.json --dry-run   # preview first
python magnetdb.py magnet add /path/to/M25032101.json

# 2. Add one or more operational sites from their JSON exports
python magnetdb.py site add /path/to/M10_M19071101_13.json
python magnetdb.py site add /path/to/M9_M19061901_xx.json         # repeat for each site

# 2b. Optionally patch positional data after the fact
python magnetdb.py site update-magnet M10_M19071101_13 M19071101 --z-offset 12.5

# 3. Verify the result
python magnetdb.py magnet view
python magnetdb.py site view
python student_queries.py

# 4. Ship student_magnetdb.duckdb + TSV record files to students
```

---

## Deprecated scripts

`add_magnet.py` and `add_site.py` are kept for backward compatibility only. They issue a `DeprecationWarning` when called directly and will be removed in a future version. Migrate to the equivalent `magnetdb.py` commands:

| Old command | New command |
|-------------|-------------|
| `python add_magnet.py <json>` | `python magnetdb.py magnet add <json>` |
| `python add_site.py add <json>` | `python magnetdb.py site add <json>` |
| `python add_site.py update-magnet <s> <m> ...` | `python magnetdb.py site update-magnet <s> <m> ...` |
