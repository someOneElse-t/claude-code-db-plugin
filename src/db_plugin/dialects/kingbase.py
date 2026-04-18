import time
from typing import Any

import psycopg2
import psycopg2.extras

from db_plugin.dialects.dialect_base import DialectBase
from db_plugin.models.config import ConnectionConfig
from db_plugin.models.result import QueryResult
from db_plugin.models.schema import ColumnSchema


class KingbaseDialect(DialectBase):
    """Kingbase (人大金仓) dialect implementation.

    Kingbase is compatible with PostgreSQL protocol, so we use psycopg2.
    """

    name: str = "kingbase"
    quote_char: str = "`"

    def __init__(self):
        self._connection: Any = None
        self._current_schema: str = "public"

    @property
    def current_schema(self) -> str:
        return self._current_schema

    @current_schema.setter
    def current_schema(self, value: str) -> None:
        self._current_schema = value

    def get_schemas(self) -> list[str]:
        result = self.execute_query(
            "SELECT schema_name FROM information_schema.schemata "
            "WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast', 'sys_catalog') "
            "ORDER BY schema_name"
        )
        if result.error_message:
            return ["public"]
        schemas = [row.get("schema_name", "") for row in result.rows]
        return schemas if schemas else ["public"]

    def connect(self, config: ConnectionConfig) -> Any:
        params = {
            "host": config.host,
            "port": config.port,
            "user": config.username,
            "password": config.password,
            "dbname": config.database,
            "sslmode": "allow",
            "client_encoding": "UTF8",
            **config.extra_params,
        }
        self._connection = psycopg2.connect(**params)
        self._connection.autocommit = False
        self._current_schema = "public"  # Kingbase default schema
        return self._connection

    def close(self) -> None:
        if self._connection:
            self._connection.close()
            self._connection = None

    def execute_query(self, sql: str, params: tuple = ()) -> QueryResult:
        if not self._connection:
            return QueryResult(
                columns=[],
                rows=[],
                row_count=0,
                execution_time_ms=0,
                error_message="Not connected to database",
            )

        start = time.monotonic()
        try:
            with self._connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(sql, params)
                if cur.description:
                    columns = [desc[0] for desc in cur.description]
                    rows = [dict(row) for row in cur.fetchall()]
                else:
                    columns = []
                    rows = []
                row_count = cur.rowcount
                self._connection.commit()
        except Exception as e:
            self._connection.rollback()
            elapsed = (time.monotonic() - start) * 1000
            return QueryResult(
                columns=[],
                rows=[],
                row_count=0,
                execution_time_ms=elapsed,
                error_message=str(e),
            )

        elapsed = (time.monotonic() - start) * 1000
        return QueryResult(
            columns=columns,
            rows=rows,
            row_count=row_count,
            execution_time_ms=elapsed,
        )

    def get_tables(self) -> list[str]:
        schema = self._current_schema
        result = self.execute_query(
            "SELECT tablename FROM sys_tables WHERE schemaname = %s "
            "UNION ALL SELECT tablename FROM pg_tables WHERE schemaname = %s",
            (schema, schema),
        )
        if result.error_message:
            result = self.execute_query(
                "SELECT tablename FROM pg_tables WHERE schemaname = %s",
                (schema,),
            )
        tables = [row.get("tablename", "") for row in result.rows]
        return list(dict.fromkeys(tables))  # deduplicate while preserving order

    def get_columns(self, table_name: str) -> list[ColumnSchema]:
        schema = self._current_schema
        result = self.execute_query(
            """
            SELECT
                c.column_name AS name,
                c.data_type,
                c.is_nullable,
                c.column_default AS default_value,
                c.column_name IN (
                    SELECT column_name
                    FROM information_schema.key_column_usage
                    WHERE table_name = %s
                    AND table_schema = %s
                    AND constraint_name IN (
                        SELECT constraint_name
                        FROM information_schema.table_constraints
                        WHERE constraint_type = 'PRIMARY KEY'
                        AND table_name = %s
                        AND table_schema = %s
                    )
                ) AS is_primary_key,
                col_description(
                    (quote_ident(%s) || '.' || quote_ident(%s))::regclass,
                    c.ordinal_position
                ) AS comment
            FROM information_schema.columns c
            WHERE c.table_name = %s
            AND c.table_schema = %s
            ORDER BY c.ordinal_position
            """,
            (table_name, schema, table_name, schema, schema, table_name, table_name, schema),
        )
        if result.error_message:
            # Fallback: try without comment (for cases where regclass cast fails)
            result = self.execute_query(
                """
                SELECT
                    c.column_name AS name,
                    c.data_type,
                    c.is_nullable,
                    c.column_default AS default_value,
                    FALSE AS is_primary_key,
                    '' AS comment
                FROM information_schema.columns c
                WHERE c.table_name = %s
                AND c.table_schema = %s
                ORDER BY c.ordinal_position
                """,
                (table_name, schema),
            )
        columns = []
        for row in result.rows:
            columns.append(ColumnSchema(
                name=row["name"],
                data_type=row["data_type"],
                is_nullable=row["is_nullable"] == "YES",
                default_value=row["default_value"],
                is_primary_key=row["is_primary_key"],
                comment=row.get("comment") or "",
            ))
        return columns

    def get_views(self) -> list[str]:
        schema = self._current_schema
        result = self.execute_query(
            "SELECT viewname FROM pg_views WHERE schemaname = %s",
            (schema,),
        )
        return [row.get("viewname", "") for row in result.rows]

    def get_primary_keys(self, table_name: str) -> list[str]:
        schema = self._current_schema
        result = self.execute_query(
            """
            SELECT column_name
            FROM information_schema.key_column_usage
            WHERE table_name = %s
            AND table_schema = %s
            AND constraint_name IN (
                SELECT constraint_name
                FROM information_schema.table_constraints
                WHERE constraint_type = 'PRIMARY KEY'
                AND table_name = %s
                AND table_schema = %s
            )
            """,
            (table_name, schema, table_name, schema),
        )
        return [row["column_name"] for row in result.rows]

    def insert(self, table: str, data: dict) -> QueryResult:
        cols = ", ".join(self.quote_identifier(k) for k in data.keys())
        placeholders = ", ".join(["%s"] * len(data))
        sql = f"INSERT INTO {self.format_table_ref(table)} ({cols}) VALUES ({placeholders})"
        return self.execute_query(sql, tuple(data.values()))

    def update(self, table: str, data: dict, where: dict) -> QueryResult:
        set_clause = ", ".join(
            f"{self.quote_identifier(k)} = %s" for k in data.keys()
        )
        where_clause = " AND ".join(
            f"{self.quote_identifier(k)} = %s" for k in where.keys()
        )
        sql = f"UPDATE {self.format_table_ref(table)} SET {set_clause} WHERE {where_clause}"
        params = tuple(data.values()) + tuple(where.values())
        return self.execute_query(sql, params)

    def delete(self, table: str, where: dict) -> QueryResult:
        where_clause = " AND ".join(
            f"{self.quote_identifier(k)} = %s" for k in where.keys()
        )
        sql = f"DELETE FROM {self.format_table_ref(table)} WHERE {where_clause}"
        return self.execute_query(sql, tuple(where.values()))

    def quote_identifier(self, name: str) -> str:
        return f'`{name}`'

    def format_table_ref(self, table_name: str) -> str:
        """For Kingbase, use schema.table with proper quoting."""
        if "." in table_name:
            schema, table = table_name.split(".", 1)
            return f"{self.quote_identifier(schema)}.{self.quote_identifier(table)}"
        if self.current_schema:
            return f"{self.quote_identifier(self.current_schema)}.{self.quote_identifier(table_name)}"
        return self.quote_identifier(table_name)

    def get_type_mapping(self) -> dict[str, type]:
        return {
            "integer": int,
            "bigint": int,
            "smallint": int,
            "serial": int,
            "real": float,
            "double precision": float,
            "numeric": float,
            "text": str,
            "varchar": str,
            "character varying": str,
            "char": str,
            "boolean": bool,
            "timestamp": str,
            "date": str,
            "time": str,
        }
