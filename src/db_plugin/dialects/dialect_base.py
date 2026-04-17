from abc import ABC, abstractmethod
from typing import Any

from db_plugin.models.config import ConnectionConfig
from db_plugin.models.result import QueryResult
from db_plugin.models.schema import ColumnSchema


class DialectBase(ABC):
    """Abstract base class for database dialects."""

    name: str
    quote_char: str

    @property
    def current_schema(self) -> str:
        """Return the currently selected schema name."""

    @current_schema.setter
    def current_schema(self, value: str) -> None:
        """Set the current schema for subsequent queries."""

    @abstractmethod
    def get_schemas(self) -> list[str]:
        """Return list of schema names."""

    @abstractmethod
    def connect(self, config: ConnectionConfig) -> Any:
        """Establish a database connection using the given config."""

    @abstractmethod
    def close(self) -> None:
        """Close the database connection."""

    @abstractmethod
    def execute_query(self, sql: str, params: tuple = ()) -> QueryResult:
        """Execute a SQL query and return QueryResult."""

    @abstractmethod
    def get_tables(self) -> list[str]:
        """Return list of table names."""

    @abstractmethod
    def get_columns(self, table_name: str) -> list[ColumnSchema]:
        """Return column schema for the given table."""

    @abstractmethod
    def get_views(self) -> list[str]:
        """Return list of view names."""

    @abstractmethod
    def get_primary_keys(self, table_name: str) -> list[str]:
        """Return list of primary key column names."""

    @abstractmethod
    def insert(self, table: str, data: dict) -> QueryResult:
        """Insert a row into the table."""

    @abstractmethod
    def update(self, table: str, data: dict, where: dict) -> QueryResult:
        """Update rows matching the where clause."""

    @abstractmethod
    def delete(self, table: str, where: dict) -> QueryResult:
        """Delete rows matching the where clause."""

    @abstractmethod
    def quote_identifier(self, name: str) -> str:
        """Quote an identifier (table/column name) with the dialect's quote character."""

    def format_table_ref(self, table_name: str) -> str:
        """Format a table reference for use in SQL FROM clause.
        Handles schema.table names appropriately per dialect.
        """
        if "." in table_name:
            schema, table = table_name.split(".", 1)
            return f"{self.quote_identifier(schema)}.{self.quote_identifier(table)}"
        return self.quote_identifier(table_name)

    @abstractmethod
    def get_type_mapping(self) -> dict[str, type]:
        """Return mapping of database type names to Python types."""
