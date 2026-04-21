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
from db_plugin.gui.widgets.data_browser import QueryResultModel
from db_plugin.gui.widgets.sql_highlighter import SqlHighlighter

logger = logging.getLogger(__name__)


class SqlEditorWidget(QWidget):
    """Widget for writing and executing SQL queries."""

    def __init__(self, connection_manager: ConnectionManager):
        super().__init__()
        self.connection_manager = connection_manager
        self.history_service = QueryHistoryService()
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # SQL input area
        self.sql_edit = QTextEdit()
        self.sql_edit.setPlaceholderText("\u5728\u6b64\u8f93\u5165 SQL...")
        self.sql_edit.setMinimumHeight(200)
        self.sql_edit.setStyleSheet("font-family: Consolas, 'Courier New', monospace; font-size: 13px;")
        self.highlighter = SqlHighlighter(self.sql_edit.document())
        layout.addWidget(self.sql_edit)

        # Controls
        controls = QHBoxLayout()
        style = self.style()

        self.execute_btn = QPushButton(
            style.standardIcon(style.StandardPixmap.SP_MediaPlay), "\u6267\u884c (Ctrl+Return)"
        )
        self.execute_btn.clicked.connect(self._execute)
        controls.addWidget(self.execute_btn)

        self.clear_btn = QPushButton(
            style.standardIcon(style.StandardPixmap.SP_DialogResetButton), "\u6e05\u7a7a"
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
        self.status_label = QLabel("\u5c31\u7eea")
        self.status_label.setStyleSheet("padding: 4px 0;")
        layout.addWidget(self.status_label)

    def _execute(self) -> None:
        if not self.connection_manager.db_connection:
            QMessageBox.warning(self, "\u63d0\u793a", "\u8bf7\u5148\u8fde\u63a5\u6570\u636e\u5e93")
            return

        sql = self.sql_edit.toPlainText().strip()
        if not sql:
            QMessageBox.warning(self, "\u63d0\u793a", "\u8bf7\u8f93\u5165 SQL \u8bed\u53e5")
            return

        start = time.monotonic()
        executor = QueryExecutor(self.connection_manager.db_connection)
        result = executor.execute(sql)
        elapsed = (time.monotonic() - start) * 1000

        # Record history
        self.history_service.add(
            sql,
            self.connection_manager.active_connection_name or "unknown",
            "error" if result.error_message else "success",
            elapsed,
        )

        if result.error_message:
            self.status_label.setText(f"\u9519\u8bef: {result.error_message}")
            self.status_label.setStyleSheet("color: red;")
            logger.error("Query failed: %s", result.error_message)
        else:
            self.model.set_result(result.columns, result.rows)
            self.time_label.setText(f"\u8017\u65f6: {result.execution_time_ms:.0f}ms")
            self.status_label.setText(f"\u6210\u529f: {result.row_count} \u884c\u53d7\u5f71\u54cd")
            self.status_label.setStyleSheet("color: green;")
            logger.info("Query executed in %.0fms, %d rows", result.execution_time_ms, result.row_count)
