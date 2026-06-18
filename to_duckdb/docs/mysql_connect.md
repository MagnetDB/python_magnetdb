# `mysql_connect.py` — MySQL ↔ DuckDB bridge

`mysql_connect.py` attaches a remote MySQL database to an in-memory DuckDB
session via the `mysql_scanner` extension.  Four independent modes are
available: **live** (schema inspection), **export** (snapshot to file),
**view** (tabular table display), and **poll** (live chart from repeated queries).

---

## Requirements

```bash
pip install duckdb matplotlib plotly textual dash rich
```

| Mode / Backend | Extra package | Notes |
|----------------|---------------|-------|
| `view` | `rich` | terminal table |
| `--plot matplotlib` (default) | `matplotlib` | native window |
| `--plot plotly` | `plotly` | auto-refreshing HTML file |
| `--plot textual` | `textual` | full-screen TUI in terminal |
| `--plot dash` | `dash` + `plotly` | interactive web app in browser |

`matplotlib` is only required for `--plot matplotlib` (default).  
`plotly` is only required for `--plot plotly`.

---

## Connection parameters

All connection flags can be supplied via environment variables (e.g. with
[direnv](https://direnv.net/)).  CLI flags always take precedence.

| CLI flag | Environment variable | Default |
|----------|----------------------|---------|
| `--host` | `MYSQL_HOST` | `localhost` |
| `--port` | `MYSQL_PORT` | `3306` |
| `--user` | `MYSQL_USER` | *(required)* |
| `--password` | `MYSQL_PASSWORD` | *(required)* |
| `--database` | `MYSQL_DB` | *(required)* |

Example `.envrc` for direnv:

```bash
export MYSQL_HOST=db.example.com
export MYSQL_USER=admin
export MYSQL_PASSWORD=secret
export MYSQL_DB=magnetdb
```

From here on the connection flags are omitted from examples for brevity.
Add `--host … --user … --password … --database …` (or source the `.envrc`)
to every command below.

---

## Mode: `live` — inspect the schema

Attaches MySQL and prints every table with its columns, types, and role markers.
No data is copied locally.

```bash
python mysql_connect.py --mode live
```

Sample output:

```
Connected to magnetdb@db.example.com:3306
3 table(s) found:

  measurements
    timestamp                      TIMESTAMP  @
    Icoil                          FLOAT      *
    Ucoil                          FLOAT      *
    tsb                            FLOAT      *
    teb                            FLOAT      *
    label                          VARCHAR

  sensors
    id                             INTEGER    *
    measurement_id                 INTEGER    *
    temp                           FLOAT      *
    flow                           FLOAT      *

  sites
    name                           VARCHAR
    description                    VARCHAR

(* = numeric / y-axis  @ = timestamp / x-axis)
```

---

## Mode: `export` — snapshot tables to a local file

### Export all tables to CSV

```bash
python mysql_connect.py --mode export --format csv --output-dir ./out
```

One `.csv` file is created per table under `./out/`.

### Export selected tables to Parquet

```bash
python mysql_connect.py --mode export --format parquet \
    --output-dir ./out \
    --tables measurements sensors
```

### Export to a DuckDB file

```bash
python mysql_connect.py --mode export --format duckdb \
    --output magnetdb_mysql.duckdb \
    --tables measurements sensors sites
```

The DuckDB file is created if it does not exist; existing tables are replaced
(`CREATE OR REPLACE`).

### Export a subset of columns from one table

`--export-fields` restricts which columns are written.  It requires exactly one
table to be named via `--tables`.

```bash
python mysql_connect.py --mode export --format csv --output-dir ./out \
    --tables measurements \
    --export-fields timestamp Icoil Ucoil tsb teb
```

### Export a time range

Use `--start` and/or `--end` with an ISO 8601 datetime string.  The
`--time-field` option names the TIMESTAMP column to filter on; if omitted the
first TIMESTAMP column found in the schema is used automatically.

```bash
# Auto-detect the timestamp column
python mysql_connect.py --mode export --format csv --output-dir ./out \
    --tables measurements \
    --start "2024-01-15 08:00:00" \
    --end   "2024-01-15 20:00:00"

# Explicit time field
python mysql_connect.py --mode export --format parquet --output-dir ./out \
    --tables measurements \
    --time-field "Timestamp Field" \
    --start "2024-01-15 08:00:00" \
    --end   "2024-01-15 20:00:00"
```

### Combine column selection and time range

```bash
python mysql_connect.py --mode export --format parquet --output-dir ./out \
    --tables measurements \
    --export-fields timestamp Icoil Ucoil tsb teb \
    --start "2024-01-15 08:00:00" \
    --end   "2024-01-15 20:00:00"
```

When `--export-fields` is used together with `--start`/`--end`, the time field
is automatically prepended to the column list if it is not already present, so
the exported file always contains the timestamp column.

```bash
# Export to DuckDB with field selection and time range
python mysql_connect.py --mode export --format duckdb \
    --output run42.duckdb \
    --tables measurements \
    --export-fields Icoil Ucoil tsb teb \
    --time-field timestamp \
    --start "2024-03-10 06:00:00" \
    --end   "2024-03-10 18:00:00" \
    --verbose
```

Add `-v` / `--verbose` to print the generated SQL and row count before writing.

---

## Mode: `view` — tabular table display

Display rows from a MySQL table (or any custom SQL query) as a styled table
in the terminal.  Requires [`rich`](https://rich.readthedocs.io/):
`pip install rich`.

### Quick view of the most recent rows

```bash
python mysql_connect.py --mode view --table measurements --limit 50
```

Sample output (columns auto-sized to terminal width):

```
 timestamp            Icoil    Ucoil    tsb    teb    label
 ──────────────────── ──────── ──────── ────── ────── ───────
 2024-01-15 10:00:00  1200.5   4.21     12.3   11.8   run42
 2024-01-15 10:00:05  1201.0   4.22     12.4   11.9   run42
 ...
50 row(s)
```

### Select specific columns

```bash
python mysql_connect.py --mode view --table measurements \
    --fields timestamp Icoil Ucoil \
    --limit 100
```

### Apply a WHERE filter

```bash
python mysql_connect.py --mode view --table measurements \
    --where "label = 'run42'" \
    --limit 200
```

### Remove the row cap (show all matching rows)

```bash
python mysql_connect.py --mode view --table measurements \
    --where "label = 'run42'" \
    --limit 0
```

`--limit 0` disables the row cap entirely.  Default is `200`.

### View results of a JOIN query

```bash
python mysql_connect.py --mode view \
    --query "SELECT m.timestamp, m.Icoil, m.Ucoil, s.temp
             FROM mysqldb.measurements m
             JOIN mysqldb.sensors s ON m.id = s.measurement_id
             ORDER BY m.timestamp DESC
             LIMIT 100"
```

### JOIN query with a time range

Time filtering is expressed directly in the SQL `WHERE` clause:

```bash
python mysql_connect.py --mode view \
    --query "SELECT m.timestamp, m.Icoil, m.Ucoil, s.temp
             FROM mysqldb.measurements m
             JOIN mysqldb.sensors s ON m.id = s.measurement_id
             WHERE m.timestamp >= '2024-01-15 08:00:00'
               AND m.timestamp <= '2024-01-15 20:00:00'
             ORDER BY m.timestamp
             LIMIT 500"
```

The same pattern applies to single-table queries:

```bash
python mysql_connect.py --mode view \
    --query "SELECT timestamp, Icoil, Ucoil
             FROM mysqldb.measurements
             WHERE timestamp >= '2024-01-15 08:00:00'
               AND timestamp <= '2024-01-15 20:00:00'
             ORDER BY timestamp"
```

> **Tip:** Use `--verbose` to print the generated SQL before execution.

---

## Mode: `poll` — live chart from repeated queries

Connects to MySQL, runs a query every `--interval` seconds, and displays the
result as a live chart.  Press **Ctrl+C** to stop.

### Discovery helpers

Always start by listing what is available:

```bash
# List all tables in the database
python mysql_connect.py --mode poll --list-tables

# List plottable columns of a table (* = y-axis, @ = x-axis)
python mysql_connect.py --mode poll --table measurements --list-fields
```

Sample `--list-fields` output:

```
Columns in 'measurements':
  timestamp                      TIMESTAMP  @
  Timestamp Field                TIMESTAMP  @
  Icoil                          FLOAT      *
  Ucoil                          FLOAT      *
  tsb                            FLOAT      *
  teb                            FLOAT      *
(* = numeric / y-axis  @ = timestamp / x-axis)
```

### Single-table polling

#### Minimal — auto-detect everything

When `--fields` and `--x-field` are both omitted, the tool selects all
numeric columns as y-fields and the first `TIMESTAMP` column as the x-axis
automatically:

```bash
python mysql_connect.py --mode poll --table measurements --interval 5
```

#### Explicit fields, matplotlib (default backend)

```bash
python mysql_connect.py --mode poll \
    --table measurements \
    --fields Icoil Ucoil tsb teb \
    --x-field timestamp \
    --interval 10 \
    --limit 300
```

#### With a WHERE filter

```bash
python mysql_connect.py --mode poll \
    --table measurements \
    --fields Icoil Ucoil \
    --x-field timestamp \
    --where "label = 'run42'" \
    --interval 5
```

#### All fields on one shared graph (`overlay`)

Use `"layout":"overlay"` to draw every y-field on a single axes instead of
one subplot per field.  This is the quickest way to compare signals whose
values are on similar scales.

```bash
python mysql_connect.py --mode poll \
    --table measurements \
    --fields Icoil Ucoil Iref \
    --x-field timestamp \
    --interval 10 \
    --plot-options '{"layout":"overlay"}'
```

With explicit colours (one per y-field, in the same order as `--fields`):

```bash
python mysql_connect.py --mode poll \
    --table measurements \
    --fields Icoil Ucoil Iref \
    --x-field timestamp \
    --interval 10 \
    --plot-options '{"layout":"overlay","colors":["steelblue","tomato","seagreen"]}'
```

#### Mixed layout — some fields overlaid, others on separate subplots (`groups`)

Use `"layout":"groups"` with a `"groups"` list when you want certain fields
to share a subplot while others get their own.  Each inner list is one subplot;
all subplots share the same x-axis.

```bash
# Icoil and Iref overlaid on subplot 1; Ucoil alone on subplot 2
python mysql_connect.py --mode poll \
    --table measurements \
    --fields Icoil Ucoil Iref \
    --x-field timestamp \
    --interval 10 \
    --plot-options '{"layout":"groups","groups":[["Icoil","Iref"],["Ucoil"]]}'
```

With colours (one entry per y-field in the order they appear across all groups):

```bash
python mysql_connect.py --mode poll \
    --table measurements \
    --fields Icoil Ucoil Iref \
    --x-field timestamp \
    --interval 10 \
    --plot-options '{
      "layout": "groups",
      "groups": [["Icoil", "Iref"], ["Ucoil"]],
      "colors": ["steelblue", "seagreen", "tomato"]
    }'
```

#### Plotly backend (auto-opens browser, writes HTML)

```bash
python mysql_connect.py --mode poll \
    --table measurements \
    --fields Icoil Ucoil tsb teb \
    --x-field timestamp \
    --interval 10 \
    --plot plotly \
    --output-html live_magnets.html
```

The HTML file contains a `<meta http-equiv="refresh">` tag so the browser
reloads automatically on each poll.

#### Run a fixed number of polls, then exit

```bash
python mysql_connect.py --mode poll \
    --table measurements \
    --fields Icoil Ucoil \
    --x-field timestamp \
    --interval 5 \
    --count 20
```

### Multi-table polling with `--query`

Use `--query` with an explicit SQL `SELECT` when you need a `JOIN`.
Tables must be prefixed with `mysqldb.` (the alias used by `mysql_scanner`).
`--limit` and `--where` are ignored in query mode — put them in the SQL.

#### Discover columns returned by a JOIN query

```bash
python mysql_connect.py --mode poll --list-fields \
    --query "SELECT m.timestamp, m.Icoil, m.Ucoil, s.temp, s.flow
             FROM mysqldb.measurements m
             JOIN mysqldb.sensors s ON m.id = s.measurement_id
             ORDER BY m.timestamp DESC LIMIT 300"
```

Sample output:

```
Columns returned by query:
  timestamp                      TIMESTAMP  @
  Icoil                          FLOAT      *
  Ucoil                          FLOAT      *
  temp                           FLOAT      *
  flow                           FLOAT      *
(* = numeric / y-axis  @ = timestamp / x-axis)
```

#### Poll a JOIN query — matplotlib

```bash
python mysql_connect.py --mode poll \
    --query "SELECT m.timestamp, m.Icoil, m.Ucoil, s.temp, s.flow
             FROM mysqldb.measurements m
             JOIN mysqldb.sensors s ON m.id = s.measurement_id
             ORDER BY m.timestamp DESC LIMIT 300" \
    --x-field timestamp \
    --fields Icoil Ucoil temp flow \
    --interval 10
```

#### Poll a JOIN query — plotly

```bash
python mysql_connect.py --mode poll \
    --query "SELECT m.timestamp, m.Icoil, m.Ucoil, s.temp, s.flow
             FROM mysqldb.measurements m
             JOIN mysqldb.sensors s ON m.id = s.measurement_id
             ORDER BY m.timestamp DESC LIMIT 300" \
    --x-field timestamp \
    --fields Icoil Ucoil temp flow \
    --interval 10 \
    --plot plotly \
    --output-html live_join.html
```

### Two-source polling (`--table2` / `--query2`)

When you need to poll **two tables simultaneously** and display their fields in
**separate subplots that share a common x-axis**, use `--table2` (or `--query2`
for raw SQL).  Zooming or panning in one subplot automatically mirrors the other.

Supported backends: `matplotlib`, `plotly`, `dash`.

#### Two tables by name — matplotlib

```bash
python mysql_connect.py --mode poll \
    --table measurements --fields timestamp Icoil Ucoil --x-field timestamp \
    --table2 temperatures --fields2 tsb teb \
    --interval 10 \
    --plot matplotlib
```

#### Two tables by name — Dash (linked zoom/pan, pause button)

```bash
python mysql_connect.py --mode poll \
    --table measurements --fields timestamp Icoil Ucoil --x-field timestamp \
    --table2 temperatures --fields2 tsb teb \
    --interval 10 \
    --plot dash
```

#### Two independent SQL queries (tables not directly joinable)

Use `--query` for the first source and `--query2` for the second when the
tables cannot be joined (different row counts, different time grids, etc.):

```bash
python mysql_connect.py --mode poll \
    --query "SELECT t, Icoil, Ucoil FROM mysqldb.measurements ORDER BY t LIMIT 500" \
    --fields Icoil Ucoil --x-field t \
    --query2 "SELECT t, tsb, teb FROM mysqldb.temperatures ORDER BY t LIMIT 500" \
    --fields2 tsb teb \
    --interval 10 \
    --plot dash
```

#### With a WHERE filter on the second table

`--where2` applies an SQL filter to `--table2` (has no effect when `--query2`
is used — put the filter directly in the SQL instead).

```bash
python mysql_connect.py --mode poll \
    --table measurements --fields timestamp Icoil Ucoil --x-field timestamp \
    --table2 temperatures --fields2 tsb teb --where2 "sensor_id = 3" \
    --interval 10 \
    --plot dash
```

---

## `--plot-options` reference

Pass a JSON object to control chart style.  All keys are optional.

| Key | Values | Default | Note |
|-----|--------|---------|------|
| `type` | `line` \| `scatter` \| `bar` | `line` | chart geometry |
| `layout` | `subplots` \| `overlay` \| `groups` | `subplots` | subplot arrangement |
| `groups` | list of field-name lists | `[]` | required when `layout=groups` |
| `figsize` | `[width, height]` | `[12, 6]` | inches, matplotlib only |
| `colors` | list of color strings | library defaults | one per y-field; applied to sparkline colour in textual |
| `font` | font family string | library default | e.g. `"Arial"`, `"monospace"`; matplotlib and plotly only |
| `fontsize` | number (points) | library default | base font size; matplotlib and plotly only |

### Layout examples

#### `overlay` — all fields on one shared axes

```bash
--plot-options '{"layout":"overlay","colors":["steelblue","tomato","seagreen","orange"]}'
```

#### `subplots` — one subplot per field (default)

```bash
--plot-options '{"layout":"subplots","figsize":[12,8]}'
```

#### `groups` — user-defined field groups, each on its own subplot

```bash
--plot-options '{
  "layout": "groups",
  "groups": [["Icoil", "Ucoil"], ["temp", "flow"]],
  "colors": ["steelblue", "tomato", "seagreen", "orange"],
  "font": "Arial",
  "fontsize": 11
}'
```

Fields within a group share one subplot and are distinguished by color and
legend.  Groups share the same x-axis.

### Full styled example

```bash
python mysql_connect.py --mode poll \
    --query "SELECT m.timestamp, m.Icoil, m.Ucoil, s.temp, s.flow
             FROM mysqldb.measurements m
             JOIN mysqldb.sensors s ON m.id = s.measurement_id
             ORDER BY m.timestamp DESC LIMIT 500" \
    --x-field timestamp \
    --fields Icoil Ucoil temp flow \
    --interval 10 \
    --plot matplotlib \
    --plot-options '{
      "layout": "groups",
      "groups": [["Icoil", "Ucoil"], ["temp", "flow"]],
      "type": "line",
      "figsize": [14, 7],
      "colors": ["steelblue", "tomato", "seagreen", "darkorange"],
      "font": "DejaVu Sans",
      "fontsize": 11
    }'
```

---

## Mode: `poll` — TUI backend (`--plot textual`)

The textual backend runs entirely in the terminal — no window manager needed.
Each y-field gets a live **Sparkline** widget that scrolls with each new poll.

```bash
pip install textual

python mysql_connect.py --mode poll \
    --table measurements \
    --interval 5 \
    --plot textual
```

### Key bindings

| Key | Action |
|-----|--------|
| `q` | Quit |
| `p` | Pause / Resume polling |

### Layout in TUI mode

`layout` from `--plot-options` controls visual grouping:

- **`subplots`** (default) — one sparkline row per field.
- **`overlay`** — all fields in a single group (one section, multiple sparklines stacked).
- **`groups`** — named sections with a header label per group, each containing its fields.

`colors` applies a custom colour to each sparkline.  `font` and `fontsize`
have no effect in textual mode.

```bash
# Grouped layout with custom colours
python mysql_connect.py --mode poll \
    --table measurements \
    --fields Icoil Ucoil tsb teb \
    --interval 5 \
    --plot textual \
    --plot-options '{
      "layout": "groups",
      "groups": [["Icoil", "Ucoil"], ["tsb", "teb"]],
      "colors": ["steelblue", "tomato", "seagreen", "orange"]
    }'
```

### Multi-table TUI poll

```bash
python mysql_connect.py --mode poll \
    --query "SELECT m.timestamp, m.Icoil, m.Ucoil, s.temp, s.flow
             FROM mysqldb.measurements m
             JOIN mysqldb.sensors s ON m.id = s.measurement_id
             ORDER BY m.timestamp DESC LIMIT 300" \
    --fields Icoil Ucoil temp flow \
    --interval 10 \
    --plot textual \
    --plot-options '{"layout":"groups","groups":[["Icoil","Ucoil"],["temp","flow"]]}'
```

---

## Mode: `poll` — Dash backend (`--plot dash`)

The Dash backend starts a local Flask/Dash web server and opens the app in
the default browser.  Unlike the plotly backend (which writes a static HTML
file that reloads the page), Dash updates only the chart data via WebSocket /
XHR — **no full page reload**, so zoom/pan state is preserved between polls.

```bash
pip install dash

python mysql_connect.py --mode poll \
    --table measurements \
    --interval 5 \
    --plot dash
```

The server listens on `127.0.0.1:8050` by default.  Use `--dash-host` and
`--dash-port` to change it (e.g. to expose it on a LAN):

```bash
python mysql_connect.py --mode poll \
    --table measurements \
    --interval 5 \
    --plot dash \
    --dash-host 0.0.0.0 \
    --dash-port 8080
```

### Pause / Resume

A **⏸ Pause / Resume** button in the app header disables the `dcc.Interval`
component, stopping queries to MySQL without closing the server.

### Layout and styling

All `--plot-options` keys (`type`, `layout`, `groups`, `colors`, `font`,
`fontsize`) work the same as for the plotly backend.  Each group gets its own
`dcc.Graph` panel.

```bash
# Two groups, line chart, custom colours
python mysql_connect.py --mode poll \
    --table measurements \
    --fields Icoil Ucoil tsb teb \
    --x-field timestamp \
    --interval 10 \
    --plot dash \
    --plot-options '{
      "layout": "groups",
      "groups": [["Icoil", "Ucoil"], ["tsb", "teb"]],
      "type": "line",
      "colors": ["steelblue", "tomato", "seagreen", "orange"],
      "font": "Arial",
      "fontsize": 12
    }'
```

### Multi-table Dash poll

```bash
python mysql_connect.py --mode poll \
    --query "SELECT m.timestamp, m.Icoil, m.Ucoil, s.temp, s.flow
             FROM mysqldb.measurements m
             JOIN mysqldb.sensors s ON m.id = s.measurement_id
             ORDER BY m.timestamp DESC LIMIT 300" \
    --fields Icoil Ucoil temp flow \
    --interval 10 \
    --plot dash \
    --plot-options '{"layout":"groups","groups":[["Icoil","Ucoil"],["temp","flow"]]}'
```

---

## Complete CLI reference

```
usage: mysql_connect.py [--mode {live,export,view,poll,plot}]
                        [--host HOST] [--port PORT]
                        [--user USER] [--password PASSWORD] [--database DATABASE]
                        [--format {csv,parquet,duckdb}]
                        [--output FILE] [--output-dir DIR] [--tables TABLE ...]
                        [--export-fields COL ...] [--time-field COL]
                        [--start DATETIME] [--end DATETIME]
                        [--table TABLE] [--query SQL]
                        [--list-tables] [--list-fields]
                        [--fields COL ...] [--x-field COL]
                        [--where EXPR] [--limit N]
                        [--table2 TABLE] [--query2 SQL]
                        [--fields2 COL ...] [--where2 EXPR]
                        [--interval SECONDS] [--count N]
                        [--plot {table,matplotlib,plotly,textual,dash}]
                        [--plot-options JSON] [--output-html FILE]
                        [--dash-host HOST] [--dash-port PORT]
                        [-v]
```

| Flag | Mode | Description |
|------|------|-------------|
| `--mode` | all | `live` (default), `export`, `view`, `poll`, `plot` |
| `--host/port/user/password/database` | all | MySQL connection (or env vars) |
| `--format` | export | `csv`, `parquet`, `duckdb` |
| `--output` | export | DuckDB output file (format duckdb) |
| `--output-dir` | export | directory for CSV / Parquet files |
| `--tables` | export | subset of tables to export (default: all) |
| `--export-fields` | export | columns to include; requires exactly one table in `--tables` |
| `--time-field` | export | TIMESTAMP column for `--start`/`--end` filtering (auto-detected) |
| `--start` | export | start of time range, ISO 8601, e.g. `'2024-01-15 08:00:00'` |
| `--end` | export | end of time range, ISO 8601, e.g. `'2024-01-15 20:00:00'` |
| `--table` | view, poll | table to query (mutually exclusive with `--query`) |
| `--query` | view, poll | raw SELECT query; reference tables as `mysqldb.<t>` |
| `--list-tables` | poll | print tables and exit |
| `--list-fields` | poll | print plottable columns and exit |
| `--fields` | poll | y-axis columns (default: all numeric columns) |
| `--x-field` | poll | x-axis column (default: first TIMESTAMP column) |
| `--where` | poll | SQL WHERE clause (single-table path only) |
| `--limit` | poll | max rows per poll, default 200 (single-table path only) |
| `--table2` | poll | second table for two-source mode (mutually exclusive with `--query2`) |
| `--query2` | poll | raw SELECT for the second subplot (mutually exclusive with `--table2`) |
| `--fields2` | poll | y-axis columns from the second source (default: all numeric) |
| `--where2` | poll | SQL WHERE clause for `--table2` only |
| `--interval` | poll | seconds between polls, default 5 |
| `--count` | poll | number of polls; 0 = run until Ctrl+C (default) |
| `--plot` | poll | `matplotlib` (default), `table`, `plotly`, `textual`, `dash` |
| `--plot-options` | poll | JSON style object (see table above) |
| `--output-html` | poll | HTML path for plotly backend (default: `poll_output.html`) |
| `--dash-host` | poll | Dash server host (default: `127.0.0.1`) |
| `--dash-port` | poll | Dash server port (default: `8050`) |
| `-v / --verbose` | all | print SQL, auto-selected fields, row counts |

---

## Running the tests

Tests live in `tests/test_mysql_connect.py` and are split into three categories.

### Unit and smoke tests (no MySQL required)

```bash
cd to_duckdb/
venv-systempackages/bin/python -m pytest tests/test_mysql_connect.py -v -m "not integration"
```

These tests cover all pure-logic helpers (`_is_numeric_type`, `_build_dsn`,
`_resolve_groups`, `_safe_widget_id`, …) and CLI argument parsing via in-memory
DuckDB — no network connection needed.

### Integration tests (live MySQL server required)

Set environment variables pointing to a test MySQL database, then run:

```bash
export MYSQL_TEST_HOST=db.example.com
export MYSQL_TEST_USER=admin
export MYSQL_TEST_PASSWORD=secret
export MYSQL_TEST_DB=magnetdb
# optional: export MYSQL_TEST_PORT=3306

venv-systempackages/bin/python -m pytest tests/test_mysql_connect.py -v -m integration
```

Integration tests verify `list_mysql_tables`, `describe_table`,
`list_numeric_columns`, and `_fetch_poll` against a real MySQL server.
They are automatically skipped when the env vars are absent.
