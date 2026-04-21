import logging

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
from db_plugin.gui.i18n import _t

logger = logging.getLogger(__name__)


class ImportExportDialog(QDialog):
    """Dialog for importing and exporting data."""

    def __init__(self, connection_manager: ConnectionManager, parent=None, mode: str = "export", default_table: str = ""):
        super().__init__(parent)
        self.connection_manager = connection_manager
        self.mode = mode
        self._default_table = default_table
        self.setWindowTitle(_t("import_export", "import_title") if mode == "import" else _t("import_export", "export_title"))
        self.resize(400, 300)
        self._setup_ui()
        self._populate_tables()

    def tr(self, context: str, key: str) -> str:
        return _t(context, key)

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        style = self.style()

        # File selection
        form = QFormLayout()
        self.file_path = QLabel(self.tr("import_export", "no_file"))

        file_btn = QPushButton(
            style.standardIcon(style.StandardPixmap.SP_DialogOpenButton), self.tr("import_export", "select_file")
        )
        file_btn.clicked.connect(self._select_file)

        file_layout = QHBoxLayout()
        file_layout.addWidget(self.file_path)
        file_layout.addWidget(file_btn)
        form.addRow(self.tr("import_export", "format") + ":", file_layout)

        self.table_combo = QComboBox()
        form.addRow(self.tr("fake_data", "target_table") + ":", self.table_combo)
        layout.addLayout(form)

        # Format selection
        format_group = QGroupBox(self.tr("import_export", "format"))
        format_layout = QHBoxLayout()
        self.csv_radio = QRadioButton(self.tr("import_export", "csv"))
        self.excel_radio = QRadioButton(self.tr("import_export", "excel"))
        self.json_radio = QRadioButton(self.tr("import_export", "json"))
        self.csv_radio.setChecked(True)
        format_layout.addWidget(self.csv_radio)
        format_layout.addWidget(self.excel_radio)
        format_layout.addWidget(self.json_radio)
        format_group.setLayout(format_layout)
        layout.addWidget(format_group)

        # Action button
        btn_layout = QHBoxLayout()
        self.action_btn = QPushButton(
            style.standardIcon(style.StandardPixmap.SP_DialogSaveButton),
            self.tr("import_export", "execute") if self.mode == "import" else self.tr("import_export", "export_execute")
        )
        self.action_btn.clicked.connect(self._execute)
        btn_layout.addWidget(self.action_btn)

        btn_layout.addStretch()
        cancel_btn = QPushButton(
            style.standardIcon(style.StandardPixmap.SP_DialogCloseButton), self.tr("import_export", "cancel")
        )
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def _select_file(self) -> None:
        fmt = self._get_format()
        ext_map = {"csv": ".csv", "excel": ".xlsx", "json": ".json"}
        ext = ext_map.get(fmt, ".csv")
        table = self.table_combo.currentText() or ""
        default_name = f"{table}{ext}" if (self.mode == "export" and table) else ""
        if self.mode == "export":
            filepath, _ = QFileDialog.getSaveFileName(
                self, self.tr("import_export", "save_file"), default_name, "CSV (*.csv);;Excel (*.xlsx);;JSON (*.json)"
            )
        else:
            filepath, _ = QFileDialog.getOpenFileName(
                self, self.tr("import_export", "select_file"), default_name, "CSV (*.csv);;Excel (*.xlsx);;JSON (*.json)"
            )
        if filepath:
            self.file_path.setText(filepath)

    def _populate_tables(self) -> None:
        if not self.connection_manager.db_connection:
            return
        dialect = self.connection_manager.db_connection.get_dialect()
        tables = dialect.get_tables()
        self.table_combo.addItems(tables)
        if self._default_table:
            bare_name = self._default_table.split(".")[-1] if "." in self._default_table else self._default_table
            if bare_name in tables:
                idx = tables.index(bare_name)
                self.table_combo.setCurrentIndex(idx)

    def _get_format(self) -> str:
        if self.csv_radio.isChecked():
            return "csv"
        elif self.excel_radio.isChecked():
            return "excel"
        return "json"

    def _execute(self) -> None:
        filepath = self.file_path.text()
        if not filepath or filepath == self.tr("import_export", "no_file"):
            QMessageBox.warning(self, self.tr("dialogs", "prompt"), self.tr("import_export", "select_file_warn"))
            return

        executor = QueryExecutor(self.connection_manager.db_connection)
        service = ImportExportService(executor)

        if self.mode == "export":
            table = self.table_combo.currentText()
            logger.info("Exporting table '%s' to %s", table, filepath)
            crud = CRUDService(executor)
            result = crud.read_records(table, limit=10000)
            if result.error_message:
                QMessageBox.critical(self, self.tr("dialogs", "error"), result.error_message)
                return

            fmt = self._get_format()
            if fmt == "csv":
                service.export_csv(result, filepath)
            elif fmt == "excel":
                service.export_excel(result, filepath)
            else:
                service.export_json(result, filepath)

            QMessageBox.information(self, self.tr("import_export", "success"), self.tr("import_export", "export_success").format(path=filepath))
            logger.info("Export to %s complete", filepath)
        else:
            table = self.table_combo.currentText()
            if not table:
                QMessageBox.warning(self, self.tr("dialogs", "prompt"), self.tr("import_export", "enter_table_warn"))
                return

            logger.info("Importing from %s into table '%s'", filepath, table)
            fmt = self._get_format()
            if fmt == "json":
                QMessageBox.information(self, self.tr("dialogs", "prompt"), self.tr("import_export", "json_import_warn"))
                return
            if fmt == "csv":
                count = service.import_csv(filepath, table)
            elif fmt == "excel":
                count = service.import_excel(filepath, table)
            else:
                count = service.import_json(filepath, table)

            QMessageBox.information(self, self.tr("import_export", "success"), self.tr("import_export", "import_success").format(count=count))
            logger.info("Import complete: %d rows into '%s'", count, table)
            self.accept()
