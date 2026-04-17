import json
import os
from pathlib import Path

from db_plugin.core.connection import DatabaseConnection
from db_plugin.models.config import ConnectionConfig


DEFAULT_CONFIG_DIR = Path.home() / ".claude-code-db-plugin"
DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "connections.json"


class ConnectionManager:
    """Manages multiple database connections with persistence."""

    def __init__(self, config_file: str | None = None):
        self._config_file = Path(config_file) if config_file else DEFAULT_CONFIG_FILE
        self._connections: dict[str, ConnectionConfig] = {}
        self._active_name: str | None = None
        self._db_connection: DatabaseConnection | None = None
        self._load()

    @property
    def active_connection_name(self) -> str | None:
        return self._active_name

    @property
    def db_connection(self) -> DatabaseConnection | None:
        return self._db_connection

    def add(self, config: ConnectionConfig) -> None:
        self._connections[config.name] = config
        self._save()

    def remove(self, name: str) -> None:
        self._connections.pop(name, None)
        if self._active_name == name:
            self._active_name = None
            self._db_connection = None
        self._save()

    def list(self) -> list[ConnectionConfig]:
        return list(self._connections.values())

    def get(self, name: str) -> ConnectionConfig | None:
        return self._connections.get(name)

    def test_connection(self, config: ConnectionConfig) -> tuple[bool, str]:
        """Try to connect and return (success, message)."""
        try:
            conn = DatabaseConnection(config)
            conn.connect()
            conn.close()
            return True, "Connection successful"
        except Exception as e:
            return False, str(e)

    def connect(self, name: str) -> tuple[bool, str]:
        """Connect to a saved connection by name."""
        config = self.get(name)
        if config is None:
            return False, f"Connection '{name}' not found"
        try:
            if self._db_connection:
                self._db_connection.close()
            self._db_connection = DatabaseConnection(config)
            self._db_connection.connect()
            self._active_name = name
            return True, f"Connected to {name}"
        except Exception as e:
            return False, str(e)

    def switch_connection(self, name: str) -> None:
        """Switch active connection to another saved connection."""
        if name not in self._connections:
            raise ValueError(f"Connection '{name}' not found")
        success, message = self.connect(name)
        if not success:
            raise RuntimeError(f"Failed to connect: {message}")

    def disconnect(self) -> None:
        """Disconnect from the current active connection."""
        if self._db_connection:
            self._db_connection.close()
            self._db_connection = None
            self._active_name = None

    def _load(self) -> None:
        if self._config_file.exists():
            data = json.loads(self._config_file.read_text(encoding="utf-8"))
            for item in data:
                config = ConnectionConfig(**item)
                self._connections[config.name] = config

    def _save(self) -> None:
        self._config_file.parent.mkdir(parents=True, exist_ok=True)
        data = [
            {
                "name": c.name,
                "dialect_name": c.dialect_name,
                "host": c.host,
                "port": c.port,
                "username": c.username,
                "password": c.password,
                "database": c.database,
                "extra_params": c.extra_params,
            }
            for c in self._connections.values()
        ]
        self._config_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
