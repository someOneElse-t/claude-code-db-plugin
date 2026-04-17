from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QMenu
from PySide6.QtCore import Signal, Qt

from db_plugin.services.connection_manager import ConnectionManager


class ObjectTreePanel(QTreeWidget):
    """Tree widget showing database objects (schemas, tables, views, etc.)."""

    table_selected = Signal(str)

    def __init__(self, connection_manager: ConnectionManager):
        super().__init__()
        self.connection_manager = connection_manager
        self.setHeaderLabel("\u6570\u636e\u5e93\u5bf9\u8c61")
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        self.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.refresh()

    def refresh(self) -> None:
        self.clear()
        if not self.connection_manager.db_connection:
            self.addTopLevelItem(QTreeWidgetItem(["\u672a\u8fde\u63a5"]))
            return

        db_conn = self.connection_manager.db_connection
        dialect = db_conn.get_dialect()

        # Query schemas
        try:
            schemas = dialect.get_schemas()
        except Exception:
            schemas = ["public"]
            if hasattr(dialect, "current_schema"):
                dialect.current_schema = "public"

        for schema_name in schemas:
            # Set current schema for dialect queries
            if hasattr(dialect, "current_schema"):
                dialect.current_schema = schema_name

            schema_item = QTreeWidgetItem([f"\u6a21\u5f0f: {schema_name}"])
            schema_item.setFlags(schema_item.flags() | Qt.ItemIsUserCheckable)
            schema_item.setCheckState(0, Qt.Unchecked)

            # Tables node under schema
            tables_item = QTreeWidgetItem(["\u8868"])
            try:
                tables = dialect.get_tables()
                for table in tables:
                    child = QTreeWidgetItem([table])
                    child.setData(0, Qt.UserRole, table)
                    child.setData(1, Qt.UserRole, schema_name)
                    tables_item.addChild(child)
            except Exception:
                tables_item.addChild(QTreeWidgetItem(["\u52a0\u8f7d\u5931\u8d25"]))
            schema_item.addChild(tables_item)

            # Views node under schema
            views_item = QTreeWidgetItem(["\u89c6\u56fe"])
            try:
                views = dialect.get_views()
                for view in views:
                    child = QTreeWidgetItem([view])
                    child.setData(0, Qt.UserRole, view)
                    child.setData(1, Qt.UserRole, schema_name)
                    views_item.addChild(child)
            except Exception:
                views_item.addChild(QTreeWidgetItem(["\u52a0\u8f7d\u5931\u8d25"]))
            schema_item.addChild(views_item)

            self.addTopLevelItem(schema_item)
            schema_item.setExpanded(True)

    def _on_item_double_clicked(self, item, column) -> None:
        parent = item.parent()
        if parent and parent.text(0) in ["\u8868", "\u89c6\u56fe"]:
            table_name = item.text(0)
            schema_name = item.data(1, Qt.UserRole)
            if schema_name:
                table_name = f"{schema_name}.{table_name}"
            self.table_selected.emit(table_name)

    def _show_context_menu(self, position) -> None:
        item = self.itemAt(position)
        if item is None or item.parent() is None:
            return

        menu = QMenu(self)
        parent_text = item.parent().text(0)

        if parent_text == "\u8868":
            table_name = item.text(0)
            schema_name = item.data(1, Qt.UserRole)
            full_name = f"{schema_name}.{table_name}" if schema_name else table_name

            view_action = menu.addAction("\u67e5\u770b\u6570\u636e")
            view_action.triggered.connect(
                lambda: self.table_selected.emit(full_name)
            )
            schema_action = menu.addAction("\u67e5\u770b\u8868\u7ed3\u6784")
            copy_action = menu.addAction("\u590d\u5236\u8868\u540d")
            copy_action.triggered.connect(
                lambda: None  # Would copy to clipboard
            )
            menu.exec(self.mapToGlobal(position))
