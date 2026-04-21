import logging

from db_plugin.core.connection import DatabaseConnection
from db_plugin.models.result import QueryResult

logger = logging.getLogger(__name__)


class QueryExecutor:
    """Executes SQL queries through a DatabaseConnection."""

    def __init__(self, connection: DatabaseConnection):
        self.connection = connection

    def execute(self, sql: str, params: tuple = ()) -> QueryResult:
        """Execute a SQL query with optional parameters."""
        logger.info("Executing SQL: %s", sql[:200])
        result = self.connection.dialect.execute_query(sql, params)
        if result.error_message:
            logger.error("SQL execution error: %s", result.error_message)
        else:
            logger.info("SQL executed, rows affected: %d", result.row_count)
        return result

    def execute_many(self, sql: str, params_list: list[tuple]) -> list[QueryResult]:
        """Execute the same SQL with multiple parameter sets."""
        return [self.execute(sql, params) for params in params_list]

    def commit(self) -> None:
        self.connection.dialect.commit()

    def rollback(self) -> None:
        self.connection.dialect.rollback()
