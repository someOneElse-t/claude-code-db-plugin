import logging

from PySide6.QtWidgets import (
    QMainWindow,
    QMenuBar,
    QMenu,
    QToolBar,
    QStatusBar,
    QDockWidget,
    QTabWidget,
    QMessageBox,
    QLabel,
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QAction, QIcon

from db_plugin.gui.widgets.object_tree import ObjectTreePanel
from db_plugin.gui.widgets.data_browser import DataBrowserWidget
from db_plugin.gui.widgets.sql_editor import SqlEditorWidget
from db_plugin.gui.dialogs.connection_dialog import ConnectionDialog
from db_plugin.services.connection_manager import ConnectionManager
from db_plugin.gui.app import toggle_theme, get_current_theme
from db_plugin.gui.i18n import _t

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self, connection_manager: ConnectionManager):
        super().__init__()
        self.connection_manager = connection_manager
        self.setWindowTitle("Claude Code DB Plugin")
        self.resize(1200, 800)
        self._setup_ui()

    def tr(self, context: str, key: str) -> str:
        return _t(context, key)

    def _setup_ui(self) -> None:
        self._setup_menu()
        self._setup_toolbar()
        self._setup_central_tabs()
        self._setup_object_tree()
        self._setup_statusbar()

    def _setup_menu(self) -> None:
        menubar = self.menuBar()

        file_menu = menubar.addMenu(self.tr("menus", "file"))
        exit_action = QAction(self.tr("menus", "exit"), self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        query_menu = menubar.addMenu(self.tr("menus", "query"))
        execute_action = QAction(self.tr("menus", "execute_sql"), self)
        execute_action.setShortcut("Ctrl+Return")
        execute_action.triggered.connect(self._execute_sql)
        query_menu.addAction(execute_action)

        history_action = QAction(self.tr("menus", "query_history"), self)
        history_action.triggered.connect(self._show_history)
        query_menu.addAction(history_action)

        tools_menu = menubar.addMenu(self.tr("menus", "tools"))
        fake_data_action = QAction(self.tr("menus", "fake_data"), self)
        tools_menu.addAction(fake_data_action)

        help_menu = menubar.addMenu(self.tr("menus", "help"))
        about_action = QAction(self.tr("menus", "about"), self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _execute_sql(self) -> None:
        """Execute the current SQL in the editor."""
        logger.info("User triggered SQL execution")
        self.sql_editor._execute()

    def _setup_toolbar(self) -> None:
        toolbar = QToolBar("Main Toolbar", self)
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(20, 20))
        toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

        style = self.style()

        connect_action = toolbar.addAction(
            style.standardIcon(style.StandardPixmap.SP_DialogOpenButton), self.tr("toolbar", "connection_manager")
        )
        connect_action.setToolTip(self.tr("toolbar", "connection_manager_tip"))
        connect_action.triggered.connect(self._show_connection_dialog)

        toolbar.addSeparator()

        exec_action = toolbar.addAction(
            style.standardIcon(style.StandardPixmap.SP_MediaPlay), self.tr("toolbar", "execute_sql")
        )
        exec_action.setToolTip(self.tr("toolbar", "execute_sql_tip"))
        exec_action.triggered.connect(self._execute_sql)

        fake_action = toolbar.addAction(
            style.standardIcon(style.StandardPixmap.SP_FileDialogDetailedView), self.tr("toolbar", "fake_data")
        )
        fake_action.setToolTip(self.tr("toolbar", "fake_data_tip"))
        fake_action.triggered.connect(self._show_fake_data_dialog)

        toolbar.addSeparator()

        import_action = toolbar.addAction(
            style.standardIcon(style.StandardPixmap.SP_DialogApplyButton), self.tr("toolbar", "import")
        )
        import_action.setToolTip(self.tr("toolbar", "import_tip"))
        import_action.triggered.connect(lambda: self._show_import_export_dialog("import"))

        export_action = toolbar.addAction(
            style.standardIcon(style.StandardPixmap.SP_DialogSaveButton), self.tr("toolbar", "export")
        )
        export_action.setToolTip(self.tr("toolbar", "export_tip"))
        export_action.triggered.connect(lambda: self._show_import_export_dialog("export"))

        toolbar.addSeparator()

        theme_action = toolbar.addAction(
            style.standardIcon(style.StandardPixmap.SP_DesktopIcon), self.tr("toolbar", "theme")
        )
        theme_action.setToolTip(self.tr("toolbar", "theme_tip"))
        theme_action.triggered.connect(self._toggle_theme)

        self.addToolBar(toolbar)

    def _setup_central_tabs(self) -> None:
        self.tabs = QTabWidget()
        self.data_browser = DataBrowserWidget(self.connection_manager)
        self.sql_editor = SqlEditorWidget(self.connection_manager)
        self.tabs.addTab(self.data_browser, self.tr("data_browser", "data_browser_tab"))
        self.tabs.addTab(self.sql_editor, self.tr("sql_editor", "tab"))
        self.setCentralWidget(self.tabs)

    def _setup_object_tree(self) -> None:
        dock = QDockWidget(self.tr("object_tree", "title"), self)
        self.object_tree = ObjectTreePanel(self.connection_manager)
        self.object_tree.table_selected.connect(self._on_table_selected)
        dock.setWidget(self.object_tree)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock)

    def _setup_statusbar(self) -> None:
        self.statusbar = QStatusBar()
        self.conn_status_label = QLabel("● ")
        self.conn_status_label.setStyleSheet("color: #BDBDBD; font-size: 16px;")
        self.statusbar.addWidget(self.conn_status_label)
        self.statusbar.showMessage(self.tr("statusbar", "not_connected"))
        self.setStatusBar(self.statusbar)

    def _show_connection_dialog(self) -> None:
        dialog = ConnectionDialog(self.connection_manager, parent=self)
        if dialog.exec():
            self._update_statusbar()
            self.object_tree.refresh()

    def _show_about(self) -> None:
        QMessageBox.about(self, self.tr("dialogs", "about_title"), self.tr("dialogs", "about_msg"))

    def _show_history(self) -> None:
        from db_plugin.gui.dialogs.history_dialog import HistoryDialog
        dialog = HistoryDialog(self.sql_editor.history_service, parent=self)
        dialog.exec()
        self._update_statusbar()

    def _update_statusbar(self) -> None:
        active = self.connection_manager.active_connection_name
        if active:
            config = self.connection_manager.get(active)
            msg = self.tr("statusbar", "connected").format(
                dialect=config.dialect_name, host=config.host, port=config.port, database=config.database
            )
            self.statusbar.showMessage(msg)
            self.conn_status_label.setStyleSheet("color: #4CAF50; font-size: 16px;")
        else:
            self.statusbar.showMessage(self.tr("statusbar", "not_connected"))
            self.conn_status_label.setStyleSheet("color: #BDBDBD; font-size: 16px;")

    def _on_table_selected(self, table_name: str) -> None:
        if "." in table_name:
            schema = table_name.split(".", 1)[0]
            db_conn = self.connection_manager.db_connection
            if db_conn:
                dialect = db_conn.get_dialect()
                if hasattr(dialect, "current_schema"):
                    dialect.current_schema = schema
        self.data_browser.load_table(table_name)
        self.tabs.setCurrentWidget(self.data_browser)

    def _show_fake_data_dialog(self) -> None:
        if not self.connection_manager.db_connection:
            QMessageBox.warning(self, self.tr("dialogs", "prompt"), self.tr("dialogs", "not_connected_warn"))
            return
        from db_plugin.gui.dialogs.fake_data_dialog import FakeDataDialog
        default_table = self.data_browser.current_table or ""
        dialog = FakeDataDialog(self.connection_manager, parent=self, default_table=default_table)
        if dialog.exec():
            if self.data_browser.current_table:
                self.data_browser._fetch_data()

    def _show_import_export_dialog(self, mode: str) -> None:
        if not self.connection_manager.db_connection:
            QMessageBox.warning(self, self.tr("dialogs", "prompt"), self.tr("dialogs", "not_connected_warn"))
            return
        from db_plugin.gui.dialogs.import_export_dialog import ImportExportDialog
        dialog = ImportExportDialog(self.connection_manager, parent=self, mode=mode, default_table=self.data_browser.current_table)
        if dialog.exec() and mode == "import" and self.data_browser.current_table:
            self.data_browser._fetch_data()

    def _toggle_theme(self) -> None:
        new_theme = toggle_theme()
        theme_name = self.tr("theme", "dark") if new_theme == "dark" else self.tr("theme", "light")
        self.statusbar.showMessage(self.tr("statusbar", "theme_switched").format(theme=theme_name))
