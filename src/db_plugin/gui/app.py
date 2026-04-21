import sys

from PySide6.QtWidgets import QApplication

from db_plugin.gui.style import get_light_stylesheet, get_dark_stylesheet

_current_theme = "light"


def create_application() -> QApplication:
    """Create and configure the QApplication."""
    app = QApplication(sys.argv)
    app.setApplicationName("Claude Code DB Plugin")
    app.setApplicationVersion("0.1.0")
    app.setStyle("Fusion")
    apply_theme("light")
    return app


def apply_theme(theme: str) -> None:
    """Apply light or dark theme to the application."""
    global _current_theme
    _current_theme = theme
    app = QApplication.instance()
    if app:
        stylesheet = get_dark_stylesheet() if theme == "dark" else get_light_stylesheet()
        app.setStyleSheet(stylesheet)


def toggle_theme() -> str:
    """Toggle between light and dark themes. Returns the new theme name."""
    global _current_theme
    new_theme = "dark" if _current_theme == "light" else "light"
    apply_theme(new_theme)
    return new_theme


def get_current_theme() -> str:
    return _current_theme
