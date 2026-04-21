import logging
import time

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QPushButton,
    QLabel,
    QTableView,
    QComboBox,
    QMessageBox,
    QSplitter,
)

from db_plugin.services.connection_manager import ConnectionManager
from db_plugin.services.query_history import QueryHistoryService
from db_plugin.core.executor import QueryExecutor
from db_plugin.core.query_worker import QueryWorker
from db_plugin.gui.widgets.data_browser import QueryResultModel
from db_plugin.gui.widgets.sql_highlighter import SqlHighlighter
from db_plugin.gui.i18n import _t

logger = logging.getLogger(__name__)


class SqlEditorWidget(QWidget):
    """Widget for writing and executing SQL queries."""

    def __init__(self, connection_manager: ConnectionManager):
        super().__init__()
        self.connection_manager = connection_manager
        self.history_service = QueryHistoryService()
        self._worker = None  # Current QueryWorker
        self._setup_ui()

    def tr(self, context: str, key: str) -> str:
        return _t(context, key)

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # SQL input area
        self.sql_edit = QTextEdit()
        self.sql_edit.setPlaceholderText(self.tr("sql_editor", "placeholder"))
        self.sql_edit.setMinimumHeight(200)
        self.sql_edit.setStyleSheet("font-family: Consolas, 'Courier New', monospace; font-size: 13px;")
        self.highlighter = SqlHighlighter(self.sql_edit.document())
        layout.addWidget(self.sql_edit)

        # Controls
        controls = QHBoxLayout()
        style = self.style()

        self.execute_btn = QPushButton(
            style.standardIcon(style.StandardPixmap.SP_MediaPlay), self.tr("sql_editor", "execute")
        )
        self.execute_btn.clicked.connect(self._execute)
        controls.addWidget(self.execute_btn)

        self.cancel_btn = QPushButton(
            style.standardIcon(style.StandardPixmap.SP_MediaStop), "\u53d6\u6d88"
        )
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self._cancel_query)
        controls.addWidget(self.cancel_btn)

        self.clear_btn = QPushButton(
            style.standardIcon(style.StandardPixmap.SP_DialogResetButton), self.tr("sql_editor", "clear")
        )
        self.clear_btn.clicked.connect(lambda: self.sql_edit.clear())
        controls.addWidget(self.clear_btn)

        controls.addStretch()
        self.time_label = QLabel("")
        controls.addWidget(self.time_label)
        layout.addLayout(controls)

        # Result table
        self.model = QueryResultModel()
        self.result_table = QTableView()
        self.result_table.setModel(self.model)
        self.result_table.setAlternatingRowColors(True)
        self.result_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.result_table.setMinimumHeight(200)
        layout.addWidget(self.result_table)

        # Status
        self.status_label = QLabel(self.tr("sql_editor", "ready"))
        self.status_label.setStyleSheet("padding: 4px 0;")
        layout.addWidget(self.status_label)

    def _execute(self) -> None:
        if not self.connection_manager.db_connection:
            QMessageBox.warning(self, self.tr("dialogs", "prompt"), self.tr("sql_editor", "not_connected"))
            return

        sql = self.sql_edit.toPlainText().strip()
        if not sql:
            QMessageBox.warning(self, self.tr("dialogs", "prompt"), self.tr("sql_editor", "enter_sql"))
            return

        # Cancel any running query
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._worker.wait()

        dialect = self.connection_manager.db_connection.get_dialect()
        self._worker = QueryWorker(dialect, sql)
        self._worker.finished.connect(self._on_query_finished)
        self._worker.progress.connect(self._on_query_progress)
        self._worker.error.connect(self._on_query_error)

        # Disable execute button, enable cancel
        self.execute_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.status_label.setStyleSheet("color: gray;")
        self.status_label.setText("Executing...")

        self._worker.start()

    def _cancel_query(self) -> None:
        """Cancel the currently running query."""
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self.status_label.setText("Cancelling...")

    def _on_query_progress(self, message: str) -> None:
        """Update status label with progress message."""
        self.status_label.setText(message)

    def _on_query_error(self, error_msg: str) -> None:
        """Handle query error signal."""
        self.status_label.setText(f"{self.tr('sql_editor', 'error')}: {error_msg}")
        self.status_label.setStyleSheet("color: red;")
        logger.error("Query failed: %s", error_msg)

    def _on_query_finished(self, result) -> None:
        """Handle query result when worker finishes."""
        self.execute_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)

        # Record history
        sql = self.sql_edit.toPlainText().strip()
        self.history_service.add(
            sql,
            self.connection_manager.active_connection_name or "unknown",
            "error" if result.error_message else "success",
            result.execution_time_ms,
        )

        if result.error_message:
            self.status_label.setText(f"{self.tr('sql_editor', 'error')}: {result.error_message}")
            self.status_label.setStyleSheet("color: red;")
        else:
            self.model.set_result(result.columns, result.rows)
            self.time_label.setText(self.tr("sql_editor", "elapsed").format(time=f"{result.execution_time_ms:.0f}"))
            self.status_label.setText(self.tr("sql_editor", "success").format(count=result.row_count))
            self.status_label.setStyleSheet("color: green;")
            logger.info("Query executed in %.0fms, %d rows", result.execution_time_ms, result.row_count)

        self._worker = None
