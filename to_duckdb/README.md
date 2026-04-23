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
    ├── seeds_to_duckdb.py
    ├── add_site.py
    └── student_queries.py
```

---

## Files

| File | Purpose |
|------|---------|
| `seeds_to_duckdb.py` | Build the DB from `python_magnetdb/seeds/` — creates materials, parts, and magnets |
| `add_magnet.py` | Add a magnet (with its parts and materials) from a MagnetDB magnet JSON export |
| `add_site.py` | Add a site (with magnet links and experiment records) from a MagnetDB JSON export |
| `student_queries.py` | Example queries to explore the DB — can be used as a notebook starting point |

---

## Requirements

```bash
pip install duckdb
```

No other dependencies. Both scripts use only the Python standard library plus `duckdb`.

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

The output is printed to the terminal, including a summary table and the full `coil_index → part` mapping for each magnet.

### Step 1b — Add a magnet from a JSON export (alternative to seeds)

When a magnet is not covered by a seed file, use `add_magnet.py` with a MagnetDB magnet JSON export. The JSON embeds all part and material definitions, so no prior data in the DB is needed.

```bash
cd to_duckdb/

# Preview without writing
python add_magnet.py /path/to/M25032101.json --dry-run

# Write to the default DB (student_magnetdb.duckdb in current directory)
python add_magnet.py /path/to/M25032101.json

# Write to a specific DB
python add_magnet.py /path/to/M25032101.json --db /path/to/student.duckdb
```

The magnet type (`insert`, `bitters`, `hybrid`) is inferred automatically from the part types. The operation is **idempotent**: running it twice with the same JSON is safe — existing materials, parts, and magnets are skipped.

Appending to an existing DB works the same way — just point `--db` at it:

```bash
python add_magnet.py /path/to/M25032101.json --db student.duckdb
```

---

### Step 2 — Add sites

Sites reference magnets by name, so Step 1 (or Step 1b) must be completed first. Use a MagnetDB site JSON export (as produced by `python_magnetapi`) to add a site with its magnet links and experiment records.

```bash
cd to_duckdb/

# Preview without writing
python add_site.py /path/to/M10_M19071101_13.json --dry-run

# Write to the default DB (student_magnetdb.duckdb in current directory)
python add_site.py /path/to/M10_M19071101_13.json

# Write to a specific DB
python add_site.py /path/to/M10_M19071101_13.json --db /path/to/student.duckdb
```

The script validates that all magnets referenced in the JSON already exist in the DB and fails with a clear message if any are missing.

The operation is **idempotent**: running it twice with the same JSON is safe — existing sites, magnet links, and experiment records are skipped.

---

## Database schema

```
materials        physical properties of conductor alloys (rpe in Pa)
parts            individual physical components (helix, ring, bitter, lead)
magnets          magnet assemblies (insert, bitters, hybrid, …)
magnet_parts     ordered parts within a magnet, with coil_index
sites            operational configurations (housing, commissioning dates)
site_magnets     which magnets are active in a site (many-to-many)
experiments      operational records (TSV files) attached to a site
```

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

The JSON expected by `add_site.py` matches the format produced by `python_magnetapi`. The minimal required fields are:

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

Notes:
- `magnets` contains magnet **names only** — no part or material definitions. The magnets must already be in the DB.
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
python add_magnet.py /path/to/M25032101.json
python add_magnet.py /path/to/M25032101.json --dry-run   # preview first

# 2. Add one or more operational sites from their JSON exports
python add_site.py /path/to/M10_M19071101_13.json
python add_site.py /path/to/M9_M19061901_xx.json   # repeat for each site

# 3. Verify the result
python student_queries.py

# 4. Ship student_magnetdb.duckdb + TSV record files to students
```
