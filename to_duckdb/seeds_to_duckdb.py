"""
seeds_to_duckdb.py
==================
Build a student DuckDB database from MagnetDB seed files,
WITHOUT requiring a running Django stack or PostgreSQL.

Usage
-----
    pip install duckdb
    python seeds_to_duckdb.py [--output student_magnetdb.duckdb] [--seeds all|bitters|M19061901|...]

How it works
------------
The seed files (seeds-Bitters.py, seed-M19061901.py, …) call functions from
`python_magnetdb.seeds.crud` which write to Django ORM / PostgreSQL.

This script replaces that entire layer with lightweight stubs that capture
every create_*/query_* call and redirect the data into DuckDB instead.
No Django, no PostgreSQL, no MinIO needed.

coil_index assignment
---------------------
Parts are ordered in the `parts` list passed to `create_magnet()`.
Only parts of type 'helix' or 'bitter' receive a coil_index (1-based,
in their order of appearance). Parts of type 'ring' or 'lead' get NULL.
This matches the Icoil_N column convention in operational records.
"""

import argparse
import sys
import types
from pathlib import Path

import duckdb

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

COIL_TYPES = {"helix", "bitter"}  # these map to Icoil_N columns

# ---------------------------------------------------------------------------
# Lightweight mock objects returned by create_*/query_* stubs
# ---------------------------------------------------------------------------


class MockObject:
    """Minimal stand-in for a Django model instance."""

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __repr__(self):
        return f"<Mock name={self.__dict__.get('name', '?')}>"


# ---------------------------------------------------------------------------
# In-memory registry (shared across all seed modules loaded in one run)
# ---------------------------------------------------------------------------

_materials: dict[str, dict] = {}
_parts: dict[str, dict] = {}
_magnets: dict[str, dict] = {}
_sites: dict[str, dict] = {}
_records: list[dict] = []


# ---------------------------------------------------------------------------
# Stub implementations of crud.py functions
# ---------------------------------------------------------------------------


def _create_material(obj: dict) -> MockObject:
    name = obj["name"]
    if name not in _materials:
        _materials[name] = {
            "name": name,
            "description": obj.get("description"),
            "nuance": obj.get("nuance"),
            "t_ref": obj.get("t_ref"),
            "volumic_mass": obj.get("volumic_mass"),
            "specific_heat": obj.get("specific_heat"),
            "alpha": obj.get("alpha"),
            "electrical_conductivity": obj.get("electrical_conductivity"),
            "thermal_conductivity": obj.get("thermal_conductivity"),
            "magnet_permeability": obj.get("magnet_permeability"),
            "young": obj.get("young"),
            "poisson": obj.get("poisson"),
            "expansion_coefficient": obj.get("expansion_coefficient"),
            "rpe": float(obj["rpe"]) if obj.get("rpe") is not None else None,
        }
    return MockObject(**_materials[name])


def _create_part(obj: dict) -> MockObject:
    name = obj["name"]
    if name not in _parts:
        material = obj.get("material")
        material_name = material.name if isinstance(material, MockObject) else material
        _parts[name] = {
            "name": name,
            "type": obj.get("type"),
            "status": obj.get("status"),
            "material_name": material_name,
            "geometry": obj.get("geometry"),
            "cad": obj.get("cad"),
            "design_office_reference": obj.get("design_office_reference"),
        }
    return MockObject(**_parts[name])


def _create_site(obj: dict) -> MockObject:
    name = obj["name"]
    if name not in _sites:
        _sites[name] = {
            "name": name,
            "status": obj.get("status"),
            "config": obj.get("config"),
        }
    return MockObject(**_sites[name])


def _create_magnet(obj: dict) -> MockObject:
    name = obj["name"]
    if name not in _magnets:
        site = obj.get("site")
        site_name = site.name if isinstance(site, MockObject) else site

        parts = obj.get("parts", []) or []

        # Assign coil_index only to helix/bitter parts
        coil_counter = 0
        parts_list = []
        for rank, part in enumerate(parts):
            part_name = part.name if isinstance(part, MockObject) else part
            part_type = _parts.get(part_name, {}).get("type", "")
            if part_type in COIL_TYPES:
                coil_counter += 1
                coil_index = coil_counter
            else:
                coil_index = None
            parts_list.append(
                {
                    "magnet_name": name,
                    "part_name": part_name,
                    "rank": rank,
                    "coil_index": coil_index,
                }
            )

        # Normalise MagnetType enum → plain string
        mag_type = obj.get("type")
        if hasattr(mag_type, "value"):
            mag_type = mag_type.value
        elif hasattr(mag_type, "name"):
            mag_type = mag_type.name.lower()

        _magnets[name] = {
            "name": name,
            "type": str(mag_type) if mag_type else None,
            "status": obj.get("status"),
            "geometry": obj.get("geometry"),
            "site_name": site_name,
            "design_office_reference": obj.get("design_office_reference"),
            "_parts": parts_list,
        }
    return MockObject(**{k: v for k, v in _magnets[name].items() if k != "_parts"})


def _create_record(obj: dict) -> None:
    site = obj.get("site")
    site_name = site.name if isinstance(site, MockObject) else site
    _records.append(
        {
            "record_file": obj.get("file"),
            "site_name": site_name,
        }
    )


def _query_material(name: str) -> MockObject | None:
    return MockObject(**_materials[name]) if name in _materials else None


def _query_part(name: str) -> MockObject | None:
    return MockObject(**_parts[name]) if name in _parts else None


def _query_magnet(name: str) -> MockObject | None:
    return MockObject(**_magnets[name]) if name in _magnets else None


def _query_site(name: str) -> MockObject | None:
    return MockObject(**_sites[name]) if name in _sites else None


# ---------------------------------------------------------------------------
# Stub module: replaces python_magnetdb.seeds.crud
# ---------------------------------------------------------------------------


def _make_crud_module() -> types.ModuleType:
    mod = types.ModuleType("python_magnetdb.seeds.crud")
    mod.create_material = _create_material
    mod.create_part = _create_part
    mod.create_site = _create_site
    mod.create_magnet = _create_magnet
    mod.create_record = _create_record
    mod.query_material = _query_material
    mod.query_part = _query_part
    mod.query_magnet = _query_magnet
    mod.query_site = _query_site
    # Some seeds also import these names directly
    mod.upload_attachment = lambda *a, **kw: None
    return mod


# ---------------------------------------------------------------------------
# Stub module: replaces python_magnetdb.models.magnet (for MagnetType enum)
# ---------------------------------------------------------------------------


def _make_models_module() -> types.ModuleType:
    from enum import Enum

    class MagnetType(str, Enum):
        INSERT = "insert"
        BITTERS = "bitters"
        SUPRA = "supra"
        HYBRID = "hybrid"

    mod = types.ModuleType("python_magnetdb.models.magnet")
    mod.MagnetType = MagnetType
    return mod


# ---------------------------------------------------------------------------
# Inject stubs into sys.modules before any seed is imported
# ---------------------------------------------------------------------------


def _install_stubs() -> None:
    # Ensure parent packages exist as empty modules so Python is happy
    for pkg in [
        "python_magnetdb",
        "python_magnetdb.models",
        "python_magnetdb.seeds",
    ]:
        if pkg not in sys.modules:
            sys.modules[pkg] = types.ModuleType(pkg)

    sys.modules["python_magnetdb.seeds.crud"] = _make_crud_module()
    sys.modules["python_magnetdb.models.magnet"] = _make_models_module()

    # Silence getenv("DATA_DIR") calls in seeds — not needed here
    import os

    os.environ.setdefault("DATA_DIR", "/tmp/dummy_data_dir")


# ---------------------------------------------------------------------------
# Load seed modules by name
# ---------------------------------------------------------------------------

SEED_MODULES = {
    "bitters": "python_magnetdb.seeds.seeds-Bitters",
    "M19061901": "python_magnetdb.seeds.seed-M19061901",
    "M19071101": "python_magnetdb.seeds.seed-M19071101",
    "M18110501": "python_magnetdb.seeds.seed-M18110501",
    "M20022001": "python_magnetdb.seeds.seed-M20022001",
    "M22011801": "python_magnetdb.seeds.seed-M22011801",
    "records": "python_magnetdb.seeds.seed-records",
}


def _load_seed(key: str, repo_root: Path) -> None:
    """
    Import a seed module from the repo without requiring it to be installed.
    We load it as a regular file using importlib.util so that relative imports
    (from .crud import …) work by virtue of the stubs already being in sys.modules.
    """
    import importlib.util

    # Map dotted name → file path
    # e.g. "python_magnetdb.seeds.seeds-Bitters" → repo_root/python_magnetdb/seeds/seeds-Bitters.py
    module_name = SEED_MODULES[key]
    rel_path = Path(*module_name.split(".")).with_suffix(".py")
    file_path = repo_root / rel_path

    if not file_path.exists():
        print(f"  [SKIP] {file_path} not found")
        return

    print(f"  Loading {file_path} …")
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    try:
        spec.loader.exec_module(mod)
    except Exception as exc:
        print(f"  [WARN] Error in {file_path.name}: {exc}")


# ---------------------------------------------------------------------------
# Write collected data to DuckDB
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
    rpe                     DOUBLE      -- Pa (elastic limit)
);

CREATE TABLE IF NOT EXISTS parts (
    name                    VARCHAR PRIMARY KEY,
    type                    VARCHAR,    -- 'helix' | 'ring' | 'bitter' | 'lead'
    status                  VARCHAR,
    material_name           VARCHAR REFERENCES materials(name),
    geometry                VARCHAR,    -- geometry YAML stem (no extension)
    geometry_data           JSON,       -- python_magnetgeo object serialized as JSON
    cad                     VARCHAR,    -- CAD file stem
    design_office_reference VARCHAR
);

CREATE TABLE IF NOT EXISTS sites (
    name    VARCHAR PRIMARY KEY,
    status  VARCHAR,
    config  VARCHAR     -- .conf filename if available
);

CREATE TABLE IF NOT EXISTS magnets (
    name                    VARCHAR PRIMARY KEY,
    type                    VARCHAR,    -- 'insert' | 'bitters' | 'supra' | 'hybrid'
    status                  VARCHAR,
    geometry                VARCHAR,
    geometry_data           JSON,       -- python_magnetgeo object serialized as JSON
    site_name               VARCHAR REFERENCES sites(name),
    design_office_reference VARCHAR
);

-- Migration: add geometry_data to existing databases (no-op if already present)
ALTER TABLE parts   ADD COLUMN IF NOT EXISTS geometry_data JSON;
ALTER TABLE magnets ADD COLUMN IF NOT EXISTS geometry_data JSON;

CREATE TABLE IF NOT EXISTS magnet_parts (
    magnet_name VARCHAR REFERENCES magnets(name),
    part_name   VARCHAR REFERENCES parts(name),
    rank        INTEGER,    -- 0-based position in original parts list
    coil_index  INTEGER,    -- 1-based index among helix/bitter parts; NULL for rings/leads
    PRIMARY KEY (magnet_name, part_name)
);

CREATE TABLE IF NOT EXISTS experiments (
    id          INTEGER PRIMARY KEY,
    site_name   VARCHAR REFERENCES sites(name),
    record_file VARCHAR,
    status      VARCHAR DEFAULT 'pending'
);
"""


def _write_to_duckdb(output_path: Path) -> None:
    print(f"\nWriting to {output_path} …")
    con = duckdb.connect(str(output_path))
    con.execute(SCHEMA_SQL)

    # Materials
    for m in _materials.values():
        con.execute(
            """
            INSERT OR REPLACE INTO materials VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
            [
                m["name"],
                m["description"],
                m["nuance"],
                m["t_ref"],
                m["volumic_mass"],
                m["specific_heat"],
                m["alpha"],
                m["electrical_conductivity"],
                m["thermal_conductivity"],
                m["magnet_permeability"],
                m["young"],
                m["poisson"],
                m["expansion_coefficient"],
                m["rpe"],
            ],
        )

    # Parts
    for p in _parts.values():
        con.execute(
            """
            INSERT OR REPLACE INTO parts
                (name, type, status, material_name, geometry, geometry_data, cad, design_office_reference)
            VALUES (?,?,?,?,?,NULL,?,?)
        """,
            [
                p["name"],
                p["type"],
                p["status"],
                p["material_name"],
                p["geometry"],
                p["cad"],
                p["design_office_reference"],
            ],
        )

    # Sites
    for s in _sites.values():
        con.execute(
            "INSERT OR REPLACE INTO sites VALUES (?,?,?)", [s["name"], s["status"], s["config"]]
        )

    # Magnets + magnet_parts
    for m in _magnets.values():
        con.execute(
            """
            INSERT OR REPLACE INTO magnets
                (name, type, status, geometry, geometry_data, site_name, design_office_reference)
            VALUES (?,?,?,?,NULL,?,?)
        """,
            [
                m["name"],
                m["type"],
                m["status"],
                m["geometry"],
                m["site_name"],
                m["design_office_reference"],
            ],
        )
        for mp in m["_parts"]:
            con.execute(
                """
                INSERT OR REPLACE INTO magnet_parts VALUES (?,?,?,?)
            """,
                [mp["magnet_name"], mp["part_name"], mp["rank"], mp["coil_index"]],
            )

    # Experiments (from seed-records)
    for i, r in enumerate(_records):
        con.execute(
            """
            INSERT OR REPLACE INTO experiments VALUES (?,?,?,'pending')
        """,
            [i + 1, r["site_name"], r["record_file"]],
        )

    con.close()

    _print_summary(output_path)


def _print_summary(output_path: Path) -> None:
    con = duckdb.connect(str(output_path), read_only=True)
    print("\n── Database summary ──────────────────────────────────")
    for table in ["materials", "parts", "sites", "magnets", "magnet_parts", "experiments"]:
        n = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  {table:<20} {n:>4} rows")

    print("\n── coil_index distribution ───────────────────────────")
    rows = con.execute(
        """
        SELECT m.name AS magnet, p.type, mp.coil_index, mp.part_name
        FROM magnet_parts mp
        JOIN parts p  ON p.name  = mp.part_name
        JOIN magnets m ON m.name = mp.magnet_name
        WHERE mp.coil_index IS NOT NULL
        ORDER BY m.name, mp.coil_index
    """
    ).fetchall()
    current_magnet = None
    for magnet, ptype, ci, pname in rows:
        if magnet != current_magnet:
            print(f"\n  {magnet}")
            current_magnet = magnet
        print(f"    Icoil{ci:<3}  {ptype:<8}  {pname}")
    con.close()


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--output",
        default="student_magnetdb.duckdb",
        help="Output DuckDB file path (default: student_magnetdb.duckdb)",
    )
    parser.add_argument(
        "--seeds",
        default="all",
        help=(
            "Comma-separated list of seeds to load, or 'all'. "
            f"Known keys: {', '.join(SEED_MODULES)}"
        ),
    )
    parser.add_argument(
        "--repo", default=".", help="Path to the magnetdb repo root (default: current directory)"
    )
    args = parser.parse_args()

    repo_root = Path(args.repo).resolve()
    output = Path(args.output)

    keys = list(SEED_MODULES) if args.seeds == "all" else [k.strip() for k in args.seeds.split(",")]

    unknown = [k for k in keys if k not in SEED_MODULES]
    if unknown:
        print(f"Unknown seed keys: {unknown}. Available: {list(SEED_MODULES)}")
        sys.exit(1)

    print("Installing Django/crud stubs …")
    _install_stubs()

    print(f"\nLoading seeds from {repo_root}:")
    for key in keys:
        _load_seed(key, repo_root)

    print(
        f"\nCollected: {len(_materials)} materials, {len(_parts)} parts, "
        f"{len(_sites)} sites, {len(_magnets)} magnets, {len(_records)} experiments"
    )

    _write_to_duckdb(output)
    print(f"\nDone → {output.resolve()}")


if __name__ == "__main__":
    main()
