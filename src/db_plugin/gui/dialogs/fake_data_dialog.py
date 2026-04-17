from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QComboBox,
    QSpinBox,
    QPushButton,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
)

from db_plugin.services.connection_manager import ConnectionManager
from db_plugin.services.crud_service import CRUDService
from db_plugin.services.fake_data_generator import FakeDataGenerator
from db_plugin.core.executor import QueryExecutor


class FakeDataDialog(QDialog):
    """Dialog for generating and inserting fake data."""

    def __init__(self, connection_manager: ConnectionManager, parent=None):
        super().__init__(parent)
        self.connection_manager = connection_manager
        self.setWindowTitle("\u5047\u6570\u636e\u751f\u6210\u5668")
        self.resize(600, 500)
        self._setup_ui()
        self._populate_tables()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        form = QFormLayout()
        self.table_combo = QComboBox()
        form.addRow("\u76ee\u6807\u8868:", self.table_combo)

        self.count_spin = QSpinBox()
        self.count_spin.setRange(1, 10000)
        self.count_spin.setValue(10)
        form.addRow("\u751f\u6210\u6761\u6570:", self.count_spin)
        layout.addLayout(form)

        # Preview table
        layout.addWidget(QLabel("\u9884\u89c8:"))
        self.preview_table = QTableWidget()
        layout.addWidget(self.preview_table)

        # Buttons
        btn_layout = QHBoxLayout()
        self.preview_btn = QPushButton("\u9884\u89c8")
        self.preview_btn.clicked.connect(self._preview)
        btn_layout.addWidget(self.preview_btn)

        self.insert_btn = QPushButton("\u751f\u6210\u5e76\u63d2\u5165")
        self.insert_btn.clicked.connect(self._insert)
        btn_layout.addWidget(self.insert_btn)

        btn_layout.addStretch()
        self.cancel_btn = QPushButton("\u53d6\u6d88")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

    def _populate_tables(self) -> None:
        if not self.connection_manager.db_connection:
            return
        dialect = self.connection_manager.db_connection.get_dialect()
        tables = dialect.get_tables()
        self.table_combo.addItems(tables)

    def _preview(self) -> None:
        if not self.connection_manager.db_connection:
            QMessageBox.warning(self, "\u63d0\u793a", "\u8bf7\u5148\u8fde\u63a5\u6570\u636e\u5e93")
            return

        executor = QueryExecutor(self.connection_manager.db_connection)
        crud = CRUDService(executor)
        table_name = self.table_combo.currentText()
        schema = crud.get_schema(table_name)

        generator = FakeDataGenerator()
        records = generator.generate(schema, count=min(self.count_spin.value(), 5))

        self.preview_table.setColumnCount(len(schema.columns))
        self.preview_table.setHorizontalHeaderLabels([c.name for c in schema.columns])
        self.preview_table.setRowCount(len(records))

        for i, record in enumerate(records):
            for j, col in enumerate(schema.columns):
                value = record.get(col.name, "")
                self.preview_table.setItem(i, j, QTableWidgetItem(str(value)))

    def _insert(self) -> None:
        if not self.connection_manager.db_connection:
            QMessageBox.warning(self, "\u63d0\u793a", "\u8bf7\u5148\u8fde\u63a5\u6570\u636e\u5e93")
            return

        table_name = self.table_combo.currentText()
        count = self.count_spin.value()

        executor = QueryExecutor(self.connection_manager.db_connection)
        crud = CRUDService(executor)
        schema = crud.get_schema(table_name)

        generator = FakeDataGenerator()

        records = generator.generate(schema, count=count)
        dialect = executor.connection.get_dialect()

        inserted = 0
        errors = 0
        for record in records:
            result = dialect.insert(table_name, record)
            if result.error_message:
                errors += 1
            else:
                inserted += 1

        QMessageBox.information(
            self,
            "\u5b8c\u6210",
            f"\u5df2\u63d2\u5165 {inserted} \u6761\u8bb0\u5f55{'\uff0c\u5931\u8d25 ' + str(errors) + ' \u6761' if errors else ''}",
        )
        self.accept()
