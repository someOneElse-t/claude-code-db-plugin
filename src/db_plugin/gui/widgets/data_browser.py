from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableView,
    QPushButton,
    QLabel,
    QLineEdit,
    QSpinBox,
    QMessageBox,
)
from PySide6.QtCore import QAbstractTableModel, Qt

from db_plugin.services.connection_manager import ConnectionManager
from db_plugin.services.crud_service import CRUDService
from db_plugin.core.executor import QueryExecutor


class QueryResultModel(QAbstractTableModel):
    """Table model for displaying query results."""

    def __init__(self, columns: list[str] = None, rows: list[dict] = None):
        super().__init__()
        self._columns = columns or []
        self._rows = rows or []

    def rowCount(self, parent=None):
        return len(self._rows)

    def columnCount(self, parent=None):
        return len(self._columns)

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            row = self._rows[index.row()]
            col = self._columns[index.column()]
            value = row.get(col)
            return str(value) if value is not None else "NULL"
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self._columns[section]
            return str(section + 1)
        return None

    def set_result(self, columns: list[str], rows: list[dict]) -> None:
        self.beginResetModel()
        self._columns = columns
        self._rows = rows
        self.endResetModel()


class DataBrowserWidget(QWidget):
    """Widget for browsing table data with pagination."""

    def __init__(self, connection_manager: ConnectionManager):
        super().__init__()
        self.connection_manager = connection_manager
        self.current_table: str | None = None
        self._limit = 100
        self._offset = 0
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Controls
        controls = QHBoxLayout()
        self.table_label = QLabel("\u8868\u540d: \u672a\u9009\u62e9")
        controls.addWidget(self.table_label)

        controls.addStretch()
        self.prev_btn = QPushButton("\u4e0a\u4e00\u9875")
        self.prev_btn.clicked.connect(self._prev_page)
        controls.addWidget(self.prev_btn)

        self.page_label = QLabel("\u7b2c 1 \u9875")
        controls.addWidget(self.page_label)

        self.next_btn = QPushButton("\u4e0b\u4e00\u9875")
        self.next_btn.clicked.connect(self._next_page)
        controls.addWidget(self.next_btn)

        layout.addLayout(controls)

        # Table view
        self.model = QueryResultModel()
        self.table_view = QTableView()
        self.table_view.setModel(self.model)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setSortingEnabled(True)
        layout.addWidget(self.table_view)

    def load_table(self, table_name: str) -> None:
        if not self.connection_manager.db_connection:
            QMessageBox.warning(self, "\u63d0\u793a", "\u8bf7\u5148\u8fde\u63a5\u6570\u636e\u5e93")
            return

        self.current_table = table_name
        self._offset = 0
        self.table_label.setText(f"\u8868\u540d: {table_name}")
        self._fetch_data()

    def _fetch_data(self) -> None:
        executor = QueryExecutor(self.connection_manager.db_connection)
        crud = CRUDService(executor)
        result = crud.read_records(self.current_table, limit=self._limit, offset=self._offset)

        if result.error_message:
            QMessageBox.critical(self, "\u9519\u8bef", result.error_message)
            return

        self.model.set_result(result.columns, result.rows)
        self.page_label.setText(f"\u7b2c {self._offset // self._limit + 1} \u9875 ({result.row_count} \u884c)")

    def _prev_page(self) -> None:
        if self._offset > 0:
            self._offset -= self._limit
            self._fetch_data()

    def _next_page(self) -> None:
        if self.model.rowCount() >= self._limit:
            self._offset += self._limit
            self._fetch_data()
