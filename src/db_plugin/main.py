import sys

from db_plugin.gui.app import create_application
from db_plugin.gui.main_window import MainWindow
from db_plugin.services.connection_manager import ConnectionManager


def main() -> None:
    app = create_application()
    connection_manager = ConnectionManager()
    window = MainWindow(connection_manager)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
