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


def get_dark_stylesheet() -> str:
    """Return the global dark mode QSS stylesheet."""
    return f"""
QWidget {{
    font-size: 13px;
    color: #E0E0E0;
    background-color: {BACKGROUND_DARK};
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

QTableView {{
    gridline-color: #424242;
    background-color: #1E1E1E;
    selection-background-color: {TABLE_SELECTED};
    alternate-background-color: #252525;
    border: 1px solid #424242;
    border-radius: 4px;
}}
QHeaderView::section {{
    background-color: #333333;
    padding: 4px 8px;
    border: none;
    border-bottom: 2px solid {PRIMARY};
    font-weight: bold;
    color: #E0E0E0;
}}
QTableView QTableCornerButton::section {{
    background-color: #333333;
    border: none;
    border-bottom: 2px solid {PRIMARY};
}}

QTabWidget::pane {{
    border: 1px solid #424242;
    border-radius: 4px;
}}
QTabBar::tab {{
    background: #333333;
    padding: 8px 20px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}}
QTabBar::tab:selected {{
    background: {BACKGROUND_DARK};
    border-bottom: 2px solid {PRIMARY};
    font-weight: bold;
}}
QTabBar::tab:hover:!selected {{
    background: #3D3D3D;
}}

QToolBar {{
    background-color: #333333;
    border-bottom: 1px solid #424242;
    spacing: 4px;
    padding: 4px;
}}
QToolBar QToolButton {{
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 4px;
    padding: 6px 10px;
    color: #E0E0E0;
}}
QToolBar QToolButton:hover {{
    background-color: #3D3D3D;
    border-color: {PRIMARY};
}}
QToolBar QToolButton:pressed {{
    background-color: {TABLE_SELECTED};
}}

QMenuBar {{
    background-color: #333333;
    border-bottom: 1px solid #424242;
}}
QMenuBar::item:selected {{
    background-color: #3D3D3D;
    border-radius: 4px;
}}
QMenu {{
    background-color: #2B2B2B;
    border: 1px solid #424242;
    border-radius: 4px;
    color: #E0E0E0;
}}
QMenu::item:selected {{
    background-color: #3D3D3D;
}}

QDockWidget {{
    border: 1px solid #424242;
}}
QDockWidget::title {{
    background-color: {DOCK_TITLE_BG};
    color: {DOCK_TITLE_TEXT};
    padding: 6px 8px;
    font-weight: bold;
}}

QStatusBar {{
    background-color: #333333;
    border-top: 1px solid #424242;
    color: #9E9E9E;
}}

QGroupBox {{
    border: 1px solid #424242;
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

QLineEdit {{
    border: 1px solid #424242;
    border-radius: 4px;
    padding: 4px 8px;
    background-color: #1E1E1E;
    color: #E0E0E0;
}}
QLineEdit:focus {{
    border-color: {PRIMARY};
}}

QComboBox {{
    border: 1px solid #424242;
    border-radius: 4px;
    padding: 4px 8px;
    background-color: #1E1E1E;
    color: #E0E0E0;
}}
QComboBox:focus {{
    border-color: {PRIMARY};
}}
QComboBox::drop-down {{
    border: none;
    padding-right: 6px;
}}
QComboBox QAbstractItemView {{
    background-color: #1E1E1E;
    color: #E0E0E0;
    selection-background-color: {PRIMARY};
}}

QListWidget {{
    border: 1px solid #424242;
    border-radius: 4px;
    background-color: #1E1E1E;
    alternate-background-color: #252525;
    color: #E0E0E0;
}}
QListWidget::item:selected {{
    background-color: {TABLE_SELECTED};
}}

QTreeWidget {{
    border: none;
    background-color: {BACKGROUND_DARK};
    alternate-background-color: #252525;
    color: #E0E0E0;
}}
QTreeWidget::item:hover {{
    background-color: #3D3D3D;
}}
QTreeWidget::item:selected {{
    background-color: {TABLE_SELECTED};
}}

QSpinBox {{
    border: 1px solid #424242;
    border-radius: 4px;
    padding: 4px 8px;
    background-color: #1E1E1E;
    color: #E0E0E0;
}}
QSpinBox:focus {{
    border-color: {PRIMARY};
}}

QProgressDialog {{
    background-color: #2B2B2B;
    border-radius: 8px;
    color: #E0E0E0;
}}
QProgressBar {{
    border: 1px solid #424242;
    border-radius: 4px;
    text-align: center;
    background-color: #1E1E1E;
}}
QProgressBar::chunk {{
    background-color: {PRIMARY};
    border-radius: 3px;
}}

QLabel {{
    color: #E0E0E0;
}}

QSplitter::handle {{
    background-color: #424242;
    border-radius: 2px;
}}
QSplitter::handle:horizontal {{
    width: 2px;
}}
QSplitter::handle:vertical {{
    height: 2px;
}}
"""
