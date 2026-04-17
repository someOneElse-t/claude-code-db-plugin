from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QComboBox,
    QPushButton,
    QLabel,
    QFileDialog,
    QMessageBox,
    QGroupBox,
    QRadioButton,
    QButtonGroup,
)

from db_plugin.services.connection_manager import ConnectionManager
from db_plugin.services.import_export import ImportExportService
from db_plugin.services.crud_service import CRUDService
from db_plugin.core.executor import QueryExecutor


class ImportExportDialog(QDialog):
    """Dialog for importing and exporting data."""

    def __init__(self, connection_manager: ConnectionManager, parent=None, mode: str = "export"):
        super().__init__(parent)
        self.connection_manager = connection_manager
        self.mode = mode
        self.setWindowTitle("\u5bfc\u5165" if mode == "import" else "\u5bfc\u51fa")
        self.resize(400, 300)
        self._setup_ui()
        if mode == "export":
            self._populate_tables()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # File selection
        form = QFormLayout()
        self.file_path = QLabel("\u672a\u9009\u62e9\u6587\u4ef6")

        file_btn = QPushButton("\u9009\u62e9\u6587\u4ef6")
        file_btn.clicked.connect(self._select_file)

        file_layout = QHBoxLayout()
        file_layout.addWidget(self.file_path)
        file_layout.addWidget(file_btn)
        form.addRow("\u6587\u4ef6:", file_layout)

        self.table_combo = QComboBox()
        form.addRow("\u76ee\u6807\u8868:", self.table_combo)
        layout.addLayout(form)

        # Format selection
        format_group = QGroupBox("\u683c\u5f0f")
        format_layout = QHBoxLayout()
        self.csv_radio = QRadioButton("CSV")
        self.excel_radio = QRadioButton("Excel")
        self.json_radio = QRadioButton("JSON")
        self.csv_radio.setChecked(True)
        format_layout.addWidget(self.csv_radio)
        format_layout.addWidget(self.excel_radio)
        format_layout.addWidget(self.json_radio)
        format_group.setLayout(format_layout)
        layout.addWidget(format_group)

        # Action button
        btn_layout = QHBoxLayout()
        self.action_btn = QPushButton("\u5bfc\u5165" if self.mode == "import" else "\u5bfc\u51fa")
        self.action_btn.clicked.connect(self._execute)
        btn_layout.addWidget(self.action_btn)

        btn_layout.addStretch()
        cancel_btn = QPushButton("\u53d6\u6d88")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def _select_file(self) -> None:
        if self.mode == "export":
            filepath, _ = QFileDialog.getSaveFileName(
                self, "\u4fdd\u5b58\u6587\u4ef6", "", "CSV (*.csv);;Excel (*.xlsx);;JSON (*.json)"
            )
        else:
            filepath, _ = QFileDialog.getOpenFileName(
                self, "\u9009\u62e9\u6587\u4ef6", "", "CSV (*.csv);;Excel (*.xlsx)"
            )
        if filepath:
            self.file_path.setText(filepath)

    def _populate_tables(self) -> None:
        if not self.connection_manager.db_connection:
            return
        dialect = self.connection_manager.db_connection.get_dialect()
        self.table_combo.addItems(dialect.get_tables())

    def _get_format(self) -> str:
        if self.csv_radio.isChecked():
            return "csv"
        elif self.excel_radio.isChecked():
            return "excel"
        return "json"

    def _execute(self) -> None:
        filepath = self.file_path.text()
        if not filepath or filepath == "\u672a\u9009\u62e9\u6587\u4ef6":
            QMessageBox.warning(self, "\u63d0\u793a", "\u8bf7\u9009\u62e9\u6587\u4ef6")
            return

        executor = QueryExecutor(self.connection_manager.db_connection)
        service = ImportExportService(executor)

        if self.mode == "export":
            table = self.table_combo.currentText()
            crud = CRUDService(executor)
            result = crud.read_records(table, limit=10000)
            if result.error_message:
                QMessageBox.critical(self, "\u9519\u8bef", result.error_message)
                return

            fmt = self._get_format()
            if fmt == "csv":
                service.export_csv(result, filepath)
            elif fmt == "excel":
                service.export_excel(result, filepath)
            else:
                service.export_json(result, filepath)

            QMessageBox.information(self, "\u6210\u529f", f"\u5df2\u5bfc\u51fa\u5230 {filepath}")
        else:
            table = self.table_combo.currentText()
            if not table:
                QMessageBox.warning(self, "\u63d0\u793a", "\u8bf7\u8f93\u5165\u76ee\u6807\u8868\u540d")
                return

            fmt = self._get_format()
            if fmt == "csv":
                count = service.import_csv(filepath, table)
            elif fmt == "excel":
                count = service.import_excel(filepath, table)
            else:
                QMessageBox.warning(self, "\u63d0\u793a", "JSON \u5bfc\u5165\u6682\u4e0d\u652f\u6301")
                return

            QMessageBox.information(self, "\u6210\u529f", f"\u5df2\u5bfc\u5165 {count} \u6761\u8bb0\u5f55")
