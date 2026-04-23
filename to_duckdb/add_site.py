"""
add_site.py
===========
Add a site to an existing student DuckDB database from a JSON file
matching the MagnetDB site export format.

Magnets referenced in the JSON that are not yet in the database are loaded
automatically from a same-named JSON file (e.g. M19071101.json) found in the
same directory as the site JSON (or the directory given by --magnet-dir).
If no such file is found the script fails with a clear message.

JSON format (as exported from MagnetDB)
----------------------------------------
{
    "name":               "M10_M19071101_13",
    "description":        "",
    "status":             "in_operation",
    "housing":            "M10",
    "commissioned_at":    "2025-11-12 00:00:00",
    "decommissioned_at":  "None",
    "magnets": [
        "M19071101",
        "M10Bitters"
    ],
    "records": [
        {
            "name":        "M10_2025.11.13---09:14:21.txt",
            "description": "",
            "file":        "M10_2025.11.13---09:14:21.txt"
        },
        ...
    ]
}

Usage
-----
    python add_site.py M10_M19071101_13.json
    python add_site.py M10_M19071101_13.json --db path/to/student.duckdb
    python add_site.py M10_M19071101_13.json --dry-run
    python add_site.py M10_M19071101_13.json --magnet-dir /path/to/magnet/jsons
"""

import argparse
import json
import sys
from pathlib import Path

import duckdb

from add_magnet import add_magnet

# ---------------------------------------------------------------------------
# Schema DDL
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

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_timestamp(value):
    if not value or str(value).lower() in ("none", "null", ""):
        return None
    return str(value)


def _exists(con, table, name):
    return con.execute(f"SELECT 1 FROM {table} WHERE name = ?", [name]).fetchone() is not None


def _next_experiment_id(con):
    row = con.execute("SELECT COALESCE(MAX(id), 0) FROM experiments").fetchone()
    return (row[0] or 0) + 1


# ---------------------------------------------------------------------------
# Auto-load missing magnets
# ---------------------------------------------------------------------------


def _ensure_magnets(magnet_names, db_path, magnet_dir, dry_run=False):
    """
    For every magnet in *magnet_names* that is absent from the DB, try to
    load it from ``<magnet_dir>/<magnet_name>.json`` using add_magnet.
    Returns a list of error strings for magnets that cannot be resolved.
    Each call to add_magnet opens and closes its own connection, so we
    check existence with a short-lived connection per iteration.
    """
    errors = []
    for name in magnet_names:
        # Check with a fresh read-only connection to avoid lock conflicts
        with duckdb.connect(str(db_path)) as chk:
            found = (
                chk.execute("SELECT 1 FROM magnets WHERE name = ?", [name]).fetchone() is not None
            )
        if found:
            continue
        json_path = Path(magnet_dir) / f"{name}.json"
        if not json_path.exists():
            errors.append(
                f"Magnet '{name}' not in DB and '{json_path}' not found. "
                f"Load it manually with:  python add_magnet.py {name}.json"
            )
            continue
        print(f"  ~ magnet '{name}' not in DB — loading from {json_path.name} …")
        magnet_data = json.loads(json_path.read_text())
        add_magnet(magnet_data, db_path, dry_run=dry_run)
    return errors


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def _validate(data):
    errors = []

    if not data.get("name"):
        errors.append("Missing 'name'")
    if not data.get("magnets"):
        errors.append("'magnets' list is empty or missing")

    return errors


# ---------------------------------------------------------------------------
# Insertion
# ---------------------------------------------------------------------------


def _insert_site(con, data):
    name = data["name"]
    if _exists(con, "sites", name):
        print(f"  ~ site      {name}  (already exists, skipped)")
        return

    con.execute(
        "INSERT INTO sites VALUES (?,?,?,?,?,?)",
        [
            name,
            data.get("description") or None,
            data.get("status", "in_study"),
            data.get("housing") or None,
            _parse_timestamp(data.get("commissioned_at")),
            _parse_timestamp(data.get("decommissioned_at")),
        ],
    )
    print(f"  + site      {name}  [{data.get('housing', '?')}]  {data.get('status', '')}")


def _insert_site_magnets(con, site_name, magnet_names):
    for magnet_name in magnet_names:
        existing = con.execute(
            "SELECT 1 FROM site_magnets WHERE site_name = ? AND magnet_name = ?",
            [site_name, magnet_name],
        ).fetchone()
        if existing:
            print(f"  ~ magnet    {magnet_name}  (already linked, skipped)")
            continue

        con.execute("INSERT INTO site_magnets VALUES (?,?)", [site_name, magnet_name])
        row = con.execute("SELECT type FROM magnets WHERE name = ?", [magnet_name]).fetchone()
        mag_type = row[0] if row else "?"
        print(f"  + magnet    {magnet_name}  ({mag_type})")


def _insert_experiments(con, site_name, records):
    next_id = _next_experiment_id(con)
    inserted = 0
    skipped = 0

    for i, rec in enumerate(records):
        file_name = rec.get("file") or rec.get("name")
        existing = con.execute(
            "SELECT 1 FROM experiments WHERE site_name = ? AND file = ?",
            [site_name, file_name],
        ).fetchone()
        if existing:
            skipped += 1
            continue

        con.execute(
            "INSERT INTO experiments VALUES (?,?,?,?,?,'pending')",
            [
                next_id + i,
                rec.get("name") or file_name,
                rec.get("description") or None,
                file_name,
                site_name,
            ],
        )
        inserted += 1

    print(f"  + records   {inserted} inserted,  {skipped} already present")


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def add_site(data, db_path, dry_run=False, magnet_dir=None):
    """
    Insert a site and its records into the student DuckDB.

    Parameters
    ----------
    data       : dict matching the MagnetDB site JSON export format
    db_path    : path to the .duckdb file
    dry_run    : if True, validate only — do not write
    magnet_dir : directory to search for <magnet_name>.json files when a
                 magnet is missing from the DB (default: current directory)
    """
    db_path = Path(db_path)
    if magnet_dir is None:
        magnet_dir = Path(".")
    else:
        magnet_dir = Path(magnet_dir)

    if not db_path.exists():
        print(f"Error: '{db_path}' does not exist.")
        print("Create it first with:  python seeds_to_duckdb.py  or  python add_magnet.py")
        sys.exit(1)

    con = duckdb.connect(str(db_path))
    # Ensure schema is current (idempotent — safe on existing DBs)
    con.execute(SCHEMA_SQL)

    errors = _validate(data)
    if errors:
        print("Validation errors:")
        for e in errors:
            print(f"  • {e}")
        con.close()
        sys.exit(1)

    # Auto-load any magnets that are missing from the DB.
    # Close our connection first so add_magnet can open its own without
    # hitting a lock on platforms that restrict concurrent writers.
    con.close()
    missing_errors = _ensure_magnets(data.get("magnets", []), db_path, magnet_dir, dry_run=dry_run)
    if missing_errors:
        print("Errors resolving magnets:")
        for e in missing_errors:
            print(f"  • {e}")
        sys.exit(1)

    if dry_run:
        print("[dry-run] Validation passed. Would insert:")
        print(f"  site     : {data['name']}  [{data.get('housing', '?')}]")
        print(f"  magnets  : {data.get('magnets', [])}")
        print(f"  records  : {len(data.get('records', []))}")
        return

    # Reopen for the actual inserts
    site_name = data["name"]
    con = duckdb.connect(str(db_path))
    print(f"\nAdding site '{site_name}' to {db_path.name} …\n")

    _insert_site(con, data)
    _insert_site_magnets(con, site_name, data.get("magnets", []))
    _insert_experiments(con, site_name, data.get("records", []))

    con.close()
    print("\nDone.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Add a site to the student DuckDB from a MagnetDB JSON export.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("json_file", help="Path to the site JSON file")
    parser.add_argument(
        "--db",
        default="student_magnetdb.duckdb",
        help="Target DuckDB file (default: student_magnetdb.duckdb)",
    )
    parser.add_argument(
        "--magnet-dir",
        default=None,
        help=(
            "Directory to search for <magnet_name>.json files when a magnet is "
            "missing from the DB (default: same directory as the site JSON file)"
        ),
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

    magnet_dir = args.magnet_dir if args.magnet_dir else json_path.parent
    data = json.loads(json_path.read_text())
    add_site(data, args.db, dry_run=args.dry_run, magnet_dir=magnet_dir)


if __name__ == "__main__":
    main()
