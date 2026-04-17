from typing import Any

from db_plugin.dialects.dialect_base import DialectBase
from db_plugin.models.config import ConnectionConfig
from db_plugin.models.result import QueryResult
from db_plugin.models.schema import ColumnSchema


class MySQLDialect(DialectBase):
    """MySQL dialect placeholder - not yet implemented."""

    name: str = "mysql"
    quote_char: str = "`"

    def connect(self, config: ConnectionConfig) -> Any:
        raise NotImplementedError("MySQL dialect is not yet implemented")

    def close(self) -> None:
        raise NotImplementedError("MySQL dialect is not yet implemented")

    def execute_query(self, sql: str, params: tuple = ()) -> QueryResult:
        raise NotImplementedError("MySQL dialect is not yet implemented")

    def get_tables(self) -> list[str]:
        raise NotImplementedError("MySQL dialect is not yet implemented")

    def get_columns(self, table_name: str) -> list[ColumnSchema]:
        raise NotImplementedError("MySQL dialect is not yet implemented")

    def get_views(self) -> list[str]:
        raise NotImplementedError("MySQL dialect is not yet implemented")

    def get_primary_keys(self, table_name: str) -> list[str]:
        raise NotImplementedError("MySQL dialect is not yet implemented")

    def insert(self, table: str, data: dict) -> QueryResult:
        raise NotImplementedError("MySQL dialect is not yet implemented")

    def update(self, table: str, data: dict, where: dict) -> QueryResult:
        raise NotImplementedError("MySQL dialect is not yet implemented")

    def delete(self, table: str, where: dict) -> QueryResult:
        raise NotImplementedError("MySQL dialect is not yet implemented")

    def quote_identifier(self, name: str) -> str:
        return f"`{name}`"

    def get_type_mapping(self) -> dict[str, type]:
        raise NotImplementedError("MySQL dialect is not yet implemented")
