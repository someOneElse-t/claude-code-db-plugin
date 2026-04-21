from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QLineEdit,
    QPushButton,
    QLabel,
    QHeaderView,
)
from PySide6.QtCore import Qt

from db_plugin.services.query_history import QueryHistoryService
from db_plugin.gui.i18n import _t


class HistoryDialog(QDialog):
    """Dialog showing query execution history."""

    def __init__(self, history_service: QueryHistoryService, parent=None):
        super().__init__(parent)
        self.history_service = history_service
        self.setWindowTitle(_t("history", "title"))
        self.resize(800, 500)
        self._setup_ui()
        self._refresh()

    def tr(self, context: str, key: str) -> str:
        return _t(context, key)

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Search bar
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(self.tr("history", "search_placeholder"))
        self.search_input.returnPressed.connect(self._search)
        search_layout.addWidget(QLabel(self.tr("history", "search") + ":"))
        search_layout.addWidget(self.search_input)

        self.search_btn = QPushButton(self.tr("history", "search"))
        self.search_btn.clicked.connect(self._search)
        search_layout.addWidget(self.search_btn)

        self.show_all_btn = QPushButton(self.tr("history", "show_all"))
        self.show_all_btn.clicked.connect(self._refresh)
        search_layout.addWidget(self.show_all_btn)
        layout.addLayout(search_layout)

        # History table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            self.tr("history", "time"),
            self.tr("history", "connection"),
            self.tr("history", "status"),
            self.tr("history", "elapsed"),
            self.tr("history", "sql"),
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.doubleClicked.connect(self._on_double_click)
        layout.addWidget(self.table)

        # Buttons
        btn_layout = QHBoxLayout()
        self.favorite_btn = QPushButton(self.tr("history", "favorite_toggle"))
        self.favorite_btn.clicked.connect(self._toggle_favorite)
        btn_layout.addWidget(self.favorite_btn)

        self.delete_btn = QPushButton(self.tr("history", "delete"))
        self.delete_btn.clicked.connect(self._delete_selected)
        btn_layout.addWidget(self.delete_btn)

        btn_layout.addStretch()
        self.close_btn = QPushButton(self.tr("history", "close"))
        self.close_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.close_btn)
        layout.addLayout(btn_layout)

    def _refresh(self) -> None:
        self.search_input.clear()
        self._load_entries(self.history_service.list())

    def _search(self) -> None:
        keyword = self.search_input.text().strip()
        if not keyword:
            self._refresh()
            return
        self._load_entries(self.history_service.search(keyword))

    def _load_entries(self, entries) -> None:
        self.table.setRowCount(len(entries))
        for i, entry in enumerate(entries):
            self.table.setItem(i, 0, QTableWidgetItem(entry.timestamp.strftime("%Y-%m-%d %H:%M:%S")))
            self.table.setItem(i, 1, QTableWidgetItem(entry.connection_name))
            status_item = QTableWidgetItem("\u2713" if entry.status == "success" else "\u2717")
            if entry.status == "error":
                status_item.setForeground(Qt.red)
            self.table.setItem(i, 2, status_item)
            self.table.setItem(i, 3, QTableWidgetItem(f"{entry.execution_time_ms:.0f}ms"))
            sql_item = QTableWidgetItem(entry.sql)
            if entry.is_favorite:
                sql_item.setForeground(Qt.yellow)
            self.table.setItem(i, 4, sql_item)
            self.table.item(i, 4).setData(Qt.UserRole, entry.id)

    def _on_double_click(self, index) -> None:
        row = index.row()
        sql = self.table.item(row, 4).text()
        if self.parent() and hasattr(self.parent(), "sql_editor"):
            self.parent().sql_editor.sql_edit.setPlainText(sql)
            self.accept()

    def _toggle_favorite(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            return
        entry_id = self.table.item(row, 4).data(Qt.UserRole)
        self.history_service.toggle_favorite(entry_id)
        self._load_entries(self.history_service.list())

    def _delete_selected(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            return
        entry_id = self.table.item(row, 4).data(Qt.UserRole)
        self.history_service.delete(entry_id)
        self._load_entries(self.history_service.list())
