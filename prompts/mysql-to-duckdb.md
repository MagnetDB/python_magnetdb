# Task: Create a MySQL-to-DuckDB connection script

## Context

Working directory: `~/github/python_magnetdb/to_duckdb`
Virtualenv to use for testing: `~/github/python_magnetdb/to_duckdb/venv-systempackages`

Before writing any code, read the existing files in `to_duckdb/` to understand
the conventions in use (schema, config, populate, crud patterns, requirements.txt).

## Goal

Create a new script `mysql_connect.py` in `~/github/python_magnetdb/to_duckdb/`
that connects DuckDB to a **remote MySQL server** and supports three modes,
selectable via a CLI flag:

1. **`--mode live`** (default)
   Use DuckDB's `mysql_scanner` extension to attach the remote MySQL database
   directly and print the full schema (tables + columns). No local copy is made.
   This is also the mode to use for inspecting an unknown MySQL schema before
   deciding on export strategy or poll watermark column.

2. **`--mode export`**
   Read every table (or a user-specified subset via `--tables`) from the remote
   MySQL server and persist them into a local file. Output format is selectable:
   - `--format csv` (default): one `.csv` file per table in `--output-dir`
   - `--format parquet`: one `.parquet` file per table in `--output-dir`
   - `--format duckdb`: all tables into a single `.duckdb` file (`--output`,
     default: `magnetdb_mysql.duckdb`, created if it does not exist)
   Tables are always created fresh (`CREATE OR REPLACE`) — no pre-creation needed.

3. **`--mode poll`** *(not yet implemented — pending MySQL schema inspection)*
   Periodic incremental pull of new/updated rows, mimicking streaming data.
   See "Mode 3 design decisions" section below.

## MySQL connection parameters

Accept all connection parameters via CLI arguments **and** via environment
variables (env vars take precedence over defaults, CLI flags take precedence
over env vars). The parameters are:

| CLI flag        | Env var          | Default      |
|-----------------|------------------|--------------|
| `--host`        | `MYSQL_HOST`     | `localhost`  |
| `--port`        | `MYSQL_PORT`     | `3306`       |
| `--user`        | `MYSQL_USER`     | *(required)* |
| `--password`    | `MYSQL_PASSWORD` | *(required)* |
| `--database`    | `MYSQL_DB`       | *(required)* |

## Detailed requirements (modes live + export)

- Use `argparse` for the CLI.
- Use the `duckdb` Python package (already installed in the venv).
- For the `mysql_scanner` extension: load it with
  `INSTALL mysql; LOAD mysql;` then use
  `ATTACH 'host=... user=... password=... database=...' AS mysqldb (TYPE mysql_scanner);`
- For `live` mode: list all tables and print column names + types for each.
  Use `SELECT table_name FROM information_schema.tables WHERE table_catalog = 'mysqldb'`
  and `DESCRIBE mysqldb.<table>`.
- For `export` mode:
  - CSV/Parquet: `COPY (SELECT * FROM mysqldb.<table>) TO '<dest>' (...)`
  - DuckDB: `CREATE OR REPLACE TABLE <table> AS SELECT * FROM mysqldb.<table>`
  - Log row counts per table when `--verbose`.
- Add a `--verbose` / `-v` flag that logs each step (tables found, rows copied, etc.).
- Handle connection errors gracefully with a clear error message (no stack trace
  for expected errors like wrong credentials or host unreachable).
- Follow the existing code style in `to_duckdb/` (PEP 8, NumPy-style docstrings
  on public functions, type annotations).

## Mode 3 design decisions (pending MySQL schema inspection)

### Use case
Periodic pull of new/updated rows from MySQL — a lightweight alternative to the
full Kafka/TimescaleDB streaming architecture described in
`to_duckdb/streaming-data-extension.md`.

### Watermark strategy
The poll loop needs a column to track "last seen value" so it only fetches new rows.

| Column type          | Example        | Catches inserts? | Catches updates? |
|----------------------|----------------|------------------|------------------|
| Auto-increment int   | `id`           | Yes              | No               |
| Insertion timestamp  | `created_at`   | Yes              | No               |
| Update timestamp     | `updated_at`   | Yes              | Yes              |
| None                 | —              | No (full scan)   | No               |

**Decision needed:** which column exists in the MySQL tables to be polled?
Use `--mode live` to inspect the schema first, then come back here.

If no suitable watermark column exists, the fallback is "re-export on a timer"
(just run `--mode export` on a cron schedule).

### Watermark persistence
| Option                              | Works for duckdb format? | Works for csv/parquet? |
|-------------------------------------|--------------------------|------------------------|
| `_poll_state` table in output .duckdb | Yes                    | No                     |
| Sidecar `.state.json` file           | Yes                     | Yes                    |

**Recommended approach:** use DuckDB table when `--format duckdb`, JSON file otherwise.

### New CLI flags for poll mode
```
--watermark-col COLUMN   column to track progress (required for poll mode)
--interval N             seconds between polls (default: 30)
--output                 accumulation store (DuckDB file)
--format {duckdb,csv,parquet}
```

### Key open questions before implementing mode 3
1. Which tables need to be polled?
2. Do those tables have an `updated_at`, `created_at`, or auto-increment `id` column?
3. Should new rows be appended to the same file used by `--mode export`, or a
   separate accumulation file?
4. Is there a maximum look-back window (e.g. "only last 24 h") or should the
   watermark go back to the beginning of time on first run?

## Verification

After writing the script:
1. Run `venv-systempackages/bin/python mysql_connect.py --help` and confirm the
   help text is correct.
2. Check that `duckdb` and the `mysql_scanner` extension are available:
   `venv-systempackages/bin/python -c "import duckdb; c=duckdb.connect(); c.execute('INSTALL mysql; LOAD mysql;'); print('ok')"`.
3. Report which packages are missing if the extension install fails.

## Implementation status

- [x] `--mode live`   — implemented in `to_duckdb/mysql_connect.py`
- [x] `--mode export` — implemented in `to_duckdb/mysql_connect.py`
- [ ] `--mode poll`   — pending MySQL schema inspection (see design decisions above)
