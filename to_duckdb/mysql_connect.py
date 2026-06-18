"""
mysql_connect.py
================
Connect DuckDB to a remote MySQL server.

Three modes are available:

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

view
    Query a MySQL table (or custom SQL) once and render the result as a
    styled table in the terminal using ``rich``.  Use ``--table`` or
    ``--query``, optionally filtered with ``--where``.  ``--limit`` caps
    the number of rows returned (default: 200; use ``--limit 0`` for all rows).

poll
    Repeatedly query a single MySQL table at a fixed interval and display
    selected columns as a live plot.  Backend is selected via ``--plot``:

    matplotlib   Live-updating chart in a native window (default).
    plotly       Writes an auto-refreshing HTML file (default: poll_output.html)
                 and opens it in the default browser on the first poll.
    textual      Full-screen TUI in the terminal.  One Sparkline per y-field,
                 updated every interval seconds.  Press q to quit, p to pause.
    dash         Interactive web app served at http://127.0.0.1:8050 (default).
                 Uses dcc.Interval for live updates — no page refresh.
                 Pause button, zoom/pan, and hover tooltips included.
                 Host and port are set via --dash-host / --dash-port.

    --plot-options accepts a JSON object with any of:
        type      "line" | "scatter" | "bar"        (default "line")
        layout    "subplots" | "overlay" | "groups" (default "subplots")
                    subplots  one subplot per field
                    overlay   all fields on a single shared axes
                    groups    user-defined groups; also set "groups" key
        groups    list of field-name lists, e.g. [["Icoil","Ucoil"],["tsb","teb"]]
                    required when layout="groups"
        figsize   [width, height] in inches         (default [12, 6], matplotlib only)
        colors    list of color strings, one per y-field
        font      font family name, e.g. "DejaVu Sans" / "Arial" / "monospace"
        fontsize  base font size in points, e.g. 12

Usage
-----
    # Inspect schema
    python mysql_connect.py --mode live \\
        --host myhost --user myuser --password mypw --database mydb

    # Export to CSV
    python mysql_connect.py --mode export --format csv --output-dir ./out \\
        --host myhost --user myuser --password mypw --database mydb

    # Export selected tables to DuckDB
    python mysql_connect.py --mode export --format duckdb \\
        --output magnetdb_mysql.duckdb --tables sites magnets \\
        --host myhost --user myuser --password mypw --database mydb

    # Poll every 10 s, matplotlib line plot
    python mysql_connect.py --mode poll --table measurements \\
        --fields timestamp Icoil Ucoil --x-field timestamp \\
        --interval 10 --limit 200 --plot matplotlib \\
        --plot-options '{"type":"line","figsize":[14,6],"colors":["steelblue","tomato"]}' \\
        --host myhost --user myuser --password mypw --database mydb

    # Same with plotly (opens browser, writes poll_output.html)
    python mysql_connect.py --mode poll --table measurements \\
        --fields timestamp Icoil Ucoil --x-field timestamp \\
        --interval 10 --limit 200 --plot plotly \\
        --plot-options '{"type":"scatter","colors":["navy","crimson"]}' \\
        --host myhost --user myuser --password mypw --database mydb

    # View most recent 50 rows of measurements as a table
    python mysql_connect.py --mode view --table measurements --limit 50 \\
        --host myhost --user myuser --password mypw --database mydb

    # View all rows matching a filter, no row cap
    python mysql_connect.py --mode view --table measurements \\
        --where "label='run42'" --limit 0 \\
        --host myhost --user myuser --password mypw --database mydb

Connection parameters may also be supplied via environment variables
(MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB).
CLI flags take precedence over env vars; env vars take precedence over
built-in defaults.
"""

import argparse
import collections
import json
import os
import sys
import time
import webbrowser
from pathlib import Path
from typing import Any, Optional

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


def list_mysql_tables(con: duckdb.DuckDBPyConnection, database: str) -> list[str]:
    """Return sorted list of table names in the attached MySQL database.

    Parameters
    ----------
    con : duckdb.DuckDBPyConnection
        Open connection with mysqldb already attached.
    database : str
        The MySQL database (schema) name to list tables from.

    Returns
    -------
    list[str]
        Table names, sorted alphabetically.
    """
    rows = con.execute(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_catalog = 'mysqldb' AND table_schema = ? ORDER BY table_name",
        [database],
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


# DuckDB type-name prefixes that are safe to plot as numeric y-values.
# MySQL types are translated by mysql_scanner: FLOAT→FLOAT, DOUBLE→DOUBLE,
# INT/BIGINT/…→INTEGER/BIGINT/…, DECIMAL→DECIMAL, etc.
_NUMERIC_PREFIXES = (
    "FLOAT", "DOUBLE", "DECIMAL", "NUMERIC", "REAL",
    "INTEGER", "INT", "BIGINT", "SMALLINT", "TINYINT",
    "HUGEINT", "UBIGINT", "UINTEGER", "USMALLINT", "UTINYINT",
)

# DuckDB type-name prefixes that are suitable as an x-axis (time axis).
# MySQL TIMESTAMP / DATETIME → DuckDB TIMESTAMP; MySQL DATE → DuckDB DATE.
_TIMESTAMP_PREFIXES = ("TIMESTAMP", "TIMESTAMPTZ", "DATE", "DATETIME")


def _is_numeric_type(col_type: str) -> bool:
    """Return True if the DuckDB column type is numeric / plottable as y."""
    upper = col_type.upper().strip()
    return upper.startswith(_NUMERIC_PREFIXES)


def _is_timestamp_type(col_type: str) -> bool:
    """Return True if the DuckDB column type is temporal (suitable as x-axis)."""
    upper = col_type.upper().strip()
    return upper.startswith(_TIMESTAMP_PREFIXES)


def _auto_x_field(cols: list[tuple[str, str]]) -> Optional[str]:
    """Return the name of the first TIMESTAMP column in *cols*, or None."""
    for name, col_type in cols:
        if _is_timestamp_type(col_type):
            return name
    return None


def list_numeric_columns(
    con: duckdb.DuckDBPyConnection, table: str
) -> list[tuple[str, str]]:
    """Return (name, type) pairs for numeric columns in *table*.

    Parameters
    ----------
    con : duckdb.DuckDBPyConnection
        Open connection with mysqldb already attached.
    table : str
        Table name (unqualified).

    Returns
    -------
    list[tuple[str, str]]
        ``[(column_name, column_type), ...]`` for all numeric columns,
        in schema order.
    """
    return [
        (c[0], c[1])
        for c in describe_table(con, table)
        if _is_numeric_type(c[1])
    ]


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

    tables = list_mysql_tables(con, args.database)
    print(f"Connected to {args.database}@{args.host}:{args.port}")
    print(f"{len(tables)} table(s) found:\n")

    for table in tables:
        cols = describe_table(con, table)
        print(f"  {table}")
        for col in cols:
            col_name, col_type = col[0], col[1]
            if _is_numeric_type(col_type):
                marker = " *"
            elif _is_timestamp_type(col_type):
                marker = " @"
            else:
                marker = ""
            print(f"    {col_name:<30}  {col_type}{marker}")
        print()
    print("(* = numeric / y-axis  @ = timestamp / x-axis)")


# ---------------------------------------------------------------------------
# Mode: export
# ---------------------------------------------------------------------------


def _build_export_select(
    table: str,
    fields: list[str],
    time_field: Optional[str],
    start: Optional[str],
    end: Optional[str],
) -> str:
    """Build a SELECT for exporting *table* with optional column and time filtering."""
    field_list = ", ".join(fields) if fields else "*"
    sql = f"SELECT {field_list} FROM mysqldb.{table}"
    conditions: list[str] = []
    if time_field and start:
        conditions.append(f"{time_field} >= CAST('{start}' AS TIMESTAMP)")
    if time_field and end:
        conditions.append(f"{time_field} <= CAST('{end}' AS TIMESTAMP)")
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    return sql


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

    all_tables = list_mysql_tables(con, args.database)
    tables = args.tables if args.tables else all_tables

    unknown = set(tables) - set(all_tables)
    if unknown:
        print(
            f"Error: unknown table(s): {', '.join(sorted(unknown))}",
            file=sys.stderr,
        )
        sys.exit(1)

    # ── field / time-range filtering (requires a single table) ──────────────
    filtered = bool(args.export_fields or args.time_field or args.start or args.end)

    if filtered and len(tables) != 1:
        print(
            "Error: --export-fields / --time-field / --start / --end require "
            "exactly one table (use --tables TABLE).",
            file=sys.stderr,
        )
        sys.exit(1)

    time_field = args.time_field
    export_fields: list[str] = args.export_fields or []

    if filtered:
        table_name = tables[0]
        all_cols_raw = describe_table(con, table_name)
        all_col_names = [c[0] for c in all_cols_raw]

        # validate requested columns
        if export_fields:
            unknown_cols = set(export_fields) - set(all_col_names)
            if unknown_cols:
                print(
                    f"Error: unknown column(s) in '{table_name}': "
                    f"{', '.join(sorted(unknown_cols))}",
                    file=sys.stderr,
                )
                sys.exit(1)

        # auto-detect time field if not given
        if not time_field and (args.start or args.end):
            all_cols_typed = [(c[0], c[1]) for c in all_cols_raw]
            time_field = _auto_x_field(all_cols_typed)
            if time_field:
                if args.verbose:
                    print(f"Auto-selected time field: {time_field}")
            else:
                print(
                    f"Error: no TIMESTAMP column found in '{table_name}'. "
                    "Use --time-field to specify one.",
                    file=sys.stderr,
                )
                sys.exit(1)

        # ensure time_field is included in the SELECT when fields are restricted
        if export_fields and time_field and time_field not in export_fields:
            export_fields = [time_field] + export_fields

    if args.verbose:
        print(f"Exporting {len(tables)} table(s): {', '.join(tables)}")

    for table in tables:
        if filtered:
            select_sql = _build_export_select(
                table, export_fields, time_field, args.start, args.end
            )
        else:
            select_sql = f"SELECT * FROM mysqldb.{table}"

        if args.verbose:
            print(f"  SQL: {select_sql}")

        if args.fmt == "duckdb":
            con.execute(f"CREATE OR REPLACE TABLE {table} AS {select_sql}")
            if args.verbose:
                n = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                print(f"  {table}: {n} row(s)")

        elif args.fmt == "csv":
            dest = Path(args.output_dir) / f"{table}.csv"
            con.execute(f"COPY ({select_sql}) TO '{dest}' (HEADER, DELIMITER ',')")
            if args.verbose:
                print(f"  {table} → {dest}")

        elif args.fmt == "parquet":
            dest = Path(args.output_dir) / f"{table}.parquet"
            con.execute(f"COPY ({select_sql}) TO '{dest}' (FORMAT PARQUET)")
            if args.verbose:
                print(f"  {table} → {dest}")

    print(f"Export complete: {len(tables)} table(s).")


# ---------------------------------------------------------------------------
# Mode: view
# ---------------------------------------------------------------------------


def mode_view(args: argparse.Namespace) -> None:
    """Display query results as a rich table in the terminal.

    Uses ``--table`` / ``--query``, ``--fields``, ``--where``, and ``--limit``
    from the CLI.  ``--limit 0`` means no row cap (show everything).
    """
    try:
        from rich.console import Console
        from rich.table import Table as RichTable
    except ImportError:
        print(
            "Error: rich is required for --mode view.  pip install rich",
            file=sys.stderr,
        )
        sys.exit(1)

    dsn = _build_dsn(args.host, args.port, args.user, args.password, args.database)
    con = duckdb.connect()
    _load_mysql_extension(con, args.verbose)
    _attach_mysql(con, dsn, args.verbose)

    if args.query:
        sql = args.query
    else:
        field_list = ", ".join(args.fields) if args.fields else "*"
        sql = f"SELECT {field_list} FROM mysqldb.{args.table}"
        if args.where:
            sql += f" WHERE {args.where}"
        if args.limit > 0:
            sql += f" LIMIT {args.limit}"

    if args.verbose:
        print(f"SQL: {sql}")

    cols, rows = _fetch_poll(con, sql)
    con.close()

    console = Console()
    rich_table = RichTable(show_header=True, header_style="bold cyan", show_lines=False)
    for col in cols:
        rich_table.add_column(col, overflow="fold")
    for row in rows:
        rich_table.add_row(*["" if v is None else str(v) for v in row])

    console.print(rich_table)
    console.print(f"[dim]{len(rows)} row(s)[/dim]")


# ---------------------------------------------------------------------------
# Mode: poll
# ---------------------------------------------------------------------------

_POLL_DEFAULTS: dict[str, Any] = {
    "type": "line",
    "figsize": [12, 6],
    "colors": [],
    # layout: "subplots" (one axes per field), "overlay" (all on one axes),
    #         "groups"   (user-defined groups; set "groups": [[f1,f2],[f3]] too)
    "layout": "subplots",
    "groups": [],
    "font": None,       # font family string, e.g. "DejaVu Sans" / "Arial"
    "fontsize": None,   # base font size in points, e.g. 12
}


def _resolve_groups(y_fields: list[str], opts: dict[str, Any]) -> list[list[str]]:
    """Return a list of field groups based on opts['layout'] / opts['groups'].

    overlay  → [[field1, field2, ...]]          (one group = all fields)
    subplots → [[field1], [field2], ...]         (one group per field)
    groups   → opts['groups'] if provided, else falls back to subplots
    """
    layout = opts.get("layout", "subplots")
    if layout == "overlay":
        return [list(y_fields)]
    if layout == "groups":
        user_groups = opts.get("groups", [])
        if user_groups:
            # Validate: every named field must be in y_fields
            flat = [f for g in user_groups for f in g]
            unknown = set(flat) - set(y_fields)
            if unknown:
                print(
                    f"Error: --plot-options groups reference unknown field(s): "
                    f"{', '.join(sorted(unknown))}",
                    file=sys.stderr,
                )
                sys.exit(1)
            return [list(g) for g in user_groups]
    # default: subplots
    return [[f] for f in y_fields]


def _parse_plot_options(raw: Optional[str]) -> dict[str, Any]:
    """Merge user-supplied JSON plot options with defaults."""
    opts = dict(_POLL_DEFAULTS)
    if raw:
        try:
            user = json.loads(raw)
        except json.JSONDecodeError as exc:
            print(f"Error: --plot-options is not valid JSON: {exc}", file=sys.stderr)
            sys.exit(1)
        if not isinstance(user, dict):
            print("Error: --plot-options must be a JSON object.", file=sys.stderr)
            sys.exit(1)
        opts.update(user)
    return opts


def _build_poll_query(table: str, fields: list[str], where: Optional[str], limit: int, order_by: Optional[str]) -> str:
    field_list = ", ".join(fields) if fields else "*"
    sql = f"SELECT {field_list} FROM mysqldb.{table}"
    if where:
        sql += f" WHERE {where}"
    if order_by:
        sql += f" ORDER BY {order_by}"
    sql += f" LIMIT {limit}"
    return sql


def _fetch_poll(con: duckdb.DuckDBPyConnection, sql: str) -> tuple[list[str], list[tuple]]:
    rel = con.execute(sql)
    cols = [desc[0] for desc in rel.description]
    return cols, rel.fetchall()


# ── matplotlib backend ──────────────────────────────────────────────────────

def _poll_matplotlib(
    con: duckdb.DuckDBPyConnection,
    sql: str,
    x_field: Optional[str],
    y_fields: list[str],
    opts: dict[str, Any],
    interval: float,
    count: Optional[int],
    verbose: bool,
) -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("Error: matplotlib is required for --plot matplotlib.  pip install matplotlib", file=sys.stderr)
        sys.exit(1)

    figsize = tuple(opts["figsize"])
    colors = opts["colors"] or [None] * len(y_fields)
    plot_type = opts["type"]
    groups = _resolve_groups(y_fields, opts)
    field_color = {f: i for i, f in enumerate(y_fields)}

    if opts["font"]:
        plt.rcParams["font.family"] = opts["font"]
    if opts["fontsize"]:
        plt.rcParams["font.size"] = opts["fontsize"]

    fig, axes = plt.subplots(len(groups), 1, figsize=figsize, sharex=True, squeeze=False)
    plt.ion()

    buffers: dict[str, collections.deque] = {
        f: collections.deque()
        for f in (y_fields + ([x_field] if x_field else []))
    }

    poll_n = 0
    try:
        while count is None or poll_n < count:
            cols, rows = _fetch_poll(con, sql)
            if verbose:
                print(f"[poll {poll_n + 1}] {len(rows)} row(s) fetched")

            for f in buffers:
                buffers[f].clear()
            for row in rows:
                row_dict = dict(zip(cols, row))
                for f in buffers:
                    if f in row_dict:
                        buffers[f].append(row_dict[f])

            x_data = (
                list(buffers[x_field])
                if x_field and x_field in buffers
                else list(range(len(rows)))
            )

            for ax, group in zip(axes[:, 0], groups):
                ax.cla()
                for y_field in group:
                    y_data = list(buffers[y_field])
                    cidx = field_color[y_field]
                    color = colors[cidx] if cidx < len(colors) else None
                    kw = {"color": color, "label": y_field} if color else {"label": y_field}
                    if plot_type == "scatter":
                        ax.scatter(x_data, y_data, s=10, **kw)
                    elif plot_type == "bar":
                        ax.bar(x_data, y_data, **kw)
                    else:
                        ax.plot(x_data, y_data, **kw)
                # show y-label: single field name, or legend for multiple
                if len(group) == 1:
                    ax.set_ylabel(group[0])
                else:
                    ax.legend(loc="upper left", fontsize="small")
                ax.grid(True, linestyle="--", alpha=0.5)

            if x_field:
                axes[-1, 0].set_xlabel(x_field)

            fig.suptitle(f"MySQL poll — {sql[:60]}…" if len(sql) > 60 else f"MySQL poll — {sql}")
            plt.tight_layout()
            plt.draw()
            plt.pause(interval)
            poll_n += 1

    except KeyboardInterrupt:
        pass
    finally:
        plt.ioff()
        plt.show()


# ── plotly backend ──────────────────────────────────────────────────────────

def _poll_plotly(
    con: duckdb.DuckDBPyConnection,
    sql: str,
    x_field: Optional[str],
    y_fields: list[str],
    opts: dict[str, Any],
    interval: float,
    count: Optional[int],
    output_html: str,
    verbose: bool,
) -> None:
    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
    except ImportError:
        print("Error: plotly is required for --plot plotly.  pip install plotly", file=sys.stderr)
        sys.exit(1)

    colors = opts["colors"] or [None] * len(y_fields)
    plot_type = opts["type"]
    groups = _resolve_groups(y_fields, opts)
    field_color = {f: i for i, f in enumerate(y_fields)}

    html_path = Path(output_html).resolve()
    browser_opened = False
    poll_n = 0

    try:
        while count is None or poll_n < count:
            cols, rows = _fetch_poll(con, sql)
            if verbose:
                print(f"[poll {poll_n + 1}] {len(rows)} row(s) fetched")

            row_dicts = [dict(zip(cols, r)) for r in rows]
            x_data = (
                [r[x_field] for r in row_dicts]
                if x_field and row_dicts and x_field in row_dicts[0]
                else list(range(len(rows)))
            )

            subplot_titles = [", ".join(g) for g in groups]
            fig = make_subplots(
                rows=len(groups),
                cols=1,
                shared_xaxes=True,
                vertical_spacing=0.04,
                subplot_titles=subplot_titles,
            )

            for row_idx, group in enumerate(groups, start=1):
                for y_field in group:
                    y_data = [r.get(y_field) for r in row_dicts]
                    cidx = field_color[y_field]
                    color = colors[cidx] if cidx < len(colors) else None
                    marker = {"color": color} if color else {}

                    if plot_type == "scatter":
                        trace = go.Scatter(x=x_data, y=y_data, mode="markers", name=y_field, marker=marker)
                    elif plot_type == "bar":
                        trace = go.Bar(x=x_data, y=y_data, name=y_field, marker=marker)
                    else:
                        trace = go.Scatter(x=x_data, y=y_data, mode="lines", name=y_field, line=marker)

                    fig.add_trace(trace, row=row_idx, col=1)

                # y-axis label: single field or blank (legend handles multi-field groups)
                y_title = group[0] if len(group) == 1 else ""
                fig.update_yaxes(title_text=y_title, row=row_idx, col=1)

            if x_field:
                fig.update_xaxes(title_text=x_field, row=len(groups), col=1)

            font_dict: dict[str, Any] = {}
            if opts["font"]:
                font_dict["family"] = opts["font"]
            if opts["fontsize"]:
                font_dict["size"] = opts["fontsize"]

            fig.update_layout(
                title=f"MySQL poll — {sql[:80]}…" if len(sql) > 80 else f"MySQL poll — {sql}",
                height=max(300, 280 * len(groups)),
                **({"font": font_dict} if font_dict else {}),
            )

            # Inject meta-refresh so the browser reloads automatically
            html_body = fig.to_html(full_html=True, include_plotlyjs="cdn")
            refresh_tag = f'<meta http-equiv="refresh" content="{int(interval)}">'
            html_body = html_body.replace("<head>", f"<head>\n  {refresh_tag}", 1)
            html_path.write_text(html_body, encoding="utf-8")

            if not browser_opened:
                webbrowser.open(html_path.as_uri())
                browser_opened = True

            poll_n += 1
            if count is None or poll_n < count:
                time.sleep(interval)

    except KeyboardInterrupt:
        pass

    print(f"Plotly output written to {html_path}")


# ── textual backend ────────────────────────────────────────────────────────


def _safe_widget_id(name: str) -> str:
    """Return a CSS-safe widget ID derived from a column name."""
    return "".join(c if c.isalnum() else "_" for c in name)


def _poll_textual(
    con: duckdb.DuckDBPyConnection,
    sql: str,
    x_field: Optional[str],
    y_fields: list[str],
    opts: dict[str, Any],
    interval: float,
    count: Optional[int],
    verbose: bool,
) -> None:
    try:
        from textual.app import App, ComposeResult
        from textual.containers import Horizontal, ScrollableContainer
        from textual.widgets import Footer, Header, Sparkline, Static
    except ImportError:
        print(
            "Error: textual is required for --plot textual.  pip install textual",
            file=sys.stderr,
        )
        sys.exit(1)

    import datetime as _dt

    colors = opts["colors"] or []
    groups = _resolve_groups(y_fields, opts)
    MAX_POINTS = 200

    class PollApp(App):  # type: ignore[type-arg]
        CSS = """
        Screen { background: $surface; }

        #scroll { height: 1fr; }

        .group-label {
            background: $primary-darken-2;
            color: $text;
            padding: 0 1;
            height: 1;
            margin-top: 1;
        }

        .field-row {
            layout: horizontal;
            height: 6;
            margin-bottom: 1;
        }

        .field-name {
            width: 24;
            content-align: left middle;
            padding: 0 1;
            color: $text-muted;
        }

        Sparkline {
            height: 6;
            width: 1fr;
        }

        .field-value {
            width: 14;
            content-align: right middle;
            padding: 0 1;
            color: $success;
            text-style: bold;
        }

        #status {
            height: 1;
            background: $primary-darken-3;
            color: $text-muted;
            padding: 0 1;
        }
        """

        BINDINGS = [
            ("q", "quit", "Quit"),
            ("p", "toggle_pause", "Pause / Resume"),
        ]

        def __init__(self) -> None:
            super().__init__()
            self.title = f"MySQL Poll — {sql[:60]}…" if len(sql) > 60 else f"MySQL Poll — {sql}"
            self._buffers: dict[str, collections.deque] = {
                f: collections.deque(maxlen=MAX_POINTS) for f in y_fields
            }
            self._poll_n = 0
            self._paused = False

        def compose(self) -> ComposeResult:
            yield Header(show_clock=True)
            with ScrollableContainer(id="scroll"):
                for group in groups:
                    if len(groups) > 1:
                        yield Static(", ".join(group), classes="group-label")
                    for field in group:
                        sid = _safe_widget_id(field)
                        with Horizontal(classes="field-row"):
                            yield Static(field, classes="field-name")
                            yield Sparkline([], id=f"spark_{sid}", summary_function=max)
                            yield Static("—", id=f"val_{sid}", classes="field-value")
            yield Static("Connecting…", id="status")
            yield Footer()

        def on_mount(self) -> None:
            for i, field in enumerate(y_fields):
                if i < len(colors) and colors[i]:
                    try:
                        self.query_one(
                            f"#spark_{_safe_widget_id(field)}", Sparkline
                        ).styles.color = colors[i]
                    except Exception:
                        pass
            self.set_interval(interval, self._do_poll)

        async def _do_poll(self) -> None:
            if self._paused:
                return
            if count is not None and self._poll_n >= count:
                self.exit()
                return

            try:
                cols, rows = _fetch_poll(con, sql)
            except Exception as exc:
                self.query_one("#status", Static).update(f"Error: {exc}")
                return

            for row in rows:
                row_dict = dict(zip(cols, row))
                for f in y_fields:
                    val = row_dict.get(f)
                    if val is not None:
                        try:
                            self._buffers[f].append(float(val))
                        except (TypeError, ValueError):
                            pass

            for field in y_fields:
                sid = _safe_widget_id(field)
                data = list(self._buffers[field])
                try:
                    self.query_one(f"#spark_{sid}", Sparkline).data = data
                    self.query_one(f"#val_{sid}", Static).update(
                        f"{data[-1]:.5g}" if data else "—"
                    )
                except Exception:
                    pass

            self._poll_n += 1
            now = _dt.datetime.now().strftime("%H:%M:%S")
            paused_tag = "  [PAUSED]" if self._paused else ""
            self.query_one("#status", Static).update(
                f"Poll #{self._poll_n}  rows={len(rows)}"
                f"  interval={interval}s  updated={now}{paused_tag}"
            )

        def action_toggle_pause(self) -> None:
            self._paused = not self._paused

    PollApp(css_theme="textual-dark").run()


# ── dash backend ───────────────────────────────────────────────────────────


def _poll_dash(
    con: duckdb.DuckDBPyConnection,
    sql: str,
    x_field: Optional[str],
    y_fields: list[str],
    opts: dict[str, Any],
    interval: float,
    count: Optional[int],
    host: str,
    port: int,
    verbose: bool,
) -> None:
    try:
        from dash import Dash, Input, Output, State, dcc, html
        from dash.exceptions import PreventUpdate
        import plotly.graph_objects as go
    except ImportError:
        print(
            "Error: dash is required for --plot dash.  pip install dash",
            file=sys.stderr,
        )
        sys.exit(1)

    import datetime as _dt
    import logging

    logging.getLogger("werkzeug").setLevel(logging.ERROR)

    colors = opts["colors"] or [None] * len(y_fields)
    plot_type = opts["type"]
    groups = _resolve_groups(y_fields, opts)
    field_color = {f: i for i, f in enumerate(y_fields)}

    font_dict: dict[str, Any] = {}
    if opts["font"]:
        font_dict["family"] = opts["font"]
    if opts["fontsize"]:
        font_dict["size"] = opts["fontsize"]

    app = Dash(__name__, title="MySQL Poll", suppress_callback_exceptions=True)
    graph_ids = [f"graph-{i}" for i in range(len(groups))]
    interval_ms = int(interval * 1000)
    heading = f"MySQL Poll — {sql[:80]}…" if len(sql) > 80 else f"MySQL Poll — {sql}"

    app.layout = html.Div(
        style={"fontFamily": opts["font"] or "sans-serif", "padding": "16px"},
        children=[
            html.H4(heading, style={"marginBottom": "8px"}),
            html.Div(
                style={"display": "flex", "alignItems": "center",
                       "gap": "16px", "marginBottom": "12px"},
                children=[
                    html.Button("⏸ Pause / Resume", id="pause-btn", n_clicks=0),
                    html.Span(id="status-text",
                              style={"color": "gray", "fontSize": "0.85em"}),
                ],
            ),
            dcc.Interval(id="interval", interval=interval_ms,
                         n_intervals=0, disabled=False),
            dcc.Store(id="paused", data=False),
            dcc.Store(id="poll-n", data=0),
            html.Div([
                dcc.Graph(id=gid, config={"displayModeBar": True})
                for gid in graph_ids
            ]),
        ],
    )

    @app.callback(
        Output("paused", "data"),
        Output("interval", "disabled"),
        Input("pause-btn", "n_clicks"),
        State("paused", "data"),
        prevent_initial_call=True,
    )
    def toggle_pause(n_clicks, paused):
        new_state = not paused
        return new_state, new_state

    @app.callback(
        [Output(gid, "figure") for gid in graph_ids]
        + [Output("status-text", "children"), Output("poll-n", "data")],
        Input("interval", "n_intervals"),
        State("poll-n", "data"),
    )
    def refresh(n_intervals, poll_n):
        if count is not None and poll_n >= count:
            raise PreventUpdate

        try:
            cols, rows = _fetch_poll(con, sql)
        except Exception as exc:
            if verbose:
                print(f"Poll error: {exc}", file=sys.stderr)
            raise PreventUpdate

        row_dicts = [dict(zip(cols, r)) for r in rows]
        x_data = (
            [r[x_field] for r in row_dicts]
            if x_field and row_dicts and x_field in row_dicts[0]
            else list(range(len(rows)))
        )

        figs = []
        for group in groups:
            fig = go.Figure()
            for y_field in group:
                y_data = [r.get(y_field) for r in row_dicts]
                cidx = field_color[y_field]
                color = colors[cidx] if cidx < len(colors) else None
                marker = {"color": color} if color else {}

                if plot_type == "scatter":
                    trace = go.Scatter(x=x_data, y=y_data, mode="markers",
                                       name=y_field, marker=marker)
                elif plot_type == "bar":
                    trace = go.Bar(x=x_data, y=y_data, name=y_field,
                                   marker=marker)
                else:
                    trace = go.Scatter(x=x_data, y=y_data, mode="lines",
                                       name=y_field, line=marker)
                fig.add_trace(trace)

            fig.update_layout(
                title=", ".join(group) if len(groups) > 1 else "",
                height=280,
                xaxis_title=x_field or "",
                yaxis_title=group[0] if len(group) == 1 else "",
                margin={"t": 40, "b": 40, "l": 60, "r": 20},
                **({"font": font_dict} if font_dict else {}),
            )
            figs.append(fig)

        poll_n += 1
        now = _dt.datetime.now().strftime("%H:%M:%S")
        status = f"Poll #{poll_n}  ·  {len(rows)} row(s)  ·  updated {now}"
        if verbose:
            print(status)

        return figs + [status, poll_n]

    url = f"http://{host}:{port}"
    print(f"Dash server at {url}  (Ctrl+C to stop)")
    webbrowser.open(url)
    app.run(host=host, port=port, debug=False, use_reloader=False)


# ── mode entry point ────────────────────────────────────────────────────────

def mode_poll(args: argparse.Namespace) -> None:
    """Poll a MySQL table and display selected fields as a live chart."""
    opts = _parse_plot_options(args.plot_options)
    dsn = _build_dsn(args.host, args.port, args.user, args.password, args.database)

    con = duckdb.connect()
    _load_mysql_extension(con, args.verbose)
    _attach_mysql(con, dsn, args.verbose)

    if args.list_tables:
        tables = list_mysql_tables(con, args.database)
        print(f"Tables in '{args.database}' ({len(tables)}):")
        for t in tables:
            print(f"  {t}")
        return

    if args.query:
        # ── raw-query path ──────────────────────────────────────────────────
        sql = args.query

        # Run the query once to discover result-column names and types.
        rel = con.execute(sql)
        result_cols = [(desc[0], desc[1]) for desc in rel.description]
        result_col_names = [c[0] for c in result_cols]

        if args.list_fields:
            print("Columns returned by query:")
            for name, col_type in result_cols:
                if _is_numeric_type(col_type):
                    marker = " *"
                elif _is_timestamp_type(col_type):
                    marker = " @"
                else:
                    marker = ""
                print(f"  {name:<30}  {col_type}{marker}")
            print("(* = numeric / y-axis  @ = timestamp / x-axis)")
            return

        # Resolve x-axis: explicit flag → first TIMESTAMP column → None
        x_field = args.x_field or _auto_x_field(result_cols)
        if x_field and x_field not in result_col_names:
            print(f"Error: x-field '{x_field}' not in query result columns.", file=sys.stderr)
            sys.exit(1)
        if x_field and not args.x_field and args.verbose:
            print(f"Auto-selected x-axis: {x_field}")

        requested = args.fields or []
        if requested:
            unknown = set(requested) - set(result_col_names)
            if unknown:
                print(f"Error: unknown column(s) in query result: {', '.join(sorted(unknown))}", file=sys.stderr)
                sys.exit(1)
            y_fields = [f for f in requested if f != x_field]
        else:
            numeric_names = [c[0] for c in result_cols if _is_numeric_type(c[1])]
            y_fields = [f for f in numeric_names if f != x_field]
            if not y_fields:
                print("Error: no numeric columns in query result. Use --fields to specify columns explicitly.", file=sys.stderr)
                sys.exit(1)
            if args.verbose:
                print(f"Auto-selected y-fields: {', '.join(y_fields)}")

    else:
        # ── single-table path ───────────────────────────────────────────────
        all_cols_raw = describe_table(con, args.table)
        all_col_names = [c[0] for c in all_cols_raw]
        all_cols_typed = [(c[0], c[1]) for c in all_cols_raw]
        numeric_cols = list_numeric_columns(con, args.table)

        if args.list_fields:
            print(f"Columns in '{args.table}':")
            for name, col_type in all_cols_typed:
                if _is_numeric_type(col_type):
                    marker = " *"
                elif _is_timestamp_type(col_type):
                    marker = " @"
                else:
                    marker = ""
                print(f"  {name:<30}  {col_type}{marker}")
            print("(* = numeric / y-axis  @ = timestamp / x-axis)")
            return

        # Resolve x-axis: explicit flag → first TIMESTAMP column → None
        x_field = args.x_field or _auto_x_field(all_cols_typed)
        if x_field and not args.x_field and args.verbose:
            print(f"Auto-selected x-axis: {x_field}")

        requested = args.fields or []
        if requested:
            unknown = set(requested) - set(all_col_names)
            if unknown:
                print(f"Error: unknown column(s) in {args.table}: {', '.join(sorted(unknown))}", file=sys.stderr)
                sys.exit(1)
            fields = [f for f in requested if f != x_field]
        else:
            fields = [name for name, _ in numeric_cols if name != x_field]
            if not fields:
                print(f"Error: no numeric columns found in '{args.table}'. Use --fields to specify columns explicitly.", file=sys.stderr)
                sys.exit(1)
            if args.verbose:
                print(f"Auto-selected y-fields: {', '.join(fields)}")

        if x_field:
            # ensure x_field is fetched even if not listed as a y-field
            select_fields = [x_field] + fields
        else:
            select_fields = fields

        y_fields = fields

        if not y_fields:
            print("Error: no y-fields to plot.", file=sys.stderr)
            sys.exit(1)

        sql = _build_poll_query(args.table, select_fields, args.where, args.limit, x_field)

    if args.verbose:
        print(f"Query: {sql}")

    count = args.count if args.count and args.count > 0 else None

    if args.plot == "plotly":
        _poll_plotly(
            con, sql, x_field, y_fields, opts,
            args.interval, count, args.output_html, args.verbose,
        )
    elif args.plot == "textual":
        _poll_textual(
            con, sql, x_field, y_fields, opts,
            args.interval, count, args.verbose,
        )
    elif args.plot == "dash":
        _poll_dash(
            con, sql, x_field, y_fields, opts,
            args.interval, count, args.dash_host, args.dash_port, args.verbose,
        )
    else:
        _poll_matplotlib(
            con, sql, x_field, y_fields, opts,
            args.interval, count, args.verbose,
        )


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
            "  %(prog)s --mode poll --table measurements --fields t Icoil Ucoil"
            " --x-field t --interval 5 --plot matplotlib"
            " --host db.example.com --user admin --password secret"
            " --database magnetdb\n"
            "  %(prog)s --mode view --table measurements --limit 50"
            " --host db.example.com --user admin --password secret"
            " --database magnetdb\n"
        ),
    )

    parser.add_argument(
        "--mode",
        choices=["live", "export", "poll", "view"],
        default="live",
        help=(
            "live: print schema (default); export: copy tables; "
            "poll: live chart; view: tabular table display"
        ),
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
    exp.add_argument(
        "--export-fields",
        nargs="+",
        metavar="COL",
        dest="export_fields",
        help="columns to include in the export; requires exactly one table in --tables",
    )
    exp.add_argument(
        "--time-field",
        metavar="COL",
        dest="time_field",
        help=(
            "TIMESTAMP column used for --start/--end filtering "
            "(auto-detected from schema if omitted)"
        ),
    )
    exp.add_argument(
        "--start",
        metavar="DATETIME",
        help="start of time range, ISO 8601, e.g. '2024-01-15 08:00:00'",
    )
    exp.add_argument(
        "--end",
        metavar="DATETIME",
        help="end of time range, ISO 8601, e.g. '2024-01-15 20:00:00'",
    )

    # Poll options
    poll = parser.add_argument_group("poll options (--mode poll only)")
    poll.add_argument(
        "--table",
        metavar="TABLE",
        help="MySQL table to poll. Mutually exclusive with --query.",
    )
    poll.add_argument(
        "--query",
        metavar="SQL",
        help=(
            "Raw SELECT query to run instead of --table/--fields. "
            "Must reference tables as mysqldb.<table>. "
            "Use --fields to choose which result columns to plot, "
            "--x-field for the x-axis column. "
            "Example: \"SELECT t, m.Icoil, s.temp "
            "FROM mysqldb.meas m JOIN mysqldb.sensors s ON m.id=s.mid "
            "ORDER BY t LIMIT 500\""
        ),
    )
    poll.add_argument(
        "--list-tables",
        action="store_true",
        dest="list_tables",
        help="print all tables in the database and exit, no polling",
    )
    poll.add_argument(
        "--list-fields",
        action="store_true",
        dest="list_fields",
        help="print numeric (plottable) columns of --table and exit, no polling",
    )
    poll.add_argument(
        "--fields",
        nargs="+",
        metavar="COL",
        help="columns to extract and plot (default: all columns)",
    )
    poll.add_argument(
        "--x-field",
        metavar="COL",
        help="column to use as x-axis (default: row index)",
    )
    poll.add_argument(
        "--where",
        metavar="EXPR",
        help="SQL WHERE clause filter (e.g. \"status='active'\")",
    )
    poll.add_argument(
        "--limit",
        type=int,
        default=200,
        metavar="N",
        help="max rows fetched per poll (default: 200)",
    )
    poll.add_argument(
        "--interval",
        type=float,
        default=5.0,
        metavar="SECONDS",
        help="seconds between polls (default: 5)",
    )
    poll.add_argument(
        "--count",
        type=int,
        default=0,
        metavar="N",
        help="number of polls to run (default: 0 = run until Ctrl+C)",
    )
    poll.add_argument(
        "--plot",
        choices=["matplotlib", "plotly", "textual", "dash"],
        default="matplotlib",
        help="plot backend: matplotlib (default), plotly, textual (TUI), dash (web app)",
    )
    poll.add_argument(
        "--plot-options",
        metavar="JSON",
        dest="plot_options",
        help=(
            'JSON object with plot style options. '
            'Keys: '
            'type (line|scatter|bar, default line); '
            'layout (subplots|overlay|groups, default subplots); '
            'groups (list of field-name lists, used when layout=groups, '
            'e.g. [["Icoil","Ucoil"],["tsb","teb"]]); '
            'figsize ([w,h] inches, matplotlib only, default [12,6]); '
            'colors (list of color strings, one per y-field); '
            'font (font family, e.g. "Arial"); '
            'fontsize (base font size in points, e.g. 12). '
            'Example: \'{"layout":"groups","groups":[["Icoil","Ucoil"],["tsb"]],'
            '"font":"Arial","fontsize":11}\''
        ),
    )
    poll.add_argument(
        "--output-html",
        metavar="FILE",
        default="poll_output.html",
        dest="output_html",
        help="HTML output path for --plot plotly (default: poll_output.html)",
    )
    poll.add_argument(
        "--dash-host",
        metavar="HOST",
        default="127.0.0.1",
        dest="dash_host",
        help="host for the Dash web server (default: 127.0.0.1)",
    )
    poll.add_argument(
        "--dash-port",
        type=int,
        metavar="PORT",
        default=8050,
        dest="dash_port",
        help="port for the Dash web server (default: 8050)",
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

    if args.mode in ("poll", "view"):
        if args.table and args.query:
            parser.error("--table and --query are mutually exclusive")

    if args.mode == "poll":
        if not args.table and not args.query and not args.list_tables:
            parser.error("--mode poll requires --table TABLE or --query SQL (or --list-tables)")

    if args.mode == "view":
        if not args.table and not args.query:
            parser.error("--mode view requires --table TABLE or --query SQL")

    return args


def main() -> None:
    args = parse_args()
    try:
        if args.mode == "live":
            mode_live(args)
        elif args.mode == "export":
            mode_export(args)
        elif args.mode == "view":
            mode_view(args)
        else:
            mode_poll(args)
    except duckdb.Error as e:
        print(f"DuckDB error: {e}", file=sys.stderr)
        sys.exit(1)
    except OSError as e:
        print(f"I/O error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
