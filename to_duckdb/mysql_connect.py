"""
mysql_connect.py
================
Connect DuckDB to a remote MySQL server.

Two modes are available:

live
    Attach the MySQL database via the ``mysql_scanner`` extension and print the
    full schema (tables + column names/types).  No local copy is made.  Use
    this mode first to inspect an unknown MySQL database before deciding on an
    export or poll strategy.

export
    Copy tables from MySQL into a local file.  Three output formats are
    supported (``--format``):

    csv      One CSV file per table in ``--output-dir``.
    parquet  One Parquet file per table in ``--output-dir``.
    duckdb   All tables in a single DuckDB file (``--output``).
             The file is created if it does not exist.
             Existing tables are replaced (``CREATE OR REPLACE``).

Usage
-----
    # Inspect schema of an unknown MySQL database
    python mysql_connect.py --mode live \\
        --host myhost --user myuser --password mypw --database mydb

    # Export all tables to CSV files in ./out/
    python mysql_connect.py --mode export --format csv --output-dir ./out \\
        --host myhost --user myuser --password mypw --database mydb

    # Export selected tables to a DuckDB file
    python mysql_connect.py --mode export --format duckdb \\
        --output magnetdb_mysql.duckdb --tables sites magnets \\
        --host myhost --user myuser --password mypw --database mydb

Connection parameters may also be supplied via environment variables
(MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB).
CLI flags take precedence over env vars; env vars take precedence over
built-in defaults.
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Optional

import duckdb


# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

_DEFAULT_HOST = "localhost"
_DEFAULT_PORT = 3306
_DEFAULT_OUTPUT = "magnetdb_mysql.duckdb"
_DEFAULT_OUTPUT_DIR = "."


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _env(key: str, default: Optional[str] = None) -> Optional[str]:
    return os.environ.get(key, default)


def _build_dsn(
    host: str, port: int, user: str, password: str, database: str
) -> str:
    """Build a mysql_scanner DSN string."""
    return (
        f"host={host} port={port} user={user} "
        f"password={password} database={database}"
    )


def _load_mysql_extension(
    con: duckdb.DuckDBPyConnection, verbose: bool = False
) -> None:
    """Install and load the mysql_scanner DuckDB extension."""
    if verbose:
        print("Loading mysql_scanner extension...")
    con.execute("INSTALL mysql; LOAD mysql;")


def _attach_mysql(
    con: duckdb.DuckDBPyConnection, dsn: str, verbose: bool = False
) -> None:
    """Attach a MySQL database as the alias 'mysqldb'."""
    if verbose:
        print("Attaching MySQL database...")
    con.execute(f"ATTACH '{dsn}' AS mysqldb (TYPE mysql_scanner)")


def list_mysql_tables(con: duckdb.DuckDBPyConnection) -> list[str]:
    """Return sorted list of table names in the attached MySQL database.

    Parameters
    ----------
    con : duckdb.DuckDBPyConnection
        Open connection with mysqldb already attached.

    Returns
    -------
    list[str]
        Table names, sorted alphabetically.
    """
    rows = con.execute(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_catalog = 'mysqldb' ORDER BY table_name"
    ).fetchall()
    return [r[0] for r in rows]


def describe_table(
    con: duckdb.DuckDBPyConnection, table: str
) -> list[tuple]:
    """Return column descriptors for a single table.

    Parameters
    ----------
    con : duckdb.DuckDBPyConnection
        Open connection with mysqldb already attached.
    table : str
        Table name (unqualified).

    Returns
    -------
    list[tuple]
        Each tuple: (column_name, column_type, ...) as returned by DESCRIBE.
    """
    return con.execute(f"DESCRIBE mysqldb.{table}").fetchall()


# ---------------------------------------------------------------------------
# Mode: live
# ---------------------------------------------------------------------------


def mode_live(args: argparse.Namespace) -> None:
    """Attach MySQL and print the full schema summary.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed CLI arguments.
    """
    dsn = _build_dsn(args.host, args.port, args.user, args.password, args.database)
    con = duckdb.connect()
    _load_mysql_extension(con, args.verbose)
    _attach_mysql(con, dsn, args.verbose)

    tables = list_mysql_tables(con)
    print(f"Connected to {args.database}@{args.host}:{args.port}")
    print(f"{len(tables)} table(s) found:\n")

    for table in tables:
        cols = describe_table(con, table)
        print(f"  {table}")
        for col in cols:
            col_name, col_type = col[0], col[1]
            print(f"    {col_name:<30}  {col_type}")
        print()


# ---------------------------------------------------------------------------
# Mode: export
# ---------------------------------------------------------------------------


def mode_export(args: argparse.Namespace) -> None:
    """Export MySQL tables to a local file (CSV, Parquet, or DuckDB).

    Parameters
    ----------
    args : argparse.Namespace
        Parsed CLI arguments.
    """
    dsn = _build_dsn(args.host, args.port, args.user, args.password, args.database)

    if args.fmt == "duckdb":
        con = duckdb.connect(args.output)
        if args.verbose:
            print(f"Output database: {args.output}")
    else:
        con = duckdb.connect()
        out_dir = Path(args.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

    _load_mysql_extension(con, args.verbose)
    _attach_mysql(con, dsn, args.verbose)

    all_tables = list_mysql_tables(con)
    tables = args.tables if args.tables else all_tables

    unknown = set(tables) - set(all_tables)
    if unknown:
        print(
            f"Error: unknown table(s): {', '.join(sorted(unknown))}",
            file=sys.stderr,
        )
        sys.exit(1)

    if args.verbose:
        print(f"Exporting {len(tables)} table(s): {', '.join(tables)}")

    for table in tables:
        if args.fmt == "duckdb":
            con.execute(
                f"CREATE OR REPLACE TABLE {table} AS SELECT * FROM mysqldb.{table}"
            )
            if args.verbose:
                n = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                print(f"  {table}: {n} row(s)")

        elif args.fmt == "csv":
            dest = Path(args.output_dir) / f"{table}.csv"
            con.execute(
                f"COPY (SELECT * FROM mysqldb.{table}) TO '{dest}' "
                f"(HEADER, DELIMITER ',')"
            )
            if args.verbose:
                print(f"  {table} → {dest}")

        elif args.fmt == "parquet":
            dest = Path(args.output_dir) / f"{table}.parquet"
            con.execute(
                f"COPY (SELECT * FROM mysqldb.{table}) TO '{dest}' "
                f"(FORMAT PARQUET)"
            )
            if args.verbose:
                print(f"  {table} → {dest}")

    print(f"Export complete: {len(tables)} table(s).")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    """Parse and validate command-line arguments.

    Returns
    -------
    argparse.Namespace
        Validated arguments with connection parameters resolved from
        CLI flags → env vars → built-in defaults (highest priority first).
    """
    parser = argparse.ArgumentParser(
        description="Connect DuckDB to a remote MySQL server.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Parameters can also be set via environment variables (e.g. direnv):\n"
            "  MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB\n"
            "  MYSQL_OUTPUT, MYSQL_OUTPUT_DIR\n\n"
            "Examples:\n"
            "  %(prog)s --mode live --host db.example.com --user admin"
            " --password secret --database magnetdb\n"
            "  %(prog)s --mode export --format csv --output-dir ./out"
            " --host db.example.com --user admin --password secret"
            " --database magnetdb\n"
        ),
    )

    parser.add_argument(
        "--mode",
        choices=["live", "export"],
        default="live",
        help="live: attach MySQL and print schema (default); "
             "export: copy tables to a local file",
    )

    # Connection parameters
    conn = parser.add_argument_group("MySQL connection")
    conn.add_argument(
        "--host",
        default=_env("MYSQL_HOST", _DEFAULT_HOST),
        metavar="HOST",
        help=f"MySQL host (env: MYSQL_HOST, default: {_DEFAULT_HOST})",
    )
    conn.add_argument(
        "--port",
        type=int,
        default=int(_env("MYSQL_PORT", str(_DEFAULT_PORT))),
        metavar="PORT",
        help=f"MySQL port (env: MYSQL_PORT, default: {_DEFAULT_PORT})",
    )
    conn.add_argument(
        "--user",
        default=_env("MYSQL_USER"),
        metavar="USER",
        help="MySQL user (env: MYSQL_USER, required)",
    )
    conn.add_argument(
        "--password",
        default=_env("MYSQL_PASSWORD"),
        metavar="PASSWORD",
        help="MySQL password (env: MYSQL_PASSWORD, required)",
    )
    conn.add_argument(
        "--database",
        default=_env("MYSQL_DB"),
        metavar="DATABASE",
        help="MySQL database name (env: MYSQL_DB, required)",
    )

    # Export options
    exp = parser.add_argument_group("export options (--mode export only)")
    exp.add_argument(
        "--format",
        choices=["csv", "parquet", "duckdb"],
        default="csv",
        dest="fmt",
        metavar="{csv,parquet,duckdb}",
        help="output format (default: csv)",
    )
    exp.add_argument(
        "--output",
        default=_env("MYSQL_OUTPUT", _DEFAULT_OUTPUT),
        metavar="FILE",
        help=f"DuckDB output file for --format duckdb "
             f"(env: MYSQL_OUTPUT, default: {_DEFAULT_OUTPUT})",
    )
    exp.add_argument(
        "--output-dir",
        default=_env("MYSQL_OUTPUT_DIR", _DEFAULT_OUTPUT_DIR),
        metavar="DIR",
        help="output directory for CSV/Parquet files "
             "(env: MYSQL_OUTPUT_DIR, default: current dir)",
    )
    exp.add_argument(
        "--tables",
        nargs="+",
        metavar="TABLE",
        help="subset of tables to export (default: all)",
    )

    parser.add_argument("-v", "--verbose", action="store_true", help="verbose output")

    args = parser.parse_args()

    missing = [
        name
        for name, val in [
            ("--user / MYSQL_USER", args.user),
            ("--password / MYSQL_PASSWORD", args.password),
            ("--database / MYSQL_DB", args.database),
        ]
        if not val
    ]
    if missing:
        parser.error(
            "Missing required connection parameter(s): "
            + ", ".join(missing)
        )

    return args


def main() -> None:
    args = parse_args()
    try:
        if args.mode == "live":
            mode_live(args)
        else:
            mode_export(args)
    except duckdb.Error as e:
        print(f"DuckDB error: {e}", file=sys.stderr)
        sys.exit(1)
    except OSError as e:
        print(f"I/O error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
