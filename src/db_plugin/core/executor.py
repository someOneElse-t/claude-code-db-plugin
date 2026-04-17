from db_plugin.core.connection import DatabaseConnection
from db_plugin.models.result import QueryResult


class QueryExecutor:
    """Executes SQL queries through a DatabaseConnection."""

    def __init__(self, connection: DatabaseConnection):
        self.connection = connection

    def execute(self, sql: str, params: tuple = ()) -> QueryResult:
        """Execute a SQL query with optional parameters."""
        return self.connection.dialect.execute_query(sql, params)

    def execute_many(self, sql: str, params_list: list[tuple]) -> list[QueryResult]:
        """Execute the same SQL with multiple parameter sets."""
        return [self.execute(sql, params) for params in params_list]

    def commit(self) -> None:
        dialect = self.connection.dialect
        if dialect._connection:
            dialect._connection.commit()

    def rollback(self) -> None:
        dialect = self.connection.dialect
        if dialect._connection:
            dialect._connection.rollback()
