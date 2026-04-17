from db_plugin.dialects import get_dialect
from db_plugin.dialects.dialect_base import DialectBase
from db_plugin.models.config import ConnectionConfig


class DatabaseConnection:
    """Manages a database connection lifecycle."""

    def __init__(self, config: ConnectionConfig):
        self.config = config
        self.dialect: DialectBase = get_dialect(config.dialect_name)

    @property
    def is_connected(self) -> bool:
        return self.dialect._connection is not None

    def connect(self) -> None:
        self.dialect.connect(self.config)

    def close(self) -> None:
        self.dialect.close()

    def get_dialect(self) -> DialectBase:
        return self.dialect
