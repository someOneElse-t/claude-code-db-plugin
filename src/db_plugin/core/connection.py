import logging

from db_plugin.dialects import get_dialect
from db_plugin.dialects.dialect_base import DialectBase
from db_plugin.models.config import ConnectionConfig

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Manages a database connection lifecycle."""

    def __init__(self, config: ConnectionConfig):
        self.config = config
        self.dialect: DialectBase = get_dialect(config.dialect_name)
        logger.info("Created DatabaseConnection for %s (dialect=%s)", config.database, config.dialect_name)

    @property
    def is_connected(self) -> bool:
        return self.dialect._connection is not None

    def connect(self) -> None:
        logger.info("Connecting to %s@%s:%s/%s", self.config.dialect_name, self.config.host, self.config.port, self.config.database)
        self.dialect.connect(self.config)
        logger.info("Connection established")

    def close(self) -> None:
        self.dialect.close()
        logger.info("Connection closed")

    def get_dialect(self) -> DialectBase:
        return self.dialect
