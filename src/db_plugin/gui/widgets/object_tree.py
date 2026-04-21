from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QMenu
from PySide6.QtCore import Signal, Qt

from db_plugin.services.connection_manager import ConnectionManager
from db_plugin.gui.i18n import _t


class ObjectTreePanel(QTreeWidget):
    """Tree widget showing database objects (schemas, tables, views, etc.)."""

    table_selected = Signal(str)

    def __init__(self, connection_manager: ConnectionManager):
        super().__init__()
        self.connection_manager = connection_manager
        self.setHeaderLabel(_t("object_tree", "title"))
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        self.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.itemClicked.connect(self._on_item_clicked)
        self.setIndentation(20)
        self.setAnimated(True)
        self.setStyleSheet("""
            QTreeWidget {
                font-size: 13px;
                padding: 4px;
            }
            QTreeWidget::item {
                padding: 2px 4px;
            }
        """)
        self.refresh()

    def tr(self, context: str, key: str) -> str:
        return _t(context, key)

    def refresh(self) -> None:
        self.clear()
        if not self.connection_manager.db_connection:
            self.addTopLevelItem(QTreeWidgetItem([self.tr("object_tree", "not_connected")]))
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

        for schema_name in sorted(schemas):
            # Set current schema for dialect queries
            if hasattr(dialect, "current_schema"):
                dialect.current_schema = schema_name

            schema_item = QTreeWidgetItem([self.tr("object_tree", "schema").format(schema=schema_name)])
            schema_item.setFlags(schema_item.flags() | Qt.ItemIsUserCheckable)
            schema_item.setCheckState(0, Qt.Unchecked)

            # Tables node under schema
            tables_item = QTreeWidgetItem([self.tr("object_tree", "tables")])
            try:
                tables = sorted(dialect.get_tables())
                for table in tables:
                    child = QTreeWidgetItem([table])
                    child.setData(0, Qt.UserRole, table)
                    child.setData(1, Qt.UserRole, schema_name)
                    tables_item.addChild(child)
            except Exception:
                tables_item.addChild(QTreeWidgetItem([self.tr("object_tree", "load_failed")]))
            schema_item.addChild(tables_item)

            # Views node under schema
            views_item = QTreeWidgetItem([self.tr("object_tree", "views")])
            try:
                views = sorted(dialect.get_views())
                for view in views:
                    child = QTreeWidgetItem([view])
                    child.setData(0, Qt.UserRole, view)
                    child.setData(1, Qt.UserRole, schema_name)
                    views_item.addChild(child)
            except Exception:
                views_item.addChild(QTreeWidgetItem([self.tr("object_tree", "load_failed")]))
            schema_item.addChild(views_item)

            self.addTopLevelItem(schema_item)
            # Schemas start collapsed; expanding them loads tables
            schema_item.setExpanded(False)

    def _on_item_clicked(self, item, column) -> None:
        """When clicking a schema node, expand it to show tables."""
        # Check if this is a top-level schema item
        if item.parent() is None and item.text(0) != self.tr("object_tree", "not_connected"):
            # Extract schema name from "模式: xxx"
            text = item.text(0)
            schema_prefix = self.tr("object_tree", "schema").format(schema="")
            if text.startswith(schema_prefix):
                schema_name = text[len(schema_prefix):]
                db_conn = self.connection_manager.db_connection
                dialect = db_conn.get_dialect()
                if hasattr(dialect, "current_schema"):
                    dialect.current_schema = schema_name
                # Expand to show tables/views
                item.setExpanded(True)

    def _on_item_double_clicked(self, item, column) -> None:
        parent = item.parent()
        if parent and parent.text(0) in [self.tr("object_tree", "tables"), self.tr("object_tree", "views")]:
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

        if parent_text == self.tr("object_tree", "tables"):
            table_name = item.text(0)
            schema_name = item.data(1, Qt.UserRole)
            full_name = f"{schema_name}.{table_name}" if schema_name else table_name

            view_action = menu.addAction(self.tr("object_tree", "view_data"))
            view_action.triggered.connect(
                lambda: self.table_selected.emit(full_name)
            )
            schema_action = menu.addAction(self.tr("object_tree", "view_schema"))
            copy_action = menu.addAction(self.tr("object_tree", "copy_name"))
            copy_action.triggered.connect(
                lambda: None  # Would copy to clipboard
            )
            menu.exec(self.mapToGlobal(position))
