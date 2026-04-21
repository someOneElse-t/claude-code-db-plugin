import logging
import os
import time

from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableView,
    QPushButton,
    QLabel,
    QMessageBox,
    QToolTip,
    QHeaderView,
)

from db_plugin.services.connection_manager import ConnectionManager
from db_plugin.services.crud_service import CRUDService
from db_plugin.core.executor import QueryExecutor
from db_plugin.core.query_worker import QueryWorker
from db_plugin.gui.i18n import _t

logger = logging.getLogger(__name__)

# Dirty cell background color
_DIRTY_BG = QColor(255, 255, 200)


class QueryResultModel(QAbstractTableModel):
    """Table model for displaying query results (read-only)."""

    def __init__(self, columns: list[str] = None, rows: list[dict] = None):
        super().__init__()
        self._columns = columns or []
        self._rows = rows or []

    def rowCount(self, parent=None):
        return len(self._rows)

    def columnCount(self, parent=None):
        return len(self._columns)

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            row = self._rows[index.row()]
            col = self._columns[index.column()]
            value = row.get(col)
            return str(value) if value is not None else "NULL"
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self._columns[section]
            return str(section + 1)
        return None

    def set_result(self, columns: list[str], rows: list[dict]) -> None:
        self.beginResetModel()
        self._columns = columns
        self._rows = rows
        self.endResetModel()


class EditableQueryResultModel(QueryResultModel):
    """Editable version of QueryResultModel with dirty tracking."""

    def __init__(self, columns: list[str] = None, rows: list[dict] = None, table_schema=None, primary_keys: list[str] = None):
        super().__init__(columns, rows)
        self._table_schema = table_schema
        self._primary_keys = primary_keys or []
        self._col_types: dict[str, str] = {}  # col_name -> data_type
        self._editable = False
        self._dirty_cells: dict[tuple[int, str], object] = {}  # (row_idx, col_name) -> original_value
        self._new_rows: list[int] = []  # row indices that are newly added
        self._deleted_row_identifiers: list[dict] = []  # [{pk_col: pk_value}, ...]
        self._existing_pks: set[tuple] = set()  # set of existing PK tuples

    def set_editable(self, editable: bool) -> None:
        self._editable = editable
        self.layoutChanged.emit()

    def set_result(self, columns: list[str], rows: list[dict], table_schema=None) -> None:
        self.beginResetModel()
        self._columns = columns
        self._rows = rows
        self._table_schema = table_schema
        self._primary_keys = table_schema.primary_keys if table_schema else []
        self._col_types = {}
        if table_schema:
            for col in table_schema.columns:
                self._col_types[col.name.lower()] = col.data_type.lower()
        self._dirty_cells.clear()
        self._new_rows.clear()
        self._deleted_row_identifiers.clear()
        self._editable = False
        # Collect existing PK values for conflict detection on new rows
        self._existing_pks: set[tuple] = set()
        for row in self._rows:
            pk_tuple = tuple(str(row.get(pk)) for pk in self._primary_keys)
            self._existing_pks.add(pk_tuple)
        self.endResetModel()

    def flags(self, index):
        base = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if not index.isValid():
            return base
        if not self._editable:
            return base
        col = self._columns[index.column()]
        # Allow PK editing only for new rows
        if col in self._primary_keys and index.row() not in self._new_rows:
            return base
        return base | Qt.ItemIsEditable

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        row = self._rows[index.row()]
        col = self._columns[index.column()]
        value = row.get(col)

        if role == Qt.DisplayRole:
            return str(value) if value is not None else "NULL"
        if role == Qt.EditRole:
            return value  # Return raw value for editing
        if role == Qt.BackgroundRole:
            if (index.row(), col) in self._dirty_cells:
                return QBrush(_DIRTY_BG)
            if index.row() in self._new_rows:
                return QBrush(QColor(200, 255, 200))
        return None

    def _get_pk_tuple_for_row(self, row_idx: int) -> tuple | None:
        """Get the PK tuple for a given row, or None if any PK is NULL."""
        row = self._rows[row_idx]
        values = []
        for pk in self._primary_keys:
            v = row.get(pk)
            if v is None:
                return None
            values.append(str(v))
        return tuple(values)

    def _is_pk_conflict(self, row_idx: int, col_name: str, new_value: object) -> bool:
        """Check if setting a PK column to new_value would cause a conflict."""
        if col_name not in self._primary_keys:
            return False

        # Build the would-be PK tuple for this row
        row = self._rows[row_idx]
        temp_pk_values = []
        for pk in self._primary_keys:
            if pk == col_name:
                temp_pk_values.append(str(new_value) if new_value is not None else None)
            else:
                v = row.get(pk)
                temp_pk_values.append(str(v) if v is not None else None)

        # If any PK column is still NULL, skip conflict check (will be checked at save time)
        if any(v is None for v in temp_pk_values):
            return False

        pk_tuple = tuple(temp_pk_values)

        # Check against all other new rows' PK values
        for other_idx in self._new_rows:
            if other_idx == row_idx or other_idx >= len(self._rows):
                continue
            other_pk = self._get_pk_tuple_for_row(other_idx)
            if other_pk is not None and other_pk == pk_tuple:
                return True

        # Check against existing data
        if pk_tuple in self._existing_pks:
            return True

        return False

    def setData(self, index, value, role=Qt.EditRole):
        if role != Qt.EditRole or not index.isValid():
            return False
        col = self._columns[index.column()]
        row_idx = index.row()
        original = self._rows[row_idx].get(col)

        # Convert value to appropriate type
        converted = self._convert_value(value, col)

        # For PK columns on new rows, check for conflicts before applying
        if col in self._primary_keys and row_idx in self._new_rows:
            if self._is_pk_conflict(row_idx, col, converted):
                QMessageBox.warning(
                    self.parent() if hasattr(self, 'parent') else None,
                    _t("data_browser", "pk_conflict"),
                    _t("data_browser", "pk_conflict_msg"),
                )
                return False

        self._rows[row_idx][col] = converted

        # Track dirty state
        if row_idx not in self._new_rows:
            # Existing row: track if this cell hasn't been tracked yet
            if (row_idx, col) not in self._dirty_cells:
                self._dirty_cells[(row_idx, col)] = original
        else:
            # New row: track PK edits to detect conflicts
            if col in self._primary_keys and (row_idx, col) not in self._dirty_cells:
                self._dirty_cells[(row_idx, col)] = original

        self.dataChanged.emit(index, index, [role])
        return True

    def _convert_value(self, value: object, col_name: str) -> object:
        """Convert a Qt string value to the appropriate Python type."""
        if value is None:
            return None
        val_str = str(value).strip()
        if not val_str:
            return None  # Empty string -> NULL

        col_type = self._col_types.get(col_name.lower(), "")
        # Integer types
        if col_type in ("integer", "bigint", "smallint", "serial", "int", "int2", "int4", "int8"):
            try:
                return int(val_str)
            except (ValueError, TypeError):
                return val_str
        # Float types
        if col_type in ("real", "double precision", "numeric", "decimal", "float", "float4", "float8", "money"):
            try:
                return float(val_str)
            except (ValueError, TypeError):
                return val_str
        # Boolean
        if col_type in ("boolean", "bool"):
            return val_str.lower() in ("true", "1", "yes", "t")
        return val_str

    def _generate_pk_value(self, col_name: str, used_values: set[str]) -> str:
        """Generate a unique primary key value for a new row."""
        col_type = self._col_types.get(col_name.lower(), "")
        max_attempts = 50
        for _ in range(max_attempts):
            if col_type in ("integer", "bigint", "smallint", "serial", "int", "int2", "int4", "int8"):
                ts_val = int(time.time() * 1000) % 1000000000 + os.urandom(1)[0]
                if str(ts_val) not in used_values:
                    return ts_val
            else:
                # varchar/uuid/char: generate timestamp-based UUIDs
                ts_ms = int(time.time() * 1000)
                rand_hex = os.urandom(8).hex()
                val = f"{ts_ms:013d}{rand_hex}"[:32]
                if val not in used_values:
                    return val
            time.sleep(0.001)
        # Fallback: use uuid4
        import uuid
        return str(uuid.uuid4()).replace("-", "")

    def fill_missing_pks(self) -> list[str]:
        """Auto-generate PK values for new rows that have NULL PKs. Returns list of conflicts."""
        conflicts = []
        # Track all PKs seen (existing + new rows) to detect intra-batch duplicates
        all_pk_values: set[tuple] = set(self._existing_pks)
        for row_idx in self._new_rows:
            if row_idx >= len(self._rows):
                continue
            row = self._rows[row_idx]
            # Check if any PK is NULL — only auto-fill NULL ones
            pk_tuple_values = []
            has_null = False
            for pk in self._primary_keys:
                v = row.get(pk)
                if v is None:
                    has_null = True
                    pk_tuple_values.append(None)
                else:
                    pk_tuple_values.append(str(v))

            if has_null:
                # Auto-generate only NULL columns
                used_for_row: set[str] = {v for v in pk_tuple_values if v is not None}
                for pk in self._primary_keys:
                    if row.get(pk) is None:
                        val = self._generate_pk_value(pk, used_for_row)
                        used_for_row.add(str(val))
                        row[pk] = val
                # Re-build tuple with all values filled
                pk_tuple = tuple(str(row.get(pk)) for pk in self._primary_keys)
                if pk_tuple in all_pk_values:
                    conflicts.append(row_idx)
                else:
                    all_pk_values.add(pk_tuple)
            else:
                pk_tuple = tuple(str(row.get(pk)) for pk in self._primary_keys)
                if pk_tuple in all_pk_values:
                    conflicts.append(row_idx)
                else:
                    all_pk_values.add(pk_tuple)
        return conflicts

    def mark_row_new(self, row_idx: int) -> None:
        """Mark a row as newly added."""
        if row_idx not in self._new_rows:
            self._new_rows.append(row_idx)

    def mark_row_deleted(self, row_idx: int) -> None:
        """Mark a row as deleted, storing its PK values."""
        if row_idx < 0 or row_idx >= len(self._rows):
            return
        row_data = self._rows[row_idx]
        pk_values = {pk: row_data.get(pk) for pk in self._primary_keys}
        self._deleted_row_identifiers.append(pk_values)

    def add_new_row(self) -> int:
        """Add a new blank row and return its index."""
        row_idx = len(self._rows)
        self.beginInsertRows(QModelIndex(), row_idx, row_idx)
        self._rows.append({col: None for col in self._columns})
        self.endInsertRows()
        self.mark_row_new(row_idx)
        return row_idx

    def remove_row(self, row_idx: int) -> bool:
        """Remove a row by index, storing its PK values for later deletion."""
        if row_idx < 0 or row_idx >= len(self._rows):
            return False
        if row_idx in self._new_rows:
            # Just remove the new row without storing PK
            self.beginRemoveRows(QModelIndex(), row_idx, row_idx)
            self._rows.pop(row_idx)
            self._new_rows.remove(row_idx)
            # Clean up dirty cells for shifted rows
            self._dirty_cells = {
                (r if r < row_idx else r - 1, c): v
                for (r, c), v in self._dirty_cells.items()
            }
            self.endRemoveRows()
            return True
        self.mark_row_deleted(row_idx)
        self.beginRemoveRows(QModelIndex(), row_idx, row_idx)
        self._rows.pop(row_idx)
        self.endRemoveRows()
        return True

    def is_dirty(self) -> bool:
        return bool(self._dirty_cells or self._new_rows or self._deleted_row_identifiers)

    def get_pending_changes(self) -> dict:
        """Build summary of all pending changes."""
        updates = []
        for (row_idx, col), original in self._dirty_cells.items():
            if row_idx < len(self._rows):
                updates.append({
                    "row": row_idx,
                    "column": col,
                    "old": original,
                    "new": self._rows[row_idx].get(col),
                })
        inserts = []
        for row_idx in self._new_rows:
            if row_idx < len(self._rows):
                inserts.append({"row": row_idx, "data": dict(self._rows[row_idx])})
        deletes = [{"row": i, "pk_values": pk} for i, pk in enumerate(self._deleted_row_identifiers)]
        return {"updates": updates, "inserts": inserts, "deletes": deletes}

    def clear_dirty(self) -> None:
        self._dirty_cells.clear()
        self._new_rows.clear()
        self._deleted_row_identifiers.clear()

    def undo_changes(self) -> None:
        """Restore all dirty cells and remove new rows. Note: deleted rows cannot be recovered."""
        for (row_idx, col), original in self._dirty_cells.items():
            if row_idx < len(self._rows):
                self._rows[row_idx][col] = original
        # Remove new rows (iterate in reverse to maintain valid indices)
        for row_idx in sorted(self._new_rows, reverse=True):
            if row_idx < len(self._rows):
                self.beginRemoveRows(QModelIndex(), row_idx, row_idx)
                self._rows.pop(row_idx)
                self.endRemoveRows()
        self._dirty_cells.clear()
        self._new_rows.clear()
        self._deleted_row_identifiers.clear()


class DataBrowserWidget(QWidget):
    """Widget for browsing table data with pagination and editing."""

    def __init__(self, connection_manager: ConnectionManager):
        super().__init__()
        self.connection_manager = connection_manager
        self.current_table: str | None = None
        self._limit = 100
        self._offset = 0
        self._column_comments: dict[str, str] = {}
        self._primary_keys: list[str] = []
        self._worker = None  # Current QueryWorker
        self._setup_ui()
        self._install_header_hover()

    def tr(self, context: str, key: str) -> str:
        return _t(context, key)

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Controls
        controls = QHBoxLayout()
        self.table_label = QLabel(self.tr("data_browser", "table_unselected"))
        self.table_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        controls.addWidget(self.table_label)

        controls.addStretch()
        self.prev_btn = QPushButton(self.tr("data_browser", "prev_page"))
        self.prev_btn.clicked.connect(self._prev_page)
        controls.addWidget(self.prev_btn)

        self.page_label = QLabel("")
        controls.addWidget(self.page_label)

        self.next_btn = QPushButton(self.tr("data_browser", "next_page"))
        self.next_btn.clicked.connect(self._next_page)
        controls.addWidget(self.next_btn)

        layout.addLayout(controls)

        # Edit toolbar
        edit_toolbar = QHBoxLayout()
        style = self.style()

        self.edit_toggle_btn = QPushButton(
            style.standardIcon(style.StandardPixmap.SP_TitleBarNormalButton), self.tr("data_browser", "edit_mode")
        )
        self.edit_toggle_btn.setCheckable(True)
        self.edit_toggle_btn.clicked.connect(self._toggle_edit_mode)
        self.edit_toggle_btn.setEnabled(False)
        edit_toolbar.addWidget(self.edit_toggle_btn)

        self.add_row_btn = QPushButton(
            style.standardIcon(style.StandardPixmap.SP_FileDialogNewFolder), self.tr("data_browser", "add_row")
        )
        self.add_row_btn.clicked.connect(self._add_row)
        self.add_row_btn.setEnabled(False)
        edit_toolbar.addWidget(self.add_row_btn)

        self.delete_row_btn = QPushButton(
            style.standardIcon(style.StandardPixmap.SP_TrashIcon), self.tr("data_browser", "delete_row")
        )
        self.delete_row_btn.clicked.connect(self._delete_row)
        self.delete_row_btn.setEnabled(False)
        edit_toolbar.addWidget(self.delete_row_btn)

        edit_toolbar.addStretch()

        self.save_btn = QPushButton(
            style.standardIcon(style.StandardPixmap.SP_DialogSaveButton), self.tr("data_browser", "save_changes")
        )
        self.save_btn.clicked.connect(self._save_changes)
        self.save_btn.setEnabled(False)
        edit_toolbar.addWidget(self.save_btn)

        self.discard_btn = QPushButton(
            style.standardIcon(style.StandardPixmap.SP_DialogResetButton), self.tr("data_browser", "discard_changes")
        )
        self.discard_btn.clicked.connect(self._discard_changes)
        self.discard_btn.setEnabled(False)
        edit_toolbar.addWidget(self.discard_btn)

        layout.addLayout(edit_toolbar)

        # Table view
        self.model = EditableQueryResultModel()
        self.table_view = QTableView()
        self.table_view.setModel(self.model)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setSortingEnabled(True)
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table_view.verticalHeader().setDefaultSectionSize(26)
        layout.addWidget(self.table_view)

        # Connect model signals to update edit buttons
        self.model.dataChanged.connect(self._update_edit_buttons)
        self.model.modelReset.connect(self._update_edit_buttons)
        self.model.rowsInserted.connect(self._update_edit_buttons)
        self.model.rowsRemoved.connect(self._update_edit_buttons)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("padding: 4px 0;")
        layout.addWidget(self.status_label)

    def _update_edit_buttons(self) -> None:
        """Update save/discard button states based on model dirty state."""
        dirty = self.model.is_dirty()
        self.save_btn.setEnabled(dirty)
        self.discard_btn.setEnabled(dirty)

    def _install_header_hover(self) -> None:
        """Install event filter on the horizontal header to show column comments on hover."""
        header = self.table_view.horizontalHeader()
        header.setMouseTracking(True)
        header.installEventFilter(self)

    def eventFilter(self, obj, event) -> bool:
        """Show/hide tooltip when hovering over table header."""
        header = self.table_view.horizontalHeader()
        if obj is header and event.type() == event.Type.MouseMove:
            pos = event.pos()
            idx = header.logicalIndexAt(pos)
            if idx >= 0 and idx < len(self.model._columns):
                col_name = self.model._columns[idx]
                comment = self._column_comments.get(col_name, "")
                if comment:
                    QToolTip.showText(event.globalPosition().toPoint(), comment, self.table_view)
                else:
                    QToolTip.hideText()
            else:
                QToolTip.hideText()
        return super().eventFilter(obj, event)

    def load_table(self, table_name: str) -> None:
        if not self.connection_manager.db_connection:
            QMessageBox.warning(self, self.tr("dialogs", "prompt"), self.tr("dialogs", "not_connected_warn"))
            return

        # Check for unsaved changes before loading new table
        if self.model.is_dirty():
            if not self._handle_unsaved_changes():
                return

        self.current_table = table_name
        self._offset = 0
        self.table_label.setText(self.tr("data_browser", "table_label").format(table=table_name))
        logger.info("Loading table data: %s", table_name)
        self._fetch_comments()
        self._fetch_data()

    def _fetch_comments(self) -> None:
        """Fetch column comments for the current table."""
        if not self.current_table:
            return
        executor = QueryExecutor(self.connection_manager.db_connection)
        crud = CRUDService(executor)
        try:
            schema = crud.get_schema(self.current_table)
            self._column_comments = {col.name: col.comment for col in schema.columns if col.comment}
            self._primary_keys = schema.primary_keys
        except Exception:
            self._column_comments = {}
            self._primary_keys = []

    def _fetch_data(self) -> None:
        if not self.connection_manager.db_connection:
            return

        # Cancel any running query
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._worker.wait()

        dialect = self.connection_manager.db_connection.get_dialect()
        sql = f"SELECT * FROM {dialect.format_table_ref(self.current_table)} LIMIT {self._limit} OFFSET {self._offset}"

        self._worker = QueryWorker(dialect, sql)
        self._worker.finished.connect(self._on_fetch_finished)
        self._worker.progress.connect(lambda m: self.status_label.setText(m))
        self._worker.error.connect(self._on_fetch_error)

        self.status_label.setText("Loading...")
        self.prev_btn.setEnabled(False)
        self.next_btn.setEnabled(False)
        self._worker.start()

    def _on_fetch_finished(self, result) -> None:
        """Handle fetch result."""
        self.prev_btn.setEnabled(True)
        self.next_btn.setEnabled(True)
        self.status_label.setText("")

        if result.error_message:
            QMessageBox.critical(self, self.tr("data_browser", "error"), result.error_message)
            return

        # Fetch schema for type information
        executor = QueryExecutor(self.connection_manager.db_connection)
        crud = CRUDService(executor)
        try:
            schema = crud.get_schema(self.current_table)
        except Exception:
            schema = None

        self.model.set_result(result.columns, result.rows, table_schema=schema)
        self.page_label.setText(self.tr("data_browser", "page_label").format(
            page=self._offset // self._limit + 1, count=result.row_count
        ))
        self.edit_toggle_btn.setEnabled(True)
        self.add_row_btn.setEnabled(True)
        self.delete_row_btn.setEnabled(True)

        self._worker = None

    def _on_fetch_error(self, error_msg: str) -> None:
        """Handle fetch error."""
        self.prev_btn.setEnabled(True)
        self.next_btn.setEnabled(True)
        self.status_label.setText("")
        QMessageBox.critical(self, self.tr("data_browser", "error"), error_msg)
        self._worker = None

    def _prev_page(self) -> None:
        if self._offset > 0:
            if self.model.is_dirty() and not self._handle_unsaved_changes():
                return
            self._offset -= self._limit
            self._fetch_data()

    def _next_page(self) -> None:
        if self.model.rowCount() >= self._limit:
            if self.model.is_dirty() and not self._handle_unsaved_changes():
                return
            self._offset += self._limit
            self._fetch_data()

    def _handle_unsaved_changes(self) -> bool:
        """Prompt user about unsaved changes. Returns True if safe to proceed."""
        reply = QMessageBox.warning(
            self,
            self.tr("data_browser", "unsaved_changes"),
            self.tr("data_browser", "unsaved_msg"),
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
        )
        if reply == QMessageBox.Save:
            self._save_changes()
            return not self.model.is_dirty()
        elif reply == QMessageBox.Discard:
            self._discard_changes()
            return True
        return False  # Cancel

    def _toggle_edit_mode(self) -> None:
        """Toggle between edit and view mode."""
        editable = self.edit_toggle_btn.isChecked()
        self.model.set_editable(editable)
        if editable:
            self.edit_toggle_btn.setText(self.tr("data_browser", "read_only"))
        else:
            self.edit_toggle_btn.setText(self.tr("data_browser", "edit_mode"))

    def _add_row(self) -> None:
        """Add a new blank row at the end. Auto-enable edit mode if needed."""
        if not self.model._editable:
            self.edit_toggle_btn.setChecked(True)
            self.model.set_editable(True)
            self.edit_toggle_btn.setText(self.tr("data_browser", "read_only"))

        row_idx = self.model.add_new_row()
        # Scroll to the new row and start editing
        self.table_view.scrollToBottom()
        # Focus on first PK column if available, otherwise first column
        if self._primary_keys:
            pk_col = self._primary_keys[0]
            pk_idx = self.model._columns.index(pk_col) if pk_col in self.model._columns else 0
        else:
            pk_idx = 0
        index = self.model.index(row_idx, pk_idx)
        self.table_view.setCurrentIndex(index)
        self.table_view.edit(index)

    def _delete_row(self) -> None:
        """Delete the currently selected row(s). Handles both row selection and cell selection."""
        sel_model = self.table_view.selectionModel()
        if sel_model is None:
            return

        # First try row selection, then fall back to cell selection
        row_indexes = sel_model.selectedRows()
        if not row_indexes:
            cell_indexes = sel_model.selectedIndexes()
            if not cell_indexes:
                QMessageBox.information(self, self.tr("dialogs", "prompt"), "\u8bf7\u5148\u9009\u62e9\u8981\u5220\u9664\u7684\u884c\u6216\u5355\u5143\u683c\u3002")
                return
            # Extract unique row indices from cell selection, sorted descending for safe deletion
            row_indexes = sorted({index.row() for index in cell_indexes}, reverse=True)
        else:
            row_indexes = sorted({index.row() for index in row_indexes}, reverse=True)

        count = len(row_indexes)
        reply = QMessageBox.question(
            self,
            self.tr("data_browser", "confirm_delete"),
            self.tr("data_browser", "confirm_delete_msg").format(count=count),
        )
        if reply != QMessageBox.Yes:
            return

        # Delete in reverse order to maintain valid indices
        for row_idx in row_indexes:
            self.model.remove_row(row_idx)

    def _save_changes(self) -> None:
        """Save all pending changes to the database."""
        if not self.current_table:
            return

        # 1. Auto-generate PKs for new rows with NULL PKs (must happen BEFORE get_pending_changes)
        conflicts = self.model.fill_missing_pks()
        if conflicts:
            conflict_rows = ", ".join(str(c + 1) for c in conflicts)
            QMessageBox.critical(self, self.tr("data_browser", "error"),
                f"\u4e3b\u952e\u51b2\u7a81\uff1a\u65b0\u589e\u7684\u7b2c {conflict_rows} \u884c\u4e3b\u952e\u4e0e\u5df2\u6709\u6570\u636e\u91cd\u590d\u3002")
            self.model.clear_dirty()
            self._fetch_data()
            self.edit_toggle_btn.setChecked(False)
            self.edit_toggle_btn.setText(self.tr("data_browser", "edit_mode"))
            return

        changes = self.model.get_pending_changes()
        total = len(changes["updates"]) + len(changes["inserts"]) + len(changes["deletes"])
        if total == 0:
            QMessageBox.information(self, self.tr("dialogs", "prompt"), self.tr("data_browser", "no_changes"))
            return

        # Build confirmation message
        msg_parts = []
        if changes["updates"]:
            msg_parts.append(f"{len(changes['updates'])} \u4e2a\u5355\u5143\u66f4\u65b0")
        if changes["inserts"]:
            msg_parts.append(f"{len(changes['inserts'])} \u884c\u65b0\u589e")
        if changes["deletes"]:
            msg_parts.append(f"{len(changes['deletes'])} \u884c\u5220\u9664")
        msg = "\u3001".join(msg_parts)

        reply = QMessageBox.question(
            self,
            self.tr("data_browser", "confirm_save"),
            self.tr("data_browser", "confirm_save_msg").format(msg=msg),
        )
        if reply != QMessageBox.Yes:
            return

        executor = QueryExecutor(self.connection_manager.db_connection)
        crud = CRUDService(executor)
        success_count = 0
        error_count = 0

        # 1. Execute deletes
        for del_info in changes["deletes"]:
            pk_values = tuple(del_info["pk_values"].get(pk) for pk in self._primary_keys)
            try:
                schema = crud.get_schema(self.current_table)
                result = crud.delete_record(self.current_table, pk_values, schema)
                if result.error_message:
                    error_count += 1
                    QMessageBox.critical(self, self.tr("data_browser", "error"), self.tr("data_browser", "delete_fail").format(msg=result.error_message))
                    return
                success_count += 1
            except Exception as e:
                QMessageBox.critical(self, self.tr("data_browser", "error"), self.tr("data_browser", "delete_error").format(msg=e))
                return

        # 2. Execute updates
        for upd in changes["updates"]:
            row_idx = upd["row"]
            col = upd["column"]
            new_value = upd["new"]
            # Build full row data for the update
            row_data = self.model._rows[row_idx] if row_idx < len(self.model._rows) else {}
            pk_values = tuple(row_data.get(pk) for pk in self._primary_keys)
            update_data = {col: new_value}
            try:
                schema = crud.get_schema(self.current_table)
                result = crud.update_record(self.current_table, update_data, pk_values, schema)
                if result.error_message:
                    error_count += 1
                    QMessageBox.critical(self, self.tr("data_browser", "error"), self.tr("data_browser", "update_fail").format(msg=result.error_message))
                    return
                success_count += 1
            except Exception as e:
                QMessageBox.critical(self, self.tr("data_browser", "error"), self.tr("data_browser", "update_error").format(msg=e))
                return

        # 3. Execute inserts
        for ins in changes["inserts"]:
            row_data = ins["data"]
            # Filter out None values for columns that allow null
            insert_data = {k: v for k, v in row_data.items() if v is not None}
            try:
                result = crud.create_record(self.current_table, insert_data)
                if result.error_message:
                    error_count += 1
                    QMessageBox.critical(self, self.tr("data_browser", "error"), self.tr("data_browser", "insert_fail").format(msg=result.error_message))
                    return
                success_count += 1
            except Exception as e:
                QMessageBox.critical(self, self.tr("data_browser", "error"), self.tr("data_browser", "insert_error").format(msg=e))
                return

        self.model.clear_dirty()
        self._fetch_data()
        self.edit_toggle_btn.setChecked(False)
        self.edit_toggle_btn.setText(self.tr("data_browser", "edit_mode"))
        QMessageBox.information(self, self.tr("data_browser", "save_success").format(count=success_count))

    def _discard_changes(self) -> None:
        """Discard all local changes."""
        reply = QMessageBox.question(
            self,
            self.tr("data_browser", "discard_title"),
            self.tr("data_browser", "discard_msg"),
        )
        if reply != QMessageBox.Yes:
            return

        self.model.undo_changes()
        self._fetch_data()
        self.edit_toggle_btn.setChecked(False)
        self.edit_toggle_btn.setText(self.tr("data_browser", "edit_mode"))
