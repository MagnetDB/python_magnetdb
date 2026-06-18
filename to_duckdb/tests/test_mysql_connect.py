"""
tests/test_mysql_connect.py
===========================
Tests for mysql_connect.py — three categories:

Unit        No external dependencies.  Tests pure-Python/DuckDB helper functions.
Smoke       Uses in-memory DuckDB; no MySQL required.  Tests CLI arg parsing.
Integration Require a live MySQL server.  Skipped unless MYSQL_TEST_HOST,
            MYSQL_TEST_USER, MYSQL_TEST_PASSWORD, and MYSQL_TEST_DB are set.
            Run with:  pytest -m integration
"""

import os
import sys

import duckdb
import pytest

from mysql_connect import (
    _auto_x_field,
    _build_dsn,
    _build_export_select,
    _build_poll_query,
    _env,
    _fetch_poll,
    _is_numeric_type,
    _is_timestamp_type,
    _parse_plot_options,
    _resolve_groups,
    _safe_widget_id,
    parse_args,
)

# ---------------------------------------------------------------------------
# Integration skip marker
# ---------------------------------------------------------------------------

_INTEGRATION_VARS = (
    "MYSQL_TEST_HOST", "MYSQL_TEST_USER",
    "MYSQL_TEST_PASSWORD", "MYSQL_TEST_DB",
)

integration = pytest.mark.skipif(
    not all(os.getenv(v) for v in _INTEGRATION_VARS),
    reason=(
        "Set MYSQL_TEST_HOST / MYSQL_TEST_USER / "
        "MYSQL_TEST_PASSWORD / MYSQL_TEST_DB to run integration tests"
    ),
)

# ---------------------------------------------------------------------------
# Smoke fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def mem_con():
    """Plain in-memory DuckDB connection — no mysqldb attachment, no schema."""
    con = duckdb.connect(":memory:")
    yield con
    con.close()


# ============================================================================
# UNIT TESTS — pure Python, no DuckDB extension, no MySQL
# ============================================================================


class TestIsNumericType:
    @pytest.mark.parametrize("col_type", [
        "FLOAT", "DOUBLE", "DECIMAL(10,2)", "NUMERIC(8,4)", "REAL",
        "INTEGER", "INT", "BIGINT", "SMALLINT", "TINYINT",
        "HUGEINT", "UBIGINT", "UINTEGER", "USMALLINT", "UTINYINT",
        "float",       # lower-case
        "integer",
        "double precision",  # PostgreSQL alias sometimes seen
    ])
    def test_recognized_as_numeric(self, col_type):
        assert _is_numeric_type(col_type)

    @pytest.mark.parametrize("col_type", [
        "VARCHAR", "TIMESTAMP", "DATE", "BOOLEAN", "BLOB",
        "JSON", "TEXT", "CHAR(10)", "DATETIME",
    ])
    def test_not_numeric(self, col_type):
        assert not _is_numeric_type(col_type)

    def test_leading_whitespace_tolerated(self):
        assert _is_numeric_type("  FLOAT  ")

    def test_empty_string_not_numeric(self):
        assert not _is_numeric_type("")


class TestIsTimestampType:
    @pytest.mark.parametrize("col_type", [
        "TIMESTAMP", "TIMESTAMPTZ", "DATE", "DATETIME",
        "timestamp", "date", "datetime",
    ])
    def test_recognized_as_timestamp(self, col_type):
        assert _is_timestamp_type(col_type)

    @pytest.mark.parametrize("col_type", [
        "FLOAT", "INTEGER", "VARCHAR", "BOOLEAN", "BLOB",
    ])
    def test_not_timestamp(self, col_type):
        assert not _is_timestamp_type(col_type)

    def test_leading_whitespace_tolerated(self):
        assert _is_timestamp_type("  TIMESTAMP  ")


class TestAutoXField:
    def test_returns_first_timestamp_column(self):
        cols = [("id", "INTEGER"), ("ts", "TIMESTAMP"), ("val", "FLOAT")]
        assert _auto_x_field(cols) == "ts"

    def test_returns_none_when_no_timestamp(self):
        cols = [("id", "INTEGER"), ("val", "FLOAT")]
        assert _auto_x_field(cols) is None

    def test_returns_none_for_empty_list(self):
        assert _auto_x_field([]) is None

    def test_picks_first_of_multiple_timestamp_columns(self):
        cols = [("t1", "DATE"), ("t2", "TIMESTAMP"), ("val", "FLOAT")]
        assert _auto_x_field(cols) == "t1"

    def test_datetime_counts_as_timestamp(self):
        cols = [("id", "INTEGER"), ("created", "DATETIME")]
        assert _auto_x_field(cols) == "created"


class TestBuildDSN:
    def test_all_fields_present(self):
        dsn = _build_dsn("myhost", 3306, "user", "pass", "mydb")
        assert "host=myhost" in dsn
        assert "port=3306" in dsn
        assert "user=user" in dsn
        assert "password=pass" in dsn
        assert "database=mydb" in dsn

    def test_non_default_port(self):
        dsn = _build_dsn("h", 5555, "u", "p", "d")
        assert "port=5555" in dsn

    def test_returns_string(self):
        assert isinstance(_build_dsn("h", 3306, "u", "p", "d"), str)


class TestBuildPollQuery:
    def test_select_star_when_no_fields(self):
        sql = _build_poll_query("t", [], None, 100, None)
        assert "SELECT *" in sql
        assert "FROM mysqldb.t" in sql
        assert "LIMIT 100" in sql

    def test_specific_fields(self):
        sql = _build_poll_query("t", ["a", "b"], None, 50, None)
        assert "SELECT a, b" in sql

    def test_where_clause_included(self):
        sql = _build_poll_query("t", ["x"], "x > 0", 10, None)
        assert "WHERE x > 0" in sql

    def test_no_where_when_none(self):
        sql = _build_poll_query("t", ["x"], None, 10, None)
        assert "WHERE" not in sql

    def test_order_by_included(self):
        sql = _build_poll_query("t", ["ts", "x"], None, 10, "ts")
        assert "ORDER BY ts" in sql

    def test_no_order_by_when_none(self):
        sql = _build_poll_query("t", ["x"], None, 10, None)
        assert "ORDER BY" not in sql

    def test_limit_at_end_of_query(self):
        sql = _build_poll_query("t", ["x"], "x>0", 77, "x")
        assert sql.endswith("LIMIT 77")

    def test_table_name_embedded(self):
        sql = _build_poll_query("measurements", [], None, 10, None)
        assert "mysqldb.measurements" in sql


class TestBuildExportSelect:
    def test_all_columns_no_filter(self):
        sql = _build_export_select("t", [], None, None, None)
        assert sql == "SELECT * FROM mysqldb.t"

    def test_specific_columns(self):
        sql = _build_export_select("t", ["a", "b"], None, None, None)
        assert "SELECT a, b" in sql
        assert "FROM mysqldb.t" in sql

    def test_start_only(self):
        sql = _build_export_select("t", [], "ts", "2024-01-01", None)
        assert "WHERE" in sql
        assert "2024-01-01" in sql
        assert "CAST" in sql
        assert ">=" in sql

    def test_end_only(self):
        sql = _build_export_select("t", [], "ts", None, "2024-12-31")
        assert "WHERE" in sql
        assert "2024-12-31" in sql
        assert "<=" in sql

    def test_start_and_end_joined_by_and(self):
        sql = _build_export_select("t", [], "ts", "2024-01-01", "2024-12-31")
        assert "AND" in sql
        assert "2024-01-01" in sql
        assert "2024-12-31" in sql

    def test_no_where_when_time_field_missing(self):
        sql = _build_export_select("t", [], None, "2024-01-01", "2024-12-31")
        assert "WHERE" not in sql

    def test_no_where_when_both_bounds_none(self):
        sql = _build_export_select("t", [], "ts", None, None)
        assert "WHERE" not in sql

    def test_timestamp_cast_syntax(self):
        sql = _build_export_select("t", [], "created", "2024-06-01 00:00:00", None)
        assert "CAST('2024-06-01 00:00:00' AS TIMESTAMP)" in sql


class TestResolveGroups:
    def test_subplots_default_one_group_per_field(self):
        groups = _resolve_groups(["a", "b", "c"], {"layout": "subplots"})
        assert groups == [["a"], ["b"], ["c"]]

    def test_overlay_single_group_all_fields(self):
        groups = _resolve_groups(["a", "b"], {"layout": "overlay"})
        assert groups == [["a", "b"]]

    def test_groups_user_defined(self):
        opts = {"layout": "groups", "groups": [["a", "b"], ["c"]]}
        groups = _resolve_groups(["a", "b", "c"], opts)
        assert groups == [["a", "b"], ["c"]]

    def test_groups_unknown_field_exits(self):
        opts = {"layout": "groups", "groups": [["x", "NONEXISTENT"]]}
        with pytest.raises(SystemExit) as exc:
            _resolve_groups(["x"], opts)
        assert exc.value.code == 1

    def test_groups_empty_list_falls_back_to_subplots(self):
        groups = _resolve_groups(["a", "b"], {"layout": "groups", "groups": []})
        assert groups == [["a"], ["b"]]

    def test_unknown_layout_falls_back_to_subplots(self):
        groups = _resolve_groups(["a", "b"], {"layout": "unknown_layout"})
        assert groups == [["a"], ["b"]]

    def test_single_field_overlay(self):
        groups = _resolve_groups(["x"], {"layout": "overlay"})
        assert groups == [["x"]]

    def test_missing_layout_key_defaults_to_subplots(self):
        groups = _resolve_groups(["a", "b"], {})
        assert groups == [["a"], ["b"]]


class TestParseOptions:
    def test_defaults_when_none(self):
        opts = _parse_plot_options(None)
        assert opts["type"] == "line"
        assert opts["layout"] == "subplots"
        assert opts["colors"] == []
        assert opts["font"] is None
        assert opts["fontsize"] is None
        assert opts["figsize"] == [12, 6]

    def test_user_values_override_defaults(self):
        opts = _parse_plot_options('{"type":"scatter","fontsize":12}')
        assert opts["type"] == "scatter"
        assert opts["fontsize"] == 12
        assert opts["layout"] == "subplots"  # untouched default

    def test_partial_override_preserves_other_defaults(self):
        opts = _parse_plot_options('{"font":"Arial"}')
        assert opts["font"] == "Arial"
        assert opts["type"] == "line"
        assert opts["figsize"] == [12, 6]

    def test_invalid_json_exits(self):
        with pytest.raises(SystemExit) as exc:
            _parse_plot_options("{not valid json}")
        assert exc.value.code == 1

    def test_non_object_json_exits(self):
        with pytest.raises(SystemExit) as exc:
            _parse_plot_options("[1, 2, 3]")
        assert exc.value.code == 1

    def test_groups_key_passed_through(self):
        opts = _parse_plot_options('{"layout":"groups","groups":[["a","b"]]}')
        assert opts["groups"] == [["a", "b"]]


class TestSafeWidgetId:
    def test_plain_name_unchanged(self):
        assert _safe_widget_id("Icoil") == "Icoil"

    def test_spaces_replaced_with_underscore(self):
        assert _safe_widget_id("Timestamp Field") == "Timestamp_Field"

    def test_dots_replaced(self):
        assert _safe_widget_id("m.Icoil") == "m_Icoil"

    def test_mixed_special_chars(self):
        result = _safe_widget_id("field (A)")
        for bad in (" ", "(", ")"):
            assert bad not in result

    def test_digits_preserved(self):
        assert _safe_widget_id("ch1_val") == "ch1_val"

    def test_empty_string(self):
        assert _safe_widget_id("") == ""

    def test_all_special_chars_replaced(self):
        result = _safe_widget_id("a-b+c/d")
        assert result == "a_b_c_d"


class TestEnv:
    def test_returns_env_var_value(self, monkeypatch):
        monkeypatch.setenv("TEST_MC_KEY", "hello")
        assert _env("TEST_MC_KEY") == "hello"

    def test_returns_default_when_not_set(self, monkeypatch):
        monkeypatch.delenv("TEST_MC_MISSING", raising=False)
        assert _env("TEST_MC_MISSING", "fallback") == "fallback"

    def test_returns_none_when_not_set_and_no_default(self, monkeypatch):
        monkeypatch.delenv("TEST_MC_MISSING", raising=False)
        assert _env("TEST_MC_MISSING") is None


# ============================================================================
# SMOKE TESTS — in-memory DuckDB, no MySQL
# ============================================================================


class TestFetchPollSmoke:
    def test_returns_column_names_and_rows(self, mem_con):
        mem_con.execute("CREATE TABLE t AS SELECT 1.5 AS x, 2.5 AS y")
        cols, rows = _fetch_poll(mem_con, "SELECT x, y FROM t")
        assert cols == ["x", "y"]
        assert len(rows) == 1
        assert rows[0] == (1.5, 2.5)

    def test_empty_result_returns_empty_rows(self, mem_con):
        mem_con.execute("CREATE TABLE empty_t (x FLOAT)")
        cols, rows = _fetch_poll(mem_con, "SELECT x FROM empty_t")
        assert cols == ["x"]
        assert rows == []

    def test_multiple_rows(self, mem_con):
        mem_con.execute(
            "CREATE TABLE multi AS "
            "SELECT UNNEST([1.0, 2.0, 3.0]) AS v"
        )
        cols, rows = _fetch_poll(mem_con, "SELECT v FROM multi")
        assert cols == ["v"]
        assert len(rows) == 3

    def test_integer_column(self, mem_con):
        mem_con.execute("CREATE TABLE ints AS SELECT 42 AS n")
        cols, rows = _fetch_poll(mem_con, "SELECT n FROM ints")
        assert cols == ["n"]
        assert rows[0][0] == 42

    def test_limit_honoured(self, mem_con):
        mem_con.execute(
            "CREATE TABLE big AS "
            "SELECT UNNEST(range(100)) AS i"
        )
        _, rows = _fetch_poll(mem_con, "SELECT i FROM big LIMIT 10")
        assert len(rows) == 10


class TestParseArgsSmoke:
    """Test CLI argument parsing without connecting to MySQL."""

    _CONN = ["--user", "u", "--password", "p", "--database", "db"]

    def _parse(self, monkeypatch, extra: list):
        # Clear MySQL env vars so they don't satisfy the "missing" check
        for v in ("MYSQL_USER", "MYSQL_PASSWORD", "MYSQL_DB"):
            monkeypatch.delenv(v, raising=False)
        sys.argv = ["mysql_connect.py"] + self._CONN + extra
        return parse_args()

    def test_default_mode_is_live(self, monkeypatch):
        args = self._parse(monkeypatch, [])
        assert args.mode == "live"

    def test_export_mode(self, monkeypatch):
        args = self._parse(monkeypatch, ["--mode", "export"])
        assert args.mode == "export"
        assert args.fmt == "csv"

    def test_export_duckdb_format(self, monkeypatch):
        args = self._parse(monkeypatch, ["--mode", "export", "--format", "duckdb"])
        assert args.fmt == "duckdb"

    def test_export_parquet_format(self, monkeypatch):
        args = self._parse(monkeypatch, ["--mode", "export", "--format", "parquet"])
        assert args.fmt == "parquet"

    def test_export_fields_and_time_range(self, monkeypatch):
        args = self._parse(monkeypatch, [
            "--mode", "export", "--tables", "measurements",
            "--export-fields", "Icoil", "Ucoil",
            "--start", "2024-01-01",
            "--end", "2024-12-31",
        ])
        assert args.export_fields == ["Icoil", "Ucoil"]
        assert args.start == "2024-01-01"
        assert args.end == "2024-12-31"

    def test_poll_with_table(self, monkeypatch):
        args = self._parse(monkeypatch, ["--mode", "poll", "--table", "measurements"])
        assert args.mode == "poll"
        assert args.table == "measurements"

    def test_poll_with_query(self, monkeypatch):
        args = self._parse(monkeypatch, ["--mode", "poll", "--query", "SELECT 1"])
        assert args.query == "SELECT 1"

    def test_poll_list_tables_requires_no_table(self, monkeypatch):
        args = self._parse(monkeypatch, ["--mode", "poll", "--list-tables"])
        assert args.list_tables is True

    def test_poll_list_fields(self, monkeypatch):
        args = self._parse(monkeypatch, [
            "--mode", "poll", "--table", "t", "--list-fields",
        ])
        assert args.list_fields is True

    def test_poll_defaults(self, monkeypatch):
        args = self._parse(monkeypatch, ["--mode", "poll", "--table", "t"])
        assert args.interval == 5.0
        assert args.limit == 200
        assert args.count == 0
        assert args.plot == "matplotlib"

    def test_poll_custom_interval_and_limit(self, monkeypatch):
        args = self._parse(monkeypatch, [
            "--mode", "poll", "--table", "t",
            "--interval", "10.5", "--limit", "500",
        ])
        assert args.interval == 10.5
        assert args.limit == 500

    @pytest.mark.parametrize("backend", ["matplotlib", "plotly", "textual", "dash"])
    def test_poll_plot_backends(self, monkeypatch, backend):
        args = self._parse(monkeypatch, [
            "--mode", "poll", "--table", "t", "--plot", backend,
        ])
        assert args.plot == backend

    def test_poll_dash_host_port(self, monkeypatch):
        args = self._parse(monkeypatch, [
            "--mode", "poll", "--table", "t",
            "--plot", "dash",
            "--dash-host", "0.0.0.0",
            "--dash-port", "9000",
        ])
        assert args.dash_host == "0.0.0.0"
        assert args.dash_port == 9000

    def test_plot_options_stored_as_raw_string(self, monkeypatch):
        raw = '{"type":"scatter","fontsize":11}'
        args = self._parse(monkeypatch, [
            "--mode", "poll", "--table", "t",
            "--plot-options", raw,
        ])
        assert args.plot_options == raw

    def test_where_clause_stored(self, monkeypatch):
        args = self._parse(monkeypatch, [
            "--mode", "poll", "--table", "t",
            "--where", "status='active'",
        ])
        assert args.where == "status='active'"

    def test_verbose_flag(self, monkeypatch):
        args = self._parse(monkeypatch, ["--verbose"])
        assert args.verbose is True

    def test_error_missing_all_credentials(self, monkeypatch):
        for v in ("MYSQL_USER", "MYSQL_PASSWORD", "MYSQL_DB"):
            monkeypatch.delenv(v, raising=False)
        sys.argv = ["mysql_connect.py"]
        with pytest.raises(SystemExit) as exc:
            parse_args()
        assert exc.value.code == 2

    def test_error_table_and_query_mutually_exclusive(self, monkeypatch):
        with pytest.raises(SystemExit) as exc:
            self._parse(monkeypatch, [
                "--mode", "poll",
                "--table", "t",
                "--query", "SELECT 1",
            ])
        assert exc.value.code == 2

    def test_error_poll_without_table_or_query(self, monkeypatch):
        with pytest.raises(SystemExit) as exc:
            self._parse(monkeypatch, ["--mode", "poll"])
        assert exc.value.code == 2

    def test_error_invalid_plot_backend(self, monkeypatch):
        with pytest.raises(SystemExit) as exc:
            self._parse(monkeypatch, [
                "--mode", "poll", "--table", "t",
                "--plot", "gnuplot",
            ])
        assert exc.value.code == 2

    def test_view_mode_with_table(self, monkeypatch):
        args = self._parse(monkeypatch, ["--mode", "view", "--table", "measurements"])
        assert args.mode == "view"
        assert args.table == "measurements"

    def test_view_mode_with_query(self, monkeypatch):
        args = self._parse(monkeypatch, [
            "--mode", "view", "--query", "SELECT 1 AS n",
        ])
        assert args.mode == "view"
        assert args.query == "SELECT 1 AS n"

    def test_view_mode_with_where_and_limit(self, monkeypatch):
        args = self._parse(monkeypatch, [
            "--mode", "view", "--table", "t",
            "--where", "status='active'", "--limit", "50",
        ])
        assert args.where == "status='active'"
        assert args.limit == 50

    def test_view_mode_limit_zero_allowed(self, monkeypatch):
        args = self._parse(monkeypatch, [
            "--mode", "view", "--table", "t", "--limit", "0",
        ])
        assert args.limit == 0

    def test_error_view_without_table_or_query(self, monkeypatch):
        with pytest.raises(SystemExit) as exc:
            self._parse(monkeypatch, ["--mode", "view"])
        assert exc.value.code == 2

    def test_error_view_table_and_query_mutually_exclusive(self, monkeypatch):
        with pytest.raises(SystemExit) as exc:
            self._parse(monkeypatch, [
                "--mode", "view",
                "--table", "t", "--query", "SELECT 1",
            ])
        assert exc.value.code == 2


# ============================================================================
# INTEGRATION TESTS — require a live MySQL server
# ============================================================================


@pytest.fixture(scope="module")
def mysql_con():
    """
    DuckDB connection with a live MySQL database attached as 'mysqldb'.

    Requires env vars:
      MYSQL_TEST_HOST, MYSQL_TEST_USER, MYSQL_TEST_PASSWORD, MYSQL_TEST_DB
    """
    from mysql_connect import _attach_mysql, _build_dsn, _load_mysql_extension

    host = os.environ["MYSQL_TEST_HOST"]
    user = os.environ["MYSQL_TEST_USER"]
    password = os.environ["MYSQL_TEST_PASSWORD"]
    database = os.environ["MYSQL_TEST_DB"]
    port = int(os.environ.get("MYSQL_TEST_PORT", "3306"))

    dsn = _build_dsn(host, port, user, password, database)
    con = duckdb.connect()
    _load_mysql_extension(con)
    _attach_mysql(con, dsn)
    yield con, database
    con.close()


@pytest.mark.integration
class TestIntegrationListTables:
    def test_returns_non_empty_list(self, mysql_con):
        con, database = mysql_con
        from mysql_connect import list_mysql_tables
        tables = list_mysql_tables(con, database)
        assert isinstance(tables, list)
        assert len(tables) > 0

    def test_sorted_alphabetically(self, mysql_con):
        con, database = mysql_con
        from mysql_connect import list_mysql_tables
        tables = list_mysql_tables(con, database)
        assert tables == sorted(tables)

    def test_all_entries_are_strings(self, mysql_con):
        con, database = mysql_con
        from mysql_connect import list_mysql_tables
        for name in list_mysql_tables(con, database):
            assert isinstance(name, str)


@pytest.mark.integration
class TestIntegrationDescribeTable:
    def test_returns_list_of_tuples(self, mysql_con):
        con, database = mysql_con
        from mysql_connect import describe_table, list_mysql_tables
        table = list_mysql_tables(con, database)[0]
        cols = describe_table(con, table)
        assert isinstance(cols, list)
        assert len(cols) > 0
        assert isinstance(cols[0], tuple)

    def test_column_names_and_types_are_strings(self, mysql_con):
        con, database = mysql_con
        from mysql_connect import describe_table, list_mysql_tables
        table = list_mysql_tables(con, database)[0]
        for col in describe_table(con, table):
            assert isinstance(col[0], str), f"column name not str: {col[0]!r}"
            assert isinstance(col[1], str), f"column type not str: {col[1]!r}"


@pytest.mark.integration
class TestIntegrationListNumericColumns:
    def test_returns_subset_of_all_columns(self, mysql_con):
        con, database = mysql_con
        from mysql_connect import describe_table, list_mysql_tables, list_numeric_columns
        table = list_mysql_tables(con, database)[0]
        all_names = {c[0] for c in describe_table(con, table)}
        numeric_names = {c[0] for c in list_numeric_columns(con, table)}
        assert numeric_names.issubset(all_names)

    def test_all_returned_types_are_numeric(self, mysql_con):
        con, database = mysql_con
        from mysql_connect import list_mysql_tables, list_numeric_columns
        table = list_mysql_tables(con, database)[0]
        for name, col_type in list_numeric_columns(con, table):
            assert _is_numeric_type(col_type), (
                f"Column {name!r} has non-numeric type {col_type!r}"
            )


@pytest.mark.integration
class TestIntegrationFetchPoll:
    def test_fetch_returns_cols_and_rows(self, mysql_con):
        con, database = mysql_con
        from mysql_connect import list_mysql_tables
        table = list_mysql_tables(con, database)[0]
        cols, rows = _fetch_poll(con, f"SELECT * FROM mysqldb.{table} LIMIT 5")
        assert isinstance(cols, list)
        assert len(cols) > 0
        assert isinstance(rows, list)
        assert len(rows) <= 5

    def test_limit_respected(self, mysql_con):
        con, database = mysql_con
        from mysql_connect import list_mysql_tables
        table = list_mysql_tables(con, database)[0]
        _, rows = _fetch_poll(con, f"SELECT * FROM mysqldb.{table} LIMIT 3")
        assert len(rows) <= 3
