import logging

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
    QTabWidget,
    QGroupBox,
    QLineEdit,
    QFileDialog,
    QHeaderView,
)

from db_plugin.models.config import FakeDataConfig, TIME_TYPE_LABELS, INT_MODE_LABELS
from db_plugin.services.connection_manager import ConnectionManager
from db_plugin.services.crud_service import CRUDService
from db_plugin.services.fake_data_generator import FakeDataGenerator, load_config, save_config
from db_plugin.core.executor import QueryExecutor

logger = logging.getLogger(__name__)


class FakeDataDialog(QDialog):
    """Dialog for generating and inserting fake data."""

    def __init__(self, connection_manager: ConnectionManager, parent=None):
        super().__init__(parent)
        self.connection_manager = connection_manager
        self.config = load_config()
        self.setWindowTitle("\u5047\u6570\u636e\u751f\u6210\u5668")
        self.resize(600, 550)
        self._setup_ui()
        self._populate_tables()
        self._load_config_to_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()

        # Tab 1: Generation
        gen_widget = self._create_generate_tab()
        self.tabs.addTab(gen_widget, "\u751f\u6210")

        # Tab 2: Configuration
        cfg_widget = self._create_config_tab()
        self.tabs.addTab(cfg_widget, "\u914d\u7f6e")

        layout.addWidget(self.tabs)

    def _create_generate_tab(self) -> QTabWidget:
        tab = QTabWidget()
        layout = QVBoxLayout()

        form = QFormLayout()
        self.table_combo = QComboBox()
        form.addRow("\u76ee\u6807\u8868:", self.table_combo)

        self.count_spin = QSpinBox()
        self.count_spin.setRange(1, 10000)
        self.count_spin.setValue(10)
        form.addRow("\u751f\u6210\u6761\u6570:", self.count_spin)
        layout.addLayout(form)

        layout.addWidget(QLabel("\u9884\u89c8:"))
        self.preview_table = QTableWidget()
        layout.addWidget(self.preview_table)

        btn_layout = QHBoxLayout()
        self.preview_btn = QPushButton("\u9884\u89c8")
        self.preview_btn.clicked.connect(self._preview)
        btn_layout.addWidget(self.preview_btn)

        self.insert_btn = QPushButton("\u751f\u6210\u5e76\u63d2\u5165")
        self.insert_btn.clicked.connect(self._insert)
        btn_layout.addWidget(self.insert_btn)

        btn_layout.addStretch()
        cancel_btn = QPushButton("\u53d6\u6d88")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        tab.setLayout(layout)
        return tab

    def _create_config_tab(self) -> QTabWidget:
        tab = QTabWidget()
        layout = QVBoxLayout()

        # Time type
        time_group = QGroupBox("\u65f6\u95f4\u7c7b\u578b\u914d\u7f6e")
        time_layout = QFormLayout()
        self.time_type_combo = QComboBox()
        for i in range(10):
            self.time_type_combo.addItem(f"{i}: {TIME_TYPE_LABELS[i]}")
        time_layout.addRow("\u65f6\u95f4\u8303\u56f4:", self.time_type_combo)
        time_group.setLayout(time_layout)
        layout.addWidget(time_group)

        # Integer mode
        int_group = QGroupBox("\u6574\u5f62\u914d\u7f6e")
        int_layout = QFormLayout()
        self.int_mode_combo = QComboBox()
        for i in range(2):
            self.int_mode_combo.addItem(f"{i}: {INT_MODE_LABELS[i]}")
        int_layout.addRow("\u6574\u5f62\u6a21\u5f0f:", self.int_mode_combo)
        int_group.setLayout(int_layout)
        layout.addWidget(int_group)

        # Address file
        addr_group = QGroupBox("\u5730\u5740\u8868\u914d\u7f6e")
        addr_layout = QHBoxLayout()
        self.addr_file_edit = QLineEdit()
        self.addr_file_edit.setPlaceholderText("\u4f7f\u7528\u5185\u7f6e\u5730\u5740\u8868")
        addr_layout.addWidget(self.addr_file_edit)
        addr_btn = QPushButton("\u9009\u62e9\u6587\u4ef6")
        addr_btn.clicked.connect(self._select_address_file)
        addr_layout.addWidget(addr_btn)
        addr_group.setLayout(addr_layout)
        layout.addWidget(addr_group)

        # Extra rules
        rules_group = QGroupBox("\u6269\u5c55\u89c4\u5219")
        rules_layout = QVBoxLayout()
        self.rules_table = QTableWidget()
        self.rules_table.setColumnCount(2)
        self.rules_table.setHorizontalHeaderLabels(["\u5217\u540d\u6a21\u5f0f", "faker \u65b9\u6cd5\u540d"])
        self.rules_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        rules_layout.addWidget(self.rules_table)

        rules_btn_layout = QHBoxLayout()
        add_rule_btn = QPushButton("+ \u6dfb\u52a0")
        add_rule_btn.clicked.connect(self._add_rule_row)
        rules_btn_layout.addWidget(add_rule_btn)
        del_rule_btn = QPushButton("- \u5220\u9664")
        del_rule_btn.clicked.connect(self._del_rule_row)
        rules_btn_layout.addWidget(del_rule_btn)
        rules_btn_layout.addStretch()
        rules_layout.addLayout(rules_btn_layout)
        rules_group.setLayout(rules_layout)
        layout.addWidget(rules_group)

        # Save / Reset buttons
        save_layout = QHBoxLayout()
        self.save_cfg_btn = QPushButton("\u4fdd\u5b58\u914d\u7f6e")
        self.save_cfg_btn.clicked.connect(self._save_config_from_ui)
        save_layout.addWidget(self.save_cfg_btn)
        self.reset_cfg_btn = QPushButton("\u91cd\u7f6e")
        self.reset_cfg_btn.clicked.connect(self._reset_config_ui)
        save_layout.addWidget(self.reset_cfg_btn)
        save_layout.addStretch()
        layout.addLayout(save_layout)

        tab.setLayout(layout)
        return tab

    def _load_config_to_ui(self) -> None:
        """Populate config UI from loaded config."""
        self.time_type_combo.setCurrentIndex(self.config.time_type)
        self.int_mode_combo.setCurrentIndex(self.config.int_mode)
        if self.config.address_file:
            self.addr_file_edit.setText(self.config.address_file)
        # Populate extra rules
        self.rules_table.setRowCount(0)
        for pattern, method in self.config.extra_rules.items():
            self._add_rule_row(pattern, method)

    def _save_config_from_ui(self) -> None:
        """Read config from UI and save to disk."""
        self.config.time_type = self.time_type_combo.currentIndex()
        self.config.int_mode = self.int_mode_combo.currentIndex()
        self.config.address_file = self.addr_file_edit.text().strip()

        extra = {}
        for row in range(self.rules_table.rowCount()):
            pattern_item = self.rules_table.item(row, 0)
            method_item = self.rules_table.item(row, 1)
            if pattern_item and method_item:
                p = pattern_item.text().strip()
                m = method_item.text().strip()
                if p and m:
                    extra[p] = m
        self.config.extra_rules = extra

        save_config(self.config)
        QMessageBox.information(self, "\u6210\u529f", "\u914d\u7f6e\u5df2\u4fdd\u5b58")
        logger.info("Saved fake data config: time_type=%d, int_mode=%d, address_file='%s', extra_rules=%s",
                     self.config.time_type, self.config.int_mode, self.config.address_file, extra)

    def _reset_config_ui(self) -> None:
        """Reset UI to defaults."""
        self.config = FakeDataConfig()
        self._load_config_to_ui()

    def _add_rule_row(self, pattern: str = "", method: str = "") -> None:
        row = self.rules_table.rowCount()
        self.rules_table.insertRow(row)
        self.rules_table.setItem(row, 0, QTableWidgetItem(pattern))
        self.rules_table.setItem(row, 1, QTableWidgetItem(method))

    def _del_rule_row(self) -> None:
        row = self.rules_table.currentRow()
        if row >= 0:
            self.rules_table.removeRow(row)

    def _select_address_file(self) -> None:
        filepath, _ = QFileDialog.getOpenFileName(
            self, "\u9009\u62e9\u5730\u5740\u6587\u4ef6", "", "JSON (*.json);;CSV (*.csv);;All (*)"
        )
        if filepath:
            self.addr_file_edit.setText(filepath)

    def _populate_tables(self) -> None:
        if not self.connection_manager.db_connection:
            return
        dialect = self.connection_manager.db_connection.get_dialect()
        tables = dialect.get_tables()
        self.table_combo.addItems(tables)

    def _make_generator(self) -> FakeDataGenerator:
        """Create a FakeDataGenerator with current config."""
        self.config.time_type = self.time_type_combo.currentIndex()
        self.config.int_mode = self.int_mode_combo.currentIndex()
        self.config.address_file = self.addr_file_edit.text().strip()

        extra = {}
        for row in range(self.rules_table.rowCount()):
            pattern_item = self.rules_table.item(row, 0)
            method_item = self.rules_table.item(row, 1)
            if pattern_item and method_item:
                p = pattern_item.text().strip()
                m = method_item.text().strip()
                if p and m:
                    extra[p] = m
        self.config.extra_rules = extra

        if self.config.address_file:
            from db_plugin.services.addresses import set_address_file
            set_address_file(self.config.address_file)

        return FakeDataGenerator(self.config)

    def _preview(self) -> None:
        if not self.connection_manager.db_connection:
            QMessageBox.warning(self, "\u63d0\u793a", "\u8bf7\u5148\u8fde\u63a5\u6570\u636e\u5e93")
            return

        executor = QueryExecutor(self.connection_manager.db_connection)
        crud = CRUDService(executor)
        table_name = self.table_combo.currentText()
        schema = crud.get_schema(table_name)
        logger.info("Previewing fake data for table '%s' (count=%d)", table_name, self.count_spin.value())

        generator = self._make_generator()
        records = generator.generate(schema, count=min(self.count_spin.value(), 5))

        self.preview_table.setColumnCount(len(schema.columns))
        self.preview_table.setHorizontalHeaderLabels([c.name for c in schema.columns])
        self.preview_table.setRowCount(len(records))

        for i, record in enumerate(records):
            for j, col in enumerate(schema.columns):
                value = record.get(col.name, "")
                self.preview_table.setItem(i, j, QTableWidgetItem(str(value)))

        logger.info("Fake data preview populated with %d records", len(records))

    def _insert(self) -> None:
        if not self.connection_manager.db_connection:
            QMessageBox.warning(self, "\u63d0\u793a", "\u8bf7\u5148\u8fde\u63a5\u6570\u636e\u5e93")
            return

        table_name = self.table_combo.currentText()
        count = self.count_spin.value()
        logger.info("Inserting fake data into '%s', requested count: %d", table_name, count)

        executor = QueryExecutor(self.connection_manager.db_connection)
        crud = CRUDService(executor)
        schema = crud.get_schema(table_name)

        generator = self._make_generator()
        records = generator.generate(schema, count=count)
        dialect = executor.connection.get_dialect()
        full_table = f"{dialect.current_schema}.{table_name}"

        inserted = 0
        errors = 0
        for record in records:
            result = dialect.insert(full_table, record)
            if result.error_message:
                errors += 1
                logger.warning("Failed to insert fake record into '%s': %s", table_name, result.error_message)
            else:
                inserted += 1

        logger.info("Fake data insert done for '%s': %d inserted, %d errors", table_name, inserted, errors)

        QMessageBox.information(
            self,
            "\u5b8c\u6210",
            f"\u5df2\u63d2\u5165 {inserted} \u6761\u8bb0\u5f55{'\uff0c\u5931\u8d25 ' + str(errors) + ' \u6761' if errors else ''}",
        )
        self.accept()
