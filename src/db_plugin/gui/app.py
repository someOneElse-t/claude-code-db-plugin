import sys

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt


def create_application() -> QApplication:
    """Create and configure the QApplication."""
    app = QApplication(sys.argv)
    app.setApplicationName("Claude Code DB Plugin")
    app.setApplicationVersion("0.1.0")
    app.setStyle("Fusion")  # Consistent cross-platform look
    return app
