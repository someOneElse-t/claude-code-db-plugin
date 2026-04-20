"""Centralized stylesheet system for the DB plugin."""

# ── Color palette ──────────────────────────────────────────────────────────
PRIMARY = "#4A90D9"
PRIMARY_HOVER = "#357ABD"
PRIMARY_DISABLED = "#8DB4DD"

SUCCESS = "#2E7D32"
WARNING = "#F57F17"
ERROR = "#C62828"

BACKGROUND_LIGHT = "#F5F5F5"
BACKGROUND_DARK = "#2B2B2B"

TEXT_PRIMARY = "#212121"
TEXT_SECONDARY = "#757575"
TEXT_ON_PRIMARY = "#FFFFFF"

BORDER = "#BDBDBD"
BORDER_LIGHT = "#E0E0E0"

TABLE_HEADER_BG = "#ECEFF1"
TABLE_ROW_ALT = "#FAFAFA"
TABLE_ROW_HOVER = "#E3F2FD"
TABLE_SELECTED = "#BBDEFB"

DIRTY_BG = "#FFFFCC"
NEW_ROW_BG = "#E8F5E9"

TAB_ACTIVE = "#FFFFFF"
TAB_INACTIVE = "#E0E0E0"

DOCK_TITLE_BG = PRIMARY
DOCK_TITLE_TEXT = TEXT_ON_PRIMARY


def get_light_stylesheet() -> str:
    """Return the global light mode QSS stylesheet."""
    return f"""
/* ── Global ──────────────────────────────────────────────────────────── */
QWidget {{
    font-size: 13px;
    color: {TEXT_PRIMARY};
}}

QPushButton {{
    background-color: {PRIMARY};
    color: {TEXT_ON_PRIMARY};
    border: none;
    border-radius: 4px;
    padding: 6px 16px;
    font-weight: bold;
}}
QPushButton:hover {{
    background-color: {PRIMARY_HOVER};
}}
QPushButton:disabled {{
    background-color: {PRIMARY_DISABLED};
}}
QPushButton:pressed {{
    background-color: #2C5F8A;
}}

/* ── Tables ──────────────────────────────────────────────────────────── */
QTableView {{
    gridline-color: {BORDER_LIGHT};
    background-color: #FFFFFF;
    selection-background-color: {TABLE_SELECTED};
    alternate-background-color: {TABLE_ROW_ALT};
    border: 1px solid {BORDER};
    border-radius: 4px;
}}
QHeaderView::section {{
    background-color: {TABLE_HEADER_BG};
    padding: 4px 8px;
    border: none;
    border-bottom: 2px solid {PRIMARY};
    font-weight: bold;
    color: {TEXT_PRIMARY};
}}
QTableView QTableCornerButton::section {{
    background-color: {TABLE_HEADER_BG};
    border: none;
    border-bottom: 2px solid {PRIMARY};
}}

/* ── Tabs ────────────────────────────────────────────────────────────── */
QTabWidget::pane {{
    border: 1px solid {BORDER};
    border-radius: 4px;
}}
QTabBar::tab {{
    background: {TAB_INACTIVE};
    padding: 8px 20px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}}
QTabBar::tab:selected {{
    background: {TAB_ACTIVE};
    border-bottom: 2px solid {PRIMARY};
    font-weight: bold;
}}
QTabBar::tab:hover:!selected {{
    background: #EEEEEE;
}}

/* ── Toolbars ────────────────────────────────────────────────────────── */
QToolBar {{
    background-color: {BACKGROUND_LIGHT};
    border-bottom: 1px solid {BORDER};
    spacing: 4px;
    padding: 4px;
}}
QToolBar QToolButton {{
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 4px;
    padding: 6px 10px;
    color: {TEXT_PRIMARY};
}}
QToolBar QToolButton:hover {{
    background-color: {TABLE_ROW_HOVER};
    border-color: {PRIMARY};
}}
QToolBar QToolButton:pressed {{
    background-color: {TABLE_SELECTED};
}}

/* ── Menus ───────────────────────────────────────────────────────────── */
QMenuBar {{
    background-color: {BACKGROUND_LIGHT};
    border-bottom: 1px solid {BORDER};
}}
QMenuBar::item:selected {{
    background-color: {TABLE_ROW_HOVER};
    border-radius: 4px;
}}
QMenu {{
    background-color: #FFFFFF;
    border: 1px solid {BORDER};
    border-radius: 4px;
}}
QMenu::item:selected {{
    background-color: {TABLE_ROW_HOVER};
}}

/* ── Dock widgets ────────────────────────────────────────────────────── */
QDockWidget {{
    border: 1px solid {BORDER};
}}
QDockWidget::title {{
    background-color: {DOCK_TITLE_BG};
    color: {DOCK_TITLE_TEXT};
    padding: 6px 8px;
    font-weight: bold;
}}

/* ── Status bar ──────────────────────────────────────────────────────── */
QStatusBar {{
    background-color: {BACKGROUND_LIGHT};
    border-top: 1px solid {BORDER};
    color: {TEXT_SECONDARY};
}}

/* ── Group boxes ─────────────────────────────────────────────────────── */
QGroupBox {{
    border: 1px solid {BORDER};
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 16px;
    font-weight: bold;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 6px;
}}

/* ── Line edits ──────────────────────────────────────────────────────── */
QLineEdit {{
    border: 1px solid {BORDER};
    border-radius: 4px;
    padding: 4px 8px;
}}
QLineEdit:focus {{
    border-color: {PRIMARY};
}}

/* ── Combo boxes ─────────────────────────────────────────────────────── */
QComboBox {{
    border: 1px solid {BORDER};
    border-radius: 4px;
    padding: 4px 8px;
}}
QComboBox:focus {{
    border-color: {PRIMARY};
}}
QComboBox::drop-down {{
    border: none;
    padding-right: 6px;
}}

/* ── List widget ─────────────────────────────────────────────────────── */
QListWidget {{
    border: 1px solid {BORDER};
    border-radius: 4px;
    background-color: #FFFFFF;
    alternate-background-color: {TABLE_ROW_ALT};
}}
QListWidget::item:selected {{
    background-color: {TABLE_SELECTED};
}}

/* ── Tree widget ─────────────────────────────────────────────────────── */
QTreeWidget {{
    border: none;
    background-color: {BACKGROUND_LIGHT};
    alternate-background-color: {TABLE_ROW_ALT};
}}
QTreeWidget::item:hover {{
    background-color: {TABLE_ROW_HOVER};
}}
QTreeWidget::item:selected {{
    background-color: {TABLE_SELECTED};
}}

/* ── Spin box ────────────────────────────────────────────────────────── */
QSpinBox {{
    border: 1px solid {BORDER};
    border-radius: 4px;
    padding: 4px 8px;
}}
QSpinBox:focus {{
    border-color: {PRIMARY};
}}

/* ── Progress dialog ─────────────────────────────────────────────────── */
QProgressDialog {{
    background-color: #FFFFFF;
    border-radius: 8px;
}}
QProgressBar {{
    border: 1px solid {BORDER};
    border-radius: 4px;
    text-align: center;
}}
QProgressBar::chunk {{
    background-color: {PRIMARY};
    border-radius: 3px;
}}

/* ── Labels ──────────────────────────────────────────────────────────── */
QLabel {{
    color: {TEXT_PRIMARY};
}}

/* ── Splitter ────────────────────────────────────────────────────────── */
QSplitter::handle {{
    background-color: {BORDER};
    border-radius: 2px;
}}
QSplitter::handle:horizontal {{
    width: 2px;
}}
QSplitter::handle:vertical {{
    height: 2px;
}}
"""
