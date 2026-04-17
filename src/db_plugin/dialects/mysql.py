import time
from typing import Any

import pymysql

from db_plugin.dialects.dialect_base import DialectBase
from db_plugin.models.config import ConnectionConfig
from db_plugin.models.result import QueryResult
from db_plugin.models.schema import ColumnSchema


class MySQLDialect(DialectBase):
    """MySQL dialect implementation using pymysql."""

    name: str = "mysql"
    quote_char: str = "`"

    def __init__(self):
        self._connection: Any = None
        self._current_schema: str = ""  # MySQL uses database as schema

    @property
    def current_schema(self) -> str:
        return self._current_schema

    @current_schema.setter
    def current_schema(self, value: str) -> None:
        self._current_schema = value

    def get_schemas(self) -> list[str]:
        result = self.execute_query("SELECT database() AS schema_name")
        if result.error_message:
            return [""]
        schema = result.rows[0].get("schema_name", "") if result.rows else ""
        return [schema] if schema else [""]

    def connect(self, config: ConnectionConfig) -> Any:
        self._connection = pymysql.connect(
            host=config.host,
            port=config.port,
            user=config.username,
            password=config.password,
            database=config.database,
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=False,
            charset="utf8mb4",
            **config.extra_params,
        )
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
            with self._connection.cursor() as cur:
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
        result = self.execute_query(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = DATABASE() AND table_type = 'BASE TABLE'"
        )
        if result.error_message:
            return []
        return [row.get("table_name", "") for row in result.rows]

    def get_columns(self, table_name: str) -> list[ColumnSchema]:
        result = self.execute_query(
            """
            SELECT
                column_name AS name,
                data_type,
                is_nullable,
                column_default AS default_value,
                column_key = 'PRI' AS is_primary_key
            FROM information_schema.columns
            WHERE table_name = %s
            AND table_schema = DATABASE()
            ORDER BY ordinal_position
            """,
            (table_name,),
        )
        columns = []
        for row in result.rows:
            columns.append(ColumnSchema(
                name=row["name"],
                data_type=row["data_type"],
                is_nullable=row["is_nullable"] == "YES",
                default_value=row["default_value"],
                is_primary_key=row["is_primary_key"],
            ))
        return columns

    def get_views(self) -> list[str]:
        result = self.execute_query(
            "SELECT table_name FROM information_schema.views "
            "WHERE table_schema = DATABASE()"
        )
        if result.error_message:
            return []
        return [row.get("table_name", "") for row in result.rows]

    def get_primary_keys(self, table_name: str) -> list[str]:
        result = self.execute_query(
            """
            SELECT column_name
            FROM information_schema.key_column_usage
            WHERE table_name = %s
            AND constraint_name = 'PRIMARY'
            AND table_schema = DATABASE()
            ORDER BY ordinal_position
            """,
            (table_name,),
        )
        return [row["column_name"] for row in result.rows]

    def insert(self, table: str, data: dict) -> QueryResult:
        cols = ", ".join(self.quote_identifier(k) for k in data.keys())
        placeholders = ", ".join(["%s"] * len(data))
        sql = f"INSERT INTO {self.quote_identifier(table)} ({cols}) VALUES ({placeholders})"
        return self.execute_query(sql, tuple(data.values()))

    def update(self, table: str, data: dict, where: dict) -> QueryResult:
        set_clause = ", ".join(
            f"{self.quote_identifier(k)} = %s" for k in data.keys()
        )
        where_clause = " AND ".join(
            f"{self.quote_identifier(k)} = %s" for k in where.keys()
        )
        sql = f"UPDATE {self.quote_identifier(table)} SET {set_clause} WHERE {where_clause}"
        params = tuple(data.values()) + tuple(where.values())
        return self.execute_query(sql, params)

    def delete(self, table: str, where: dict) -> QueryResult:
        where_clause = " AND ".join(
            f"{self.quote_identifier(k)} = %s" for k in where.keys()
        )
        sql = f"DELETE FROM {self.quote_identifier(table)} WHERE {where_clause}"
        return self.execute_query(sql, tuple(where.values()))

    def quote_identifier(self, name: str) -> str:
        return f"`{name}`"

    def get_type_mapping(self) -> dict[str, type]:
        return {
            "int": int,
            "integer": int,
            "bigint": int,
            "smallint": int,
            "mediumint": int,
            "tinyint": int,
            "float": float,
            "double": float,
            "decimal": float,
            "varchar": str,
            "char": str,
            "text": str,
            "tinytext": str,
            "mediumtext": str,
            "longtext": str,
            "boolean": bool,
            "datetime": str,
            "timestamp": str,
            "date": str,
            "time": str,
            "year": int,
            "blob": bytes,
            "tinyblob": bytes,
            "mediumblob": bytes,
            "longblob": bytes,
        }
