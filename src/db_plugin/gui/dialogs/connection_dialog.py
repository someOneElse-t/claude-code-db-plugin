from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QComboBox,
    QPushButton,
    QMessageBox,
    QGroupBox,
    QListWidget,
    QListWidgetItem,
)
from PySide6.QtCore import Qt

from db_plugin.services.connection_manager import ConnectionManager
from db_plugin.models.config import ConnectionConfig
from db_plugin.dialects import DIALECT_REGISTRY

DEFAULT_PORTS = {"mysql": 3306, "kingbase": 54321}


class ConnectionDialog(QDialog):
    """Dialog for managing database connections."""

    def __init__(self, connection_manager: ConnectionManager, parent=None):
        super().__init__(parent)
        self.connection_manager = connection_manager
        self.setWindowTitle("\u8fde\u63a5\u7ba1\u7406")
        self.resize(500, 400)
        self._setup_ui()
        self._populate_saved_connections()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Saved connections list
        list_group = QGroupBox("\u5df2\u4fdd\u5b58\u7684\u8fde\u63a5")
        list_layout = QHBoxLayout()
        self.conn_list = QListWidget()
        list_layout.addWidget(self.conn_list)

        btn_layout = QVBoxLayout()
        self.add_btn = QPushButton("\u65b0\u5efa")
        self.delete_btn = QPushButton("\u5220\u9664")
        self.connect_btn = QPushButton("\u8fde\u63a5")
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addWidget(self.connect_btn)
        btn_layout.addStretch()
        list_layout.addLayout(btn_layout)
        list_group.setLayout(list_layout)
        layout.addWidget(list_group)

        # Connection form
        form_group = QGroupBox("\u8fde\u63a5\u914d\u7f6e")
        form = QFormLayout()

        self.name_edit = QLineEdit()
        self.dialect_combo = QComboBox()
        self.dialect_combo.addItems(DIALECT_REGISTRY.keys())
        self.host_edit = QLineEdit("localhost")
        self.port_spin = QSpinBox()
        self.port_spin.setRange(1, 65535)
        self.port_spin.setValue(DEFAULT_PORTS.get(self.dialect_combo.currentText(), 54321))
        self.username_edit = QLineEdit()
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.database_edit = QLineEdit()

        form.addRow("\u540d\u79f0:", self.name_edit)
        form.addRow("\u65b9\u8a00:", self.dialect_combo)
        form.addRow("\u4e3b\u673a:", self.host_edit)
        form.addRow("\u7aef\u53e3:", self.port_spin)
        form.addRow("\u7528\u6237\u540d:", self.username_edit)
        form.addRow("\u5bc6\u7801:", self.password_edit)
        form.addRow("\u6570\u636e\u5e93:", self.database_edit)
        form_group.setLayout(form)
        layout.addWidget(form_group)

        # Test and save
        action_layout = QHBoxLayout()
        self.test_btn = QPushButton("\u6d4b\u8bd5\u8fde\u63a5")
        self.save_btn = QPushButton("\u4fdd\u5b58")
        action_layout.addWidget(self.test_btn)
        action_layout.addWidget(self.save_btn)
        layout.addLayout(action_layout)

        # Signals
        self.add_btn.clicked.connect(self._clear_form)
        self.delete_btn.clicked.connect(self._delete_connection)
        self.connect_btn.clicked.connect(self._connect)
        self.test_btn.clicked.connect(self._test_connection)
        self.save_btn.clicked.connect(self._save_connection)
        self.conn_list.currentItemChanged.connect(self._load_connection)
        self.dialect_combo.currentTextChanged.connect(self._on_dialect_changed)

    def _populate_saved_connections(self) -> None:
        self.conn_list.clear()
        for config in self.connection_manager.list():
            item = QListWidgetItem(f"{config.name} ({config.dialect_name}@{config.host}:{config.port})")
            item.setData(Qt.UserRole, config.name)
            self.conn_list.addItem(item)

    def _on_dialect_changed(self, dialect: str) -> None:
        default_port = DEFAULT_PORTS.get(dialect, 54321)
        self.port_spin.setValue(default_port)

    def _clear_form(self) -> None:
        self.name_edit.clear()
        self.host_edit.setText("localhost")
        self._on_dialect_changed(self.dialect_combo.currentText())
        self.username_edit.clear()
        self.password_edit.clear()
        self.database_edit.clear()

    def _load_connection(self, current, previous) -> None:
        if current is None:
            return
        name = current.data(Qt.UserRole)
        config = self.connection_manager.get(name)
        if config:
            self.name_edit.setText(config.name)
            self.dialect_combo.setCurrentText(config.dialect_name)
            self.host_edit.setText(config.host)
            self.port_spin.setValue(config.port)
            self.username_edit.setText(config.username)
            self.password_edit.setText(config.password)
            self.database_edit.setText(config.database)

    def _save_connection(self) -> None:
        config = ConnectionConfig(
            name=self.name_edit.text(),
            dialect_name=self.dialect_combo.currentText(),
            host=self.host_edit.text(),
            port=self.port_spin.value(),
            username=self.username_edit.text(),
            password=self.password_edit.text(),
            database=self.database_edit.text(),
        )
        if not config.name:
            QMessageBox.warning(self, "\u9519\u8bef", "\u8fde\u63a5\u540d\u79f0\u4e0d\u80fd\u4e3a\u7a7a")
            return
        self.connection_manager.add(config)
        self._populate_saved_connections()
        QMessageBox.information(self, "\u6210\u529f", f"\u8fde\u63a5 '{config.name}' \u5df2\u4fdd\u5b58")

    def _delete_connection(self) -> None:
        current = self.conn_list.currentItem()
        if current is None:
            return
        name = current.data(Qt.UserRole)
        self.connection_manager.remove(name)
        self._populate_saved_connections()

    def _test_connection(self) -> None:
        config = ConnectionConfig(
            name="_test",
            dialect_name=self.dialect_combo.currentText(),
            host=self.host_edit.text(),
            port=self.port_spin.value(),
            username=self.username_edit.text(),
            password=self.password_edit.text(),
            database=self.database_edit.text(),
        )
        success, message = self.connection_manager.test_connection(config)
        if success:
            QMessageBox.information(self, "\u6210\u529f", message)
        else:
            QMessageBox.critical(self, "\u5931\u8d25", message)

    def _connect(self) -> None:
        current = self.conn_list.currentItem()
        if current is None:
            QMessageBox.warning(self, "\u63d0\u793a", "\u8bf7\u5148\u9009\u62e9\u4e00\u4e2a\u8fde\u63a5")
            return
        name = current.data(Qt.UserRole)
        success, message = self.connection_manager.connect(name)
        if success:
            QMessageBox.information(self, "\u6210\u529f", message)
            self.accept()
        else:
            QMessageBox.critical(self, "\u5931\u8d25", message)
