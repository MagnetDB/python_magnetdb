"""
add_magnet.py
=============
Add a magnet (with its parts and materials) to an existing student DuckDB
database from a MagnetDB magnet JSON export.

Unlike add_site.py, the JSON here is a *magnet* export: it contains the full
definition of every part, including embedded material objects.  No prior data
in the DB is required — materials and parts are created on the fly.

JSON format (as exported from MagnetDB)
----------------------------------------
{
    "name":                    "M25032101",
    "status":                  "in_operation",
    "design_office_reference": "",
    "description":             "14 Helices, Phi = 34 mm",
    "parts": [
        {
            "name":                    "H24110501",
            "description":             "H1",
            "status":                  "in_operation",
            "type":                    "helix",
            "design_office_reference": "HL-37-021-B",
            "geometry":                "/path/to/HL-37_H1.yaml",
            "material": {
                "name":                    "MA24032701",
                "description":             "",
                "t_ref":                   293,
                "volumic_mass":            9000.0,
                "specific_heat":           385,
                "alpha":                   0.0036,
                "electrical_conductivity": 52900000.0,
                "thermal_conductivity":    380,
                "magnet_permeability":     1,
                "young":                   117000000000.0,
                "poisson":                 0.33,
                "expansion_coefficient":   1.8e-05,
                "rpe":                     490000000.0,
                "nuance":                  "CuAg2,75"
            }
        },
        ...
    ]
}

Usage
-----
    python add_magnet.py M25032101.json
    python add_magnet.py M25032101.json --db path/to/student.duckdb
    python add_magnet.py M25032101.json --dry-run
"""

import argparse
import json
import sys
from pathlib import Path

import duckdb

# ---------------------------------------------------------------------------
# Schema DDL  (same tables as add_site.py — idempotent on existing DBs)
# ---------------------------------------------------------------------------

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS materials (
    name                    VARCHAR PRIMARY KEY,
    description             VARCHAR,
    nuance                  VARCHAR,
    t_ref                   DOUBLE,
    volumic_mass            DOUBLE,
    specific_heat           DOUBLE,
    alpha                   DOUBLE,
    electrical_conductivity DOUBLE,
    thermal_conductivity    DOUBLE,
    magnet_permeability     DOUBLE,
    young                   DOUBLE,
    poisson                 DOUBLE,
    expansion_coefficient   DOUBLE,
    rpe                     DOUBLE
);

CREATE TABLE IF NOT EXISTS parts (
    name                    VARCHAR PRIMARY KEY,
    type                    VARCHAR,
    status                  VARCHAR,
    material_name           VARCHAR REFERENCES materials(name),
    geometry                VARCHAR,
    geometry_data           JSON,
    cad                     VARCHAR,
    design_office_reference VARCHAR
);

CREATE TABLE IF NOT EXISTS magnets (
    name                    VARCHAR PRIMARY KEY,
    type                    VARCHAR,
    status                  VARCHAR,
    geometry                VARCHAR,
    geometry_data           JSON,
    design_office_reference VARCHAR
);

-- Migration: add geometry_data to existing databases (no-op if already present)
ALTER TABLE parts   ADD COLUMN IF NOT EXISTS geometry_data JSON;
ALTER TABLE magnets ADD COLUMN IF NOT EXISTS geometry_data JSON;

CREATE TABLE IF NOT EXISTS magnet_parts (
    magnet_name VARCHAR REFERENCES magnets(name),
    part_name   VARCHAR REFERENCES parts(name),
    rank        INTEGER,
    coil_index  INTEGER,
    PRIMARY KEY (magnet_name, part_name)
);

CREATE TABLE IF NOT EXISTS sites (
    name               VARCHAR PRIMARY KEY,
    description        VARCHAR,
    status             VARCHAR,
    housing            VARCHAR,
    commissioned_at    TIMESTAMP,
    decommissioned_at  TIMESTAMP
);

CREATE TABLE IF NOT EXISTS site_magnets (
    site_name   VARCHAR REFERENCES sites(name),
    magnet_name VARCHAR REFERENCES magnets(name),
    PRIMARY KEY (site_name, magnet_name)
);

CREATE TABLE IF NOT EXISTS experiments (
    id          INTEGER PRIMARY KEY,
    name        VARCHAR,
    description VARCHAR,
    file        VARCHAR,
    site_name   VARCHAR REFERENCES sites(name),
    status      VARCHAR DEFAULT 'pending'
);
"""

# Part types that receive a coil_index (i.e. map to an Icoil_N column)
COIL_TYPES = {"helix", "bitter"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_geometry_json(geometry_path) -> str | None:
    """
    Load a geometry YAML file via python_magnetgeo and return a JSON string
    (with ``__classname__`` annotations) suitable for storing in DuckDB.
    Returns None if the file is absent or python_magnetgeo is not available.
    """
    if not geometry_path:
        return None
    path = Path(geometry_path)
    if not path.exists():
        return None
    try:
        import json as _json
        import yaml as _yaml
        from python_magnetgeo.deserialize import serialize_instance
        with open(path) as f:
            obj = _yaml.load(f, Loader=_yaml.FullLoader)
        return _json.dumps(obj, default=serialize_instance)
    except Exception as exc:
        print(f"  [WARN] Could not serialize geometry '{geometry_path}': {exc}")
        return None


def _exists(con, table, name):
    return con.execute(f"SELECT 1 FROM {table} WHERE name = ?", [name]).fetchone() is not None


def _infer_magnet_type(parts):
    """Infer magnet assembly type from the types of its constituent parts."""
    coil_types = {p["type"] for p in parts if p["type"] in COIL_TYPES}
    if coil_types == {"helix"}:
        return "insert"
    if coil_types == {"bitter"}:
        return "bitters"
    if len(coil_types) > 1:
        return "hybrid"
    return "unknown"


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def _validate(data):
    errors = []
    if not data.get("name"):
        errors.append("Missing top-level 'name'")
    if not data.get("parts"):
        errors.append("'parts' list is empty or missing")
    for i, part in enumerate(data.get("parts", [])):
        if not part.get("name"):
            errors.append(f"Part[{i}] is missing 'name'")
        if not part.get("type"):
            errors.append(f"Part '{part.get('name', i)}' is missing 'type'")
        if not part.get("material") or not part["material"].get("name"):
            errors.append(f"Part '{part.get('name', i)}' is missing 'material.name'")
    return errors


# ---------------------------------------------------------------------------
# Insertion
# ---------------------------------------------------------------------------


def _insert_material(con, mat):
    name = mat["name"]
    if _exists(con, "materials", name):
        print(f"  ~ material  {name}  (already exists, skipped)")
        return
    con.execute(
        "INSERT INTO materials VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        [
            name,
            mat.get("description") or None,
            mat.get("nuance") or None,
            mat.get("t_ref"),
            mat.get("volumic_mass"),
            mat.get("specific_heat"),
            mat.get("alpha"),
            mat.get("electrical_conductivity"),
            mat.get("thermal_conductivity"),
            mat.get("magnet_permeability"),
            mat.get("young"),
            mat.get("poisson"),
            mat.get("expansion_coefficient"),
            mat.get("rpe"),
        ],
    )
    print(f"  + material  {name}  [{mat.get('nuance', '?')}]")


def _insert_part(con, part):
    name = part["name"]
    if _exists(con, "parts", name):
        print(f"  ~ part      {name}  (already exists, skipped)")
        return
    con.execute(
        """
        INSERT INTO parts
            (name, type, status, material_name, geometry, geometry_data, cad, design_office_reference)
        VALUES (?,?,?,?,?,?,?,?)
        """,
        [
            name,
            part.get("type"),
            part.get("status"),
            part["material"]["name"],
            part.get("geometry") or None,
            _load_geometry_json(part.get("geometry")),
            part.get("cad") or None,
            part.get("design_office_reference") or None,
        ],
    )
    print(f"  + part      {name}  [{part.get('type', '?')}]")


def _insert_magnet(con, data, magnet_type):
    name = data["name"]
    if _exists(con, "magnets", name):
        print(f"  ~ magnet    {name}  (already exists, skipped)")
        return
    con.execute(
        """
        INSERT INTO magnets
            (name, type, status, geometry, geometry_data, design_office_reference)
        VALUES (?,?,?,?,?,?)
        """,
        [
            name,
            magnet_type,
            data.get("status"),
            data.get("geometry") or None,
            _load_geometry_json(data.get("geometry")),
            data.get("design_office_reference") or None,
        ],
    )
    print(f"  + magnet    {name}  [{magnet_type}]  {data.get('status', '')}")


def _insert_magnet_parts(con, magnet_name, parts):
    coil_counter = 0
    inserted = 0
    skipped = 0
    for rank, part in enumerate(parts):
        part_name = part["name"]
        part_type = part.get("type", "")

        coil_index = None
        if part_type in COIL_TYPES:
            coil_counter += 1
            coil_index = coil_counter

        existing = con.execute(
            "SELECT 1 FROM magnet_parts WHERE magnet_name = ? AND part_name = ?",
            [magnet_name, part_name],
        ).fetchone()
        if existing:
            skipped += 1
            continue

        con.execute(
            "INSERT INTO magnet_parts VALUES (?,?,?,?)",
            [magnet_name, part_name, rank, coil_index],
        )
        inserted += 1

    print(
        f"  + magnet_parts  {inserted} inserted,  {skipped} already present"
        f"  ({coil_counter} coil channel(s))"
    )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def add_magnet(data, db_path, dry_run=False):
    """
    Insert a magnet (and its parts and materials) into the student DuckDB.

    Parameters
    ----------
    data     : dict matching the MagnetDB magnet JSON export format
    db_path  : path to the .duckdb file (created if it does not exist)
    dry_run  : if True, validate only — do not write
    """
    db_path = Path(db_path)

    errors = _validate(data)
    if errors:
        print("Validation errors:")
        for e in errors:
            print(f"  • {e}")
        sys.exit(1)

    parts = data["parts"]
    magnet_type = _infer_magnet_type(parts)

    if dry_run:
        coil_parts = [p for p in parts if p.get("type") in COIL_TYPES]
        print("[dry-run] Validation passed. Would insert:")
        print(f"  magnet   : {data['name']}  [{magnet_type}]  {data.get('status', '')}")
        print(f"  parts    : {len(parts)}  ({len(coil_parts)} coil channel(s))")
        mats = {p["material"]["name"] for p in parts if p.get("material")}
        print(f"  materials: {len(mats)}")
        return

    con = duckdb.connect(str(db_path))
    con.execute(SCHEMA_SQL)

    print(f"\nAdding magnet '{data['name']}' to {db_path.name} …\n")

    # 1. Materials (deduplicated — multiple parts may share one)
    seen_materials = set()
    for part in parts:
        mat = part.get("material", {})
        mat_name = mat.get("name")
        if mat_name and mat_name not in seen_materials:
            _insert_material(con, mat)
            seen_materials.add(mat_name)

    print()

    # 2. Parts
    for part in parts:
        _insert_part(con, part)

    print()

    # 3. Magnet
    _insert_magnet(con, data, magnet_type)

    print()

    # 4. Magnet–part links with coil_index
    _insert_magnet_parts(con, data["name"], parts)

    con.close()
    print("\nDone.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Add a magnet to the student DuckDB from a MagnetDB JSON export.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("json_file", help="Path to the magnet JSON file")
    parser.add_argument(
        "--db",
        default="student_magnetdb.duckdb",
        help="Target DuckDB file (default: student_magnetdb.duckdb; created if absent)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and preview without writing to the DB",
    )
    args = parser.parse_args()

    json_path = Path(args.json_file)
    if not json_path.exists():
        print(f"Error: '{json_path}' not found.")
        sys.exit(1)

    data = json.loads(json_path.read_text())
    add_magnet(data, args.db, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
