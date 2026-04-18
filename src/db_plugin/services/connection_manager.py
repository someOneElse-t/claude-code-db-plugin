import json
import logging
from pathlib import Path
from base64 import urlsafe_b64encode, urlsafe_b64decode

from cryptography.fernet import Fernet

from db_plugin.core.connection import DatabaseConnection
from db_plugin.models.config import ConnectionConfig

logger = logging.getLogger(__name__)


DEFAULT_CONFIG_DIR = Path.home() / ".claude-code-db-plugin"
DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "connections.json"
KEY_FILE = DEFAULT_CONFIG_DIR / ".key"


def _get_or_create_key() -> bytes:
    """Load existing encryption key or generate a new one."""
    if KEY_FILE.exists():
        return urlsafe_b64decode(KEY_FILE.read_bytes())
    key = Fernet.generate_key()
    KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
    KEY_FILE.write_bytes(urlsafe_b64encode(key))
    return key


_cipher = Fernet(_get_or_create_key())


def _encrypt(text: str) -> str:
    """Encrypt plaintext and return base64-encoded ciphertext."""
    return _cipher.encrypt(text.encode()).decode()


def _decrypt(token: str) -> str:
    """Decrypt a base64-encoded Fernet token."""
    return _cipher.decrypt(token.encode()).decode()


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
        logger.info("Added connection config: %s", config.name)

    def remove(self, name: str) -> None:
        self._connections.pop(name, None)
        if self._active_name == name:
            self._active_name = None
            self._db_connection = None
        self._save()
        logger.info("Removed connection config: %s", name)

    def list(self) -> list[ConnectionConfig]:
        return list(self._connections.values())

    def get(self, name: str) -> ConnectionConfig | None:
        return self._connections.get(name)

    def test_connection(self, config: ConnectionConfig) -> tuple[bool, str]:
        """Try to connect and return (success, message)."""
        logger.info("Testing connection to %s@%s:%s/%s", config.dialect_name, config.host, config.port, config.database)
        try:
            conn = DatabaseConnection(config)
            conn.connect()
            conn.close()
            logger.info("Connection test successful: %s", config.name)
            return True, "Connection successful"
        except Exception as e:
            logger.warning("Connection test failed: %s", e)
            return False, str(e)

    def connect(self, name: str) -> tuple[bool, str]:
        """Connect to a saved connection by name."""
        config = self.get(name)
        if config is None:
            return False, f"Connection '{name}' not found"
        try:
            if self._db_connection:
                self._db_connection.close()
                logger.info("Closed previous active connection")
            self._db_connection = DatabaseConnection(config)
            self._db_connection.connect()
            self._active_name = name
            logger.info("Connected to %s (%s@%s:%s/%s)", name, config.dialect_name, config.host, config.port, config.database)
            return True, f"Connected to {name}"
        except Exception as e:
            logger.error("Failed to connect to %s: %s", name, e)
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
            logger.info("Disconnected from active connection")

    def _load(self) -> None:
        if self._config_file.exists():
            logger.info("Loading connection configs from %s", self._config_file)
            data = json.loads(self._config_file.read_text(encoding="utf-8"))
            for item in data:
                password = item.get("password", "")
                if password:
                    password = _decrypt(password)
                config = ConnectionConfig(**{**item, "password": password})
                self._connections[config.name] = config
            logger.info("Loaded %d connection config(s)", len(self._connections))
        else:
            logger.info("No config file found at %s", self._config_file)

    def _save(self) -> None:
        self._config_file.parent.mkdir(parents=True, exist_ok=True)
        data = [
            {
                "name": c.name,
                "dialect_name": c.dialect_name,
                "host": c.host,
                "port": c.port,
                "username": c.username,
                "password": _encrypt(c.password) if c.password else "",
                "database": c.database,
                "extra_params": c.extra_params,
            }
            for c in self._connections.values()
        ]
        self._config_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
        logger.info("Saved %d connection config(s) to %s", len(self._connections), self._config_file)
