from PySide6.QtWidgets import (
    QMainWindow,
    QMenuBar,
    QMenu,
    QToolBar,
    QStatusBar,
    QDockWidget,
    QTabWidget,
    QMessageBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction

from db_plugin.gui.widgets.object_tree import ObjectTreePanel
from db_plugin.gui.widgets.data_browser import DataBrowserWidget
from db_plugin.gui.widgets.sql_editor import SqlEditorWidget
from db_plugin.gui.dialogs.connection_dialog import ConnectionDialog
from db_plugin.services.connection_manager import ConnectionManager


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self, connection_manager: ConnectionManager):
        super().__init__()
        self.connection_manager = connection_manager
        self.setWindowTitle("Claude Code DB Plugin")
        self.resize(1200, 800)
        self._setup_ui()

    def _setup_ui(self) -> None:
        self._setup_menu()
        self._setup_toolbar()
        self._setup_central_tabs()
        self._setup_object_tree()
        self._setup_statusbar()

    def _setup_menu(self) -> None:
        menubar = self.menuBar()

        file_menu = menubar.addMenu("\u6587\u4ef6")
        exit_action = QAction("\u9000\u51fa", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        query_menu = menubar.addMenu("\u67e5\u8be2")
        execute_action = QAction("\u6267\u884cSQL", self)
        execute_action.setShortcut("Ctrl+Return")
        query_menu.addAction(execute_action)

        tools_menu = menubar.addMenu("\u5de5\u5177")
        fake_data_action = QAction("\u5047\u6570\u636e\u751f\u6210", self)
        tools_menu.addAction(fake_data_action)

        help_menu = menubar.addMenu("\u5e2e\u52a9")
        about_action = QAction("\u5173\u4e8e", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _setup_toolbar(self) -> None:
        toolbar = QToolBar("Main Toolbar", self)
        toolbar.setMovable(False)

        connect_action = toolbar.addAction("\u8fde\u63a5\u7ba1\u7406")
        connect_action.triggered.connect(self._show_connection_dialog)

        toolbar.addSeparator()
        toolbar.addAction("\u6267\u884cSQL")
        toolbar.addAction("\u5047\u6570\u636e")
        toolbar.addAction("\u5bfc\u5165")
        toolbar.addAction("\u5bfc\u51fa")

        # Connect placeholder actions to real dialogs
        actions = toolbar.actions()
        for action in actions:
            if action.text() == "\u5047\u6570\u636e":
                action.triggered.connect(self._show_fake_data_dialog)
            elif action.text() == "\u5bfc\u5165":
                action.triggered.connect(lambda: self._show_import_export_dialog("import"))
            elif action.text() == "\u5bfc\u51fa":
                action.triggered.connect(lambda: self._show_import_export_dialog("export"))

        self.addToolBar(toolbar)

    def _setup_central_tabs(self) -> None:
        self.tabs = QTabWidget()
        self.data_browser = DataBrowserWidget(self.connection_manager)
        self.sql_editor = SqlEditorWidget(self.connection_manager)
        self.tabs.addTab(self.data_browser, "\u6570\u636e\u6d4f\u89c8")
        self.tabs.addTab(self.sql_editor, "SQL \u7f16\u8f91\u5668")
        self.setCentralWidget(self.tabs)

    def _setup_object_tree(self) -> None:
        dock = QDockWidget("\u6570\u636e\u5e93\u5bf9\u8c61", self)
        self.object_tree = ObjectTreePanel(self.connection_manager)
        self.object_tree.table_selected.connect(self._on_table_selected)
        dock.setWidget(self.object_tree)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock)

    def _setup_statusbar(self) -> None:
        self.statusbar = QStatusBar()
        self.statusbar.showMessage("\u672a\u8fde\u63a5")
        self.setStatusBar(self.statusbar)

    def _show_connection_dialog(self) -> None:
        dialog = ConnectionDialog(self.connection_manager, parent=self)
        if dialog.exec():
            self._update_statusbar()

    def _show_about(self) -> None:
        QMessageBox.about(self, "\u5173\u4e8e", "Claude Code DB Plugin v0.1.0")

    def _update_statusbar(self) -> None:
        active = self.connection_manager.active_connection_name
        if active:
            config = self.connection_manager.get(active)
            self.statusbar.showMessage(
                f"\u5df2\u8fde\u63a5: {config.dialect_name}@{config.host}:{config.port}/{config.database}"
            )
        else:
            self.statusbar.showMessage("\u672a\u8fde\u63a5")

    def _on_table_selected(self, table_name: str) -> None:
        self.data_browser.load_table(table_name)
        self.tabs.setCurrentWidget(self.data_browser)

    def _show_fake_data_dialog(self) -> None:
        if not self.connection_manager.db_connection:
            QMessageBox.warning(self, "\u63d0\u793a", "\u8bf7\u5148\u8fde\u63a5\u6570\u636e\u5e93")
            return
        from db_plugin.gui.dialogs.fake_data_dialog import FakeDataDialog
        dialog = FakeDataDialog(self.connection_manager, parent=self)
        dialog.exec()

    def _show_import_export_dialog(self, mode: str) -> None:
        if not self.connection_manager.db_connection:
            QMessageBox.warning(self, "\u63d0\u793a", "\u8bf7\u5148\u8fde\u63a5\u6570\u636e\u5e93")
            return
        from db_plugin.gui.dialogs.import_export_dialog import ImportExportDialog
        dialog = ImportExportDialog(self.connection_manager, parent=self, mode=mode)
        dialog.exec()
