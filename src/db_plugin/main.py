import sys
import traceback

from db_plugin.core.logger import setup_logger
from db_plugin.gui.app import create_application
from db_plugin.gui.main_window import MainWindow
from db_plugin.services.connection_manager import ConnectionManager

logger = setup_logger()


def main() -> None:
    try:
        logger.info("Starting DB Plugin application")
        app = create_application()
        connection_manager = ConnectionManager()
        window = MainWindow(connection_manager)
        window.show()
        logger.info("Application window displayed")
        sys.exit(app.exec())
    except Exception:
        logger.exception("Fatal error during application startup: %s", traceback.format_exc())
        raise


if __name__ == "__main__":
    main()
