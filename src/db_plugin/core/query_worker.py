import logging
import time
from typing import Any

from PySide6.QtCore import QThread, Signal

from db_plugin.dialects.dialect_base import DialectBase
from db_plugin.models.result import QueryResult

logger = logging.getLogger(__name__)


class QueryWorker(QThread):
    """Executes a SQL query in a background thread and emits the result."""

    finished = Signal(object)  # QueryResult
    progress = Signal(str)     # Status message
    error = Signal(str)        # Error message

    def __init__(self, dialect: DialectBase, sql: str, params: tuple = ()) -> None:
        super().__init__()
        self._dialect = dialect
        self._sql = sql
        self._params = params
        self._cancelled = False

    def run(self) -> None:
        """Execute the query in the background thread."""
        logger.info("QueryWorker started: %s", self._sql[:100])
        self.progress.emit("Executing...")

        if self._cancelled:
            self.progress.emit("Cancelled")
            self.finished.emit(QueryResult(columns=[], rows=[], row_count=0, execution_time_ms=0))
            return

        result = self._dialect.execute_query(self._sql, self._params)

        if self._cancelled:
            self.progress.emit("Cancelled")
            self.finished.emit(QueryResult(columns=[], rows=[], row_count=0, execution_time_ms=0))
            return

        if result.error_message:
            self.error.emit(result.error_message)
            logger.error("QueryWorker error: %s", result.error_message)
        else:
            logger.info("QueryWorker finished: %d rows", result.row_count)

        self.finished.emit(result)

    def cancel(self) -> None:
        """Mark the worker as cancelled."""
        self._cancelled = True
        self.progress.emit("Cancelling...")
